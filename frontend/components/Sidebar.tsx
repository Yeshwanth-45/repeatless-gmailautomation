'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getCategoryStats } from '@/lib/api';
import type { CategoryStats } from '@/types';
import SyncButton from './SyncButton';

interface SidebarProps {
  userId: string;
  activeCategory: string | null;
  onCategoryChange: (cat: string | null) => void;
}

const CATEGORY_CONFIG: Record<
  string,
  { label: string; badgeClass: string; dotColor: string }
> = {
  Newsletter: {
    label: 'Newsletter',
    badgeClass: 'badge-newsletter',
    dotColor: 'bg-purple-400',
  },
  'Job/Recruitment': {
    label: 'Job/Recruitment',
    badgeClass: 'badge-job',
    dotColor: 'bg-blue-400',
  },
  Finance: {
    label: 'Finance',
    badgeClass: 'badge-finance',
    dotColor: 'bg-green-400',
  },
  Notifications: {
    label: 'Notifications',
    badgeClass: 'badge-notifications',
    dotColor: 'bg-amber-400',
  },
  Personal: {
    label: 'Personal',
    badgeClass: 'badge-personal',
    dotColor: 'bg-pink-400',
  },
  'Work/Professional': {
    label: 'Work/Professional',
    badgeClass: 'badge-work',
    dotColor: 'bg-indigo-400',
  },
};

export default function Sidebar({
  userId,
  activeCategory,
  onCategoryChange,
}: SidebarProps) {
  const [stats, setStats] = useState<CategoryStats[]>([]);

  useEffect(() => {
    if (!userId) return;
    getCategoryStats(userId)
      .then(setStats)
      .catch(() => setStats([]));
  }, [userId]);

  const getCount = (cat: string) => {
    const found = stats.find(
      (s) => s.category?.toLowerCase() === cat.toLowerCase()
    );
    return found?.count ?? 0;
  };

  return (
    <aside className="glass-strong fixed left-0 top-0 z-40 flex h-screen w-72 flex-col border-r border-white/[0.06] bg-gray-950/80">
      {/* ── Logo ────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-6 py-5">
        <span className="text-2xl">✨</span>
        <h1 className="gradient-text text-xl font-bold tracking-tight">
          Gmail Intelligence
        </h1>
      </div>

      {/* ── Navigation ──────────────────────────────────────── */}
      <nav className="mt-2 space-y-1 px-3">
        <button
          onClick={() => onCategoryChange(null)}
          className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium transition-all duration-200 ${
            activeCategory === null
              ? 'bg-white/10 text-white shadow-sm'
              : 'text-gray-400 hover:bg-white/[0.05] hover:text-gray-200'
          }`}
        >
          <span className="text-lg">📬</span>
          All Mail
        </button>

        <Link
          href="/dashboard/chat"
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium text-gray-400 transition-all duration-200 hover:bg-white/[0.05] hover:text-gray-200"
        >
          <span className="text-lg">💬</span>
          Chat Agent
        </Link>

        <Link
          href="/dashboard/compose"
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium text-gray-400 transition-all duration-200 hover:bg-white/[0.05] hover:text-gray-200"
        >
          <span className="text-lg">✏️</span>
          Compose
        </Link>
      </nav>

      {/* ── Divider ─────────────────────────────────────────── */}
      <div className="mx-6 my-4 h-px bg-white/[0.06]" />

      {/* ── Categories ──────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3">
        <h2 className="mb-2 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500">
          Categories
        </h2>
        <div className="space-y-1">
          {Object.entries(CATEGORY_CONFIG).map(([key, cfg]) => {
            const isActive = activeCategory === key;
            const count = getCount(key);
            return (
              <button
                key={key}
                onClick={() => onCategoryChange(isActive ? null : key)}
                className={`flex w-full items-center justify-between rounded-xl px-4 py-2.5 text-left text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-300'
                }`}
              >
                <span className="flex items-center gap-2.5">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${cfg.dotColor}`}
                  />
                  {cfg.label}
                </span>
                {count > 0 && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${cfg.badgeClass}`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Sync Button ─────────────────────────────────────── */}
      <div className="border-t border-white/[0.06] p-4">
        <SyncButton userId={userId} />
      </div>
    </aside>
  );
}
