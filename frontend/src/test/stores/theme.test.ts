import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useThemeStore } from '@/stores/theme';

describe('ThemeStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useThemeStore.setState({ mode: 'system' });
  });

  it('initializes with system mode', () => {
    expect(useThemeStore.getState().mode).toBe('system');
  });

  it('sets theme mode', () => {
    useThemeStore.getState().setMode('dark');
    expect(useThemeStore.getState().mode).toBe('dark');

    useThemeStore.getState().setMode('light');
    expect(useThemeStore.getState().mode).toBe('light');
  });

  it('persists theme to localStorage', () => {
    useThemeStore.getState().setMode('dark');

    const stored = localStorage.getItem('theme-storage');
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed.state.mode).toBe('dark');
  });
});
