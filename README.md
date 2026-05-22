# Laundry Scheduler - Fullstack Application

Система бронирования стиральных машин и сушилок для общежития.

## 📋 Технологии

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy (ORM)
- SQLite (БД)
- JWT (аутентификация)
- MinIO (S3-хранилище)

### Frontend
- React 18
- TypeScript
- React Router
- Axios

### DevOps
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Nginx

## 🚀 Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repository-url>
cd Fullstack_Martinez

# Скопировать .env.example в .env
cp .env.example .env

# Запустить все сервисы
docker-compose up -d

# Приложение доступно по адресу:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# MinIO Console: http://localhost:9001
```

### Вариант 2: Локальная разработка

#### Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API доступно по адресу: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm start

# Приложение доступно по адресу: http://localhost:3000
```

## 📁 Структура проекта

```
Fullstack_Martinez/
├── backend/
│   ├── app/
│   │   ├── main.py           # Точка входа
│   │   ├── models.py         # SQLAlchemy модели
│   │   ├── schemas.py        # Pydantic схемы
│   │   ├── crud.py           # CRUD операции
│   │   ├── repositories.py   # Repository паттерн
│   │   ├── auth.py           # Аутентификация
│   │   ├── services/         # Сервисный слой
│   │   └── routers/          # API роутеры
│   ├── tests/                # Тесты
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React компоненты
│   │   ├── services/         # API сервисы
│   │   ├── contexts/         # React контексты
│   │   ├── types/            # TypeScript типы
│   │   └── __tests__/        # Тесты
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .github/workflows/        # CI/CD
```

## 🔐 Безопасность

### Роли и разрешения

| Роль | Описание | Разрешения |
|------|----------|------------|
| guest | Гость | Просмотр машин и бронирований |
| user | Пользователь | Создание и управление своими бронированиями |
| admin | Администратор | Полный доступ ко всем функциям |

### API Endpoints

#### Аутентификация
- `POST /auth/register` - Регистрация
- `POST /auth/login` - Вход
- `GET /auth/me` - Текущий пользователь
- `POST /auth/refresh` - Обновление токена
- `POST /auth/logout` - Выход

#### Машины
- `GET /machines/` - Список машин (с фильтрацией)
- `GET /machines/{id}` - Машина по ID
- `POST /machines/` - Создать машину (admin)
- `PUT /machines/{id}` - Обновить машину (admin)
- `DELETE /machines/{id}` - Удалить машину (admin)

#### Бронирования
- `GET /bookings/` - Список бронирований (с фильтрацией)
- `GET /bookings/my-bookings` - Мои бронирования
- `POST /bookings/` - Создать бронирование
- `POST /bookings/{id}/cancel` - Отменить бронирование
- `PUT /bookings/{id}` - Обновить бронирование
- `DELETE /bookings/{id}` - Удалить бронирование (admin)

#### Файлы (S3)
- `POST /files/upload` - Загрузить файл
- `GET /files/{path}` - Скачать файл
- `DELETE /files/{path}` - Удалить файл
- `GET /files/{path}/url` - Получить временную ссылку

#### SEO
- `GET /robots.txt` - Robots.txt
- `GET /sitemap.xml` - Sitemap
- `GET /manifest.json` - Web App Manifest

#### Внешние API
- `GET /external/weather` - Погода по координатам
- `GET /external/weather/recommendation` - Рекомендация по сушке

## 🧪 Тестирование

### Backend

```bash
cd backend
pip install -r test_requirements.txt
pytest --cov=app
```

### Frontend

```bash
cd frontend
npm test -- --coverage
```

## 📊 Метрики качества

- Покрытие тестами backend: ~80%
- Покрытие тестами frontend: ~70%
- Линтинг: flake8 (Python), ESLint (TypeScript)

## 🔧 Конфигурация

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
# Backend
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./laundry.db

# S3/MinIO
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=laundry-files

# OpenWeatherMap (опционально)
OPENWEATHER_API_KEY=your-api-key
```

## 📝 Лабораторные работы

Выполненные лабораторные работы:

1. ✅ RBAC - Роли и права доступа
2. ✅ Аутентификация (access/refresh токены)
3. ✅ Фильтрация, поиск, пагинация + S3
4. ✅ SEO-оптимизация + сторонний API
5. ✅ Тестирование (unit, integration, E2E)
6. ✅ Контейнеризация (Docker, CI/CD)

## 👥 Авторы

Студент группы [Ваша группа]
Martinez Fullstack Project
