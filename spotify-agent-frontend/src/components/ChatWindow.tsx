'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square } from 'lucide-react';
import MessageList from './MessageList';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  audio_url?: string;
}

interface ChatWindowProps {
  sessionId: string;
}

export default function ChatWindow({ sessionId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const [audioProcessing, setAudioProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRefsRef = useRef<{ [key: number]: HTMLAudioElement }>({});

  // Fetch chat history when sessionId changes
  useEffect(() => {
    fetchChatHistory();
  }, [sessionId]);

  const fetchChatHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/chat/history/${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        const formattedMessages: Message[] = data.map((item: any) => ({
          role: item.role,
          content: item.transcript,
          audio_url: item.audio_url,
        }));
        setMessages(formattedMessages);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
      setMessages([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage = { role: 'user' as const, content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setPlayingIndex(null);

    try {
      const response = await fetch(`http://localhost:5000/chat/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode: 'text' }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      if (data.message) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.message,
          audio_url: data.audio_url,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        audioChunksRef.current = [];

        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64Audio = (reader.result as string).split(',')[1];
          await sendAudio(base64Audio);
        };
        reader.readAsDataURL(audioBlob);

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      setPlayingIndex(null);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudio = async (base64Audio: string) => {
    setLoading(true);
    setAudioProcessing(true);
    setPlayingIndex(null);

    try {
      const response = await fetch(`http://localhost:5000/audio/interact/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio: base64Audio }),
      });

      if (!response.ok) {
        throw new Error('Failed to send audio');
      }

      const data = await response.json();

      if (data.user_said && data.assistant_said) {
        setMessages((prev) => [
          ...prev,
          { role: 'user', content: data.user_said },
          {
            role: 'assistant',
            content: data.assistant_said,
            audio_url: data.audio_url,
          },
        ]);

        setTimeout(() => {
          const assistantMsgIndex = messages.length + 1;
          playAudio(assistantMsgIndex);
          setAudioProcessing(false);
        }, 300);
      }
    } catch (error) {
      console.error('Error sending audio:', error);
      alert('Failed to process audio');
      setAudioProcessing(false);
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (messageIndex: number) => {
    Object.entries(audioRefsRef.current).forEach(([idx, audio]) => {
      if (parseInt(idx) !== messageIndex && audio) {
        audio.pause();
        audio.currentTime = 0;
      }
    });

    setPlayingIndex(messageIndex);

    const audio = audioRefsRef.current[messageIndex];
    if (audio) {
      audio
        .play()
        .catch((err) => {
          console.error('Error playing audio:', err);
          setPlayingIndex(null);
        });
    } else {
      console.warn(`Audio element not found for index ${messageIndex}`);
      setPlayingIndex(null);
    }
  };

  const handleAudioEnded = () => {
    setPlayingIndex(null);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-900 via-gray-900 to-black">
      {/* Conversation Display - Top Section */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {historyLoading ? (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <p>Loading conversation...</p>
          </div>
        ) : (
          <MessageList
            messages={messages}
            audioRefsRef={audioRefsRef}
            playingIndex={playingIndex}
            onPlayAudio={playAudio}
            onAudioEnded={handleAudioEnded}
          />
        )}
      </div>

      {/* Input Section - Bottom Center */}
      <div className="flex-shrink-0 bg-gradient-to-t from-black via-gray-900 to-transparent pt-8 pb-8 px-4">
        <div className="max-w-2xl mx-auto space-y-3">
          {/* Status Messages */}
          {audioProcessing && (
            <div className="text-center text-sm text-blue-400">
              Processing audio response...
            </div>
          )}

          {isRecording && (
            <div className="flex items-center justify-center gap-2 text-blue-400 text-sm">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              Recording audio...
            </div>
          )}

          {/* Text Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) =>
                e.key === 'Enter' && !loading && !historyLoading && sendMessage(input)
              }
              placeholder="Ask me anything..."
              className="flex-1 bg-gray-800/80 backdrop-blur-sm text-white rounded-lg px-4 py-3 border border-gray-700 focus:outline-none focus:border-green-600 focus:ring-1 focus:ring-green-600/50 placeholder-gray-400"
              disabled={loading || isRecording || historyLoading || audioProcessing}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim() || historyLoading || audioProcessing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white p-3 rounded-lg transition shrink-0"
              title="Send message"
            >
              <Send size={20} />
            </button>
          </div>

          {/* Microphone Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading || historyLoading || audioProcessing}
            className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold transition ${
              isRecording
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600'
            }`}
          >
            {isRecording ? (
              <>
                <Square size={20} />
              </>
            ) : (
              <>
                <Mic size={20} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}