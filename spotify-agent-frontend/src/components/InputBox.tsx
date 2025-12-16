'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';

interface InputBoxProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

export default function InputBox({ onSendMessage, disabled }: InputBoxProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border-t border-gray-700 bg-gray-800 flex gap-2"
    >
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Message DJ Spot..."
        disabled={disabled}
        className="flex-1 bg-gray-700 text-white placeholder-gray-400 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-600 disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white p-2 rounded-lg transition"
      >
        <Send size={20} />
      </button>
    </form>
  );
}