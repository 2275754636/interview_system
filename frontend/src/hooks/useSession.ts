import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { sessionApi } from '@/services/api';
import { useInterviewStore } from '@/stores';
import type { Message } from '@/types';
import { createClientId } from '@/lib/ids';
import { STATS_REFETCH_INTERVAL_MS, STATS_STALE_TIME_MS } from '@/lib/query';

export function useStartSession() {
  const { setSession, setMessages, setLoading } = useInterviewStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sessionApi.start,
    onMutate: () => setLoading(true),
    onSuccess: ({ session, messages }) => {
      setSession(session);
      setMessages(messages);
      queryClient.invalidateQueries({ queryKey: ['session'] });
    },
    onSettled: () => setLoading(false),
  });
}

type SendMessageVariables = { sessionId: string; text: string };

function createUserMessage(content: string): Message {
  return {
    id: createClientId('user_'),
    role: 'user',
    content,
    timestamp: Date.now(),
  };
}

export function useSendMessage() {
  const { addMessage, setLoading } = useInterviewStore();

  return useMutation({
    mutationFn: ({ sessionId, text }: SendMessageVariables) => {
      if (!sessionId) throw new Error('Missing sessionId');
      return sessionApi.sendMessage(sessionId, text);
    },
    onMutate: ({ text }) => {
      setLoading(true);
      addMessage(createUserMessage(text));
    },
    onSuccess: (message) => addMessage(message),
    onSettled: () => setLoading(false),
  });
}

export function useUndo() {
  const { setMessages } = useInterviewStore();

  return useMutation({
    mutationFn: ({ sessionId }: { sessionId: string }) => sessionApi.undo(sessionId),
    onSuccess: (messages) => setMessages(messages),
  });
}

export function useSkip() {
  const { addMessage } = useInterviewStore();

  return useMutation({
    mutationFn: ({ sessionId }: { sessionId: string }) => sessionApi.skip(sessionId),
    onSuccess: (message) => addMessage(message),
  });
}

export function useSessionStats(sessionId: string | null) {
  return useQuery({
    queryKey: ['session', sessionId, 'stats'],
    queryFn: () => sessionApi.getStats(sessionId!),
    enabled: !!sessionId,
    staleTime: STATS_STALE_TIME_MS,
    refetchInterval: STATS_REFETCH_INTERVAL_MS,
  });
}
