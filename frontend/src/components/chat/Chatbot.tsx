import { useEffect, useRef } from 'react';
import type { Message } from '@/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ActionBar } from './ActionBar';
import { MessageSkeleton } from './MessageSkeleton';

interface ChatbotProps {
  messages: Message[];
  onSend: (text: string) => void;
  onUndo?: () => void;
  onSkip?: () => void;
  onRestart?: () => void;
  canUndo?: boolean;
  canSkip?: boolean;
  isLoading?: boolean;
}

export function Chatbot({
  messages,
  onSend,
  onUndo,
  onSkip,
  onRestart,
  canUndo = false,
  canSkip = false,
  isLoading = false,
}: ChatbotProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex h-full flex-col gap-4">
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="flex flex-col gap-4 p-4">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && <MessageSkeleton count={1} />}
        </div>
      </ScrollArea>

      <div className="flex flex-col gap-2 border-t border-border p-4">
        <ActionBar
          onUndo={onUndo}
          onSkip={onSkip}
          onRestart={onRestart}
          canUndo={canUndo}
          canSkip={canSkip}
        />
        <MessageInput onSend={onSend} disabled={isLoading} />
      </div>
    </div>
  );
}
