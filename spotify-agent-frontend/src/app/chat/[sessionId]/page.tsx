'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import ChatWindow from '@/components/ChatWindow';

export default function ChatPage() {
  const params = useParams();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (params?.sessionId) {
      setSessionId(params.sessionId as string);
      setIsLoading(false);
    }
  }, [params?.sessionId]);

  if (isLoading || !sessionId) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <p>Loading chat...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-900">
      <Sidebar currentSessionId={sessionId} />
      <ChatWindow sessionId={sessionId} />
    </div>
  );
}