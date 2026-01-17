import type { Message, Session, SessionStats, StartSessionResult, ErrorResponse, ErrorCode } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export class ApiError extends Error {
  constructor(
    public code: ErrorCode,
    public detail: string,
    public statusCode: number,
    public details?: Record<string, unknown>
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

interface ApiConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, config?: ApiConfig): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: config?.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...config?.headers,
    },
    body: config?.body ? JSON.stringify(config.body) : undefined,
  });

  if (!response.ok) {
    const errorData: ErrorResponse = await response.json().catch(() => ({
      error: { code: 'INTERNAL_ERROR' as ErrorCode, message: `HTTP ${response.status}` },
    }));
    throw new ApiError(
      errorData.error.code,
      errorData.error.message,
      response.status,
      errorData.error.details
    );
  }

  return response.json();
}

export const sessionApi = {
  start: async (topics?: string[]) => {
    const session = await request<Session>('/session/start', { method: 'POST', body: { topics } });
    const messages = await request<Message[]>(`/session/${session.id}/messages`);
    return { session, messages } satisfies StartSessionResult;
  },

  sendMessage: (sessionId: string, text: string) =>
    request<Message>(`/session/${sessionId}/message`, { method: 'POST', body: { text } }),

  getMessages: (sessionId: string) =>
    request<Message[]>(`/session/${sessionId}/messages`),

  undo: (sessionId: string) =>
    request<Message[]>(`/session/${sessionId}/undo`, { method: 'POST' }),

  skip: (sessionId: string) =>
    request<Message>(`/session/${sessionId}/skip`, { method: 'POST' }),

  restart: (sessionId: string) =>
    request<Session>(`/session/${sessionId}/restart`, { method: 'POST' }),

  getStats: (sessionId: string) =>
    request<SessionStats>(`/session/${sessionId}/stats`),
};
