import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bookingAPI, machineAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Booking, Machine } from '../types';
import Spinner from './Spinner';

const EditBooking: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { hasPermission, hasRole } = useAuth();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [machineId, setMachineId] = useState<number>(0);
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canDelete = hasPermission('bookings:delete') || hasRole('admin');

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setError(null);
    try {
      const [bookingRes, machinesRes] = await Promise.all([
        bookingAPI.getById(parseInt(id!)),
        machineAPI.getAll(),
      ]);
      const b = bookingRes.data;
      setBooking(b);
      setMachineId(b.machine_id);
      setStartTime(b.start_time.substring(0, 16));
      setEndTime(b.end_time.substring(0, 16));
      setMachines(machinesRes.data);
    } catch (err: any) {
      const status = err.response?.status;
      if (status === 403) {
        setError('У вас нет доступа к этому бронированию.');
      } else if (status === 404) {
        setError('Бронирование не найдено.');
      } else {
        setError('Ошибка загрузки: ' + (err.response?.data?.detail || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startTime || !endTime) return;
    setSaving(true);
    setError(null);
    try {
      await bookingAPI.update(parseInt(id!), {
        machine_id: machineId,
        start_time: startTime,
        end_time: endTime,
      });
      navigate('/bookings');
    } catch (err: any) {
      setError('Ошибка сохранения: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Отменить это бронирование?')) return;
    setSaving(true);
    setError(null);
    try {
      await bookingAPI.cancel(parseInt(id!));
      navigate('/bookings');
    } catch (err: any) {
      setError('Ошибка отмены: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Удалить бронирование полностью? Это действие нельзя отменить.')) return;
    setSaving(true);
    setError(null);
    try {
      await bookingAPI.delete(parseInt(id!));
      navigate('/bookings');
    } catch (err: any) {
      setError('Ошибка удаления: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="edit-booking-page"><Spinner /></div>;
  }

  if (error && !booking) {
    return (
      <div className="edit-booking-page">
        <div className="error">{error}</div>
        <button onClick={() => navigate('/bookings')} className="cancel-btn" style={{ marginTop: '1rem' }}>
          Назад к бронированиям
        </button>
      </div>
    );
  }

  return (
    <div className="edit-booking-page">
      <h1>Редактировать бронирование #{id}</h1>

      {error && <div className="error">{error}</div>}
      {saving && <div className="loading">Сохранение...</div>}

      {booking && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#f8f9fa', borderRadius: '8px', fontSize: '0.95rem', color: '#555' }}>
          <strong>Владелец:</strong> {booking.user_name} &nbsp;|&nbsp;
          <strong>Статус:</strong> {booking.status}
        </div>
      )}

      <form onSubmit={handleSubmit} className="booking-form">
        <div className="form-group">
          <label htmlFor="machine_id">Машина:</label>
          <select
            id="machine_id"
            value={machineId}
            onChange={e => setMachineId(parseInt(e.target.value))}
            required
            disabled={saving}
          >
            <option value="">Выберите машину</option>
            {machines.map(m => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.type === 'washer' ? 'Стиральная' : 'Сушилка'})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="start_time">Начало:</label>
          <input
            type="datetime-local"
            id="start_time"
            value={startTime}
            onChange={e => setStartTime(e.target.value)}
            required
            disabled={saving}
          />
        </div>

        <div className="form-group">
          <label htmlFor="end_time">Конец:</label>
          <input
            type="datetime-local"
            id="end_time"
            value={endTime}
            onChange={e => setEndTime(e.target.value)}
            required
            disabled={saving}
          />
        </div>

        <div className="form-actions">
          <button type="submit" disabled={saving}>
            Сохранить изменения
          </button>

          {booking?.status === 'active' && !canDelete && (
            <button type="button" onClick={handleCancel} className="cancel-btn" disabled={saving}>
              Отменить бронь
            </button>
          )}

          {canDelete && (
            <button type="button" onClick={handleDelete} className="delete-btn" disabled={saving}>
              Удалить бронь
            </button>
          )}

          <button type="button" onClick={() => navigate('/bookings')} className="cancel-btn" disabled={saving}>
            Назад
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditBooking;
