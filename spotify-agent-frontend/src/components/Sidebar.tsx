'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export default function Sidebar({ currentSessionId }: { currentSessionId?: string }) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('http://localhost:5000/chat/sessions');
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await fetch('http://localhost:5000/chat/new', {
        method: 'POST',
      });
      const data = await response.json();
      router.push(`/chat/${data.session_id}`);
      fetchSessions();
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleDeleteChat = async (sessionId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm('Delete this chat?')) {
      try {
        await fetch(`http://localhost:5000/chat/${sessionId}`, {
          method: 'DELETE',
        });
        setSessions(sessions.filter((s) => s.id !== sessionId));
        if (currentSessionId === sessionId) {
          router.push('/');
        }
      } catch (error) {
        console.error('Failed to delete chat:', error);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="w-64 bg-gray-900 text-white h-screen flex flex-col border-r border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition"
        >
          <Plus size={20} />
          New Chat
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="text-gray-400 text-sm p-2">Loading chats...</div>
        ) : sessions.length === 0 ? (
          <div className="text-gray-400 text-sm p-2">No chats yet</div>
        ) : (
          sessions.map((session) => (
            <Link
              key={session.id}
              href={`/chat/${session.id}`}
              className={`block p-3 rounded-lg hover:bg-gray-800 transition group ${
                currentSessionId === session.id ? 'bg-gray-800' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{session.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{formatDate(session.created_at)}</p>
                </div>
                <button
                  onClick={(e) => handleDeleteChat(session.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition p-1"
                  title="Delete chat"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700 text-xs text-gray-400">
        <p>DJ Spot</p>
      </div>
    </div>
  );
}