"""Transcript downloader module for Dynamics 365 Customer Service."""

import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone

from . import config
from .dataverse_client import DataverseClient
from .models import Annotation, Conversation, DownloadSummary, Transcript
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
        max_conversations: int | None = None,
    ):
        """
        Initialize the transcript downloader.

        Args:
            client: Dataverse client instance.
            workstream_id: ID of the workstream to fetch conversations from.
            output_folder: Folder to save transcript files.
            days_to_fetch: Number of days to look back for conversations.
            max_content_size: Maximum size in bytes for base64 content.
            max_conversations: Maximum number of conversations to download (required, 1-1000).

        Raises:
            ValueError: If max_conversations is not set or is outside the valid range.
        """
        # Validate workstream_id is a valid GUID
        self.workstream_id = validate_guid(workstream_id, "workstream_id")
        
        # Validate max_conversations
        if max_conversations is None:
            raise ValueError(
                "max_conversations is required. Please set D365_MAX_CONVERSATIONS environment variable "
                "or use --max-conversations argument (valid range: 1-1000)"
            )
        
        if not isinstance(max_conversations, int):
            raise ValueError(f"max_conversations must be an integer, got {type(max_conversations).__name__}")
        
        if max_conversations < 1 or max_conversations > 1000:
            raise ValueError(
                f"max_conversations must be between 1 and 1000, got {max_conversations}"
            )
        
        self.client = client
        self.output_folder = os.path.abspath(output_folder)
        self.days_to_fetch = days_to_fetch
        self.max_content_size = max_content_size
        self.max_conversations = max_conversations

        # Ensure output folder exists
        os.makedirs(self.output_folder, exist_ok=True)

    def get_conversations(self) -> list[Conversation]:
        """
        Fetch conversations (live work items) from the specified workstream.

        Returns:
            List of Conversation objects.
        """
        # Calculate the date threshold
        date_threshold = datetime.now(timezone.utc) - timedelta(days=self.days_to_fetch)
        date_str = date_threshold.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Escape values for safe XML usage (workstream_id already validated as GUID)
        safe_workstream_id = escape_xml_value(self.workstream_id)
        safe_date_str = escape_xml_value(date_str)

        # Build FetchXML query with escaped values
        fetch_xml = f"""
        <fetch top='{self.max_conversations}'>
            <entity name='msdyn_ocliveworkitem'>
                <attribute name='msdyn_ocliveworkitemid' />
                <attribute name='msdyn_title' />
                <attribute name='createdon' />
                <attribute name='msdyn_liveworkstreamid' />
                <attribute name='statecode' />
                <filter type='and'>
                    <condition attribute='msdyn_liveworkstreamid' operator='eq' value='{safe_workstream_id}'/>
                    <condition attribute='createdon' operator='ge' value='{safe_date_str}'/>
                    <condition attribute='statecode' operator='eq' value='1'/>
                </filter>
                <order attribute='createdon' descending='true' />
            </entity>
        </fetch>
        """

        print(f"Fetching conversations from workstream {self.workstream_id}...")
        print(f"Looking for closed conversations created in the last {self.days_to_fetch} days...")
        print(f"Limiting query to {self.max_conversations} conversations...")

        raw_conversations = self.client.execute_fetch_xml(
            entity_name="msdyn_ocliveworkitem",
            fetch_xml=fetch_xml,
        )

        conversations = [Conversation.from_dict(c) for c in raw_conversations]
        print(f"Found {len(conversations)} conversations.")
        return conversations

    def get_transcript_for_conversation(self, conversation_id: str) -> Transcript | None:
        """
        Fetch the transcript record for a conversation using FetchXML.

        Args:
            conversation_id: The ID of the live work item (conversation).

        Returns:
            Transcript object or None if not found.
        """
        # Validate conversation_id is a valid GUID to prevent injection
        validated_id = validate_guid(conversation_id, "conversation_id")
        safe_conversation_id = escape_xml_value(validated_id)

        # Build FetchXML query to fetch transcript by conversation ID
        fetch_xml = f"""
        <fetch top='1'>
            <entity name='msdyn_transcript'>
                <attribute name='msdyn_transcriptid' />
                <attribute name='msdyn_name' />
                <attribute name='createdon' />
                <filter type='and'>
                    <condition attribute='msdyn_liveworkitemid' operator='eq' value='{safe_conversation_id}'/>
                </filter>
            </entity>
        </fetch>
        """

        raw_transcripts = self.client.execute_fetch_xml(
            entity_name="msdyn_transcript",
            fetch_xml=fetch_xml,
        )

        if raw_transcripts:
            return Transcript.from_dict(raw_transcripts[0])
        return None

    def get_annotation_for_transcript(self, transcript_id: str) -> Annotation | None:
        """
        Fetch the annotation record for a transcript using FetchXML.

        Args:
            transcript_id: The ID of the transcript.

        Returns:
            Annotation object or None if not found.
        """
        try:
            # Validate transcript_id is a valid GUID to prevent injection
            validated_id = validate_guid(transcript_id, "transcript_id")
            safe_transcript_id = escape_xml_value(validated_id)

            # Build FetchXML query to fetch annotation by transcript ID
            fetch_xml = f"""
            <fetch top='1'>
                <entity name='annotation'>
                    <attribute name='annotationid' />
                    <attribute name='documentbody' />
                    <attribute name='filename' />
                    <attribute name='mimetype' />
                    <filter type='and'>
                        <condition attribute='objectid' operator='eq' value='{safe_transcript_id}'/>
                    </filter>
                </entity>
            </fetch>
            """

            raw_annotations = self.client.execute_fetch_xml(
                entity_name="annotation",
                fetch_xml=fetch_xml,
            )

            if raw_annotations:
                return Annotation.from_dict(raw_annotations[0])
            return None

        except Exception as e:
            print(f"Error fetching annotation for transcript {transcript_id}: {e}")
            return None

    def decode_annotation_content(self, annotation: Annotation) -> str | None:
        """
        Decode the base64 document body from an annotation.

        Args:
            annotation: The Annotation object containing the document body.

        Returns:
            Decoded transcript content as string, or None if not available.
        """
        if not annotation.document_body:
            return None

        # Check content size before decoding to prevent memory issues
        if len(annotation.document_body) > self.max_content_size:
            print(f"  Warning: Content size exceeds limit ({len(annotation.document_body)} bytes)")
            return None

        try:
            # Decode base64 content
            decoded_bytes = base64.b64decode(annotation.document_body)
            decoded_str = decoded_bytes.decode("utf-8")

            # Clean up escaped characters
            decoded_str = self._unescape_json_string(decoded_str)

            return decoded_str
        except Exception as e:
            print(f"Error decoding annotation content: {e}")
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
        conversation: Conversation,
        content: str,
    ) -> str:
        """
        Save transcript content to a JSON file.

        Args:
            conversation: The Conversation object.
            content: The transcript content.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If the resulting path is outside the output folder.
        """
        # Validate conversation_id format
        validated_id = validate_guid(conversation.id, "conversation_id")

        # Build filename
        timestamp = ""
        if conversation.created_on:
            try:
                # Parse ISO format datetime
                dt = datetime.fromisoformat(conversation.created_on.replace("Z", "+00:00"))
                timestamp = dt.strftime("%Y%m%d_%H%M%S")
            except ValueError:
                timestamp = "unknown"

        title_part = ""
        if conversation.title:
            sanitized_title = self._sanitize_filename(conversation.title)
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

    def get_all_transcripts_for_conversations(
        self, conversation_ids: list[str]
    ) -> dict[str, Transcript]:
        """
        Fetch all transcripts for multiple conversations in a single query using FetchXML.

        Args:
            conversation_ids: List of conversation IDs to fetch transcripts for.

        Returns:
            Dictionary mapping conversation_id to Transcript object.
        """
        if not conversation_ids:
            return {}

        # Validate all conversation IDs
        validated_ids = [validate_guid(cid, "conversation_id") for cid in conversation_ids]
        
        # Build FetchXML with multiple conditions (using OR)
        conditions = [
            f"                    <condition attribute='msdyn_liveworkitemid' operator='eq' value='{escape_xml_value(conv_id)}'/>"
            for conv_id in validated_ids
        ]
        conditions_str = "\n".join(conditions)

        fetch_xml = f"""
        <fetch>
            <entity name='msdyn_transcript'>
                <attribute name='msdyn_transcriptid' />
                <attribute name='msdyn_name' />
                <attribute name='createdon' />
                <attribute name='msdyn_liveworkitemid' />
                <filter type='or'>
{conditions_str}
                </filter>
            </entity>
        </fetch>
        """

        raw_transcripts = self.client.execute_fetch_xml(
            entity_name="msdyn_transcript",
            fetch_xml=fetch_xml,
        )

        # Map transcripts by conversation ID
        transcripts_by_conversation = {}
        for raw_transcript in raw_transcripts:
            transcript = Transcript.from_dict(raw_transcript)
            # Extract the conversation ID from the lookup field
            conversation_id = raw_transcript.get("_msdyn_liveworkitemid_value")
            if conversation_id:
                transcripts_by_conversation[conversation_id] = transcript

        return transcripts_by_conversation

    def get_all_annotations_for_transcripts(
        self, transcript_ids: list[str]
    ) -> dict[str, Annotation]:
        """
        Fetch all annotations for multiple transcripts in a single query using FetchXML.

        Args:
            transcript_ids: List of transcript IDs to fetch annotations for.

        Returns:
            Dictionary mapping transcript_id to Annotation object.
        """
        if not transcript_ids:
            return {}

        # Validate all transcript IDs
        validated_ids = [validate_guid(tid, "transcript_id") for tid in transcript_ids]
        
        # Build FetchXML with multiple conditions (using OR)
        conditions = [
            f"                    <condition attribute='objectid' operator='eq' value='{escape_xml_value(transcript_id)}'/>"
            for transcript_id in validated_ids
        ]
        conditions_str = "\n".join(conditions)

        fetch_xml = f"""
        <fetch>
            <entity name='annotation'>
                <attribute name='annotationid' />
                <attribute name='documentbody' />
                <attribute name='filename' />
                <attribute name='mimetype' />
                <attribute name='objectid' />
                <filter type='or'>
{conditions_str}
                </filter>
            </entity>
        </fetch>
        """

        raw_annotations = self.client.execute_fetch_xml(
            entity_name="annotation",
            fetch_xml=fetch_xml,
        )

        # Map annotations by transcript ID (objectid)
        annotations_by_transcript = {}
        for raw_annotation in raw_annotations:
            annotation = Annotation.from_dict(raw_annotation)
            # Extract the transcript ID from the objectid field
            transcript_id = raw_annotation.get("_objectid_value")
            if transcript_id:
                annotations_by_transcript[transcript_id] = annotation

        return annotations_by_transcript

    def download_all_transcripts(self) -> DownloadSummary:
        """
        Download all transcripts for conversations in the workstream.
        Uses optimized batch fetching: 1st query fetches closed conversations,
        2nd query fetches all transcripts, 3rd query fetches all annotations.

        Returns:
            DownloadSummary object with success/failure counts.
        """
        summary = DownloadSummary()

        # Get all conversations (1st query)
        conversations = self.get_conversations()
        summary.total_conversations = len(conversations)

        if not conversations:
            print("No conversations found.")
            return summary

        # Batch fetch all transcripts for all conversations (2nd query - optimized)
        print(f"\nFetching transcripts for {len(conversations)} conversations...")
        conversation_ids = [c.id for c in conversations]
        transcripts_by_conversation = self.get_all_transcripts_for_conversations(conversation_ids)
        
        print(f"Found {len(transcripts_by_conversation)} transcripts.")
        summary.transcripts_found = len(transcripts_by_conversation)

        if not transcripts_by_conversation:
            print("No transcripts found for any conversations.")
            return summary

        # Batch fetch all annotations for all transcripts (3rd query - optimized)
        print(f"\nFetching annotations for {len(transcripts_by_conversation)} transcripts...")
        transcript_ids = [t.id for t in transcripts_by_conversation.values()]
        annotations_by_transcript = self.get_all_annotations_for_transcripts(transcript_ids)
        
        print(f"Found {len(annotations_by_transcript)} annotations.")

        # Process each conversation with its transcript and annotation
        for i, conversation in enumerate(conversations, 1):
            print(f"\nProcessing conversation {i}/{len(conversations)}: {conversation.id}")

            # Get transcript for this conversation
            transcript = transcripts_by_conversation.get(conversation.id)
            if not transcript:
                print(f"  No transcript found for conversation {conversation.id}")
                continue

            # Get annotation for transcript
            annotation = annotations_by_transcript.get(transcript.id)
            if not annotation:
                print(f"  No annotation found for transcript {transcript.id}")
                summary.errors += 1
                continue

            # Decode annotation content
            content = self.decode_annotation_content(annotation)
            if not content:
                print(f"  No content available for transcript {transcript.id}")
                summary.errors += 1
                continue

            # Save transcript
            try:
                filepath = self.save_transcript(
                    conversation=conversation,
                    content=content,
                )
                summary.transcripts_downloaded += 1
                summary.files.append(filepath)
                print(f"  Saved: {filepath}")
            except Exception as e:
                print(f"  Error saving transcript: {e}")
                summary.errors += 1

        return summary
