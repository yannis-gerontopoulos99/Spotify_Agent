'use client';

import { useState, useRef } from 'react';
import { Send, Mic, Square } from 'lucide-react';

interface InputBoxProps {
  onSendMessage: (text: string) => void;
  onAudioSubmit: (audio: Blob) => void;
  loading: boolean;
}

export default function InputBox({
  onSendMessage,
  onAudioSubmit,
  loading,
}: InputBoxProps) {
  const [text, setText] = useState('');
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        onAudioSubmit(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setRecording(false);
      setMediaRecorder(null);
    }
  };

  const handleSend = () => {
    if (text.trim()) {
      onSendMessage(text);
      setText('');
    }
  };

  return (
    <div className="flex gap-3 items-end">
      {/* Text Input */}
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        placeholder="Message your DJ..."
        disabled={loading || recording}
        className="flex-1 bg-slate-700/50 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20 transition-all duration-200 disabled:opacity-50"
      />

      {/* Audio Button */}
      <button
        onClick={recording ? stopRecording : startRecording}
        disabled={loading}
        className={`p-3 rounded-lg transition-all duration-200 ${
          recording
            ? 'bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/50'
            : 'bg-blue-500 hover:bg-blue-600'
        } text-white disabled:opacity-50`}
      >
        {recording ? <Square size={20} /> : <Mic size={20} />}
      </button>

      {/* Send Button */}
      <button
        onClick={handleSend}
        disabled={loading || !text.trim()}
        className="p-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg transition-all duration-200 disabled:opacity-50 shadow-lg hover:shadow-green-500/50"
      >
        <Send size={20} />
      </button>
    </div>
  );
}