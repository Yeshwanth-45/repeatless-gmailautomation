from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: str


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    thread_id: Optional[str] = None
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    sender_email: Optional[str] = None
    recipients: Optional[list[str]] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    snippet: Optional[str] = None
    received_at: Optional[str] = None
    labels: Optional[list[str]] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    in_reply_to: Optional[str] = None
    references_header: Optional[str] = None
    is_read: Optional[bool] = None
    created_at: Optional[str] = None


class EmailListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emails: list[EmailResponse]
    total: int
    page: int


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    gmail_thread_id: Optional[str] = None
    subject: Optional[str] = None
    participants: Optional[list[str]] = None
    last_message_at: Optional[str] = None
    thread_summary: Optional[str] = None
    category: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[str] = None


class ThreadListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    threads: list[ThreadResponse]
    total: int
    page: int


class ThreadDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    gmail_thread_id: Optional[str] = None
    subject: Optional[str] = None
    participants: Optional[list[str]] = None
    last_message_at: Optional[str] = None
    thread_summary: Optional[str] = None
    category: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[str] = None
    messages: list[EmailResponse] = []


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: str
    message: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    sources: list = []


class ComposeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    prompt: str


class ReplyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    thread_id: str
    prompt: str


class SendEmailRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    to: str
    subject: str
    body: str
    draft_id: Optional[str] = None


class SendReplyRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    thread_id: str
    body: str
    to: str
    subject: str


class SyncResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emails_synced: int
    threads_synced: int
    status: str


class EmbedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emails_processed: int
    chunks_created: int
    emails_skipped: int
    errors: int
    status: str


class SourceCitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sender: str
    sender_email: str
    subject: str
    date: str
    gmail_message_id: str


class ChatSessionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    created_at: str


class ChatMessageRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[list] = None
    created_at: str


class CategoryStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    count: int
