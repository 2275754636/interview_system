import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStartSession, useSendMessage, useUndo, useSkip, useSessionStats } from '@/hooks/useSession';
import { useInterviewStore } from '@/stores';
import { sessionApi } from '@/services/api';
import type { ReactNode } from 'react';

vi.mock('@/services/api');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

afterEach(() => {
  vi.clearAllMocks();
});

describe('useStartSession', () => {
  beforeEach(() => {
    useInterviewStore.setState({
      session: null,
      messages: [],
      isLoading: false,
    });
  });

  it('calls sessionApi.start and updates store', async () => {
    const mockSession = {
      id: 'session-1',
      status: 'active' as const,
      current_question: 0,
      total_questions: 10,
      created_at: Date.now(),
      user_name: '访谈者_session-1',
    };
    const mockMessages = [
      { id: 'msg-1', role: 'assistant' as const, content: 'Q1', timestamp: Date.now() },
    ];

    vi.mocked(sessionApi.start).mockResolvedValueOnce({ session: mockSession, messages: mockMessages });

    const { result } = renderHook(() => useStartSession(), {
      wrapper: createWrapper(),
    });

    result.current.mutate(['react']);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calls = vi.mocked(sessionApi.start).mock.calls;
    expect(calls[0][0]).toEqual(['react']);
    expect(useInterviewStore.getState().session).toEqual(mockSession);
    expect(useInterviewStore.getState().messages).toEqual(mockMessages);
  });

  it('sets loading state during mutation', async () => {
    const mockSession = {
      id: 'session-1',
      status: 'active' as const,
      current_question: 0,
      total_questions: 10,
      created_at: Date.now(),
      user_name: '访谈者_session-1',
    };
    const mockMessages = [
      { id: 'msg-1', role: 'assistant' as const, content: 'Q1', timestamp: Date.now() },
    ];

    vi.mocked(sessionApi.start).mockImplementation(
      () =>
        new Promise((resolve) => setTimeout(() => resolve({ session: mockSession, messages: mockMessages }), 50))
    );

    const { result } = renderHook(() => useStartSession(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(useInterviewStore.getState().isLoading).toBe(true));

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(useInterviewStore.getState().isLoading).toBe(false);
  });
});

describe('useSendMessage', () => {
  beforeEach(() => {
    useInterviewStore.setState({ messages: [], isLoading: false });
  });

  it('sends message and adds to store', async () => {
    const mockMessage = {
      id: 'msg-1',
      role: 'assistant' as const,
      content: 'Hello back',
      timestamp: Date.now(),
    };

    vi.mocked(sessionApi.sendMessage).mockResolvedValueOnce(mockMessage);

    const { result } = renderHook(() => useSendMessage(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ sessionId: 'session-1', text: 'Hello' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(sessionApi.sendMessage).toHaveBeenCalledWith('session-1', 'Hello');
    expect(useInterviewStore.getState().messages).toContainEqual(mockMessage);
    expect(useInterviewStore.getState().messages).toContainEqual(
      expect.objectContaining({ role: 'user', content: 'Hello' })
    );
  });
});

describe('useUndo', () => {
  beforeEach(() => {
    useInterviewStore.setState({ messages: [], isLoading: false });
  });

  it('calls undo and updates messages', async () => {
    const mockMessages = [
      { id: 'msg-1', role: 'user' as const, content: 'Hi', timestamp: Date.now() },
    ];

    vi.mocked(sessionApi.undo).mockResolvedValueOnce(mockMessages);

    const { result } = renderHook(() => useUndo(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ sessionId: 'session-1' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(sessionApi.undo).toHaveBeenCalledWith('session-1');
    expect(useInterviewStore.getState().messages).toEqual(mockMessages);
  });
});

describe('useSkip', () => {
  it('skips question and adds message', async () => {
    const mockMessage = {
      id: 'msg-2',
      role: 'assistant' as const,
      content: 'Skipped',
      timestamp: Date.now(),
    };

    vi.mocked(sessionApi.skip).mockResolvedValueOnce(mockMessage);

    const { result } = renderHook(() => useSkip(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ sessionId: 'session-1' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(sessionApi.skip).toHaveBeenCalledWith('session-1');
    expect(useInterviewStore.getState().messages).toContainEqual(mockMessage);
  });
});

describe('useSessionStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches stats when sessionId is provided', async () => {
    const mockStats = {
      total_messages: 10,
      user_messages: 5,
      assistant_messages: 5,
      average_response_time: 1.2,
      duration_seconds: 60,
    };

    vi.mocked(sessionApi.getStats).mockResolvedValueOnce(mockStats);

    const { result } = renderHook(() => useSessionStats('session-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(sessionApi.getStats).toHaveBeenCalledWith('session-1');
    expect(result.current.data).toEqual(mockStats);
  });

  it('does not fetch when sessionId is null', async () => {
    const { result } = renderHook(() => useSessionStats(null), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isFetching).toBe(false), { timeout: 100 });

    expect(sessionApi.getStats).not.toHaveBeenCalled();
  });
});
