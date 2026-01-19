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

export interface AdminOverviewSummary {
  totalSessions: number;
  totalMessages: number;
  activeUsers: number;
  avgDepthScore: number;
}

export interface AdminTimeSeriesPoint {
  bucket: string;
  sessions: number;
  messages: number;
  uniqueUsers: number;
  avgDepthScore: number;
}

export interface AdminUserActivityRow {
  userName: string;
  sessions: number;
  messages: number;
}

export interface AdminTopicRow {
  topic: string;
  messages: number;
  avgDepthScore: number;
}

export interface AdminOverviewResponse {
  summary: AdminOverviewSummary;
  timeSeries: AdminTimeSeriesPoint[];
  topUsers: AdminUserActivityRow[];
  topTopics: AdminTopicRow[];
}

export interface AdminListResponse<TItem = Record<string, unknown>> {
  total: number;
  items: TItem[];
}

export interface AdminSearchRow {
  id: number;
  sessionId: string;
  userName: string;
  timestamp: string;
  topic: string;
  questionType: string;
  question: string;
  answer: string;
  depthScore: number;
  isAiGenerated: boolean;
}

export const ErrorCode = {
  SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',
  SESSION_COMPLETED: 'SESSION_COMPLETED',
  NO_MESSAGES_TO_UNDO: 'NO_MESSAGES_TO_UNDO',
  INVALID_INPUT: 'INVALID_INPUT',
  ADMIN_DISABLED: 'ADMIN_DISABLED',
  ADMIN_UNAUTHORIZED: 'ADMIN_UNAUTHORIZED',
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
