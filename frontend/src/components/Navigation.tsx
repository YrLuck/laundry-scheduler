import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navigation.css';

const Navigation: React.FC = () => {
  const { isAuthenticated, user, hasRole, logout } = useAuth();
  const location = useLocation();

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <Link to="/">Стиралка Онлайн</Link>
      </div>
      <ul className="nav-menu">
        <li><Link to="/">Главная</Link></li>
        <li><Link to="/machines">Машины</Link></li>
        <li><Link to="/bookings">Бронирования</Link></li>
        
        {isAuthenticated ? (
          <>
            <li><Link to="/profile">Профиль ({user?.username})</Link></li>
            {hasRole('admin') && (
              <li><Link to="/admin">Админка</Link></li>
            )}
            <li>
              <button onClick={handleLogout} className="logout-btn">
                Выйти
              </button>
            </li>
          </>
        ) : (
          <>
            <li><Link to="/login">Вход</Link></li>
            <li><Link to="/register">Регистрация</Link></li>
          </>
        )}
      </ul>
    </nav>
  );
};

export default Navigation;
