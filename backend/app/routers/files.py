"""
Router для работы с файлами (загрузка, скачивание, удаление).
Интеграция с S3-совместимым хранилищем.
"""
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.schemas import User
from app import auth, crud
from app.services.s3_service import get_s3_service

router = APIRouter(prefix="/files", tags=["files"])

# Допустимые типы файлов
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "text/plain",
    "application/json",
}

# Максимальный размер файла (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="Файл для загрузки"),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Загрузка файла в S3 хранилище.
    
    Требования:
    - Аутентификация пользователя
    - Допустимый тип файла
    - Размер файла не более 10 MB
    """
    # Проверка типа файла
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    # Чтение файла и проверка размера
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // 1024 // 1024} MB"
        )
    
    # Генерация уникального имени файла
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    object_name = f"user_{current_user.id}/{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}{file_extension}"
    
    # Загрузка в S3
    s3_service = get_s3_service()
    
    from io import BytesIO
    file_url = s3_service.upload_file(
        file=BytesIO(file_content),
        object_name=object_name,
        content_type=file.content_type,
        file_size=len(file_content)
    )
    
    if not file_url:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке файла")
    
    return {
        "message": "Файл успешно загружен",
        "file_name": file.filename,
        "object_name": object_name,
        "file_url": file_url,
        "content_type": file.content_type,
        "file_size": len(file_content)
    }


@router.get("/{object_name:path}")
async def download_file(
    object_name: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Скачивание файла из S3 хранилища.
    
    Доступ к файлам имеют:
    - Владелец файла (по префиксу user_id)
    - Администраторы
    """
    # Проверка доступа к файлу
    if not object_name.startswith(f"user_{current_user.id}/"):
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Нет доступа к этому файлу")
    
    s3_service = get_s3_service()
    file_content = s3_service.download_file(object_name)
    
    if not file_content:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Определение content_type
    content_type = "application/octet-stream"
    if object_name.endswith(".jpg") or object_name.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif object_name.endswith(".png"):
        content_type = "image/png"
    elif object_name.endswith(".gif"):
        content_type = "image/gif"
    elif object_name.endswith(".pdf"):
        content_type = "application/pdf"
    elif object_name.endswith(".txt"):
        content_type = "text/plain"
    
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={object_name.split('/')[-1]}"
        }
    )


@router.get("/{object_name:path}/url")
async def get_presigned_url(
    object_name: str,
    expires: int = Query(3600, ge=300, le=604800, description="Время действия ссылки в секундах"),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение временной ссылки для доступа к файлу.
    
    :param expires: Время действия ссылки (от 5 минут до 7 дней)
    """
    # Проверка доступа
    if not object_name.startswith(f"user_{current_user.id}/"):
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Нет доступа к этому файлу")
    
    from datetime import timedelta
    s3_service = get_s3_service()
    url = s3_service.get_presigned_url(
        object_name=object_name,
        expires=timedelta(seconds=expires)
    )
    
    if not url:
        raise HTTPException(status_code=500, detail="Ошибка при генерации ссылки")
    
    return {"url": url, "expires_in": expires}


@router.delete("/{object_name:path}")
async def delete_file(
    object_name: str,
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Удаление файла из S3 хранилища.
    """
    # Проверка доступа
    if not object_name.startswith(f"user_{current_user.id}/"):
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Нет доступа к этому файлу")
    
    s3_service = get_s3_service()
    success = s3_service.delete_file(object_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Файл не найден или ошибка при удалении")
    
    return {"message": "Файл успешно удален"}


@router.get("/")
async def list_files(
    prefix: Optional[str] = Query(None, description="Префикс для фильтрации файлов"),
    current_user: User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка файлов пользователя.
    """
    # По умолчанию показываем только файлы текущего пользователя
    if prefix is None:
        prefix = f"user_{current_user.id}/"
    elif not prefix.startswith(f"user_{current_user.id}/"):
        if not (current_user.role and current_user.role.name == "admin"):
            raise HTTPException(status_code=403, detail="Нет доступа к этим файлам")
    
    s3_service = get_s3_service()
    files = s3_service.list_files(prefix=prefix)
    
    return {
        "files": files,
        "count": len(files)
    }
