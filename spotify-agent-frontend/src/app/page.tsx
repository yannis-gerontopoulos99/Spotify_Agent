'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const createNewChat = async () => {
      try {
        const response = await fetch('http://localhost:5000/chat/new', {
          method: 'POST',
        });
        const data = await response.json();
        router.push(`/chat/${data.session_id}`);
      } catch (error) {
        console.error('Failed to create chat:', error);
      }
    };

    createNewChat();
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <p className="text-white">Creating new chat...</p>
    </div>
  );
}