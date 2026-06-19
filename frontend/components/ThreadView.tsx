'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getThread } from '@/lib/api';
import type { ThreadDetail, Email } from '@/types';

interface ThreadViewProps {
  threadId: string;
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diff = now - date;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

const BADGE_CLASS: Record<string, string> = {
  Newsletter: 'badge-newsletter',
  'Job/Recruitment': 'badge-job',
  Finance: 'badge-finance',
  Notifications: 'badge-notifications',
  Personal: 'badge-personal',
  'Work/Professional': 'badge-work',
};

function MessageCard({ message, idx }: { message: Email; idx: number }) {
  const [showSummary, setShowSummary] = useState(false);

  return (
    <div
      className="animate-slide-up rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 opacity-0 transition-all duration-300"
      style={{ animationDelay: `${idx * 0.08}s`, animationFillMode: 'forwards' }}
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-bold text-white">
            {(message.sender?.[0] || message.sender_email?.[0] || '?').toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-100">
              {message.sender || 'Unknown'}
            </p>
            <p className="text-xs text-gray-500">{message.sender_email}</p>
          </div>
        </div>
        <span className="shrink-0 text-xs text-gray-500">
          {timeAgo(message.received_at)}
        </span>
      </div>

      {/* Body */}
      <div className="mb-3 whitespace-pre-wrap text-sm leading-relaxed text-gray-300">
        {message.body_text || message.snippet || 'No content'}
      </div>

      {/* Collapsible AI Summary */}
      {message.summary && (
        <div className="border-t border-white/[0.06] pt-3">
          <button
            onClick={() => setShowSummary(!showSummary)}
            className="flex items-center gap-2 text-xs font-medium text-purple-400 transition-colors hover:text-purple-300"
          >
            <span>🧠</span>
            {showSummary ? 'Hide AI Summary' : 'Show AI Summary'}
            <svg
              className={`h-3 w-3 transition-transform duration-200 ${
                showSummary ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            className={`overflow-hidden transition-all duration-300 ${
              showSummary ? 'mt-2 max-h-40 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <p className="rounded-lg bg-purple-500/5 border border-purple-500/10 p-3 text-xs leading-relaxed text-purple-200/80">
              {message.summary}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ThreadView({ threadId }: ThreadViewProps) {
  const router = useRouter();
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!threadId) return;
    setLoading(true);
    getThread(threadId)
      .then(setThread)
      .catch(() => setThread(null))
      .finally(() => setLoading(false));
  }, [threadId]);

  /* ── Loading State ─────────────────────────────── */
  if (loading) {
    return (
      <div className="space-y-4 p-6">
        <div className="skeleton h-8 w-48 rounded-lg" />
        <div className="skeleton h-6 w-3/4 rounded-lg" />
        <div className="skeleton mt-4 h-32 w-full rounded-xl" />
        <div className="skeleton h-40 w-full rounded-xl" />
        <div className="skeleton h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-lg text-gray-400">Thread not found</p>
        <button
          onClick={() => router.push('/dashboard')}
          className="mt-4 text-sm text-purple-400 hover:underline"
        >
          ← Back to inbox
        </button>
      </div>
    );
  }

  const badge = BADGE_CLASS[thread.category] ?? 'badge-work';

  return (
    <div className="mx-auto max-w-4xl p-6">
      {/* ── Back Button ─────────────────────────────── */}
      <button
        onClick={() => router.push('/dashboard')}
        className="mb-6 flex items-center gap-2 text-sm font-medium text-gray-400 transition-colors hover:text-white"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path d="M15 19l-7-7 7-7" />
        </svg>
        Back to inbox
      </button>

      {/* ── Thread Header ─────────────────────────── */}
      <div className="mb-6">
        <div className="mb-3 flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">
            {thread.subject || '(No subject)'}
          </h1>
          {thread.category && (
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${badge}`}>
              {thread.category}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500">
          {thread.message_count} message{thread.message_count !== 1 ? 's' : ''} ·{' '}
          {thread.participants?.join(', ')}
        </p>
      </div>

      {/* ── AI Thread Summary ────────────────────── */}
      {thread.thread_summary && (
        <div className="glass mb-8 rounded-2xl p-5">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-purple-300">
            <span>🧠</span>
            AI Thread Summary
          </div>
          <p className="text-sm leading-relaxed text-gray-300">
            {thread.thread_summary}
          </p>
        </div>
      )}

      {/* ── Messages ─────────────────────────────── */}
      <div className="space-y-4">
        {(thread.messages ?? []).map((msg, idx) => (
          <MessageCard key={msg.id} message={msg} idx={idx} />
        ))}
      </div>

      {/* ── Reply Button ─────────────────────────── */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={() =>
            router.push(`/dashboard/compose?threadId=${thread.id}`)
          }
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-purple-500/20 transition-all duration-300 hover:scale-105 hover:shadow-purple-500/30"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
          </svg>
          Reply
        </button>
      </div>
    </div>
  );
}
