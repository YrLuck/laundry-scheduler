"""
Конфигурация и фикстуры для тестов.
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import crud, schemas
from app.auth import get_password_hash


# Создаем тестовую БД в памяти
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Фикстура для создания сессии БД.
    Создает таблицы перед каждым тестом и удаляет после.
    """
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Создаем сессию
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Удаляем все таблицы после теста
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Generator) -> Generator:
    """
    Фикстура для создания тестового клиента.
    Подменяет зависимость get_db на тестовую сессию.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session) -> dict:
    """
    Фикстура для создания тестового пользователя.
    """
    from app.repositories import RoleRepository, UserRepository, PermissionRepository
    from app.schemas import PermissionCreate

    # Создаём разрешения для роли "user"
    perm_repo = PermissionRepository(db_session)
    perm_create = perm_repo.get_by_name("bookings:create") or perm_repo.create(
        PermissionCreate(name="bookings:create", description="Create bookings")
    )
    perm_update = perm_repo.get_by_name("bookings:update") or perm_repo.create(
        PermissionCreate(name="bookings:update", description="Update bookings")
    )

    # Создаем роль "user" с разрешениями если нет
    role_repo = RoleRepository(db_session)
    user_role = role_repo.get_by_name("user")
    if not user_role:
        user_role = role_repo.create(schemas.RoleCreate(
            name="user",
            description="Test user role",
            permission_ids=[perm_create.id, perm_update.id]
        ))

    # Создаем пользователя
    user_repo = UserRepository(db_session)
    user_data = schemas.UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="password123"
    )

    hashed_password = get_password_hash(user_data.password)
    user = user_repo.create(user_data, hashed_password, role_id=user_role.id)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": "password123"
    }


@pytest.fixture(scope="function")
def test_admin(db_session) -> dict:
    """
    Фикстура для создания тестового администратора.
    """
    from app.repositories import RoleRepository, UserRepository
    
    # Создаем роль "admin" если нет
    role_repo = RoleRepository(db_session)
    admin_role = role_repo.get_by_name("admin")
    if not admin_role:
        admin_role = role_repo.create(schemas.RoleCreate(name="admin", description="Admin role"))
    
    # Создаем админа
    user_repo = UserRepository(db_session)
    admin_data = schemas.UserCreate(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        password="adminpass123"
    )
    
    hashed_password = get_password_hash(admin_data.password)
    admin = user_repo.create(admin_data, hashed_password, role_id=admin_role.id)
    
    return {
        "id": admin.id,
        "username": "admin",
        "email": admin.email,
        "password": "adminpass123"
    }


@pytest.fixture(scope="function")
def auth_token(client: TestClient, test_user: dict) -> str:
    """
    Фикстура для получения токена аутентификации.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client: TestClient, test_admin: dict) -> str:
    """
    Фикстура для получения токена администратора.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": test_admin["username"],
            "password": test_admin["password"]
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]
