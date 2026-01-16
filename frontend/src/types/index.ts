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
