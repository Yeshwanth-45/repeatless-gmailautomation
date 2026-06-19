'use client';

import { useState } from 'react';
import type { SourceCitation } from '@/types';

interface SourceCitationsProps {
  sources: SourceCitation[];
}

export default function SourceCitations({ sources }: SourceCitationsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium text-gray-400 transition-all duration-200 hover:bg-white/[0.05] hover:text-gray-300"
      >
        <span>📎</span>
        Sources ({sources.length})
        <svg
          className={`h-3 w-3 transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
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
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          expanded ? 'mt-2 max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="space-y-1.5">
          {sources.map((source, idx) => (
            <div
              key={idx}
              className="glass rounded-lg px-3 py-2 text-xs transition-all duration-200 hover:bg-white/[0.06]"
            >
              <div className="flex items-center gap-1.5 text-gray-300">
                <span>👤</span>
                <span className="font-medium">{source.sender}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-1.5 text-gray-400">
                <span>📧</span>
                <span className="truncate">{source.subject}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-1.5 text-gray-500">
                <span>📅</span>
                <span>
                  {new Date(source.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
