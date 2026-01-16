import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '@/components/chat/MessageBubble';
import type { Message } from '@/types';

describe('MessageBubble', () => {
  const userMessage: Message = {
    id: '1',
    role: 'user',
    content: 'Hello',
    timestamp: Date.now(),
  };

  const aiMessage: Message = {
    id: '2',
    role: 'assistant',
    content: 'Hi there',
    timestamp: Date.now(),
  };

  it('renders user message with correct styling', () => {
    const { container } = render(<MessageBubble message={userMessage} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(container.querySelector('.bg-primary')).toBeInTheDocument();
    expect(container.querySelector('.justify-end')).toBeInTheDocument();
  });

  it('renders AI message with correct styling', () => {
    const { container } = render(<MessageBubble message={aiMessage} />);
    expect(screen.getByText('Hi there')).toBeInTheDocument();
    expect(container.querySelector('.bg-card')).toBeInTheDocument();
    expect(container.querySelector('.justify-start')).toBeInTheDocument();
  });

  it('displays timestamp', () => {
    render(<MessageBubble message={userMessage} />);
    const timeElement = screen.getByRole('time');
    expect(timeElement).toBeInTheDocument();
  });
});
