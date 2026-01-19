import { describe, it, expect, beforeEach } from 'vitest';
import { useInterviewStore } from '@/stores/interview';
import type { Message, Session } from '@/types';

describe('InterviewStore', () => {
  beforeEach(() => {
    useInterviewStore.setState({
      session: null,
      messages: [],
      undoStack: [],
      isLoading: false,
      sessionState: 'IDLE',
    });
  });

  it('initializes with empty state', () => {
    const state = useInterviewStore.getState();

    expect(state.session).toBeNull();
    expect(state.messages).toEqual([]);
    expect(state.undoStack).toEqual([]);
    expect(state.isLoading).toBe(false);
  });

  it('sets session', () => {
    const session: Session = {
      id: 'test-session',
      status: 'active',
      currentQuestion: 1,
      totalQuestions: 5,
      createdAt: Date.now(),
      userName: '访谈者_test-session',
    };

    useInterviewStore.getState().setSession(session);
    expect(useInterviewStore.getState().session).toEqual(session);
  });

  it('adds message and saves to undo stack', () => {
    const message: Message = {
      id: '1',
      role: 'user',
      content: 'Hello',
      timestamp: Date.now(),
    };

    useInterviewStore.getState().addMessage(message);

    const state = useInterviewStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual(message);
    expect(state.undoStack).toHaveLength(1);
  });

  it('limits undo stack to 10 entries', () => {
    const { addMessage } = useInterviewStore.getState();

    for (let i = 0; i < 12; i++) {
      addMessage({
        id: `${i}`,
        role: 'user',
        content: `Message ${i}`,
        timestamp: Date.now(),
      });
    }

    expect(useInterviewStore.getState().undoStack).toHaveLength(10);
  });

  it('undoes last message', () => {
    const { addMessage, undo } = useInterviewStore.getState();

    addMessage({
      id: '1',
      role: 'user',
      content: 'First',
      timestamp: Date.now(),
    });

    addMessage({
      id: '2',
      role: 'user',
      content: 'Second',
      timestamp: Date.now(),
    });

    undo();

    const state = useInterviewStore.getState();
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].id).toBe('1');
  });

  it('canUndo returns correct state', () => {
    const { addMessage, canUndo } = useInterviewStore.getState();

    expect(canUndo()).toBe(false);

    addMessage({
      id: '0',
      role: 'assistant',
      content: 'Q1',
      timestamp: Date.now(),
    });

    addMessage({
      id: '1',
      role: 'user',
      content: 'Test',
      timestamp: Date.now(),
    });

    expect(canUndo()).toBe(true);
  });

  it('clears messages', () => {
    const { addMessage, clearMessages } = useInterviewStore.getState();

    addMessage({
      id: '1',
      role: 'user',
      content: 'Test',
      timestamp: Date.now(),
    });

    clearMessages();

    const state = useInterviewStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.undoStack).toEqual([]);
  });

  it('sets loading state', () => {
    useInterviewStore.getState().setLoading(true);
    expect(useInterviewStore.getState().isLoading).toBe(true);

    useInterviewStore.getState().setLoading(false);
    expect(useInterviewStore.getState().isLoading).toBe(false);
  });

  it('setMessages replaces all messages', () => {
    const messages: Message[] = [
      { id: '1', role: 'user', content: 'A', timestamp: Date.now() },
      { id: '2', role: 'assistant', content: 'B', timestamp: Date.now() },
    ];

    useInterviewStore.getState().setMessages(messages);
    expect(useInterviewStore.getState().messages).toEqual(messages);
  });
});
