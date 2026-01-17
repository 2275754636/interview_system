import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query';
import App from '@/App';

vi.mock('@/services/api', () => ({
  sessionApi: {
    start: vi.fn(() =>
      Promise.resolve({
        session: {
          id: 'test-session',
          status: 'active',
          currentQuestion: 0,
          totalQuestions: 6,
          createdAt: Date.now(),
          userName: '访谈者_test-session',
        },
        messages: [],
      })
    ),
    sendMessage: vi.fn(() =>
      Promise.resolve({ id: '1', role: 'assistant', content: 'Test', timestamp: Date.now() })
    ),
    undo: vi.fn(() => Promise.resolve([])),
    skip: vi.fn(() =>
      Promise.resolve({ id: '2', role: 'assistant', content: 'Skipped', timestamp: Date.now() })
    ),
    getStats: vi.fn(() =>
      Promise.resolve({
        totalMessages: 0,
        userMessages: 0,
        assistantMessages: 0,
        averageResponseTime: 0,
        durationSeconds: 0,
      })
    ),
  },
}));

function TestWrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('App', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('renders main interface', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByText('AI 教育访谈系统')).toBeInTheDocument();
    expect(screen.getByText('智能对话式学习评估')).toBeInTheDocument();
  });

  it('renders sidebar with instructions', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByText('使用说明')).toBeInTheDocument();
    expect(screen.getByText(/输入回答后按 Enter 发送/)).toBeInTheDocument();
  });

  it('renders chatbot component', async () => {
    render(<App />, { wrapper: TestWrapper });

    expect(await screen.findByPlaceholderText('输入消息...')).toBeInTheDocument();
  });

  it('renders command palette trigger', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByText('Ctrl+K')).toBeInTheDocument();
  });

  it('renders action bar buttons', async () => {
    render(<App />, { wrapper: TestWrapper });

    expect(await screen.findByText('撤回')).toBeInTheDocument();
    expect(await screen.findByText('跳过')).toBeInTheDocument();
    expect(await screen.findByText('重新开始')).toBeInTheDocument();
  });
});
