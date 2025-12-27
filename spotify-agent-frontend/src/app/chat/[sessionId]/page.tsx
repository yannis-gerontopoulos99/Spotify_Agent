'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import ChatWindow from '@/components/ChatWindow';
import Sidebar from '@/components/Sidebar';
import { Menu, X } from 'lucide-react';

export default function ChatPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNewChat = () => {
    window.location.href = '/';
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black">
      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-white transition"
        title="Toggle sidebar"
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:relative lg:inset-auto">
          {/* Mobile overlay */}
          <div
            className="absolute inset-0 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          {/* Sidebar content */}
          <div className="relative z-40 h-full">
            <Sidebar
              currentSessionId={sessionId}
              onNewChat={handleNewChat}
              onClose={() => setSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col items-center justify-center overflow-hidden bg-gray-900 relative">
        
        {/* Centering Wrapper - This ensures vertical and horizontal alignment */}
        <div className="w-full h-full flex items-center justify-center p-4 md:p-8">
          
          {/* The Chat Window "Container" */}
          {/* max-w-4xl keeps it readable, h-[85vh] prevents it from hitting the edges */}
          <div className="w-full max-w-4xl h-[85vh] flex flex-col bg-gray-800/50 rounded-2xl border border-gray-700/50 shadow-2xl overflow-hidden">
            <ChatWindow sessionId={sessionId} />
          </div>

        </div>
      </div>

      {/* Agent Logo - Bottom Left */}
      <div className="fixed bottom-4 left-4 z-50">
        <div 
          style={{ 
            width: '48px', 
            height: '48px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            backgroundColor: '#1f2937', // bg-gray-800
            borderRadius: '9999px',
            overflow: 'hidden',
            border: '2px solid #374151', // border-gray-700
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
          }}
        >
          <img 
            src="/Gemini_Generated_Image_rf3m8frf3m8frf3m.png" 
            alt="Agent" 
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'cover',
              display: 'block'
            }} 
          />
        </div>
      </div>
    </div>
  );
}