import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI, rbacAPI, machineAPI } from '../services/api';
import { User, Role, Machine } from '../types';
import SEO from './SEO';
import './AdminPanel.css';

type Tab = 'users' | 'machines';

interface MachineFormData {
  name: string;
  type: string;
  status: string;
}

const AdminPanel: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('users');

  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  const [machines, setMachines] = useState<Machine[]>([]);
  const [machinesLoading, setMachinesLoading] = useState(false);
  const [showMachineForm, setShowMachineForm] = useState(false);
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null);
  const [machineForm, setMachineForm] = useState<MachineFormData>({
    name: '',
    type: 'washer',
    status: 'available',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
      loadRoles();
    } else {
      loadMachines();
    }
  }, [activeTab]);

  const showSuccess = (msg: string) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(''), 3000);
  };

  const loadUsers = async () => {
    setUsersLoading(true);
    setError('');
    try {
      const response = await userAPI.getAll(0, 200);
      setUsers(response.data);
    } catch (err: any) {
      setError('Ошибка загрузки пользователей: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUsersLoading(false);
    }
  };

  const loadRoles = async () => {
    try {
      const response = await rbacAPI.getRoles();
      setRoles(response.data);
    } catch {
      setError('Ошибка загрузки ролей');
    }
  };

  const loadMachines = async () => {
    setMachinesLoading(true);
    setError('');
    try {
      const response = await machineAPI.getAll({ limit: 200 });
      setMachines(response.data);
    } catch (err: any) {
      setError('Ошибка загрузки машин: ' + (err.response?.data?.detail || err.message));
    } finally {
      setMachinesLoading(false);
    }
  };

  const handleAssignRole = async (userId: number, roleId: number) => {
    if (!roleId) return;
    try {
      await rbacAPI.assignRoleToUser(userId, roleId);
      showSuccess('Роль успешно назначена');
      loadUsers();
    } catch (err: any) {
      setError('Ошибка назначения роли: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!window.confirm(`Удалить пользователя "${username}"?`)) return;
    try {
      await userAPI.delete(userId);
      showSuccess('Пользователь удалён');
      loadUsers();
    } catch (err: any) {
      setError('Ошибка удаления: ' + (err.response?.data?.detail || err.message));
    }
  };

  const openAddMachine = () => {
    setEditingMachine(null);
    setMachineForm({ name: '', type: 'washer', status: 'available' });
    setShowMachineForm(true);
  };

  const openEditMachine = (machine: Machine) => {
    setEditingMachine(machine);
    setMachineForm({ name: machine.name, type: machine.type, status: machine.status });
    setShowMachineForm(true);
  };

  const handleMachineSubmit = async () => {
    if (!machineForm.name.trim()) {
      setError('Введите название машины');
      return;
    }
    try {
      if (editingMachine) {
        await machineAPI.update(editingMachine.id, machineForm);
        showSuccess('Машина обновлена');
      } else {
        await machineAPI.create(machineForm);
        showSuccess('Машина добавлена');
      }
      setShowMachineForm(false);
      setEditingMachine(null);
      loadMachines();
    } catch (err: any) {
      setError('Ошибка: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteMachine = async (machineId: number, machineName: string) => {
    if (!window.confirm(`Удалить машину "${machineName}"?`)) return;
    try {
      await machineAPI.delete(machineId);
      showSuccess('Машина удалена');
      loadMachines();
    } catch (err: any) {
      setError('Ошибка удаления: ' + (err.response?.data?.detail || err.message));
    }
  };

  const statusLabel = (s: string) =>
    s === 'available' ? 'Доступна' : s === 'in_use' ? 'Занята' : 'Обслуживание';

  return (
    <>
      <SEO
        title="Панель администратора | Laundry Scheduler"
        description="Управление пользователями и оборудованием прачечной"
      />
      <div className="admin-panel">
        <h1>Панель администратора</h1>
        <p className="admin-welcome">
          Вы вошли как <strong>{currentUser?.username}</strong> (роль: admin)
        </p>

        <div className="admin-tabs">
          <button
            className={`tab${activeTab === 'users' ? ' active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            Пользователи
          </button>
          <button
            className={`tab${activeTab === 'machines' ? ' active' : ''}`}
            onClick={() => setActiveTab('machines')}
          >
            Машины
          </button>
        </div>

        {error && (
          <div className="admin-error">
            {error}
            <button onClick={() => setError('')}>×</button>
          </div>
        )}
        {success && <div className="admin-success">{success}</div>}

        {/* Вкладка: Пользователи */}
        {activeTab === 'users' && (
          <div className="tab-content">
            <h2>Управление пользователями ({users.length})</h2>
            {usersLoading ? (
              <p>Загрузка...</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Имя пользователя</th>
                    <th>Email</th>
                    <th>Текущая роль</th>
                    <th>Назначить роль</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className={u.id === currentUser?.id ? 'current-user-row' : ''}>
                      <td>{u.id}</td>
                      <td>
                        {u.username}
                        {u.id === currentUser?.id && (
                          <span className="you-badge">Вы</span>
                        )}
                      </td>
                      <td>{u.email || '—'}</td>
                      <td>
                        <span className={`role-badge role-${u.role?.name || 'none'}`}>
                          {u.role?.name || 'нет роли'}
                        </span>
                      </td>
                      <td>
                        <select
                          defaultValue={u.role_id || ''}
                          onChange={e => handleAssignRole(u.id, Number(e.target.value))}
                          disabled={u.id === currentUser?.id}
                        >
                          <option value="">— выбрать —</option>
                          {roles.map(r => (
                            <option key={r.id} value={r.id}>
                              {r.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <button
                          className="btn-danger"
                          onClick={() => handleDeleteUser(u.id, u.username)}
                          disabled={u.id === currentUser?.id}
                          title={u.id === currentUser?.id ? 'Нельзя удалить себя' : ''}
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Вкладка: Машины */}
        {activeTab === 'machines' && (
          <div className="tab-content">
            <div className="tab-header">
              <h2>Управление машинами ({machines.length})</h2>
              <button className="btn-primary" onClick={openAddMachine}>
                + Добавить машину
              </button>
            </div>

            {showMachineForm && (
              <div className="machine-form">
                <h3>{editingMachine ? 'Редактировать машину' : 'Новая машина'}</h3>
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="Название машины"
                    value={machineForm.name}
                    onChange={e => setMachineForm(f => ({ ...f, name: e.target.value }))}
                  />
                  <select
                    value={machineForm.type}
                    onChange={e => setMachineForm(f => ({ ...f, type: e.target.value }))}
                  >
                    <option value="washer">Стиральная машина</option>
                    <option value="dryer">Сушилка</option>
                  </select>
                  <select
                    value={machineForm.status}
                    onChange={e => setMachineForm(f => ({ ...f, status: e.target.value }))}
                  >
                    <option value="available">Доступна</option>
                    <option value="in_use">Занята</option>
                    <option value="maintenance">Обслуживание</option>
                  </select>
                </div>
                <div className="form-actions">
                  <button className="btn-primary" onClick={handleMachineSubmit}>
                    {editingMachine ? 'Сохранить' : 'Добавить'}
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => { setShowMachineForm(false); setEditingMachine(null); }}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}

            {machinesLoading ? (
              <p>Загрузка...</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Название</th>
                    <th>Тип</th>
                    <th>Статус</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {machines.map(m => (
                    <tr key={m.id}>
                      <td>{m.id}</td>
                      <td>{m.name}</td>
                      <td>{m.type === 'washer' ? 'Стиральная машина' : 'Сушилка'}</td>
                      <td>
                        <span className={`status-badge ${m.status}`}>
                          {statusLabel(m.status)}
                        </span>
                      </td>
                      <td>
                        <button className="btn-edit" onClick={() => openEditMachine(m)}>
                          Изменить
                        </button>
                        <button
                          className="btn-danger"
                          onClick={() => handleDeleteMachine(m.id, m.name)}
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </>
  );
};

export default AdminPanel;
