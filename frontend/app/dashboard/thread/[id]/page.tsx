'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import ThreadView from '@/components/ThreadView';

interface ThreadPageProps {
  params: Promise<{ id: string }>;
}

export default function ThreadPage({ params }: ThreadPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('gmail_intel_user_id');
    if (stored) {
      setUserId(stored);
    } else {
      router.replace('/');
    }
  }, [router]);

  if (!userId) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <svg
          className="animate-spin h-8 w-8 text-purple-400"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <Sidebar
        userId={userId}
        activeCategory={null}
        onCategoryChange={() => router.push('/dashboard')}
      />
      <main className="ml-72 min-h-screen py-4">
        <ThreadView threadId={id} />
      </main>
    </div>
  );
}
