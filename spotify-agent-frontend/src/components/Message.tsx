import { Message as MessageType } from '@/types';

export default function Message({ message }: { message: MessageType }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-900'
        }`}
      >
        <p className="text-sm">{message.content}</p>
      </div>
    </div>
  );
}