// Типы для RBAC
export interface Permission {
  id: number;
  name: string;
  description?: string;
  created_at: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  permissions?: Permission[];
}

// Типы для пользователя
export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  is_active: boolean;
  role_id?: number;
  role?: Role;
  created_at: string;
}

// Типы для машины
export interface Machine {
  id: number;
  name: string;
  type: 'washer' | 'dryer';
  status: 'available' | 'in_use' | 'maintenance';
  created_at: string;
}

// Типы для бронирования
export interface Booking {
  id: number;
  machine_id: number;
  user_id?: number;
  user_name: string;
  start_time: string;
  end_time: string;
  status: 'active' | 'completed' | 'cancelled';
  created_at: string;
  machine?: Machine;
}

// Типы для временных слотов
export interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
  booked_by?: string;
}

// Типы для токенов
export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Типы для форм
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  full_name?: string;
  password: string;
}

export interface BookingCreate {
  machine_id: number;
  start_time: string;
  end_time: string;
}

export interface BookingUpdate {
  machine_id?: number;
  start_time?: string;
  end_time?: string;
}

// Параметры фильтрации для машин
export interface MachineFilters {
  skip?: number;
  limit?: number;
  search?: string;
  machine_type?: string;
  status?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Параметры фильтрации для бронирований
export interface BookingFilters {
  skip?: number;
  limit?: number;
  user_id?: number;
  machine_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Ответ с пагинацией
export interface PaginatedResponse<T> {
  data: T[];
  total?: number;
  skip: number;
  limit: number;
}

// Контекст аутентификации
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}
