from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db, SessionLocal
from app import models
from app.routers import machines, bookings, auth, users, rbac, files, external, seo

# Создаём все таблицы в БД при старте (если их ещё нет)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Laundry Scheduler", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(machines.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rbac.router)
app.include_router(files.router)
app.include_router(external.router)
app.include_router(seo.router)

@app.get("/")
def read_root():
    return {"message": "Laundry Scheduler API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
def startup_event():
    """Инициализация ролей и разрешений при старте приложения"""
    from app import crud
    from app.schemas import RoleCreate, PermissionCreate
    
    db = SessionLocal()
    try:
        # Создаем разрешения
        permissions_data = [
            {"name": "machines:create", "description": "Создание машин"},
            {"name": "machines:update", "description": "Обновление машин"},
            {"name": "machines:delete", "description": "Удаление машин"},
            {"name": "bookings:create", "description": "Создание бронирований"},
            {"name": "bookings:update", "description": "Обновление бронирований"},
            {"name": "bookings:delete", "description": "Удаление бронирований"},
            {"name": "users:manage", "description": "Управление пользователями"},
            {"name": "roles:manage", "description": "Управление ролями"},
        ]
        
        permissions = {}
        for perm_data in permissions_data:
            perm = crud.get_permission_by_name(db, name=perm_data["name"])
            if not perm:
                perm = crud.create_permission(db, PermissionCreate(**perm_data))
            permissions[perm_data["name"]] = perm
        
        # Создаем роли
        roles_data = {
            "guest": {
                "description": "Гость - может только просматривать машины и бронирования",
                "permissions": []
            },
            "user": {
                "description": "Пользователь - может создавать и управлять своими бронированиями",
                "permissions": ["bookings:create", "bookings:update"]
            },
            "admin": {
                "description": "Администратор - полный доступ ко всем функциям",
                "permissions": list(permissions.keys())
            }
        }
        
        for role_name, role_data in roles_data.items():
            role = crud.get_role_by_name(db, name=role_name)
            if not role:
                # Получаем объекты разрешений
                perm_ids = [permissions[p_name].id for p_name in role_data["permissions"]]
                role_create = RoleCreate(name=role_name, description=role_data["description"], permission_ids=perm_ids)
                crud.create_role(db, role_create)
                print(f"Role '{role_name}' created successfully")
            else:
                print(f"Role '{role_name}' already exists")
        
        db.commit()
        print("RBAC initialization completed")

        # Создаём дефолтного администратора если его ещё нет
        from app.auth import get_password_hash
        from app.schemas import UserCreate
        admin_user = crud.get_user_by_username(db, username="admin")
        if not admin_user:
            admin_role = crud.get_role_by_name(db, name="admin")
            admin_create = UserCreate(
                username="admin",
                email="admin@example.com",
                full_name="Administrator",
                password="admin123"
            )
            crud.create_user(db, admin_create, get_password_hash("admin123"), role_id=admin_role.id if admin_role else None)
            print("Admin user created: login=admin, password=admin123")
        else:
            print("Admin user already exists")

        # Seed машины для демонстрации пагинации
        from app.schemas import MachineCreate
        seed_machines = [
            ("Стиральная машина A1", "washer", "available"),
            ("Стиральная машина A2", "washer", "available"),
            ("Стиральная машина A3", "washer", "in_use"),
            ("Стиральная машина A4", "washer", "available"),
            ("Стиральная машина B1", "washer", "maintenance"),
            ("Стиральная машина B2", "washer", "available"),
            ("Стиральная машина B3", "washer", "available"),
            ("Стиральная машина B4", "washer", "in_use"),
            ("Сушилка 1", "dryer", "available"),
            ("Сушилка 2", "dryer", "available"),
            ("Сушилка 3", "dryer", "in_use"),
            ("Сушилка 4", "dryer", "available"),
            ("Сушилка 5", "dryer", "maintenance"),
        ]
        for name, mtype, mstatus in seed_machines:
            existing = db.query(models.Machine).filter(models.Machine.name == name).first()
            if not existing:
                crud.create_machine(db, MachineCreate(name=name, type=mtype, status=mstatus))
        print("Seed machines created")
    except Exception as e:
        db.rollback()
        print(f"Error during RBAC initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)