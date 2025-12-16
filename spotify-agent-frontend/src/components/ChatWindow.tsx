'use client';

import { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import InputBox from './InputBox';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export default function ChatWindow({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch existing chat session
    const fetchSession = async () => {
      try {
        const response = await fetch(`http://localhost:5000/chat/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          // The backend returns the session object directly, not wrapped
          setMessages(data.messages || []);
        }
      } catch (error) {
        console.error('Failed to fetch session:', error);
      }
    };
    fetchSession();
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`http://localhost:5000/chat/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, something went wrong. Please try again.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-gray-800">
      <MessageList messages={messages} />
      <div ref={messagesEndRef} />
      <InputBox onSendMessage={handleSendMessage} disabled={loading} />
    </div>
  );
}