import { ErrorCode } from '@/types';
import type {
  Message,
  Session,
  SessionStats,
  StartSessionResult,
  PublicUrlResponse,
  ErrorResponse,
  ErrorCode as ErrorCodeType,
} from '@/types';

type ApiSession = {
  id: string;
  status: 'idle' | 'active' | 'completed';
  current_question: number;
  total_questions: number;
  created_at: number;
  user_name: string;
};

type ApiSessionStats = {
  total_messages: number;
  user_messages: number;
  assistant_messages: number;
  average_response_time: number;
  duration_seconds: number;
};

type ApiStartSessionResult = {
  session: ApiSession;
  messages: Message[];
};

type ApiPublicUrlResponse = {
  url: string | null;
  is_public: boolean;
};

const ERROR_CODE_VALUES = new Set<string>(Object.values(ErrorCode));

function parseErrorCode(code: unknown): ErrorCodeType {
  if (typeof code === 'string' && ERROR_CODE_VALUES.has(code)) {
    return code as ErrorCodeType;
  }
  return ErrorCode.INTERNAL_ERROR;
}

function toSession(api: ApiSession): Session {
  return {
    id: api.id,
    status: api.status,
    currentQuestion: api.current_question,
    totalQuestions: api.total_questions,
    createdAt: api.created_at,
    userName: api.user_name,
  };
}

function toSessionStats(api: ApiSessionStats): SessionStats {
  return {
    totalMessages: api.total_messages,
    userMessages: api.user_messages,
    assistantMessages: api.assistant_messages,
    averageResponseTime: api.average_response_time,
    durationSeconds: api.duration_seconds,
  };
}

function toPublicUrlResponse(api: ApiPublicUrlResponse): PublicUrlResponse {
  return {
    url: api.url,
    isPublic: api.is_public,
  };
}

function getApiBase(): string {
  const fromEnv = (import.meta.env.VITE_API_URL || '').trim();
  if (fromEnv) return fromEnv;
  if (import.meta.env.PROD) {
    throw new Error('缺少 VITE_API_URL 配置，请在前端环境变量中设置后端 API 地址。');
  }
  return 'http://localhost:8000/api';
}

const API_BASE = getApiBase();

export class ApiError extends Error {
  code: ErrorCodeType;
  detail: string;
  statusCode: number;
  details?: Record<string, unknown>;

  constructor(
    code: ErrorCodeType,
    detail: string,
    statusCode: number,
    details?: Record<string, unknown>
  ) {
    super(detail);
    this.name = 'ApiError';
    this.code = code;
    this.detail = detail;
    this.statusCode = statusCode;
    this.details = details;
  }
}

interface ApiConfig<TBody = unknown> {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: TBody;
  headers?: Record<string, string>;
}

function isErrorResponse(data: unknown): data is ErrorResponse {
  if (!data || typeof data !== 'object') return false;
  const error = (data as { error?: unknown }).error;
  if (!error || typeof error !== 'object') return false;
  const code = (error as { code?: unknown }).code;
  const message = (error as { message?: unknown }).message;
  return typeof message === 'string' && typeof code === 'string';
}

async function readErrorResponse(response: Response): Promise<ErrorResponse> {
  const fallback: ErrorResponse = {
    error: { code: ErrorCode.INTERNAL_ERROR, message: `HTTP ${response.status}` },
  };

  try {
    const data: unknown = await response.json();
    if (!isErrorResponse(data)) return fallback;
    return {
      error: {
        code: parseErrorCode(data.error.code),
        message: data.error.message || fallback.error.message,
        details: data.error.details,
      },
    };
  } catch (e) {
    console.error('[API] 解析错误响应失败:', e);
    return fallback;
  }
}

async function request<TResponse, TBody = unknown>(
  endpoint: string,
  config?: ApiConfig<TBody>
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: config?.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...config?.headers,
    },
    body: config?.body !== undefined ? JSON.stringify(config.body) : undefined,
  });

  if (!response.ok) {
    const errorData = await readErrorResponse(response);
    throw new ApiError(
      parseErrorCode(errorData.error.code),
      errorData.error.message,
      response.status,
      errorData.error.details
    );
  }

  return response.json();
}

export const sessionApi = {
  start: (topics?: string[]): Promise<StartSessionResult> =>
    request<ApiStartSessionResult, { topics?: string[] }>('/session/start', {
      method: 'POST',
      body: { topics },
    }).then(({ session, messages }) => ({ session: toSession(session), messages })),

  sendMessage: (sessionId: string, text: string) =>
    request<Message, { text: string }>(`/session/${sessionId}/message`, {
      method: 'POST',
      body: { text },
    }),

  getMessages: (sessionId: string) =>
    request<Message[]>(`/session/${sessionId}/messages`),

  undo: (sessionId: string) =>
    request<Message[]>(`/session/${sessionId}/undo`, { method: 'POST' }),

  skip: (sessionId: string) =>
    request<Message>(`/session/${sessionId}/skip`, { method: 'POST' }),

  restart: (sessionId: string) =>
    request<ApiSession>(`/session/${sessionId}/restart`, { method: 'POST' }).then(toSession),

  getStats: (sessionId: string) =>
    request<ApiSessionStats>(`/session/${sessionId}/stats`).then(toSessionStats),
};

export const publicUrlApi = {
  get: () => request<ApiPublicUrlResponse>('/public-url').then(toPublicUrlResponse),
};
