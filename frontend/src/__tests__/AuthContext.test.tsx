/**
 * Тесты для AuthContext.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Моки для API
jest.mock('../services/api', () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    getProfile: jest.fn(),
  },
}));

// Тестовый компонент для использования контекста
const TestComponent: React.FC = () => {
  const { user, isAuthenticated, isLoading, hasPermission, hasRole } = useAuth();
  
  return (
    <div>
      <div data-testid="user">{user?.username || 'Not logged in'}</div>
      <div data-testid="authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="loading">{isLoading.toString()}</div>
      <div data-testid="has-admin-role">{hasRole('admin').toString()}</div>
    </div>
  );
};

const renderWithAuthProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('initial state is not authenticated', () => {
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockRejectedValue(new Error('Not authenticated'));

    renderWithAuthProvider(<TestComponent />);

    expect(screen.getByTestId('authenticated').textContent).toBe('false');
  });

  test('hasRole returns false for non-admin user', () => {
    const { authAPI } = require('../services/api');
    
    // Мокаем пользователя без роли admin
    authAPI.getProfile.mockResolvedValue({
      data: {
        id: 1,
        username: 'testuser',
        role: { name: 'user', permissions: [] }
      }
    });

    renderWithAuthProvider(<TestComponent />);

    waitFor(() => {
      expect(screen.getByTestId('has-admin-role').textContent).toBe('false');
    });
  });

  test('login updates authentication state', async () => {
    const { authAPI } = require('../services/api');

    authAPI.getProfile.mockResolvedValue({
      data: {
        id: 1,
        username: 'testuser',
        role: { name: 'user', permissions: [] }
      }
    });

    // Устанавливаем токен ДО рендера — AuthContext читает его при mount
    localStorage.setItem('access_token', 'test_access_token');

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('testuser');
    });
  });

  test('logout clears authentication state', () => {
    // Устанавливаем токен
    localStorage.setItem('access_token', 'test_access_token');
    
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockRejectedValue(new Error('Not authenticated'));

    renderWithAuthProvider(<TestComponent />);

    // Очищаем токен
    localStorage.removeItem('access_token');
    
    expect(screen.getByTestId('authenticated').textContent).toBe('false');
  });
});
