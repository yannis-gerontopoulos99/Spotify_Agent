'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await fetch('http://localhost:5000/chat/new', {
          method: 'POST',
        });
        const data = await response.json();
        router.push(`/chat/${data.session_id}`);
      } catch (error) {
        console.error('Failed to create session:', error);
      }
    };

    initSession();
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white">
      <div className="text-center">
        <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">♪</span>
        </div>
        <p className="text-xl">DJ Agent</p>
        <p className="text-gray-400 mt-2">Loading your chat...</p>
      </div>
    </div>
  );
}