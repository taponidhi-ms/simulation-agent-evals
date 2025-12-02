"""Transcript downloader module for Dynamics 365 Customer Service."""

import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone

from . import config
from .dataverse_client import DataverseClient
from .validators import escape_xml_value, is_safe_path_component, validate_guid


class TranscriptDownloader:
    """Downloads and saves transcripts from Dynamics 365 conversations."""

    def __init__(
        self,
        client: DataverseClient,
        workstream_id: str = config.WORKSTREAM_ID,
        output_folder: str = config.OUTPUT_FOLDER,
        days_to_fetch: int = config.DAYS_TO_FETCH,
        max_content_size: int = config.MAX_CONTENT_SIZE,
    ):
        """
        Initialize the transcript downloader.

        Args:
            client: Dataverse client instance.
            workstream_id: ID of the workstream to fetch conversations from.
            output_folder: Folder to save transcript files.
            days_to_fetch: Number of days to look back for conversations.
            max_content_size: Maximum size in bytes for base64 content.
        """
        # Validate workstream_id is a valid GUID
        self.workstream_id = validate_guid(workstream_id, "workstream_id")
        self.client = client
        self.output_folder = os.path.abspath(output_folder)
        self.days_to_fetch = days_to_fetch
        self.max_content_size = max_content_size

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def get_conversations(self) -> list[dict]:
        """
        Fetch conversations (live work items) from the specified workstream.

        Returns:
            List of conversation records.
        """
        # Calculate the date threshold
        date_threshold = datetime.now(timezone.utc) - timedelta(days=self.days_to_fetch)
        date_str = date_threshold.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Escape values for safe XML usage (workstream_id already validated as GUID)
        safe_workstream_id = escape_xml_value(self.workstream_id)
        safe_date_str = escape_xml_value(date_str)

        # Build FetchXML query with escaped values
        fetch_xml = f"""
        <fetch>
            <entity name='msdyn_ocliveworkitem'>
                <attribute name='msdyn_ocliveworkitemid' />
                <attribute name='msdyn_title' />
                <attribute name='createdon' />
                <attribute name='msdyn_liveworkstreamid' />
                <filter type='and'>
                    <condition attribute='msdyn_liveworkstreamid' operator='eq' value='{safe_workstream_id}'/>
                    <condition attribute='createdon' operator='ge' value='{safe_date_str}'/>
                </filter>
                <order attribute='createdon' descending='true' />
            </entity>
        </fetch>
        """

        print(f"Fetching conversations from workstream {self.workstream_id}...")
        print(f"Looking for conversations created in the last {self.days_to_fetch} days...")

        conversations = self.client.execute_fetch_xml(
            entity_name="msdyn_ocliveworkitem",
            fetch_xml=fetch_xml,
        )

        print(f"Found {len(conversations)} conversations.")
        return conversations

    def get_transcript_for_conversation(self, conversation_id: str) -> dict | None:
        """
        Fetch the transcript record for a conversation.

        Args:
            conversation_id: The ID of the live work item (conversation).

        Returns:
            Transcript record or None if not found.
        """
        # Validate conversation_id is a valid GUID to prevent injection
        validated_id = validate_guid(conversation_id, "conversation_id")

        # Query transcripts linked to this conversation
        # The field linking transcript to liveworkitem is _msdyn_liveworkitemid_value
        # OData GUID values don't need quotes when used directly
        filter_query = f"_msdyn_liveworkitemid_value eq '{validated_id}'"

        transcripts = self.client.query_entities(
            entity_name="msdyn_transcript",
            filter_query=filter_query,
            select=["msdyn_transcriptid", "msdyn_name", "createdon"],
        )

        if transcripts:
            return transcripts[0]
        return None

    def get_annotation_content(self, transcript_id: str) -> str | None:
        """
        Fetch the annotation (document body) for a transcript.

        The annotation ID is the same as the transcript ID.

        Args:
            transcript_id: The ID of the transcript.

        Returns:
            Decoded transcript content as string, or None if not found.
        """
        try:
            # Validate transcript_id is a valid GUID to prevent injection
            validated_id = validate_guid(transcript_id, "transcript_id")

            # The annotation's objectid should reference the transcript
            filter_query = f"_objectid_value eq '{validated_id}'"

            annotations = self.client.query_entities(
                entity_name="annotation",
                filter_query=filter_query,
                select=["annotationid", "documentbody", "filename", "mimetype"],
            )

            if not annotations:
                return None

            annotation = annotations[0]
            document_body = annotation.get("documentbody")

            if not document_body:
                return None

            # Check content size before decoding to prevent memory issues
            if len(document_body) > self.max_content_size:
                print(f"  Warning: Content size exceeds limit ({len(document_body)} bytes)")
                return None

            # Decode base64 content
            decoded_bytes = base64.b64decode(document_body)
            decoded_str = decoded_bytes.decode("utf-8")

            # Clean up escaped characters
            decoded_str = self._unescape_json_string(decoded_str)

            return decoded_str

        except Exception as e:
            print(f"Error fetching annotation for transcript {transcript_id}: {e}")
            return None

    def _unescape_json_string(self, content: str) -> str:
        """
        Unescape a JSON string that may have extra escape characters.

        Args:
            content: The string to unescape.

        Returns:
            Unescaped string.
        """
        # Handle common escape sequences
        content = content.replace('\\"', '"')
        content = content.replace("\\\\", "\\")
        content = content.replace("\\n", "\n")
        content = content.replace("\\r", "\r")
        content = content.replace("\\t", "\t")

        return content

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename.

        Args:
            name: The original name.

        Returns:
            Sanitized filename.
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Remove any path traversal attempts
        sanitized = sanitized.replace("..", "_")
        # Limit length
        return sanitized[:100]

    def save_transcript(
        self,
        conversation_id: str,
        content: str,
        conversation_title: str | None = None,
        created_on: str | None = None,
    ) -> str:
        """
        Save transcript content to a JSON file.

        Args:
            conversation_id: The conversation ID.
            content: The transcript content.
            conversation_title: Optional title for the conversation.
            created_on: Optional creation date.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If the resulting path is outside the output folder.
        """
        # Validate conversation_id format
        validated_id = validate_guid(conversation_id, "conversation_id")

        # Build filename
        timestamp = ""
        if created_on:
            try:
                # Parse ISO format datetime
                dt = datetime.fromisoformat(created_on.replace("Z", "+00:00"))
                timestamp = dt.strftime("%Y%m%d_%H%M%S")
            except ValueError:
                timestamp = "unknown"

        title_part = ""
        if conversation_title:
            sanitized_title = self._sanitize_filename(conversation_title)
            # Additional validation for path safety
            if is_safe_path_component(sanitized_title):
                title_part = f"_{sanitized_title}"

        filename = f"transcript_{timestamp}_{validated_id[:8]}{title_part}.json"
        filepath = os.path.abspath(os.path.join(self.output_folder, filename))

        # Verify the file path is within the output folder (prevent path traversal)
        if not filepath.startswith(self.output_folder):
            raise ValueError(f"Path traversal detected: {filepath}")

        # Try to parse as JSON to format nicely
        try:
            json_content = json.loads(content)
            formatted_content = json.dumps(json_content, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            formatted_content = content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        return filepath

    def download_all_transcripts(self) -> dict:
        """
        Download all transcripts for conversations in the workstream.

        Returns:
            Summary dictionary with success/failure counts.
        """
        summary = {
            "total_conversations": 0,
            "transcripts_found": 0,
            "transcripts_downloaded": 0,
            "errors": 0,
            "files": [],
        }

        # Get all conversations
        conversations = self.get_conversations()
        summary["total_conversations"] = len(conversations)

        for i, conversation in enumerate(conversations, 1):
            conv_id = conversation.get("msdyn_ocliveworkitemid")
            conv_title = conversation.get("msdyn_title", "")
            created_on = conversation.get("createdon", "")

            print(f"\nProcessing conversation {i}/{len(conversations)}: {conv_id}")

            # Get transcript for this conversation
            transcript = self.get_transcript_for_conversation(conv_id)

            if not transcript:
                print(f"  No transcript found for conversation {conv_id}")
                continue

            summary["transcripts_found"] += 1
            transcript_id = transcript.get("msdyn_transcriptid")

            # Get annotation content
            content = self.get_annotation_content(transcript_id)

            if not content:
                print(f"  No annotation content found for transcript {transcript_id}")
                summary["errors"] += 1
                continue

            # Save transcript
            try:
                filepath = self.save_transcript(
                    conversation_id=conv_id,
                    content=content,
                    conversation_title=conv_title,
                    created_on=created_on,
                )
                summary["transcripts_downloaded"] += 1
                summary["files"].append(filepath)
                print(f"  Saved: {filepath}")
            except Exception as e:
                print(f"  Error saving transcript: {e}")
                summary["errors"] += 1

        return summary
