import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query';
import { ThemeProvider } from '@/components/common/ThemeProvider';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { StatsSkeleton } from '@/components/chat/StatsSkeleton';
import { LazyChatbot, LazyCommandPalette } from '@/lib/lazy';
import { useInterviewStore, useCommandStore, useThemeStore } from '@/stores';
import { useStartSession, useSendMessage, useUndo, useSkip, useSessionStats } from '@/hooks';
import { logError } from '@/services/logger';
import { AdminApp } from '@/components/admin/AdminApp';
import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Shield } from 'lucide-react';
import type { ThemeMode } from '@/types';

type CommandMeta =
  | { id: string; label: string; shortcut: string; kind: 'theme'; mode: ThemeMode }
  | { id: string; label: string; shortcut: string; kind: 'restart' }
  | { id: string; label: string; shortcut: string; kind: 'admin' };

const COMMAND_META: CommandMeta[] = [
  { id: 'theme-light', label: '浅色模式', shortcut: '⌘1', kind: 'theme', mode: 'light' },
  { id: 'theme-dark', label: '深色模式', shortcut: '⌘2', kind: 'theme', mode: 'dark' },
  { id: 'theme-system', label: '跟随系统', shortcut: '⌘3', kind: 'theme', mode: 'system' },
  { id: 'restart', label: '重新开始', shortcut: '⌘R', kind: 'restart' },
  { id: 'admin', label: '后台监管仪表盘', shortcut: '⌘D', kind: 'admin' },
];

function useHashLocation() {
  const [hash, setHash] = React.useState(() => window.location.hash || '');

  React.useEffect(() => {
    const handler = () => setHash(window.location.hash || '');
    window.addEventListener('hashchange', handler);
    return () => window.removeEventListener('hashchange', handler);
  }, []);

  return hash.replace(/^#/, '');
}

function isAdminHash(hash: string) {
  return hash === 'admin' || hash.startsWith('admin/');
}

function InterviewApp() {
  const { session, messages, isLoading, canUndo, sessionState, setSessionState } = useInterviewStore();
  const { isOpen, toggle, close } = useCommandStore();
  const { setMode } = useThemeStore();

  const startSession = useStartSession();
  const sendMessage = useSendMessage();
  const undo = useUndo();
  const skip = useSkip();
  const { data: stats, isLoading: statsLoading } = useSessionStats(session?.id || null);

  const openAdmin = () => {
    window.location.hash = '#admin/overview';
  };

  const beginSession = async () => {
    setSessionState('INITIALIZING');
    try {
      await startSession.mutateAsync(undefined);
    } catch (err: unknown) {
      logError('App', '启动访谈失败', err);
      setSessionState('IDLE');
    }
  };

  const commands = COMMAND_META.map((cmd) => {
    if (cmd.kind === 'theme') {
      return { id: cmd.id, label: cmd.label, shortcut: cmd.shortcut, onSelect: () => setMode(cmd.mode) };
    }
    if (cmd.kind === 'restart') {
      return { id: cmd.id, label: cmd.label, shortcut: cmd.shortcut, onSelect: () => void beginSession() };
    }
    return { id: cmd.id, label: cmd.label, shortcut: cmd.shortcut, onSelect: openAdmin };
  });

  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (!session || sessionState !== 'ACTIVE') return;
    sendMessage.mutate({ sessionId: session.id, text: trimmed });
  };

  return (
    <>
      <LazyCommandPalette
        isOpen={isOpen}
        onOpenChange={(open) => (open ? toggle() : close())}
        commands={commands}
        placeholder="搜索命令..."
      />

      <div className="flex min-h-screen flex-col fade-in">
        <Header
          title="AI 教育访谈系统"
          subtitle="智能对话式学习评估"
          onCommandOpen={toggle}
        />

        <div className="flex flex-1">
          <Sidebar>
            <div className="space-y-4">
              <div className="rounded-xl bg-card p-4 shadow-card card-interactive">
                <h3 className="mb-2 font-semibold">使用说明</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• 输入回答后按 Enter 发送</li>
                  <li>• 按 Ctrl+K 打开命令面板</li>
                  <li>• 可随时撤回或跳过问题</li>
                </ul>

                <div className="mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-start gap-2"
                    onClick={() => (window.location.hash = '#admin/overview')}
                  >
                    <Shield className="h-4 w-4" />
                    后台监管仪表盘
                  </Button>
                </div>
              </div>

              {session && statsLoading && <StatsSkeleton />}

              {stats && (
                <div className="rounded-xl bg-card p-4 shadow-card card-interactive scale-in">
                  <h3 className="mb-2 font-semibold">实时统计</h3>
                  <div className="space-y-1 text-sm">
                    <p>总消息: {stats.totalMessages}</p>
                    <p>平均响应: {stats.averageResponseTime.toFixed(1)}s</p>
                  </div>
                </div>
              )}
            </div>
          </Sidebar>

          <main className="flex-1 p-4">
            <div className="mx-auto h-[calc(100vh-8rem)] max-w-4xl">
              <LazyChatbot
                messages={messages}
                onSend={handleSend}
                onUndo={() => session && undo.mutate({ sessionId: session.id })}
                onSkip={() => session && skip.mutate({ sessionId: session.id })}
                onRestart={() => void beginSession()}
                onStartInterview={beginSession}
                canUndo={canUndo()}
                canSkip={!!session}
                isLoading={isLoading}
                sessionState={sessionState}
              />
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

export default function App() {
  const hash = useHashLocation();
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {isAdminHash(hash) ? <AdminApp currentHash={hash} /> : <InterviewApp />}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
