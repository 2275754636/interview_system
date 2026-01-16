import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MessageInput } from '@/components/chat/MessageInput';

describe('MessageInput', () => {
  it('renders input and button', () => {
    render(<MessageInput onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText('输入消息...')).toBeInTheDocument();
    expect(screen.getByText('发送')).toBeInTheDocument();
  });

  it('calls onSend when button clicked', () => {
    const onSend = vi.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    const button = screen.getByText('发送');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(button);

    expect(onSend).toHaveBeenCalledWith('Test message');
  });

  it('clears input after send', () => {
    const onSend = vi.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入消息...') as HTMLInputElement;
    const button = screen.getByText('发送');

    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(button);

    expect(input.value).toBe('');
  });

  it('sends on Enter key', () => {
    const onSend = vi.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

    expect(onSend).toHaveBeenCalledWith('Test');
  });

  it('does not send on Shift+Enter', () => {
    const onSend = vi.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
  });

  it('disables input when disabled prop is true', () => {
    render(<MessageInput onSend={vi.fn()} disabled />);
    expect(screen.getByPlaceholderText('输入消息...')).toBeDisabled();
    expect(screen.getByText('发送')).toBeDisabled();
  });

  it('does not send empty messages', () => {
    const onSend = vi.fn();
    render(<MessageInput onSend={onSend} />);

    const button = screen.getByText('发送');
    fireEvent.click(button);

    expect(onSend).not.toHaveBeenCalled();
  });
});
