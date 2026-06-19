'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  createChatSession,
  sendChatMessage,
  getChatSessions,
  getChatMessages,
} from '@/lib/api';
import type { ChatSession, ChatMessage } from '@/types';
import SourceCitations from './SourceCitations';

interface ChatInterfaceProps {
  userId: string;
}

const SUGGESTED_QUERIES = [
  'Which companies rejected my job application?',
  'Summarize emails from last week',
  'What emails did I get about finance?',
];

export default function ChatInterface({ userId }: ChatInterfaceProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /* Fetch sessions on mount */
  useEffect(() => {
    if (!userId) return;
    setSessionsLoading(true);
    getChatSessions(userId)
      .then((s) => {
        setSessions(s ?? []);
        setSessionsLoading(false);
      })
      .catch(() => {
        setSessions([]);
        setSessionsLoading(false);
      });
  }, [userId]);

  /* Load messages when activeSession changes */
  useEffect(() => {
    if (!activeSession) {
      setMessages([]);
      return;
    }
    getChatMessages(activeSession)
      .then((m) => setMessages(m ?? []))
      .catch(() => setMessages([]));
  }, [activeSession]);

  /* Scroll on new messages */
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleNewChat = async () => {
    try {
      const session = await createChatSession(userId);
      setSessions((prev) => [session, ...prev]);
      setActiveSession(session.id);
      setMessages([]);
    } catch {
      /* silently ignore */
    }
  };

  const handleSend = async (text?: string) => {
    const msg = text ?? input.trim();
    if (!msg || loading) return;

    let sessionId = activeSession;

    /* Auto-create session if none active */
    if (!sessionId) {
      try {
        const session = await createChatSession(userId);
        setSessions((prev) => [session, ...prev]);
        sessionId = session.id;
        setActiveSession(session.id);
      } catch {
        return;
      }
    }

    /* Optimistic user message */
    const optimistic: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content: msg,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setInput('');
    setLoading(true);

    try {
      const reply = await sendChatMessage(sessionId, userId, msg);
      const assistantMsg: ChatMessage = {
        id: reply.id || `reply-${Date.now()}`,
        session_id: sessionId,
        role: 'assistant',
        content: reply.content,
        sources: reply.sources ?? null,
        created_at: reply.created_at || new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        session_id: sessionId,
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        sources: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-2rem)] gap-0 overflow-hidden rounded-2xl border border-white/[0.06]">
      {/* ═══ Left Panel — Sessions ═══ */}
      <div className="flex w-64 shrink-0 flex-col border-r border-white/[0.06] bg-gray-950/50">
        {/* New Chat */}
        <div className="border-b border-white/[0.06] p-3">
          <button
            onClick={handleNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-purple-500/15 transition-all duration-300 hover:scale-[1.02] hover:shadow-purple-500/25"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2">
          {sessionsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="skeleton h-10 w-full rounded-lg" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <p className="px-3 py-6 text-center text-xs text-gray-600">
              No conversations yet
            </p>
          ) : (
            <div className="space-y-1">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSession(s.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-all duration-200 ${
                    activeSession === s.id
                      ? 'bg-white/10 text-white'
                      : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-300'
                  }`}
                >
                  <span className="text-base">💬</span>
                  <span className="truncate">
                    {s.title || 'New conversation'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ═══ Right Panel — Chat ═══ */}
      <div className="flex flex-1 flex-col bg-gray-950/30">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 && !loading ? (
            /* ── Empty State with Suggestions ── */
            <div className="flex h-full flex-col items-center justify-center">
              <div className="mb-4 text-5xl opacity-40">🤖</div>
              <h3 className="mb-2 text-lg font-semibold text-gray-300">
                Ask anything about your emails
              </h3>
              <p className="mb-8 text-sm text-gray-500">
                Try one of these to get started
              </p>
              <div className="grid w-full max-w-lg gap-3">
                {SUGGESTED_QUERIES.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="glass rounded-xl px-5 py-3.5 text-left text-sm text-gray-300 transition-all duration-200 hover:bg-white/[0.08] hover:text-white"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div className="max-w-[80%]">
                    <div
                      className={`px-4 py-3 text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'message-user'
                          : 'message-assistant'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {msg.role === 'assistant' && msg.sources && (
                      <SourceCitations sources={msg.sources} />
                    )}
                  </div>
                </div>
              ))}

              {/* Bouncing dots loader */}
              {loading && (
                <div className="flex justify-start">
                  <div className="message-assistant flex items-center gap-1.5 px-5 py-4">
                    <span className="bounce-dot inline-block h-2 w-2 rounded-full bg-gray-400" />
                    <span className="bounce-dot inline-block h-2 w-2 rounded-full bg-gray-400" />
                    <span className="bounce-dot inline-block h-2 w-2 rounded-full bg-gray-400" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="border-t border-white/[0.06] bg-gray-950/60 p-4">
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about your emails…"
              rows={1}
              disabled={loading}
              className="max-h-32 min-h-[44px] flex-1 resize-none rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-sm text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:ring-1 focus:ring-purple-500/20 disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-purple-500/20 transition-all duration-300 hover:scale-105 hover:shadow-purple-500/30 disabled:opacity-40 disabled:hover:scale-100"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
