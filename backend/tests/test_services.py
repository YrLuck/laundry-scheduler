"""
Модульные тесты для сервисного слоя.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.repositories import UserRepository, RoleRepository
from app.schemas import UserCreate, RoleCreate
from app.auth import get_password_hash


class TestAuthService:
    """Тесты для AuthService"""
    
    def test_verify_password_correct(self, db_session: Session):
        """Тест проверки правильного пароля"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        auth_service = AuthService(UserRepository(db_session))
        result = auth_service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_wrong(self, db_session: Session):
        """Тест проверки неправильного пароля"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        auth_service = AuthService(UserRepository(db_session))
        result = auth_service.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_get_password_hash(self, db_session: Session):
        """Тест хеширования пароля"""
        password = "testpassword123"
        
        auth_service = AuthService(UserRepository(db_session))
        hashed = auth_service.get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_create_access_token(self, db_session: Session):
        """Тест создания access токена"""
        auth_service = AuthService(UserRepository(db_session))
        
        token = auth_service.create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_create_refresh_token(self, db_session: Session):
        """Тест создания refresh токена"""
        auth_service = AuthService(UserRepository(db_session))
        
        token = auth_service.create_refresh_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(days=7)
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_create_token_pair(self, db_session: Session):
        """Тест создания пары токенов"""
        auth_service = AuthService(UserRepository(db_session))
        
        tokens = auth_service.create_token_pair("testuser")
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_validate_access_token(self, db_session: Session):
        """Тест валидации access токена"""
        auth_service = AuthService(UserRepository(db_session))
        
        token = auth_service.create_access_token({"sub": "testuser"})
        result = auth_service.validate_token(token, token_type="access")
        
        assert result is not None
        assert result.username == "testuser"
    
    def test_validate_invalid_token(self, db_session: Session):
        """Тест валидации невалидного токена"""
        auth_service = AuthService(UserRepository(db_session))
        
        result = auth_service.validate_token("invalid_token", token_type="access")
        
        assert result is None
    
    def test_validate_wrong_token_type(self, db_session: Session):
        """Тест валидации токена неправильного типа"""
        auth_service = AuthService(UserRepository(db_session))
        
        # Создаем access токен
        access_token = auth_service.create_access_token({"sub": "testuser"})
        
        # Пытаемся валидировать как refresh
        result = auth_service.validate_token(access_token, token_type="refresh")
        
        assert result is None
    
    def test_refresh_tokens(self, db_session: Session):
        """Тест обновления токенов"""
        auth_service = AuthService(UserRepository(db_session))
        
        # Создаем refresh токен
        refresh_token = auth_service.create_refresh_token({"sub": "testuser"})
        
        # Обновляем токены
        new_tokens = auth_service.refresh_tokens(refresh_token)
        
        assert new_tokens is not None
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
    
    def test_authenticate_success(self, db_session: Session, test_user: dict):
        """Тест успешной аутентификации"""
        auth_service = AuthService(UserRepository(db_session))
        
        result = auth_service.authenticate(
            test_user["username"],
            test_user["password"]
        )
        
        assert result is not None
        assert result["username"] == test_user["username"]
    
    def test_authenticate_wrong_password(self, db_session: Session, test_user: dict):
        """Тест аутентификации с неправильным паролем"""
        auth_service = AuthService(UserRepository(db_session))
        
        result = auth_service.authenticate(
            test_user["username"],
            "wrongpassword"
        )
        
        assert result is None
    
    def test_authenticate_nonexistent_user(self, db_session: Session):
        """Тест аутентификации несуществующего пользователя"""
        auth_service = AuthService(UserRepository(db_session))
        
        result = auth_service.authenticate("nonexistent", "password123")
        
        assert result is None


class TestHasPermission:
    """Тесты для проверки разрешений"""
    
    def test_admin_has_all_permissions(self, db_session: Session, test_admin: dict):
        """Тест что админ имеет все разрешения"""
        from app.repositories import UserRepository
        
        user_repo = UserRepository(db_session)
        
        # Админ должен иметь любое разрешение
        assert user_repo.has_permission(test_admin["id"], "machines:create") is True
        assert user_repo.has_permission(test_admin["id"], "bookings:delete") is True
        assert user_repo.has_permission(test_admin["id"], "any:permission") is True
    
    def test_user_has_limited_permissions(self, db_session: Session, test_user: dict):
        """Тест что обычный пользователь имеет ограниченные разрешения"""
        from app.repositories import UserRepository
        
        user_repo = UserRepository(db_session)
        
        # Обычный пользователь должен иметь bookings:create и bookings:update
        assert user_repo.has_permission(test_user["id"], "bookings:create") is True
        assert user_repo.has_permission(test_user["id"], "bookings:update") is True
        
        # Но не должен иметь machines:create
        assert user_repo.has_permission(test_user["id"], "machines:create") is False
