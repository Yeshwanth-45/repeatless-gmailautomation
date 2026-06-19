'use client';

import { useState } from 'react';
import {
  draftEmail,
  sendEmail,
  draftReply,
  sendReply,
} from '@/lib/api';

interface ComposeModalProps {
  userId: string;
  threadId?: string;
}

export default function ComposeModal({ userId, threadId }: ComposeModalProps) {
  const isReply = !!threadId;

  const [prompt, setPrompt] = useState('');
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [drafted, setDrafted] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim() || generating) return;
    setGenerating(true);
    setStatus(null);
    try {
      if (isReply && threadId) {
        const res = await draftReply(userId, threadId, prompt);
        setBody(res.body);
        setSubject((prev) => prev || 'Re: ');
        setDrafted(true);
      } else {
        const res = await draftEmail(userId, prompt);
        setSubject(res.subject);
        setBody(res.body);
        setDrafted(true);
      }
    } catch {
      setStatus({ type: 'error', msg: 'Failed to generate draft. Try again.' });
    } finally {
      setGenerating(false);
    }
  };

  const handleSend = async () => {
    if (!to.trim() || !body.trim() || sending) return;
    setSending(true);
    setStatus(null);
    try {
      if (isReply && threadId) {
        await sendReply(userId, threadId, body, to, subject);
      } else {
        await sendEmail(userId, to, subject, body);
      }
      setStatus({ type: 'success', msg: 'Email sent successfully!' });
      // Reset after short delay
      setTimeout(() => {
        handleDiscard();
        setStatus(null);
      }, 3000);
    } catch {
      setStatus({ type: 'error', msg: 'Failed to send. Please try again.' });
    } finally {
      setSending(false);
    }
  };

  const handleDiscard = () => {
    setPrompt('');
    setTo('');
    setSubject('');
    setBody('');
    setDrafted(false);
    setStatus(null);
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* ── Header ──────────────────────────────────────── */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">
          {isReply ? '↩️ Reply' : '✏️ Compose'}
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          {isReply
            ? 'Describe what you want to reply and AI will draft it'
            : 'Describe what you want to write and AI will draft it for you'}
        </p>
      </div>

      {/* ── Status Message ──────────────────────────────── */}
      {status && (
        <div
          className={`animate-slide-up mb-4 rounded-xl px-4 py-3 text-sm font-medium ${
            status.type === 'success'
              ? 'border border-green-500/20 bg-green-500/10 text-green-400'
              : 'border border-red-500/20 bg-red-500/10 text-red-400'
          }`}
        >
          {status.msg}
        </div>
      )}

      {/* ── Prompt Input ─────────────────────────────────── */}
      {!drafted && (
        <div className="space-y-4">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={
              isReply
                ? 'Describe what you want to reply…'
                : 'Describe what you want to write…'
            }
            rows={4}
            className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-sm text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:ring-1 focus:ring-purple-500/20"
          />
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || generating}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-purple-500/20 transition-all duration-300 hover:scale-105 hover:shadow-purple-500/30 disabled:opacity-40 disabled:hover:scale-100"
          >
            {generating ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating…
              </>
            ) : (
              <>
                <span>✨</span>
                Generate {isReply ? 'Reply' : 'Draft'}
              </>
            )}
          </button>
        </div>
      )}

      {/* ── Draft Editor ─────────────────────────────────── */}
      {drafted && (
        <div className="animate-slide-up space-y-4">
          {/* To field */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">
              To
            </label>
            <input
              type="email"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="recipient@example.com"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2.5 text-sm text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:ring-1 focus:ring-purple-500/20"
            />
          </div>

          {/* Subject field */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">
              Subject
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2.5 text-sm text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:ring-1 focus:ring-purple-500/20"
            />
          </div>

          {/* Body field */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-gray-400">
              Body
            </label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={10}
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-sm leading-relaxed text-gray-200 placeholder-gray-500 outline-none transition-all duration-200 focus:border-purple-500/40 focus:ring-1 focus:ring-purple-500/20"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleSend}
              disabled={!to.trim() || !body.trim() || sending}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-green-500/20 transition-all duration-300 hover:scale-105 hover:shadow-green-500/30 disabled:opacity-40 disabled:hover:scale-100"
            >
              {sending ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Sending…
                </>
              ) : (
                <>
                  <span>📤</span>
                  Send
                </>
              )}
            </button>

            <button
              onClick={() => {
                setDrafted(false);
                // keep prompt so user can re-generate
              }}
              className="flex items-center gap-2 rounded-xl border border-purple-500/30 px-6 py-3 text-sm font-medium text-purple-400 transition-all duration-200 hover:bg-purple-500/10"
            >
              <span>✨</span>
              Regenerate
            </button>

            <button
              onClick={handleDiscard}
              className="flex items-center gap-2 rounded-xl border border-red-500/30 px-6 py-3 text-sm font-medium text-red-400 transition-all duration-200 hover:bg-red-500/10"
            >
              <span>🗑️</span>
              Discard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
