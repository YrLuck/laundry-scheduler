/**
 * Тесты для компонента Login.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../components/Login';
import { AuthProvider } from '../contexts/AuthContext';

// Мокаем весь API-модуль — включая getProfile чтобы AuthProvider не падал
jest.mock('../services/api', () => ({
  authAPI: {
    login: jest.fn(),
    getProfile: jest.fn().mockRejectedValue(new Error('No token')),
    refreshToken: jest.fn().mockRejectedValue(new Error('No token')),
  },
  default: {
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  },
}));

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockRejectedValue(new Error('No token'));
  });

  test('renders login form', () => {
    renderWithProviders(<Login />);

    expect(screen.getByLabelText(/имя пользователя/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument();
  });

  test('shows error on failed login', async () => {
    const { authAPI } = require('../services/api');
    authAPI.login.mockRejectedValue({
      response: { data: { detail: 'Invalid credentials' } }
    });

    renderWithProviders(<Login />);

    fireEvent.change(screen.getByLabelText(/имя пользователя/i), {
      target: { value: 'testuser' }
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'wrongpassword' }
    });

    fireEvent.click(screen.getByRole('button', { name: /войти/i }));

    await waitFor(() => {
      expect(screen.getByText(/ошибка входа/i)).toBeInTheDocument();
    });
  });

  test('password visibility toggle works', () => {
    renderWithProviders(<Login />);

    const passwordInput = screen.getByLabelText(/пароль/i);
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleButton = screen.getByText('👁️');
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');

    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('form validation requires both fields', () => {
    renderWithProviders(<Login />);

    const submitButton = screen.getByRole('button', { name: /войти/i });
    fireEvent.click(submitButton);

    const { authAPI } = require('../services/api');
    expect(authAPI.login).not.toHaveBeenCalled();
  });
});
