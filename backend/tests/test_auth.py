"""
Тесты для аутентификации и авторизации.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_password_hash


class TestAuth:
    """Тесты для аутентификации"""
    
    def test_register_user(self, client: TestClient, db_session: Session):
        """Тест регистрации нового пользователя"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepassword123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "hashed_password" not in data  # Пароль не должен возвращаться
    
    def test_register_duplicate_username(self, client: TestClient, test_user: dict):
        """Тест регистрации с дублирующимся username"""
        user_data = {
            "username": test_user["username"],
            "email": "another@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user: dict):
        """Тест регистрации с дублирующимся email"""
        user_data = {
            "username": "anotheruser",
            "email": test_user["email"],
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_login_success(self, client: TestClient, test_user: dict):
        """Тест успешного входа"""
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client: TestClient, test_user: dict):
        """Тест входа с неправильным паролем"""
        login_data = {
            "username": test_user["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Тест входа для несуществующего пользователя"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient, auth_token: str):
        """Тест получения текущего пользователя"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Тест получения текущего пользователя без токена"""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_token_refresh(self, client: TestClient, test_user: dict):
        """Тест обновления токена"""
        # Логинимся
        login_response = client.post(
            "/auth/login",
            data={"username": test_user["username"], "password": test_user["password"]}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Обновляем токены
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = client.post("/auth/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, client: TestClient, auth_token: str):
        """Тест выхода из системы"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "message" in response.json()


class TestRoleBasedAccess:
    """Тесты для RBAC"""
    
    def test_admin_access_to_users(self, client: TestClient, admin_token: str):
        """Тест доступа админа к списку пользователей"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/users/", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_user_no_access_to_users(self, client: TestClient, auth_token: str):
        """Тест запрета доступа обычного пользователя к пользователям"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.get("/users/", headers=headers)
        
        assert response.status_code == 403
    
    def test_unauthorized_access_to_protected_route(self, client: TestClient):
        """Тест доступа к защищенному роуту без авторизации"""
        response = client.get("/auth/me")

        # FastAPI вернет 401/403 для защищенного endpoint
        assert response.status_code in (401, 403)
