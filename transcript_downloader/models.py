"""Data models for Dynamics 365 entities."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Conversation:
    """Represents a Dynamics 365 live work item (conversation)."""

    id: str
    title: str | None = None
    created_on: str | None = None
    workstream_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        """
        Create a Conversation instance from a Dataverse API response dictionary.

        Args:
            data: Dictionary from Dataverse API response.

        Returns:
            Conversation instance.

        Raises:
            ValueError: If required 'msdyn_ocliveworkitemid' field is missing.
        """
        conversation_id = data.get("msdyn_ocliveworkitemid")
        if not conversation_id:
            raise ValueError("Missing required field 'msdyn_ocliveworkitemid' in conversation data")

        return cls(
            id=conversation_id,
            title=data.get("msdyn_title"),
            created_on=data.get("createdon"),
            workstream_id=data.get("_msdyn_liveworkstreamid_value"),
        )


@dataclass
class Transcript:
    """Represents a Dynamics 365 transcript record."""

    id: str
    name: str | None = None
    created_on: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transcript":
        """
        Create a Transcript instance from a Dataverse API response dictionary.

        Args:
            data: Dictionary from Dataverse API response.

        Returns:
            Transcript instance.

        Raises:
            ValueError: If required 'msdyn_transcriptid' field is missing.
        """
        transcript_id = data.get("msdyn_transcriptid")
        if not transcript_id:
            raise ValueError("Missing required field 'msdyn_transcriptid' in transcript data")

        return cls(
            id=transcript_id,
            name=data.get("msdyn_name"),
            created_on=data.get("createdon"),
        )


@dataclass
class Annotation:
    """Represents a Dynamics 365 annotation (note) record."""

    id: str
    document_body: str | None = None
    filename: str | None = None
    mimetype: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Annotation":
        """
        Create an Annotation instance from a Dataverse API response dictionary.

        Args:
            data: Dictionary from Dataverse API response.

        Returns:
            Annotation instance.

        Raises:
            ValueError: If required 'annotationid' field is missing.
        """
        annotation_id = data.get("annotationid")
        if not annotation_id:
            raise ValueError("Missing required field 'annotationid' in annotation data")

        return cls(
            id=annotation_id,
            document_body=data.get("documentbody"),
            filename=data.get("filename"),
            mimetype=data.get("mimetype"),
        )


@dataclass
class TranscriptMessage:
    """Represents a single message in a transcript."""

    createdDateTime: str | None = None
    isControlMessage: bool = False
    content: str | None = None
    contentType: str | None = None
    fromAppName: str | None = None
    fromAppId: str | None = None
    fromUserId: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranscriptMessage":
        """
        Create a TranscriptMessage from raw message data.

        Args:
            data: Dictionary containing message data.

        Returns:
            TranscriptMessage instance with filtered fields.
        """
        # Extract from.application.displayName and from.application.id
        from_app_name = None
        from_app_id = None
        if "from" in data and isinstance(data["from"], dict):
            app = data["from"].get("application")
            if isinstance(app, dict):
                from_app_name = app.get("displayName")
                from_app_id = app.get("id")

        return cls(
            createdDateTime=data.get("createdDateTime"),
            isControlMessage=data.get("isControlMessage", False),
            content=data.get("content"),
            contentType=data.get("contentType"),
            fromAppName=from_app_name,
            fromAppId=from_app_id,
            fromUserId=data.get("fromUserId"),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary format.

        Returns:
            Dictionary representation of the message.
        """
        return {
            "createdDateTime": self.createdDateTime,
            "isControlMessage": self.isControlMessage,
            "content": self.content,
            "contentType": self.contentType,
            "fromAppName": self.fromAppName,
            "fromAppId": self.fromAppId,
            "fromUserId": self.fromUserId,
        }


@dataclass
class TranscriptData:
    """Represents the complete transcript data with metadata and messages."""

    Content: str  # Original JSON string
    Type: int
    Mode: int
    Tag: str | None = None
    CreatedOn: str | None = None
    Sender: str | None = None
    AttachmentInfo: str | None = None
    subject: str | None = None
    annotationid: str | None = None
    messages: list[TranscriptMessage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary format.

        Returns:
            Dictionary representation of the transcript data.
        """
        return {
            "Content": self.Content,
            "Type": self.Type,
            "Mode": self.Mode,
            "Tag": self.Tag,
            "CreatedOn": self.CreatedOn,
            "Sender": self.Sender,
            "AttachmentInfo": self.AttachmentInfo,
            "subject": self.subject,
            "annotationid": self.annotationid,
            "messages": [msg.to_dict() for msg in self.messages],
        }


@dataclass
class DownloadSummary:
    """Summary of transcript download operation."""

    total_conversations: int = 0
    transcripts_found: int = 0
    transcripts_downloaded: int = 0
    errors: int = 0
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert summary to dictionary format.

        Returns:
            Dictionary representation of the summary.
        """
        return {
            "total_conversations": self.total_conversations,
            "transcripts_found": self.transcripts_found,
            "transcripts_downloaded": self.transcripts_downloaded,
            "errors": self.errors,
            "files": self.files,
        }
