export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface Session {
  id: string;
  status: 'idle' | 'active' | 'completed';
  currentQuestion: number;
  totalQuestions: number;
  createdAt: number;
  userName: string;
}

export type ThemeMode = 'light' | 'dark' | 'system';

export interface SessionStats {
  totalMessages: number;
  userMessages: number;
  assistantMessages: number;
  averageResponseTime: number;
  durationSeconds: number;
}

export interface StartSessionResult {
  session: Session;
  messages: Message[];
}

export interface PublicUrlResponse {
  url: string | null;
  isPublic: boolean;
}

export const ErrorCode = {
  SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',
  SESSION_COMPLETED: 'SESSION_COMPLETED',
  NO_MESSAGES_TO_UNDO: 'NO_MESSAGES_TO_UNDO',
  INVALID_INPUT: 'INVALID_INPUT',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCode = (typeof ErrorCode)[keyof typeof ErrorCode];

export interface ErrorDetail {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

