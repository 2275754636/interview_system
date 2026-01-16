import { describe, it, expect, beforeEach } from 'vitest';
import { useCommandStore } from '@/stores/command';

describe('CommandStore', () => {
  beforeEach(() => {
    useCommandStore.setState({ isOpen: false });
  });

  it('initializes with closed state', () => {
    expect(useCommandStore.getState().isOpen).toBe(false);
  });

  it('opens command palette', () => {
    useCommandStore.getState().open();
    expect(useCommandStore.getState().isOpen).toBe(true);
  });

  it('closes command palette', () => {
    useCommandStore.setState({ isOpen: true });
    useCommandStore.getState().close();
    expect(useCommandStore.getState().isOpen).toBe(false);
  });

  it('toggles command palette', () => {
    const { toggle } = useCommandStore.getState();

    toggle();
    expect(useCommandStore.getState().isOpen).toBe(true);

    toggle();
    expect(useCommandStore.getState().isOpen).toBe(false);
  });
});
