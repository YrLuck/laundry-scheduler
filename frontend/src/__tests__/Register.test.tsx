/**
 * Тесты для компонента Register.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Register from '../components/Register';
import { AuthProvider } from '../contexts/AuthContext';

// Моки для API
jest.mock('../services/api', () => ({
  authAPI: {
    register: jest.fn(),
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

  test('password visibility toggles work', () => {
    renderWithProviders(<Register />);

    const passwordInput = screen.getByLabelText(/пароль/i);
    const confirmPasswordInput = screen.getByLabelText(/подтверждение пароля/i);
    const toggleButtons = screen.getAllByRole('button');
    
    // Начальное состояние - пароли скрыты
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');

    // Находим кнопки переключения видимости
    const passwordToggle = toggleButtons.find(btn => 
      btn.textContent === '👁️' || btn.textContent === '🙈'
    );

    if (passwordToggle) {
      fireEvent.click(passwordToggle);
      expect(passwordInput).toHaveAttribute('type', 'text');
    }
  });

  test('form validation requires all required fields', () => {
    renderWithProviders(<Register />);

    const submitButton = screen.getByRole('button', { name: /зарегистрироваться/i });
    
    // Пытаемся отправить форму с пустыми полями
    fireEvent.click(submitButton);

    // Форма не должна отправляться
    const { authAPI } = require('../services/api');
    expect(authAPI.register).not.toHaveBeenCalled();
  });
});
