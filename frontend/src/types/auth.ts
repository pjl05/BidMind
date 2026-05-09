export interface User {
  user_id: string;
  email: string;
  nickname: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse {
  user_id: string;
  email: string;
  nickname: string;
}

export interface Task {
  task_id: string;
  file_name: string;
  status: string;
  progress: number;
  llm_cost: number;
  created_at: string;
  completed_at: string | null;
}

export interface TaskListResponse {
  total: number;
  page: number;
  items: Task[];
}