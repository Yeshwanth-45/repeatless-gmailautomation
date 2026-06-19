export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Email {
  id: string;
  user_id: string;
  thread_id: string;
  gmail_message_id: string;
  gmail_thread_id: string;
  subject: string;
  sender: string;
  sender_email: string;
  recipients: string[];
  body_text: string;
  body_html: string;
  snippet: string;
  received_at: string;
  labels: string[];
  category: string;
  summary: string;
  in_reply_to: string;
  references_header: string;
  is_read: boolean;
  created_at: string;
}

export interface EmailListResponse {
  emails: Email[];
  total: number;
  page: number;
}

export interface Thread {
  id: string;
  user_id: string;
  gmail_thread_id: string;
  subject: string;
  participants: string[];
  last_message_at: string;
  thread_summary: string;
  category: string;
  message_count: number;
  created_at: string;
}

export interface ThreadListResponse {
  threads: Thread[];
  total: number;
  page: number;
}

export interface ThreadDetail extends Thread {
  messages: Email[];
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: SourceCitation[] | null;
  created_at: string;
}

export interface SourceCitation {
  sender: string;
  sender_email: string;
  subject: string;
  date: string;
  gmail_message_id: string;
}

export interface CategoryStats {
  category: string;
  count: number;
}

export interface DraftResponse {
  subject: string;
  body: string;
}

export interface ReplyDraftResponse {
  body: string;
  in_reply_to: string;
  references: string;
}

export interface SyncResponse {
  emails_synced: number;
  threads_synced: number;
  status: string;
}
