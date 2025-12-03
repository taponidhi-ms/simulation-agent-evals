"""Transcript downloader module for Dynamics 365 Customer Service."""

import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone

from . import config
from .dataverse_client import DataverseClient
from .models import Annotation, Conversation, DownloadSummary, Transcript, TranscriptMessage
from .validators import escape_xml_value, is_safe_path_component, validate_guid


class TranscriptDownloader:
    """Downloads and saves transcripts from Dynamics 365 conversations."""

    def __init__(
        self,
        client: DataverseClient,
        workstream_id: str = config.WORKSTREAM_ID,
        days_to_fetch: int = config.DAYS_TO_FETCH,
        max_content_size: int = config.MAX_CONTENT_SIZE,
        max_conversations: int | None = None,
    ):
        """
        Initialize the transcript downloader.

        Args:
            client: Dataverse client instance.
            workstream_id: ID of the workstream to fetch conversations from.
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
        
        # Create timestamp-based folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder = os.path.abspath(os.path.join("output", "transcripts", timestamp))
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

        # Build filename using conversation ID
        filename = f"{validated_id}.json"
        filepath = os.path.abspath(os.path.join(self.output_folder, filename))

        # Verify the file path is within the output folder (prevent path traversal)
        if not filepath.startswith(self.output_folder):
            raise ValueError(f"Path traversal detected: {filepath}")

        # Try to parse as JSON to format nicely and add messages field
        try:
            json_content = json.loads(content)
            
            # Add messages field and decodedContent if Content exists and is a JSON string
            if isinstance(json_content, list):
                for item in json_content:
                    if isinstance(item, dict) and "Content" in item:
                        try:
                            raw_messages = json.loads(item["Content"])
                            # Keep original decodedContent for debugging
                            item["decodedContent"] = raw_messages
                            # Filter and transform messages to keep only specified fields
                            if isinstance(raw_messages, list):
                                filtered_messages = [
                                    TranscriptMessage.from_dict(msg).to_dict()
                                    for msg in raw_messages
                                    if isinstance(msg, dict)
                                ]
                                item["messages"] = filtered_messages
                        except (json.JSONDecodeError, TypeError) as e:
                            # If Content is not valid JSON, skip adding messages
                            print(f"  Warning: Content field is not valid JSON: {e}")
                            pass
            
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
        Fetch all transcripts for multiple conversations using FetchXML.
        Processes conversations in batches of 10 using the 'in' operator for efficiency.

        Args:
            conversation_ids: List of conversation IDs to fetch transcripts for.

        Returns:
            Dictionary mapping conversation_id to Transcript object.
        """
        if not conversation_ids:
            return {}

        # Validate all conversation IDs
        validated_ids = [validate_guid(cid, "conversation_id") for cid in conversation_ids]
        
        # Process in batches of 10
        batch_size = 10
        all_transcripts = {}
        
        for i in range(0, len(validated_ids), batch_size):
            batch = validated_ids[i:i + batch_size]
            
            # Build FetchXML using 'in' operator with separate value tags
            value_tags = "\n".join([
                f"                            <value>{escape_xml_value(conv_id)}</value>"
                for conv_id in batch
            ])

            fetch_xml = f"""
            <fetch>
                <entity name='msdyn_transcript'>
                    <attribute name='msdyn_transcriptid' />
                    <attribute name='msdyn_name' />
                    <attribute name='createdon' />
                    <attribute name='msdyn_liveworkitemidid' />
                    <filter>
                        <condition attribute='msdyn_liveworkitemidid' operator='in'>
{value_tags}
                        </condition>
                    </filter>
                </entity>
            </fetch>
            """

            raw_transcripts = self.client.execute_fetch_xml(
                entity_name="msdyn_transcript",
                fetch_xml=fetch_xml,
            )

            # Map transcripts by conversation ID
            for raw_transcript in raw_transcripts:
                transcript = Transcript.from_dict(raw_transcript)
                # Extract the conversation ID from the lookup field
                conversation_id = raw_transcript.get("_msdyn_liveworkitemidid_value")
                if conversation_id:
                    all_transcripts[conversation_id] = transcript

        return all_transcripts

    def get_all_annotations_for_transcripts(
        self, transcript_ids: list[str]
    ) -> dict[str, Annotation]:
        """
        Fetch all annotations for multiple transcripts using FetchXML.
        Processes transcripts in batches of 10 using the 'in' operator for efficiency.

        Args:
            transcript_ids: List of transcript IDs to fetch annotations for.

        Returns:
            Dictionary mapping transcript_id to Annotation object.
        """
        if not transcript_ids:
            return {}

        # Validate all transcript IDs
        validated_ids = [validate_guid(tid, "transcript_id") for tid in transcript_ids]
        
        # Process in batches of 10
        batch_size = 10
        all_annotations = {}
        
        for i in range(0, len(validated_ids), batch_size):
            batch = validated_ids[i:i + batch_size]
            
            # Build FetchXML using 'in' operator with separate value tags
            value_tags = "\n".join([
                f"                            <value>{escape_xml_value(transcript_id)}</value>"
                for transcript_id in batch
            ])

            fetch_xml = f"""
            <fetch>
                <entity name='annotation'>
                    <attribute name='annotationid' />
                    <attribute name='documentbody' />
                    <attribute name='filename' />
                    <attribute name='mimetype' />
                    <attribute name='objectid' />
                    <filter>
                        <condition attribute='objectid' operator='in'>
{value_tags}
                        </condition>
                    </filter>
                </entity>
            </fetch>
            """

            raw_annotations = self.client.execute_fetch_xml(
                entity_name="annotation",
                fetch_xml=fetch_xml,
            )

            # Map annotations by transcript ID (objectid)
            for raw_annotation in raw_annotations:
                annotation = Annotation.from_dict(raw_annotation)
                # Extract the transcript ID from the objectid field
                transcript_id = raw_annotation.get("_objectid_value")
                if transcript_id:
                    all_annotations[transcript_id] = annotation

        return all_annotations

    def download_all_transcripts(self) -> DownloadSummary:
        """
        Download all transcripts for conversations in the workstream.
        Uses optimized batch fetching: 1st query fetches closed conversations,
        then queries fetch transcripts and annotations in batches of 10 using FetchXML 'in' operator.

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
