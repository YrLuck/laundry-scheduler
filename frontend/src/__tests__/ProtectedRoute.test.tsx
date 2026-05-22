/**
 * Тесты для компонента ProtectedRoute.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import { AuthProvider } from '../contexts/AuthContext';

// Моки для API
jest.mock('../services/api', () => ({
  authAPI: {
    getProfile: jest.fn(),
  },
}));

const TestPage: React.FC = () => <div data-testid="protected-page">Protected Content</div>;
const LoginPage: React.FC = () => <div data-testid="login-page">Login Page</div>;

const renderWithProviders = (
  component: React.ReactElement,
  initialEntries: string[] = ['/']
) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={component} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>,
    { initialEntries }
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('redirects to login when not authenticated', () => {
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockRejectedValue(new Error('Not authenticated'));

    renderWithProviders(
      <ProtectedRoute>
        <TestPage />
      </ProtectedRoute>
    );

    // Должна быть переадресация на login
    expect(window.location.pathname).toBe('/login');
  });

  test('renders content when authenticated', () => {
    // Устанавливаем токен
    localStorage.setItem('access_token', 'test_token');

    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockResolvedValue({
      data: {
        id: 1,
        username: 'testuser',
        role: { name: 'user', permissions: [] }
      }
    });

    renderWithProviders(
      <ProtectedRoute>
        <TestPage />
      </ProtectedRoute>
    );

    // Контент должен отображаться
    expect(screen.getByTestId('protected-page')).toBeInTheDocument();
  });

  test('blocks access when required role is missing', () => {
    localStorage.setItem('access_token', 'test_token');

    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockResolvedValue({
      data: {
        id: 1,
        username: 'testuser',
        role: { name: 'user', permissions: [] }
      }
    });

    renderWithProviders(
      <ProtectedRoute requiredRole="admin">
        <TestPage />
      </ProtectedRoute>
    );

    // Должен показать ошибку 403
    expect(screen.getByText(/403/i)).toBeInTheDocument();
  });

  test('allows access when user has required role', () => {
    localStorage.setItem('access_token', 'test_token');

    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockResolvedValue({
      data: {
        id: 1,
        username: 'admin',
        role: { name: 'admin', permissions: [] }
      }
    });

    renderWithProviders(
      <ProtectedRoute requiredRole="admin">
        <TestPage />
      </ProtectedRoute>
    );

    // Контент должен отображаться
    expect(screen.getByTestId('protected-page')).toBeInTheDocument();
  });

  test('shows loading state while checking auth', () => {
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockImplementation(
      () => new Promise(() => {}) // Никогда не разрешается
    );

    renderWithProviders(
      <ProtectedRoute>
        <TestPage />
      </ProtectedRoute>
    );

    // Должен показывать индикатор загрузки
    expect(screen.getByText(/загрузка/i)).toBeInTheDocument();
  });
});
