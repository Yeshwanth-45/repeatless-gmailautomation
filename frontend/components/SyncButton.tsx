'use client';

import { useState } from 'react';
import { syncEmails } from '@/lib/api';

interface SyncButtonProps {
  userId: string;
}

export default function SyncButton({ userId }: SyncButtonProps) {
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [result, setResult] = useState('');

  const handleSync = async () => {
    if (syncing) return;
    setSyncing(true);
    setStatus('idle');
    try {
      const res = await syncEmails(userId);
      setStatus('success');
      setResult(`Synced ${res.emails_synced} emails, ${res.threads_synced} threads`);
      setTimeout(() => {
        setStatus('idle');
        setResult('');
      }, 4000);
    } catch {
      setStatus('error');
      setResult('Sync failed. Try again.');
      setTimeout(() => {
        setStatus('idle');
        setResult('');
      }, 4000);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={handleSync}
        disabled={syncing}
        className="group flex w-full items-center justify-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm font-medium text-gray-300 transition-all duration-300 hover:border-purple-500/30 hover:bg-white/[0.08] hover:text-white hover:shadow-lg hover:shadow-purple-500/5 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {syncing ? (
          <>
            <svg
              className="animate-spin h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Syncing…
          </>
        ) : (
          <>
            <svg
              className="h-4 w-4 transition-transform duration-300 group-hover:rotate-180"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Sync Emails
          </>
        )}
      </button>

      {status !== 'idle' && (
        <div
          className={`animate-slide-up rounded-lg px-3 py-2 text-xs font-medium ${
            status === 'success'
              ? 'bg-green-500/10 text-green-400 border border-green-500/20'
              : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}
        >
          {result}
        </div>
      )}
    </div>
  );
}
