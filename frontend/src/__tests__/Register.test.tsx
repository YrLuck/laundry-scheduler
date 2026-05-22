/**
 * Тесты для компонента Register.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Register from '../components/Register';
import { AuthProvider } from '../contexts/AuthContext';

// Мокаем весь API-модуль — включая getProfile чтобы AuthProvider не падал
jest.mock('../services/api', () => ({
  authAPI: {
    register: jest.fn(),
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

describe('Register Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    const { authAPI } = require('../services/api');
    authAPI.getProfile.mockRejectedValue(new Error('No token'));
  });

  test('renders registration form', () => {
    renderWithProviders(<Register />);

    expect(screen.getByLabelText(/имя пользователя/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/полное имя/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/подтверждение пароля/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /зарегистрироваться/i })).toBeInTheDocument();
  });

  test('shows error when passwords do not match', async () => {
    renderWithProviders(<Register />);

    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/подтверждение пароля/i), {
      target: { value: 'password456' }
    });

    fireEvent.click(screen.getByRole('button', { name: /зарегистрироваться/i }));

    await waitFor(() => {
      expect(screen.getByText(/пароли не совпадают/i)).toBeInTheDocument();
    });
  });

  test('shows error on failed registration', async () => {
    const { authAPI } = require('../services/api');
    authAPI.register.mockRejectedValue({
      response: { data: { detail: 'Username already registered' } }
    });

    renderWithProviders(<Register />);

    fireEvent.change(screen.getByLabelText(/имя пользователя/i), {
      target: { value: 'existinguser' }
    });
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText(/пароль/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/подтверждение пароля/i), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /зарегистрироваться/i }));

    await waitFor(() => {
      expect(screen.getByText(/ошибка регистрации/i)).toBeInTheDocument();
    });
  });

  test('form validation requires all required fields', () => {
    renderWithProviders(<Register />);

    const submitButton = screen.getByRole('button', { name: /зарегистрироваться/i });
    fireEvent.click(submitButton);

    const { authAPI } = require('../services/api');
    expect(authAPI.register).not.toHaveBeenCalled();
  });
});
