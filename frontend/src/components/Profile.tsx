import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { bookingAPI } from '../services/api';
import { Booking } from '../types';
import Spinner from './Spinner';

const Profile: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();
  const [userBookings, setUserBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      loadUserBookings();
    }
  }, [user]);

  const loadUserBookings = async () => {
    if (!user) return;

    setLoading(true);
    setError('');
    try {
      const response = await bookingAPI.getMyBookings();
      setUserBookings(response.data);
    } catch (err: any) {
      setError('Ошибка загрузки бронирований: ' + (err.response?.data?.detail || err.message));
      console.error('Error loading user bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="profile-page">
        <Spinner />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-page">
        <h1>Профиль пользователя</h1>
        <p>Пожалуйста, <Link to="/login">войдите</Link> в систему.</p>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <h1>Профиль пользователя</h1>

      {error && <div className="error">{error}</div>}

      <div className="user-info">
        <h2>Информация о пользователе</h2>
        <p><strong>Имя пользователя:</strong> {user.username}</p>
        <p><strong>Полное имя:</strong> {user.full_name || 'Не указано'}</p>
        <p><strong>Email:</strong> {user.email || 'Не указан'}</p>
        <p><strong>Роль:</strong> {user.role?.name || 'Не назначена'}</p>
        <p><strong>Дата регистрации:</strong> {new Date(user.created_at).toLocaleString()}</p>
        
        {user.role && (
          <div className="user-role-info">
            <h3>Разрешения:</h3>
            <ul>
              {user.role.permissions?.map(perm => (
                <li key={perm.id}>{perm.name} - {perm.description}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {loading ? (
        <div className="loading"><Spinner /></div>
      ) : (
        <div className="user-bookings-section">
          <h2>Ваши бронирования</h2>

          {userBookings.length === 0 ? (
            <p>У вас нет активных бронирований</p>
          ) : (
            <div className="user-bookings-list">
              {userBookings.map(booking => (
                <div key={booking.id} className="booking-card">
                  <h3>{booking.machine?.name || `Машина #${booking.machine_id}`} ({booking.machine?.type})</h3>
                  <p><strong>Дата начала:</strong> {new Date(booking.start_time).toLocaleString()}</p>
                  <p><strong>Дата окончания:</strong> {new Date(booking.end_time).toLocaleString()}</p>
                  <p><strong>Статус:</strong> {booking.status}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Profile;
