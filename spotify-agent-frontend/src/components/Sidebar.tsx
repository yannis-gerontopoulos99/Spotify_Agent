'use client';

import { useEffect, useState } from 'react';
import { Plus, MessageCircle, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface ConversationSummary {
  session_id: string;
  first_message: string;
  message_count: number;
  last_message_time: string;
}

interface SidebarProps {
  currentSessionId: string | null;
  onNewChat: () => void;
  onClose?: () => void;
}

export default function Sidebar({ currentSessionId, onNewChat, onClose }: SidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchAllConversations();
    const interval = setInterval(fetchAllConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllConversations = async () => {
    try {
      setError(null);
      const response = await fetch('http://localhost:5000/chat/all-conversations', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setConversations(data);
      } else {
        setConversations([]);
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      setError('Failed to load conversation history');
      setLoading(false);
    }
  };

  const deleteConversation = async (sessionId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/chat/delete/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      setConversations(conversations.filter((c) => c.session_id !== sessionId));

      if (sessionId === currentSessionId) {
        router.push('/');
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('Failed to delete conversation');
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await fetch('http://localhost:5000/chat/new', {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to create new chat');
      }
      const data = await response.json();
      onClose?.();
      router.push(`/chat/${data.session_id}`);
    } catch (error) {
      console.error('Failed to create new session:', error);
      alert('Failed to create new chat');
    }
  };

  const handleConversationClick = () => {
    onClose?.();
  };

  return (
    <div className="w-64 bg-gray-800 text-white flex flex-col border-r border-gray-700 h-screen overflow-hidden">
      {/* New Chat Button */}
      <button
        onClick={handleNewChat}
        className="m-4 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition"
      >
        <Plus size={20} />
        New Chat
      </button>

      {/* Divider */}
      <div className="px-4">
        <div className="h-px bg-gray-700"></div>
      </div>

      {/* History Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-3">
          <h2 className="text-xs uppercase tracking-wider text-gray-400 font-semibold">
            Conversation History
          </h2>
        </div>

        {loading ? (
          <div className="px-4 py-2 text-sm text-gray-400">Loading conversations...</div>
        ) : error ? (
          <div className="px-4 py-2 text-sm text-red-400">{error}</div>
        ) : conversations.length === 0 ? (
          <div className="px-4 py-2 text-sm text-gray-400">No conversations yet</div>
        ) : (
          <div className="space-y-1 px-2">
            {conversations.map((conversation) => (
              <Link
                key={conversation.session_id}
                href={`/chat/${conversation.session_id}`}
                onClick={handleConversationClick}
                className={`block p-3 rounded-lg transition group ${
                  currentSessionId === conversation.session_id
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-100'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <MessageCircle size={14} className="flex-shrink-0 mt-0.5" />
                      <p className="font-semibold text-sm truncate">
                        {conversation.first_message?.substring(0, 25) || 'Untitled'}...
                      </p>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {conversation.message_count} messages
                    </p>
                    <span className="text-xs text-gray-500">
                      {new Date(conversation.last_message_time).toLocaleDateString()}
                    </span>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(conversation.session_id, e)}
                    className="opacity-0 group-hover:opacity-100 transition flex-shrink-0 mt-1"
                  >
                    <Trash2 size={16} className="text-red-400 hover:text-red-300" />
                  </button>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-700 p-4">
        <button
          onClick={fetchAllConversations}
          disabled={loading}
          className="w-full text-xs text-gray-400 hover:text-gray-200 transition disabled:opacity-50"
        >
          Refresh History
        </button>
      </div>
    </div>
  );
}