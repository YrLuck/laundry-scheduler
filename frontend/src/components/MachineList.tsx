import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { machineAPI, bookingAPI, authAPI } from '../services/api';
import { Machine, TimeSlot, Booking, User, MachineFilters } from '../types';
import Spinner from './Spinner';
import SEO from './SEO';
import './MachineList.css';

const PAGE_SIZE = 6;

const MachineList: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [machineType, setMachineType] = useState(searchParams.get('type') || '');
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || '');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(
    (searchParams.get('sort_order') as 'asc' | 'desc') || 'asc'
  );
  const [page, setPage] = useState(Number(searchParams.get('page') || '1'));

  const [machines, setMachines] = useState<Machine[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [user, setUser] = useState<User | null>(null);
  const [userBookings, setUserBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [error, setError] = useState('');

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Sync filters to URL query params for back-nav preservation (Lab 3 requirement)
  useEffect(() => {
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (machineType) params.type = machineType;
    if (status) params.status = status;
    if (sortBy) params.sort_by = sortBy;
    if (sortOrder !== 'asc') params.sort_order = sortOrder;
    if (page > 1) params.page = String(page);
    setSearchParams(params, { replace: true });
  }, [search, machineType, status, sortBy, sortOrder, page, setSearchParams]);

  const loadMachines = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const filters: MachineFilters = {
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        search: search || undefined,
        machine_type: machineType || undefined,
        status: status || undefined,
        sort_by: sortBy || undefined,
        sort_order: sortOrder,
      };
      const [machinesRes, countRes] = await Promise.all([
        machineAPI.getAll(filters),
        machineAPI.getCount({
          search: search || undefined,
          machine_type: machineType || undefined,
          status: status || undefined,
        }),
      ]);
      setMachines(machinesRes.data);
      setTotal(countRes.data.total);
    } catch (err: any) {
      setError('Ошибка загрузки машин: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }, [search, machineType, status, sortBy, sortOrder, page]);

  useEffect(() => {
    loadMachines();
  }, [loadMachines]);

  useEffect(() => {
    loadUserProfile();
  }, []);

  useEffect(() => {
    if (user) loadUserBookings();
  }, [user]);

  const loadUserProfile = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const response = await authAPI.getProfile();
      setUser(response.data);
    } catch {}
  };

  const loadUserBookings = async () => {
    if (!user) return;
    try {
      const response = await bookingAPI.getMyBookings();
      setUserBookings(response.data);
    } catch {}
  };

  const handleFilterReset = () => {
    setSearch('');
    setMachineType('');
    setStatus('');
    setSortBy('');
    setSortOrder('asc');
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setSelectedMachine(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleMachineSelect = (machine: Machine) => {
    setSelectedMachine(machine);
    loadTimeSlots(machine.id, selectedDate);
  };

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    if (selectedMachine) loadTimeSlots(selectedMachine.id, date);
  };

  const loadTimeSlots = async (machineId: number, date: string) => {
    setSlotsLoading(true);
    try {
      const response = await machineAPI.getTimeSlots(machineId, date);
      setTimeSlots(response.data);
    } catch (err: any) {
      setError('Ошибка загрузки слотов: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSlotsLoading(false);
    }
  };

  const handleBookSlot = async (slot: TimeSlot) => {
    if (!user) {
      alert('Пожалуйста, войдите в систему для бронирования');
      window.location.href = '/login';
      return;
    }
    setLoading(true);
    try {
      await bookingAPI.create({
        machine_id: selectedMachine!.id,
        start_time: slot.start_time,
        end_time: slot.end_time,
      });
      alert('Бронь успешно создана!');
      loadTimeSlots(selectedMachine!.id, selectedDate);
      loadUserBookings();
    } catch (err: any) {
      setError('Ошибка при создании брони: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId: number) => {
    setLoading(true);
    try {
      await bookingAPI.cancel(bookingId);
      alert('Бронь отменена!');
      loadUserBookings();
      if (selectedMachine) loadTimeSlots(selectedMachine.id, selectedDate);
    } catch (err: any) {
      setError('Ошибка при отмене брони: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const statusLabel = (s: string) =>
    s === 'available' ? 'Доступна' : s === 'in_use' ? 'Занята' : 'Обслуживание';

  return (
    <>
      <SEO
        title="Машины для стирки и сушки | Laundry Scheduler"
        description="Забронируйте стиральную машину или сушилку онлайн. Просмотр доступного времени и статусов оборудования."
        canonical="https://laundry-scheduler.local/machines"
      />

      <div className="machine-list">
        <div className="page-navigation">
          <Link to="/">Главная</Link> | <Link to="/bookings">Все бронирования</Link> | <Link to="/profile">Профиль</Link>
        </div>

        {error && <div className="error">{error}</div>}

        {/* Панель фильтров — Lab 3: фильтрация, поиск, сортировка, пагинация с сохранением в URL */}
        <div className="filters-panel">
          <h3>Фильтры и поиск</h3>
          <div className="filters-row">
            <input
              type="text"
              placeholder="Поиск по названию..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="filter-input"
            />
            <select
              value={machineType}
              onChange={e => { setMachineType(e.target.value); setPage(1); }}
              className="filter-select"
            >
              <option value="">Все типы</option>
              <option value="washer">Стиральная машина</option>
              <option value="dryer">Сушилка</option>
            </select>
            <select
              value={status}
              onChange={e => { setStatus(e.target.value); setPage(1); }}
              className="filter-select"
            >
              <option value="">Все статусы</option>
              <option value="available">Доступна</option>
              <option value="in_use">Занята</option>
              <option value="maintenance">Обслуживание</option>
            </select>
            <select
              value={sortBy}
              onChange={e => { setSortBy(e.target.value); setPage(1); }}
              className="filter-select"
            >
              <option value="">Без сортировки</option>
              <option value="name">По названию</option>
              <option value="type">По типу</option>
              <option value="status">По статусу</option>
              <option value="created_at">По дате</option>
            </select>
            <select
              value={sortOrder}
              onChange={e => { setSortOrder(e.target.value as 'asc' | 'desc'); setPage(1); }}
              className="filter-select"
            >
              <option value="asc">По возрастанию</option>
              <option value="desc">По убыванию</option>
            </select>
            <button className="filter-reset" onClick={handleFilterReset}>
              Сбросить
            </button>
          </div>
          <div className="filters-summary">
            Найдено: <strong>{total}</strong> машин
          </div>
        </div>

        {/* Секция бронирований пользователя */}
        <div className="user-section">
          <h2>Ваши бронирования</h2>
          {user ? (
            <p>Здравствуйте, <strong>{user.username}</strong>!</p>
          ) : (
            <p>Пожалуйста, <Link to="/login">войдите</Link> для просмотра бронирований</p>
          )}
          {userBookings.filter(b => b.status === 'active').length > 0 && (
            <div className="user-bookings">
              <h3>Активные брони:</h3>
              {userBookings.filter(b => b.status === 'active').map(booking => (
                <div key={booking.id} className="booking-item">
                  <span>
                    {booking.machine?.name} ({booking.machine?.type === 'washer' ? 'Стиралка' : 'Сушилка'}) —{' '}
                    {new Date(booking.start_time).toLocaleString()} до{' '}
                    {new Date(booking.end_time).toLocaleString()}
                  </span>
                  <button onClick={() => handleCancelBooking(booking.id)}>Отменить</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Сетка машин */}
        <div className="machines-section">
          <h2>Стиральные машины и сушилки</h2>
          {loading ? (
            <div className="loading"><Spinner /></div>
          ) : (
            <>
              <div className="machines-grid">
                {machines.length === 0 ? (
                  <p className="no-results">Ничего не найдено. Попробуйте изменить фильтры.</p>
                ) : (
                  machines.map(machine => (
                    <div
                      key={machine.id}
                      className={`machine-card ${selectedMachine?.id === machine.id ? 'selected' : ''}`}
                      onClick={() => handleMachineSelect(machine)}
                    >
                      <h3>{machine.name}</h3>
                      <p>Тип: {machine.type === 'washer' ? 'Стиральная машина' : 'Сушилка'}</p>
                      <p>
                        Статус:{' '}
                        <span className={`status-badge ${machine.status}`}>
                          {statusLabel(machine.status)}
                        </span>
                      </p>
                    </div>
                  ))
                )}
              </div>

              {/* Пагинация */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => handlePageChange(page - 1)}
                    disabled={page === 1}
                  >
                    ← Предыдущая
                  </button>
                  <span className="pagination-info">Страница {page} из {totalPages}</span>
                  <button
                    onClick={() => handlePageChange(page + 1)}
                    disabled={page === totalPages}
                  >
                    Следующая →
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Временные слоты */}
        {selectedMachine && (
          <div className="time-slots-section">
            <h3>Доступное время для {selectedMachine.name}</h3>
            <input
              type="date"
              value={selectedDate}
              onChange={e => handleDateChange(e.target.value)}
            />
            {slotsLoading ? (
              <div className="loading"><Spinner /></div>
            ) : (
              <div className="time-slots-grid">
                {timeSlots.map((slot, index) => (
                  <div key={index} className={`time-slot ${slot.available ? 'available' : 'booked'}`}>
                    <span>
                      {new Date(slot.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                      {new Date(slot.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {slot.available ? (
                      <button onClick={() => handleBookSlot(slot)}>Забронировать</button>
                    ) : (
                      <span className="booked-by">Занято: {slot.booked_by}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};

export default MachineList;
