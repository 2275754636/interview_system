import { create } from 'zustand';
import type { Message, Session } from '@/types';

const MAX_UNDO_STACK = 10;

interface InterviewState {
  session: Session | null;
  messages: Message[];
  undoStack: Message[][];
  isLoading: boolean;

  setSession: (session: Session | null) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  undo: () => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  canUndo: () => boolean;
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  session: null,
  messages: [],
  undoStack: [],
  isLoading: false,

  setSession: (session) => set({ session }),

  addMessage: (message) =>
    set((state) => {
      const newMessages = [...state.messages, message];
      const newStack = [...state.undoStack, state.messages].slice(-MAX_UNDO_STACK);

      return {
        messages: newMessages,
        undoStack: newStack,
      };
    }),

  setMessages: (messages) => set({ messages, undoStack: [] }),

  undo: () =>
    set((state) => {
      if (state.undoStack.length === 0) return state;

      const previous = state.undoStack[state.undoStack.length - 1];
      const newStack = state.undoStack.slice(0, -1);

      return {
        messages: previous,
        undoStack: newStack,
      };
    }),

  clearMessages: () => set({ messages: [], undoStack: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  canUndo: () => get().messages.length > 1,
}));
