import { create } from 'zustand';
import type { Message, Session } from '@/types';

const MAX_UNDO_STACK = 10;

export type SessionState = 'IDLE' | 'INITIALIZING' | 'ACTIVE' | 'FINISHED';

function deriveSessionState(session: Session | null, messages: Message[]): SessionState {
  if (!session) return 'IDLE';
  if (session.status === 'completed') return 'FINISHED';
  if (messages.some((m) => m.role === 'assistant')) return 'ACTIVE';
  return 'INITIALIZING';
}

interface InterviewState {
  session: Session | null;
  messages: Message[];
  undoStack: Message[][];
  isLoading: boolean;
  sessionState: SessionState;

  setSession: (session: Session | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  undo: () => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setSessionState: (state: SessionState) => void;
  canUndo: () => boolean;
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  session: null,
  messages: [],
  undoStack: [],
  isLoading: false,
  sessionState: 'IDLE',

  setSession: (session) =>
    set((state) => ({
      session,
      sessionState: deriveSessionState(session, state.messages),
    })),

  addMessage: (message) =>
    set((state) => {
      const newMessages = [...state.messages, message];
      const newStack = [...state.undoStack, state.messages].slice(-MAX_UNDO_STACK);

      return {
        messages: newMessages,
        undoStack: newStack,
        sessionState: deriveSessionState(state.session, newMessages),
      };
    }),

  setMessages: (messages) =>
    set((state) => ({
      messages,
      undoStack: [],
      sessionState: deriveSessionState(state.session, messages),
    })),

  undo: () =>
    set((state) => {
      if (state.undoStack.length === 0) return state;

      const previous = state.undoStack[state.undoStack.length - 1];
      const newStack = state.undoStack.slice(0, -1);

      return {
        messages: previous,
        undoStack: newStack,
        sessionState: deriveSessionState(state.session, previous),
      };
    }),

  clearMessages: () => set({ messages: [], undoStack: [], sessionState: 'IDLE' }),

  setLoading: (loading) => set({ isLoading: loading }),

  setSessionState: (sessionState) => set({ sessionState }),

  canUndo: () => get().undoStack.length > 0,
}));
