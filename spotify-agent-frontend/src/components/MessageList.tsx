'use client';

import { useEffect, useRef } from 'react';
import Message from './Message';

interface MessageData {
  role: 'user' | 'assistant';
  content: string;
  audio_url?: string;
}

interface MessageListProps {
  messages: MessageData[];
  audioRefsRef: React.MutableRefObject<{ [key: number]: HTMLAudioElement }>;
  playingIndex: number | null;
  onPlayAudio: (index: number) => void;
  onAudioEnded: () => void;
}

export default function MessageList({
  messages,
  audioRefsRef,
  playingIndex,
  onPlayAudio,
  onAudioEnded,
}: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 w-full flex justify-center">
      <div className="max-w-2xl w-full space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-center py-12">
            <div>
              <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">♪</span>
              </div>
              <p className="text-lg">Start a conversation</p>
              <p className="text-sm text-gray-500 mt-2">
                Type a message or use voice to interact with the DJ Agent
              </p>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <Message
              key={index}
              message={message}
              messageIndex={index}
              audioRefsRef={audioRefsRef}
              isPlaying={playingIndex === index}
              onPlayAudio={onPlayAudio}
              onAudioEnded={onAudioEnded}
            />
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}