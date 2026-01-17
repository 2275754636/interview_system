import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiError, sessionApi } from '@/services/api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const originalFetch = global.fetch;

describe('sessionApi', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error 测试环境中 fetch 可能不存在
      delete global.fetch;
    }
  });

  describe('start', () => {
    it('sends POST to /session/start', async () => {
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

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: mockSession, messages: mockMessages }),
      });

      const result = await sessionApi.start(['react', 'typescript']);

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/start`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topics: ['react', 'typescript'] }),
        })
      );

      expect(result).toEqual({
        session: {
          id: mockSession.id,
          status: mockSession.status,
          currentQuestion: mockSession.current_question,
          totalQuestions: mockSession.total_questions,
          createdAt: mockSession.created_at,
          userName: mockSession.user_name,
        },
        messages: mockMessages,
      });
    });

    it('throws on non-ok response', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: { code: 'INTERNAL_ERROR', message: 'HTTP 500' } }),
      });

      await expect(sessionApi.start()).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe('sendMessage', () => {
    it('sends POST to /session/:id/message', async () => {
      const mockMessage = {
        id: 'msg-1',
        role: 'assistant' as const,
        content: 'Hello back',
        timestamp: Date.now(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessage,
      });

      const result = await sessionApi.sendMessage('session-1', 'Hello');

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/session-1/message`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ text: 'Hello' }),
        })
      );
      expect(result).toEqual(mockMessage);
    });
  });

  describe('undo', () => {
    it('sends POST to /session/:id/undo', async () => {
      const mockResponse = [];

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sessionApi.undo('session-1');

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/session-1/undo`,
        expect.objectContaining({ method: 'POST' })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('skip', () => {
    it('sends POST to /session/:id/skip', async () => {
      const mockMessage = {
        id: 'msg-2',
        role: 'assistant' as const,
        content: 'Skipped',
        timestamp: Date.now(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessage,
      });

      const result = await sessionApi.skip('session-1');

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/session-1/skip`,
        expect.objectContaining({ method: 'POST' })
      );
      expect(result).toEqual(mockMessage);
    });
  });

  describe('restart', () => {
    it('sends POST to /session/:id/restart', async () => {
      const mockSession = {
        id: 'session-2',
        status: 'active' as const,
        current_question: 0,
        total_questions: 10,
        created_at: Date.now(),
        user_name: '访谈者_session-2',
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      });

      const result = await sessionApi.restart('session-1');

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/session-1/restart`,
        expect.objectContaining({ method: 'POST' })
      );
      expect(result).toEqual({
        id: mockSession.id,
        status: mockSession.status,
        currentQuestion: mockSession.current_question,
        totalQuestions: mockSession.total_questions,
        createdAt: mockSession.created_at,
        userName: mockSession.user_name,
      });
    });
  });

  describe('getStats', () => {
    it('sends GET to /session/:id/stats', async () => {
      const mockStats = {
        total_messages: 10,
        user_messages: 5,
        assistant_messages: 5,
        average_response_time: 1.2,
        duration_seconds: 60,
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      });

      const result = await sessionApi.getStats('session-1');

      expect(global.fetch).toHaveBeenCalledWith(
        `${BASE_URL}/session/session-1/stats`,
        expect.objectContaining({ method: 'GET' })
      );
      expect(result).toEqual({
        totalMessages: mockStats.total_messages,
        userMessages: mockStats.user_messages,
        assistantMessages: mockStats.assistant_messages,
        averageResponseTime: mockStats.average_response_time,
        durationSeconds: mockStats.duration_seconds,
      });
    });
  });
});
