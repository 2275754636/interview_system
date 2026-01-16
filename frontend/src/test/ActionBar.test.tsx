import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ActionBar } from '@/components/chat/ActionBar';

describe('ActionBar', () => {
  it('renders undo button when onUndo provided', () => {
    render(<ActionBar onUndo={vi.fn()} />);
    expect(screen.getByText('撤回')).toBeInTheDocument();
  });

  it('renders skip button when onSkip provided', () => {
    render(<ActionBar onSkip={vi.fn()} />);
    expect(screen.getByText('跳过')).toBeInTheDocument();
  });

  it('renders restart button when onRestart provided', () => {
    render(<ActionBar onRestart={vi.fn()} />);
    expect(screen.getByText('重新开始')).toBeInTheDocument();
  });

  it('calls onUndo when undo button clicked', () => {
    const onUndo = vi.fn();
    render(<ActionBar onUndo={onUndo} canUndo />);

    fireEvent.click(screen.getByText('撤回'));
    expect(onUndo).toHaveBeenCalled();
  });

  it('calls onSkip when skip button clicked', () => {
    const onSkip = vi.fn();
    render(<ActionBar onSkip={onSkip} canSkip />);

    fireEvent.click(screen.getByText('跳过'));
    expect(onSkip).toHaveBeenCalled();
  });

  it('calls onRestart when restart button clicked', () => {
    const onRestart = vi.fn();
    render(<ActionBar onRestart={onRestart} />);

    fireEvent.click(screen.getByText('重新开始'));
    expect(onRestart).toHaveBeenCalled();
  });

  it('disables undo button when canUndo is false', () => {
    render(<ActionBar onUndo={vi.fn()} canUndo={false} />);
    expect(screen.getByText('撤回')).toBeDisabled();
  });

  it('disables skip button when canSkip is false', () => {
    render(<ActionBar onSkip={vi.fn()} canSkip={false} />);
    expect(screen.getByText('跳过')).toBeDisabled();
  });

  it('does not render buttons when handlers not provided', () => {
    render(<ActionBar />);
    expect(screen.queryByText('撤回')).not.toBeInTheDocument();
    expect(screen.queryByText('跳过')).not.toBeInTheDocument();
    expect(screen.queryByText('重新开始')).not.toBeInTheDocument();
  });
});
