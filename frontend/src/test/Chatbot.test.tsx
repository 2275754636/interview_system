import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Chatbot } from '@/components/chat/Chatbot';
import type { Message } from '@/types';

describe('Chatbot', () => {
  const mockMessages: Message[] = [
    { id: '1', role: 'assistant', content: 'Hello', timestamp: Date.now() },
    { id: '2', role: 'user', content: 'Hi', timestamp: Date.now() },
  ];

  it('renders messages', () => {
    render(<Chatbot messages={mockMessages} onSend={vi.fn()} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi')).toBeInTheDocument();
  });

  it('renders message input', () => {
    render(<Chatbot messages={[]} onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument();
  });

  it('calls onSend when message sent', () => {
    const onSend = vi.fn();
    render(<Chatbot messages={[]} onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    const button = screen.getByText('发送');

    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(button);

    expect(onSend).toHaveBeenCalledWith('Test');
  });

  it('renders action bar when handlers provided', () => {
    render(
      <Chatbot
        messages={[]}
        onSend={vi.fn()}
        onUndo={vi.fn()}
        onSkip={vi.fn()}
        onRestart={vi.fn()}
      />
    );

    expect(screen.getByText('撤回')).toBeInTheDocument();
    expect(screen.getByText('跳过')).toBeInTheDocument();
    expect(screen.getByText('重新开始')).toBeInTheDocument();
  });

  it('shows loading skeleton when isLoading true', () => {
    const { container } = render(<Chatbot messages={[]} onSend={vi.fn()} isLoading />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('disables input when loading', () => {
    render(<Chatbot messages={[]} onSend={vi.fn()} isLoading />);
    expect(screen.getByPlaceholderText('输入消息...')).toBeDisabled();
  });

  it('passes canUndo and canSkip to ActionBar', () => {
    render(
      <Chatbot
        messages={[]}
        onSend={vi.fn()}
        onUndo={vi.fn()}
        onSkip={vi.fn()}
        canUndo={false}
        canSkip={false}
      />
    );

    expect(screen.getByText('撤回')).toBeDisabled();
    expect(screen.getByText('跳过')).toBeDisabled();
  });
});
