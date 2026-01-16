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
          current_question: 0,
          total_questions: 6,
          created_at: Date.now(),
          user_name: '访谈者_test-session',
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
        total_messages: 0,
        user_messages: 0,
        assistant_messages: 0,
        average_response_time: 0,
        duration_seconds: 0,
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

  it('renders chatbot component', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument();
  });

  it('renders command palette trigger', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByText('Ctrl+K')).toBeInTheDocument();
  });

  it('renders action bar buttons', () => {
    render(<App />, { wrapper: TestWrapper });

    expect(screen.getByText('撤回')).toBeInTheDocument();
    expect(screen.getByText('跳过')).toBeInTheDocument();
    expect(screen.getByText('重新开始')).toBeInTheDocument();
  });
});
