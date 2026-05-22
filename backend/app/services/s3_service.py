"""
Сервис для работы с S3-совместимым хранилищем (MinIO).
Используется для загрузки и хранения пользовательских файлов.
"""
import os
import io
from typing import Optional, BinaryIO
from datetime import timedelta

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False


class S3Service:
    """
    Сервис для работы с S3-совместимым объектным хранилищем.
    Поддерживает MinIO, AWS S3, Yandex Object Storage и др.
    """
    
    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        bucket_name: str = None,
        secure: bool = False
    ):
        """
        Инициализация S3 сервиса.
        
        :param endpoint: URL S3 эндпоинта (например, localhost:9000)
        :param access_key: Access key для аутентификации
        :param secret_key: Secret key для аутентификации
        :param bucket_name: Имя бакета по умолчанию
        :param secure: Использовать HTTPS
        """
        self.endpoint = endpoint or os.getenv("S3_ENDPOINT", "localhost:9000")
        self.access_key = access_key or os.getenv("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = secret_key or os.getenv("S3_SECRET_KEY", "minioadmin")
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "laundry-files")
        self.secure = secure or os.getenv("S3_SECURE", "false").lower() == "true"
        
        self._client: Optional[Minio] = None
        
        if MINIO_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Инициализация Minio клиента"""
        try:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            # Создаем бакет если не существует
            self._ensure_bucket_exists()
        except Exception as e:
            print(f"Warning: S3 service initialization failed: {e}")
            self._client = None
    
    def _ensure_bucket_exists(self):
        """Создание бакета если он не существует"""
        if not self._client:
            return
        
        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def upload_file(
        self,
        file: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        file_size: Optional[int] = None
    ) -> Optional[str]:
        """
        Загрузка файла в S3.
        
        :param file: Файловый объект для загрузки
        :param object_name: Имя объекта в хранилище
        :param content_type: MIME тип файла
        :param file_size: Размер файла в байтах
        :return: URL загруженного файла или None при ошибке
        """
        if not self._client or not MINIO_AVAILABLE:
            return None
        
        try:
            # Получаем данные файла
            file_data = file.read()
            file_size = file_size or len(file_data)
            
            # Загружаем в S3
            self._client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(file_data),
                length=file_size,
                content_type=content_type
            )
            
            return f"{self.endpoint}/{self.bucket_name}/{object_name}"
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return None
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        Скачивание файла из S3.
        
        :param object_name: Имя объекта в хранилище
        :return: Байты файла или None при ошибке
        """
        if not self._client or not MINIO_AVAILABLE:
            return None
        
        try:
            response = self._client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return None
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Получение временной ссылки для доступа к файлу.
        
        :param object_name: Имя объекта в хранилище
        :param expires: Время действия ссылки
        :return: Presigned URL или None при ошибке
        """
        if not self._client or not MINIO_AVAILABLE:
            return None
        
        try:
            return self._client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """
        Удаление файла из S3.
        
        :param object_name: Имя объекта в хранилище
        :return: True если успешно, False при ошибке
        """
        if not self._client or not MINIO_AVAILABLE:
            return False
        
        try:
            self._client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """
        Получение списка файлов в бакете.
        
        :param prefix: Префикс для фильтрации файлов
        :return: Список имен файлов
        """
        if not self._client or not MINIO_AVAILABLE:
            return []
        
        try:
            objects = self._client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []
    
    def file_exists(self, object_name: str) -> bool:
        """Проверка существования файла"""
        if not self._client or not MINIO_AVAILABLE:
            return False
        
        try:
            self._client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Получение экземпляра S3 сервиса (singleton)"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
