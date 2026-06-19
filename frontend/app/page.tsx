'use client';

import { login } from '@/lib/api';

export default function LandingPage() {
  const features = [
    {
      icon: '📧',
      title: 'Gmail Sync',
      description: 'Seamlessly sync your inbox with OAuth 2.0 authentication. All your emails, instantly accessible.',
    },
    {
      icon: '🧠',
      title: 'AI Summaries',
      description: 'Get instant AI-powered email summaries. Understand threads at a glance without reading everything.',
    },
    {
      icon: '📂',
      title: 'Smart Categories',
      description: 'Auto-categorize emails intelligently into newsletters, jobs, finance, and more.',
    },
    {
      icon: '💬',
      title: 'Chat Agent',
      description: 'Ask questions about your emails using natural language. Your personal email intelligence agent.',
    },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-gray-950">
      {/* ── Animated Background Orbs ──────────────────────────── */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="animate-float absolute -left-32 -top-32 h-96 w-96 rounded-full bg-purple-600/20 blur-3xl" />
        <div
          className="animate-float absolute -right-32 top-1/3 h-[28rem] w-[28rem] rounded-full bg-blue-600/15 blur-3xl"
          style={{ animationDelay: '2s' }}
        />
        <div
          className="animate-float absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-indigo-600/15 blur-3xl"
          style={{ animationDelay: '4s' }}
        />
        <div
          className="animate-float absolute -bottom-20 right-1/4 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl"
          style={{ animationDelay: '3s' }}
        />
      </div>

      {/* ── Main Content ────────────────────────────────────────── */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 py-20">
        {/* Logo Badge */}
        <div className="animate-fade-in mb-8">
          <span className="glass inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium text-gray-300">
            ✨ AI-Powered Email Intelligence
          </span>
        </div>

        {/* Title */}
        <h1
          className="animate-slide-up text-center text-6xl font-extrabold tracking-tight sm:text-7xl lg:text-8xl"
          style={{ animationDelay: '0.1s' }}
        >
          <span className="gradient-text">Gmail Intelligence</span>
        </h1>

        {/* Subtitle */}
        <p
          className="animate-slide-up mt-6 max-w-2xl text-center text-lg text-gray-400 sm:text-xl"
          style={{ animationDelay: '0.2s' }}
        >
          Your AI-powered email assistant. Summarize, categorize, and chat with
          your inbox like never before.
        </p>

        {/* CTA Button */}
        <div
          className="animate-slide-up mt-10"
          style={{ animationDelay: '0.3s' }}
        >
          <button
            onClick={() => login()}
            className="animate-pulse-glow group relative inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 px-10 py-4 text-lg font-semibold text-white shadow-2xl shadow-purple-500/25 transition-all duration-300 hover:scale-105 hover:shadow-purple-500/40"
          >
            <svg
              className="h-6 w-6 transition-transform duration-300 group-hover:rotate-12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
            Connect Gmail Account
            <svg
              className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>

        {/* Feature Cards */}
        <div
          className="animate-slide-up mt-20 grid w-full max-w-5xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
          style={{ animationDelay: '0.45s' }}
        >
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className="glass group cursor-default rounded-2xl p-6 transition-all duration-300 hover:scale-[1.04] hover:bg-white/[0.07] hover:shadow-xl hover:shadow-purple-500/5"
              style={{ animationDelay: `${0.5 + i * 0.1}s` }}
            >
              <div className="mb-4 text-4xl transition-transform duration-300 group-hover:scale-110">
                {feature.icon}
              </div>
              <h3 className="mb-2 text-lg font-semibold text-gray-100">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-gray-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Bottom subtle text */}
        <p
          className="animate-fade-in mt-16 text-sm text-gray-600"
          style={{ animationDelay: '0.8s' }}
        >
          Powered by Gemini AI &bull; Secure OAuth 2.0 &bull; Your data stays private
        </p>
      </div>
    </div>
  );
}
