import type {
  User,
  Email,
  EmailListResponse,
  Thread,
  ThreadListResponse,
  ThreadDetail,
  ChatSession,
  ChatMessage,
  CategoryStats,
  DraftResponse,
  ReplyDraftResponse,
  SyncResponse,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${errorBody}`);
  }

  return res.json() as Promise<T>;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export function login(): void {
  window.location.href = `${API_URL}/auth/gmail/login`;
}

export async function getUser(userId: string): Promise<User> {
  return request<User>(`/auth/me?user_id=${encodeURIComponent(userId)}`);
}

// ─── Sync ────────────────────────────────────────────────────────────────────

export async function syncEmails(userId: string): Promise<SyncResponse> {
  return request<SyncResponse>(`/sync/${encodeURIComponent(userId)}`, {
    method: 'POST',
  });
}

// ─── Emails ──────────────────────────────────────────────────────────────────

export async function getEmails(
  userId: string,
  category?: string,
  page: number = 1,
  limit: number = 20
): Promise<EmailListResponse> {
  const params = new URLSearchParams({
    user_id: userId,
    page: String(page),
    limit: String(limit),
  });
  if (category) params.set('category', category);
  return request<EmailListResponse>(`/emails?${params.toString()}`);
}

export async function getEmail(emailId: string): Promise<Email> {
  return request<Email>(`/emails/${encodeURIComponent(emailId)}`);
}

// ─── Threads ─────────────────────────────────────────────────────────────────

export async function getThreads(
  userId: string,
  category?: string,
  page: number = 1,
  limit: number = 20
): Promise<ThreadListResponse> {
  const params = new URLSearchParams({
    user_id: userId,
    page: String(page),
    limit: String(limit),
  });
  if (category) params.set('category', category);
  return request<ThreadListResponse>(`/threads?${params.toString()}`);
}

export async function getThread(threadId: string): Promise<ThreadDetail> {
  return request<ThreadDetail>(`/threads/${encodeURIComponent(threadId)}`);
}

// ─── Category Stats ─────────────────────────────────────────────────────────

export async function getCategoryStats(
  userId: string
): Promise<CategoryStats[]> {
  return request<CategoryStats[]>(
    `/emails/categories/stats?user_id=${encodeURIComponent(userId)}`
  );
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export async function createChatSession(
  userId: string
): Promise<ChatSession> {
  return request<ChatSession>('/chat/session', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function sendChatMessage(
  sessionId: string,
  userId: string,
  message: string
): Promise<ChatMessage> {
  return request<ChatMessage>('/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId,
      message,
    }),
  });
}

export async function getChatSessions(
  userId: string
): Promise<ChatSession[]> {
  return request<ChatSession[]>(
    `/chat/sessions?user_id=${encodeURIComponent(userId)}`
  );
}

export async function getChatMessages(
  sessionId: string
): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(
    `/chat/sessions/${encodeURIComponent(sessionId)}/messages`
  );
}

// ─── Compose ─────────────────────────────────────────────────────────────────

export async function draftEmail(
  userId: string,
  prompt: string
): Promise<DraftResponse> {
  return request<DraftResponse>('/compose/draft', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, prompt }),
  });
}

export async function sendEmail(
  userId: string,
  to: string,
  subject: string,
  body: string
): Promise<{ status: string }> {
  return request<{ status: string }>('/compose/send', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, to, subject, body }),
  });
}

export async function draftReply(
  userId: string,
  threadId: string,
  prompt: string
): Promise<ReplyDraftResponse> {
  return request<ReplyDraftResponse>('/compose/reply/draft', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, thread_id: threadId, prompt }),
  });
}

export async function sendReply(
  userId: string,
  threadId: string,
  body: string,
  to: string,
  subject: string
): Promise<{ status: string }> {
  return request<{ status: string }>('/compose/reply/send', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      thread_id: threadId,
      body,
      to,
      subject,
    }),
  });
}
