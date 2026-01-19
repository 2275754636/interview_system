import { useEffect, useRef } from 'react';
import type { Message } from '@/types';
import type { SessionState } from '@/stores';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';
import { ActionBar } from './ActionBar';
import { MessageSkeleton } from './MessageSkeleton';

const PLACEHOLDER_BY_STATE: Record<SessionState, string> = {
  IDLE: '点击"快速访谈"开始',
  INITIALIZING: '正在初始化访谈...',
  ACTIVE: '输入您的回答...',
  FINISHED: '访谈已结束，可重新开始',
};

interface ChatbotProps {
  messages: Message[];
  onSend: (text: string) => void;
  onUndo?: () => void;
  onSkip?: () => void;
  onRestart?: () => void;
  onStartInterview?: () => void;
  canUndo?: boolean;
  canSkip?: boolean;
  isLoading?: boolean;
  sessionState?: SessionState;
}

export function Chatbot({
  messages,
  onSend,
  onUndo,
  onSkip,
  onRestart,
  onStartInterview,
  canUndo = false,
  canSkip = false,
  isLoading = false,
  sessionState = 'IDLE',
}: ChatbotProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isEmpty = messages.length === 0 && !isLoading;
  const isInputDisabled = sessionState !== 'ACTIVE' || isLoading;
  const placeholder = isLoading ? '等待回复...' : PLACEHOLDER_BY_STATE[sessionState];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex h-full flex-col gap-4" role="region" aria-label="访谈对话区域">
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div
          className="flex flex-col gap-4 p-4"
          role="log"
          aria-live="polite"
          aria-label="对话消息列表"
        >
          {isEmpty ? (
            <div className="flex h-full min-h-[400px] flex-col items-center justify-center gap-6 text-center scale-in">
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold">欢迎使用 AI 教育访谈系统</h2>
                <p className="text-muted-foreground">
                  点击下方按钮开始访谈，系统将引导你完成学习评估
                </p>
              </div>
              <Button
                size="lg"
                onClick={onStartInterview}
                className="btn-hover"
                aria-label="开始新的访谈"
                disabled={sessionState === 'INITIALIZING'}
              >
                {sessionState === 'INITIALIZING' ? '正在启动...' : '快速访谈'}
              </Button>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div aria-busy="true" aria-label="正在加载回复">
                  <MessageSkeleton count={1} />
                </div>
              )}
            </>
          )}
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
        <MessageInput
          onSend={onSend}
          disabled={isInputDisabled}
          placeholder={placeholder}
        />
      </div>
    </div>
  );
}
