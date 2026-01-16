import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommandPalette } from '@/components/common/CommandPalette';

describe('CommandPalette', () => {
  const mockCommands = [
    { id: '1', label: 'Open Settings', onSelect: vi.fn() },
    { id: '2', label: 'Toggle Theme', shortcut: '⌘T', onSelect: vi.fn() },
    { id: '3', label: 'Search Files', icon: <span>🔍</span>, onSelect: vi.fn() },
  ];

  it('renders when open', () => {
    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={vi.fn()}
        commands={mockCommands}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(
      <CommandPalette
        isOpen={false}
        onOpenChange={vi.fn()}
        commands={mockCommands}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('displays all commands', () => {
    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={vi.fn()}
        commands={mockCommands}
      />
    );

    expect(screen.getByText('Open Settings')).toBeInTheDocument();
    expect(screen.getByText('Toggle Theme')).toBeInTheDocument();
    expect(screen.getByText('Search Files')).toBeInTheDocument();
  });

  it('displays shortcuts', () => {
    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={vi.fn()}
        commands={mockCommands}
      />
    );

    expect(screen.getByText('⌘T')).toBeInTheDocument();
  });

  it('filters commands on search', () => {
    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={vi.fn()}
        commands={mockCommands}
        placeholder="Search commands..."
      />
    );

    const input = screen.getByPlaceholderText('Search commands...');
    fireEvent.change(input, { target: { value: 'theme' } });

    expect(screen.getByText('Toggle Theme')).toBeInTheDocument();
    expect(screen.queryByText('Open Settings')).not.toBeInTheDocument();
  });

  it('calls onSelect when command clicked', () => {
    const onSelect = vi.fn();
    const commands = [{ id: '1', label: 'Test Command', onSelect }];

    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={vi.fn()}
        commands={commands}
      />
    );

    fireEvent.click(screen.getByText('Test Command'));
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('calls onOpenChange when closed', () => {
    const onOpenChange = vi.fn();

    render(
      <CommandPalette
        isOpen={true}
        onOpenChange={onOpenChange}
        commands={mockCommands}
      />
    );

    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
