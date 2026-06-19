'use client';

import type { Email } from '@/types';

interface EmailCardProps {
  email: Email;
  onClick: () => void;
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
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `${weeks}w ago`;
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
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

export default function EmailCard({ email, onClick }: EmailCardProps) {
  const badge = BADGE_CLASS[email.category] ?? 'badge-work';

  return (
    <button
      onClick={onClick}
      className={`group relative w-full rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-left transition-all duration-300 hover:-translate-y-0.5 hover:border-white/[0.12] hover:bg-white/[0.05] hover:shadow-lg hover:shadow-black/20 ${
        !email.is_read
          ? 'border-l-2 border-l-blue-400/70'
          : ''
      }`}
    >
      {/* Row 1: Sender + Date */}
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <span
          className={`truncate text-sm ${
            !email.is_read ? 'font-bold text-white' : 'font-semibold text-gray-200'
          }`}
        >
          {email.sender || email.sender_email}
        </span>
        <span className="shrink-0 text-xs text-gray-500">
          {timeAgo(email.received_at)}
        </span>
      </div>

      {/* Subject */}
      <p
        className={`mb-1.5 truncate text-sm ${
          !email.is_read ? 'font-semibold text-gray-100' : 'font-medium text-gray-300'
        }`}
      >
        {email.subject || '(No subject)'}
      </p>

      {/* Summary Preview */}
      <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-gray-500">
        {email.summary || email.snippet || 'No preview available'}
      </p>

      {/* Bottom: Category Badge + Unread Dot */}
      <div className="flex items-center justify-between">
        {email.category && (
          <span
            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badge}`}
          >
            {email.category}
          </span>
        )}
        {!email.is_read && (
          <span className="ml-auto h-2 w-2 rounded-full bg-blue-400 shadow-sm shadow-blue-400/50" />
        )}
      </div>
    </button>
  );
}
