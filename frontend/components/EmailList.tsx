'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { getThreads } from '@/lib/api';
import type { Thread } from '@/types';
import type { Email } from '@/types';
import EmailCard from './EmailCard';

interface EmailListProps {
  userId: string;
  category: string | null;
}

/* Build a pseudo-Email from a Thread so EmailCard can render it */
function threadToEmail(thread: Thread): Email {
  return {
    id: thread.id,
    user_id: thread.user_id,
    thread_id: thread.id,
    gmail_message_id: '',
    gmail_thread_id: thread.gmail_thread_id,
    subject: thread.subject,
    sender: thread.participants?.[0] ?? 'Unknown',
    sender_email: thread.participants?.[0] ?? '',
    recipients: thread.participants ?? [],
    body_text: '',
    body_html: '',
    snippet: '',
    received_at: thread.last_message_at,
    labels: [],
    category: thread.category,
    summary: thread.thread_summary,
    in_reply_to: '',
    references_header: '',
    is_read: true,
    created_at: thread.created_at,
  };
}

export default function EmailList({ userId, category }: EmailListProps) {
  const router = useRouter();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    getThreads(userId, category ?? undefined)
      .then((res) => setThreads(res.threads ?? []))
      .catch(() => setThreads([]))
      .finally(() => setLoading(false));
  }, [userId, category]);

  const filtered = useMemo(() => {
    if (!search.trim()) return threads;
    const q = search.toLowerCase();
    return threads.filter(
      (t) =>
        t.subject?.toLowerCase().includes(q) ||
        t.participants?.some((p) => p.toLowerCase().includes(q))
    );
  }, [threads, search]);

  /* ── Loading Skeletons ───────────────────────────────────── */
  if (loading) {
    return (
      <div className="space-y-3 p-6">
        <div className="skeleton mb-6 h-11 w-full rounded-xl" />
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton h-28 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* ── Search Bar ──────────────────────────────────────── */}
      <div className="sticky top-0 z-10 border-b border-white/[0.06] bg-gray-950/80 p-4 backdrop-blur-xl">
        <div className="relative">
          <svg
            className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by subject or sender…"
            className="w-full rounded-xl border border-white/[0.06] bg-white/[0.04] py-2.5 pl-10 pr-4 text-sm text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:bg-white/[0.06] focus:ring-1 focus:ring-purple-500/20"
          />
        </div>
      </div>

      {/* ── Email Cards ──────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="mb-4 text-5xl opacity-40">📭</div>
            <h3 className="text-lg font-semibold text-gray-400">
              No emails found
            </h3>
            <p className="mt-1 text-sm text-gray-600">
              {search
                ? 'Try a different search term'
                : 'Sync your inbox to get started'}
            </p>
          </div>
        ) : (
          <div className="stagger-children space-y-2">
            {filtered.map((thread) => (
              <div key={thread.id} className="animate-slide-up opacity-0">
                <EmailCard
                  email={threadToEmail(thread)}
                  onClick={() =>
                    router.push(`/dashboard/thread/${thread.id}`)
                  }
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
