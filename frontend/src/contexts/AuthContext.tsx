import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';
import { User, AuthContextType, LoginCredentials, RegisterData } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const response = await authAPI.getProfile();
        setUser(response.data);
      } catch (error) {
        console.error('Error loading user profile:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_type');
      }
    }
    setIsLoading(false);
  };

  const login = async (credentials: LoginCredentials) => {
    const response = await authAPI.login(credentials);
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    localStorage.setItem('token_type', response.data.token_type);
    
    const profileResponse = await authAPI.getProfile();
    setUser(profileResponse.data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
    setUser(null);
  };

  const register = async (data: RegisterData) => {
    await authAPI.register(data);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user?.role) return false;
    if (user.role.name === 'admin') return true;
    
    return user.role.permissions?.some(p => p.name === permission) ?? false;
  };

  const hasRole = (roleName: string): boolean => {
    if (!user?.role) return false;
    return user.role.name === roleName;
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
    hasPermission,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
