/**
 * Тесты для компонента ProtectedRoute.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';

// Мокаем useAuth напрямую — не зависим от async API
jest.mock('../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const { useAuth } = require('../contexts/AuthContext');

const TestPage = () => <div data-testid="protected-page">Protected Content</div>;

const renderRoute = (props = {}) =>
  render(
    <BrowserRouter>
      <ProtectedRoute {...props}>
        <TestPage />
      </ProtectedRoute>
    </BrowserRouter>
  );

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading state while checking auth', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      hasRole: () => false,
      hasPermission: () => false,
    });

    renderRoute();

    expect(screen.getByText(/загрузка/i)).toBeInTheDocument();
  });

  test('redirects when not authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      hasRole: () => false,
      hasPermission: () => false,
    });

    renderRoute();

    // Navigate мок возвращает null — контент не должен рендериться
    expect(screen.queryByTestId('protected-page')).not.toBeInTheDocument();
  });

  test('renders content when authenticated', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      hasRole: () => true,
      hasPermission: () => true,
    });

    renderRoute();

    expect(screen.getByTestId('protected-page')).toBeInTheDocument();
  });

  test('shows 403 when required role is missing', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      hasRole: (role: string) => role !== 'admin',
      hasPermission: () => true,
    });

    renderRoute({ requiredRole: 'admin' });

    expect(screen.getByText(/403/i)).toBeInTheDocument();
    expect(screen.queryByTestId('protected-page')).not.toBeInTheDocument();
  });

  test('renders content when user has required role', () => {
    useAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      hasRole: (role: string) => role === 'admin',
      hasPermission: () => true,
    });

    renderRoute({ requiredRole: 'admin' });

    expect(screen.getByTestId('protected-page')).toBeInTheDocument();
  });
});
