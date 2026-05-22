import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  Token,
  User,
  Machine,
  Booking,
  BookingCreate,
  BookingUpdate,
  TimeSlot,
  Role,
  Permission,
  LoginCredentials,
  RegisterData,
  MachineFilters,
  BookingFilters,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Функция для получения токена из localStorage
const getAuthToken = (): string | null => localStorage.getItem('access_token');

// Request interceptor для добавления токена в заголовки
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor для обработки истечения токена
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Пытаемся обновить токен
        const refreshResponse = await authAPI.refreshToken();

        // Сохраняем новые токены
        localStorage.setItem('access_token', refreshResponse.data.access_token);
        localStorage.setItem('refresh_token', refreshResponse.data.refresh_token);
        localStorage.setItem('token_type', refreshResponse.data.token_type);

        // Обновляем оригинальный запрос с новым токеном
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
        }

        return api(originalRequest);
      } catch (refreshError) {
        // Если обновление не удалось, очищаем токены и редиректим на login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_type');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Вспомогательная функция для построения query параметров
const buildQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
};

// Authentication API
export const authAPI = {
  login: (credentials: LoginCredentials) => {
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);

    return axios.post<Token>(`${API_BASE_URL}/auth/login`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },

  register: (userData: RegisterData) => api.post<User>('/auth/register', userData),

  getProfile: () => api.get<User>('/auth/me'),

  refreshToken: () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return Promise.reject('No refresh token available');
    }

    return axios.post<Token>(`${API_BASE_URL}/auth/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
  },

  getMyPermissions: () => api.get<string[]>('/rbac/users/me/permissions'),
};

// Machine API
export const machineAPI = {
  getAll: (filters?: MachineFilters) => {
    const params = buildQueryParams(filters || {});
    return api.get<Machine[]>(`/machines/${params ? `?${params}` : ''}`);
  },
  getCount: (filters?: Omit<MachineFilters, 'skip' | 'limit' | 'sort_by' | 'sort_order'>) => {
    const params = buildQueryParams(filters || {});
    return api.get<{ total: number }>(`/machines/count${params ? `?${params}` : ''}`);
  },
  getById: (id: number) => api.get<Machine>(`/machines/${id}`),
  getTimeSlots: (id: number, date: string) => 
    api.get<TimeSlot[]>(`/machines/${id}/time-slots?date=${date}`),
  create: (data: { name: string; type: string; status?: string }) => 
    api.post<Machine>('/machines/', data),
  update: (id: number, data: { name: string; type: string; status?: string }) => 
    api.put<Machine>(`/machines/${id}`, data),
  delete: (id: number) => api.delete(`/machines/${id}`),
};

// Booking API
export const bookingAPI = {
  getAll: (filters?: BookingFilters) => {
    const params = buildQueryParams(filters || {});
    return api.get<Booking[]>(`/bookings/${params ? `?${params}` : ''}`);
  },
  getCount: (filters?: Omit<BookingFilters, 'skip' | 'limit' | 'start_date' | 'end_date' | 'sort_by' | 'sort_order'>) => {
    const params = buildQueryParams(filters || {});
    return api.get<{ total: number }>(`/bookings/count${params ? `?${params}` : ''}`);
  },
  getById: (id: number) => api.get<Booking>(`/bookings/${id}`),
  getMyBookings: (skip = 0, limit = 100, status?: string) => {
    const params = buildQueryParams({ skip, limit, status });
    return api.get<Booking[]>(`/bookings/my-bookings${params ? `?${params}` : ''}`);
  },
  getByUser: (userId: number, skip = 0, limit = 100) => 
    api.get<Booking[]>(`/bookings/user/${userId}?skip=${skip}&limit=${limit}`),
  create: (data: BookingCreate) => api.post<Booking>('/bookings/', data),
  update: (id: number, data: BookingUpdate) => api.put<Booking>(`/bookings/${id}`, data),
  cancel: (id: number) => api.post<Booking>(`/bookings/${id}/cancel`),
  delete: (id: number) => api.delete<Booking>(`/bookings/${id}`),
};

// RBAC API
export const rbacAPI = {
  // Permissions
  getPermissions: (skip = 0, limit = 100) => 
    api.get<Permission[]>(`/rbac/permissions/?skip=${skip}&limit=${limit}`),
  getPermission: (id: number) => api.get<Permission>(`/rbac/permissions/${id}`),
  createPermission: (data: { name: string; description?: string }) => 
    api.post<Permission>('/rbac/permissions/', data),
  deletePermission: (id: number) => api.delete(`/rbac/permissions/${id}`),

  // Roles
  getRoles: (skip = 0, limit = 100) => 
    api.get<Role[]>(`/rbac/roles/?skip=${skip}&limit=${limit}`),
  getRole: (id: number) => api.get<Role>(`/rbac/roles/${id}`),
  createRole: (data: { name: string; description?: string; permission_ids?: number[] }) => 
    api.post<Role>('/rbac/roles/', data),
  updateRole: (id: number, data: { name: string; description?: string; permission_ids?: number[] }) => 
    api.put<Role>(`/rbac/roles/${id}`, data),
  deleteRole: (id: number) => api.delete(`/rbac/roles/${id}`),

  // User roles
  assignRoleToUser: (userId: number, roleId: number) => 
    api.post(`/rbac/users/${userId}/assign-role/${roleId}`),
};

// User API
export const userAPI = {
  getAll: (skip = 0, limit = 100) => api.get<User[]>(`/users/?skip=${skip}&limit=${limit}`),
  getById: (id: number) => api.get<User>(`/users/${id}`),
  update: (id: number, data: Partial<User>) => api.put<User>(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
};

// Files API (S3)
export const filesAPI = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  download: (objectName: string) => 
    api.get(`/files/${encodeURIComponent(objectName)}`, { responseType: 'blob' }),
  getPresignedUrl: (objectName: string, expiresIn = 3600) => 
    api.get<{ url: string; expires_in: number }>(
      `/files/${encodeURIComponent(objectName)}/url?expires=${expiresIn}`
    ),
  delete: (objectName: string) => api.delete(`/files/${encodeURIComponent(objectName)}`),
  list: (prefix?: string) => {
    const params = prefix ? `?prefix=${encodeURIComponent(prefix)}` : '';
    return api.get<{ files: string[]; count: number }>(`/files/${params}`);
  },
};

// External API (weather)
export const externalAPI = {
  getWeather: (lat: number, lon: number) =>
    api.get(`/external/weather?lat=${lat}&lon=${lon}`),
  getForecast: (lat: number, lon: number, days = 3) =>
    api.get(`/external/weather/forecast?lat=${lat}&lon=${lon}&days=${days}`),
  getRecommendation: (lat: number, lon: number) =>
    api.get<{ recommendation: string; location: { lat: number; lon: number } }>(
      `/external/weather/recommendation?lat=${lat}&lon=${lon}`
    ),
};

export default api;
