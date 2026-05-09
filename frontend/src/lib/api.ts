import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface ApiResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

export const authService = {
  register: async (email: string, password: string, nickname: string) => {
    const response = await api.post<ApiResponse>('/auth/register', {
      email,
      password,
      nickname,
    });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post<ApiResponse>('/auth/login', {
      email,
      password,
    });
    if (response.data.data?.access_token) {
      Cookies.set('access_token', response.data.data.access_token, { expires: 1 });
    }
    return response.data;
  },

  getMe: async () => {
    const response = await api.get<ApiResponse>('/auth/me');
    return response.data;
  },

  logout: () => {
    Cookies.remove('access_token');
  },
};

export const taskService = {
  create: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const token = Cookies.get('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await axios.post(`${API_URL}/tasks`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  list: async (page = 1, pageSize = 10, status?: string) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
    if (status) params.append('status', status);

    const response = await api.get<ApiResponse>(`/tasks?${params}`);
    return response.data;
  },
};

export default api;