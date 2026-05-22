import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredPermission,
}) => {
  const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner-container">
          <div className="spinner"></div>
          <p>Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Проверка роли
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div className="error-page">
        <h1>403 - Доступ запрещен</h1>
        <p>У вас недостаточно прав для просмотра этой страницы.</p>
      </div>
    );
  }

  // Проверка разрешения
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="error-page">
        <h1>403 - Доступ запрещен</h1>
        <p>У вас недостаточно прав для выполнения этого действия.</p>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
