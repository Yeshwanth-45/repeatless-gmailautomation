'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import Sidebar from '@/components/Sidebar';
import EmailList from '@/components/EmailList';

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [userId, setUserId] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  useEffect(() => {
    const paramUserId = searchParams.get('user_id');
    const storedUserId = localStorage.getItem('gmail_intel_user_id');
    const id = paramUserId || storedUserId;

    if (id) {
      setUserId(id);
      if (paramUserId) {
        localStorage.setItem('gmail_intel_user_id', paramUserId);
      }
    } else {
      router.replace('/');
    }
  }, [searchParams, router]);

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
        activeCategory={activeCategory}
        onCategoryChange={setActiveCategory}
      />
      <main className="ml-72 min-h-screen">
        <EmailList userId={userId} category={activeCategory} />
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
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
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
