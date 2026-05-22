import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { bookingAPI } from '../services/api';
import { Booking } from '../types';
import Spinner from './Spinner';
import { useAuth } from '../contexts/AuthContext';

const STATUS_LABELS: Record<string, string> = {
  active: 'Активна',
  cancelled: 'Отменена',
  completed: 'Завершена',
};

const Bookings: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { hasRole, user } = useAuth();

  const isAdmin = hasRole('admin');

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    setLoading(true);
    setError(null);
    try {
      // Admin sees all bookings; regular user sees only their own
      const response = isAdmin
        ? await bookingAPI.getAll()
        : await bookingAPI.getMyBookings();
      setBookings(response.data);
    } catch (err: any) {
      setError('Ошибка загрузки бронирований: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId: number) => {
    if (!window.confirm('Отменить это бронирование?')) return;
    try {
      await bookingAPI.cancel(bookingId);
      loadBookings();
    } catch (err: any) {
      setError('Ошибка при отмене: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (bookingId: number) => {
    if (!window.confirm('Удалить бронирование полностью?')) return;
    try {
      await bookingAPI.delete(bookingId);
      loadBookings();
    } catch (err: any) {
      setError('Ошибка при удалении: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) return <div className="bookings-page"><Spinner /></div>;

  return (
    <div className="bookings-page">
      <h1>{isAdmin ? 'Все бронирования' : 'Мои бронирования'}</h1>

      {error && <div className="error">{error}</div>}

      {bookings.length === 0 ? (
        <p style={{ color: '#718096', marginTop: '1rem' }}>
          {isAdmin ? 'Нет бронирований' : 'У вас пока нет бронирований'}
        </p>
      ) : (
        <div className="bookings-list">
          {bookings.map(booking => (
            <div key={booking.id} className="booking-card">
              <h3>{booking.machine?.name || `Машина #${booking.machine_id}`}</h3>
              {isAdmin && (
                <p><strong>Пользователь:</strong> {booking.user_name || '—'}</p>
              )}
              <p><strong>Начало:</strong> {new Date(booking.start_time).toLocaleString('ru-RU')}</p>
              <p><strong>Конец:</strong> {new Date(booking.end_time).toLocaleString('ru-RU')}</p>
              <p>
                <strong>Статус:</strong>{' '}
                <span className={`status-badge status-${booking.status}`}>
                  {STATUS_LABELS[booking.status] ?? booking.status}
                </span>
              </p>

              <div className="booking-actions">
                {booking.status === 'active' && (
                  <Link to={`/bookings/${booking.id}/edit`} className="edit-btn">
                    Редактировать
                  </Link>
                )}
                {booking.status === 'active' && !isAdmin && (
                  <button onClick={() => handleCancel(booking.id)} className="cancel-btn">
                    Отменить
                  </button>
                )}
                {isAdmin && (
                  <button onClick={() => handleDelete(booking.id)} className="delete-btn">
                    Удалить
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Bookings;
