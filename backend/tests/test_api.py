"""
Тесты для машин и бронирований.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app import crud, schemas
from app.models import Machine, Booking


class TestMachines:
    """Тесты для машин"""
    
    def test_get_machines_public(self, client: TestClient, db_session: Session):
        """Тест получения списка машин (публично)"""
        # Создаем тестовые машины
        machine1 = Machine(name="Machine 1", type="washer", status="available")
        machine2 = Machine(name="Machine 2", type="dryer", status="available")
        db_session.add_all([machine1, machine2])
        db_session.commit()
        
        response = client.get("/machines/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_machines_with_filters(self, client: TestClient, db_session: Session):
        """Тест фильтрации машин"""
        machine1 = Machine(name="Washer 1", type="washer", status="available")
        machine2 = Machine(name="Dryer 1", type="dryer", status="available")
        machine3 = Machine(name="Washer 2", type="washer", status="in_use")
        db_session.add_all([machine1, machine2, machine3])
        db_session.commit()
        
        # Фильтр по типу
        response = client.get("/machines/?machine_type=washer")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Фильтр по статусу
        response = client.get("/machines/?status=available")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Поиск по названию
        response = client.get("/machines/?search=Washer")
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_get_machines_pagination(self, client: TestClient, db_session: Session):
        """Тест пагинации машин"""
        # Создаем 15 машин
        for i in range(15):
            db_session.add(Machine(name=f"Machine {i}", type="washer", status="available"))
        db_session.commit()
        
        # Получаем первые 10
        response = client.get("/machines/?skip=0&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 10
        
        # Получаем следующие 5
        response = client.get("/machines/?skip=10&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 5
    
    def test_get_machines_sorting(self, client: TestClient, db_session: Session):
        """Тест сортировки машин"""
        machine1 = Machine(name="Zebra", type="washer", status="available")
        machine2 = Machine(name="Alpha", type="washer", status="available")
        machine3 = Machine(name="Beta", type="washer", status="available")
        db_session.add_all([machine1, machine2, machine3])
        db_session.commit()
        
        # Сортировка по имени (asc)
        response = client.get("/machines/?sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Alpha"
        assert data[2]["name"] == "Zebra"
        
        # Сортировка по имени (desc)
        response = client.get("/machines/?sort_by=name&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Zebra"
    
    def test_create_machine_admin(self, client: TestClient, admin_token: str):
        """Тест создания машины админом"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        machine_data = {
            "name": "New Machine",
            "type": "washer",
            "status": "available"
        }
        
        response = client.post("/machines/", json=machine_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == machine_data["name"]
        assert data["type"] == machine_data["type"]
    
    def test_create_machine_unauthorized(self, client: TestClient):
        """Тест создания машины без авторизации"""
        machine_data = {
            "name": "New Machine",
            "type": "washer"
        }
        
        response = client.post("/machines/", json=machine_data)
        
        assert response.status_code == 401
    
    def test_get_machine_by_id(self, client: TestClient, db_session: Session):
        """Тест получения машины по ID"""
        machine = Machine(name="Test Machine", type="washer", status="available")
        db_session.add(machine)
        db_session.commit()
        
        response = client.get(f"/machines/{machine.id}")
        
        assert response.status_code == 200
        assert response.json()["name"] == "Test Machine"
    
    def test_get_nonexistent_machine(self, client: TestClient):
        """Тест получения несуществующей машины"""
        response = client.get("/machines/999")
        
        assert response.status_code == 404


class TestBookings:
    """Тесты для бронирований"""
    
    def test_create_booking(self, client: TestClient, auth_token: str, db_session: Session):
        """Тест создания бронирования"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем машину
        machine = Machine(name="Test Machine", type="washer", status="available")
        db_session.add(machine)
        db_session.commit()
        
        booking_data = {
            "machine_id": machine.id,
            "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat()
        }
        
        response = client.post("/bookings/", json=booking_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["machine_id"] == booking_data["machine_id"]
        assert data["status"] == "active"
    
    def test_create_booking_conflict(self, client: TestClient, auth_token: str, db_session: Session):
        """Тест создания конфликтующего бронирования"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем машину
        machine = Machine(name="Test Machine", type="washer", status="available")
        db_session.add(machine)
        db_session.commit()
        
        # Создаем первое бронирование
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        booking1 = Booking(
            machine_id=machine.id,
            user_id=1,
            user_name="testuser",
            start_time=start_time,
            end_time=end_time,
            status="active"
        )
        db_session.add(booking1)
        db_session.commit()
        
        # Пытаемся создать конфликтующее бронирование
        booking_data = {
            "machine_id": machine.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        response = client.post("/bookings/", json=booking_data, headers=headers)
        
        assert response.status_code == 400
        assert "Booking conflict" in response.json()["detail"]
    
    def test_get_my_bookings(self, client: TestClient, auth_token: str, db_session: Session):
        """Тест получения своих бронирований"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем машину и бронирование
        machine = Machine(name="Test Machine", type="washer", status="available")
        db_session.add(machine)
        db_session.commit()
        
        booking = Booking(
            machine_id=machine.id,
            user_id=1,
            user_name="testuser",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            status="active"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.get("/bookings/my-bookings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_cancel_booking(self, client: TestClient, auth_token: str, db_session: Session):
        """Тест отмены бронирования"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем машину и бронирование
        machine = Machine(name="Test Machine", type="washer", status="available")
        db_session.add(machine)
        db_session.commit()
        
        booking = Booking(
            machine_id=machine.id,
            user_id=1,
            user_name="testuser",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            status="active"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.post(f"/bookings/{booking.id}/cancel", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_get_bookings_with_filters(self, client: TestClient, auth_token: str, db_session: Session):
        """Тест фильтрации бронирований"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Создаем машины и бронирования
        machine1 = Machine(name="Machine 1", type="washer", status="available")
        machine2 = Machine(name="Machine 2", type="dryer", status="available")
        db_session.add_all([machine1, machine2])
        db_session.commit()
        
        booking1 = Booking(machine_id=machine1.id, user_id=1, user_name="testuser", status="active",
                          start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=1))
        booking2 = Booking(machine_id=machine2.id, user_id=1, user_name="testuser", status="completed",
                          start_time=datetime.now(), end_time=datetime.now() + timedelta(hours=1))
        db_session.add_all([booking1, booking2])
        db_session.commit()
        
        # Фильтр по статусу
        response = client.get("/bookings/?status=active", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
