'use client';

import { useRef, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    audio_url?: string;
  };
  messageIndex: number;
  audioRefsRef: React.MutableRefObject<{ [key: number]: HTMLAudioElement }>;
  isPlaying: boolean;
  onPlayAudio: (index: number) => void;
  onAudioEnded: () => void;
}

export default function Message({
  message,
  messageIndex,
  audioRefsRef,
  isPlaying,
  onPlayAudio,
  onAudioEnded,
}: MessageProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (audioRef.current) {
      audioRefsRef.current[messageIndex] = audioRef.current;
    }
  }, [messageIndex, audioRefsRef]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.play().catch((err) => console.error('Error playing audio:', err));
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  const togglePlay = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (isPlaying) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      onAudioEnded();
    } else {
      onPlayAudio(messageIndex);
    }
  };

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs px-4 py-3 rounded-lg ${
          message.role === 'user'
            ? 'bg-green-600/90 text-white'
            : 'bg-gray-800/90 text-gray-100 border border-gray-700'
        }`}
      >
        <p className="text-sm break-words">{message.content}</p>

        {message.audio_url && (
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={togglePlay}
              className={`transition p-2 rounded ${
                isPlaying
                  ? 'bg-red-600 hover:bg-red-500'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <Pause size={16} className="text-white" />
              ) : (
                <Play size={16} className="text-white" />
              )}
            </button>
            <span className="text-xs text-gray-400">
              {isPlaying ? 'Playing...' : 'Audio'}
            </span>
            <audio
              ref={audioRef}
              src={message.audio_url}
              onEnded={onAudioEnded}
              crossOrigin="anonymous"
              className="hidden"
            />
          </div>
        )}
      </div>
    </div>
  );
}