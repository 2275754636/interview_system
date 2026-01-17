export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface Session {
  id: string;
  status: 'idle' | 'active' | 'completed';
  current_question: number;
  total_questions: number;
  created_at: number;
  user_name: string;
}

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface SessionStats {
  total_messages: number;
  user_messages: number;
  assistant_messages: number;
  average_response_time: number;
  duration_seconds: number;
}

export interface StartSessionResult {
  session: Session;
  messages: Message[];
}

export enum ErrorCode {
  SESSION_NOT_FOUND = 'SESSION_NOT_FOUND',
  SESSION_COMPLETED = 'SESSION_COMPLETED',
  NO_MESSAGES_TO_UNDO = 'NO_MESSAGES_TO_UNDO',
  INVALID_INPUT = 'INVALID_INPUT',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
}

export interface ErrorDetail {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

