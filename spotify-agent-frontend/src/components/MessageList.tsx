'use client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export default function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-400">
          <p>Start a conversation with DJ Spot!</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}