/**
 * Тесты для компонента Login.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../components/Login';
import { AuthProvider } from '../contexts/AuthContext';

// Моки для API
jest.mock('../services/api', () => ({
  authAPI: {
    login: jest.fn(),
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
    const toggleButton = screen.getByRole('button', { name: /👁️/i });

    expect(passwordInput).toHaveAttribute('type', 'password');

    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');

    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('form validation requires both fields', () => {
    renderWithProviders(<Login />);

    const submitButton = screen.getByRole('button', { name: /войти/i });
    
    // Пытаемся отправить пустую форму
    fireEvent.click(submitButton);

    // Форма не должна отправляться
    const { authAPI } = require('../services/api');
    expect(authAPI.login).not.toHaveBeenCalled();
  });
});
