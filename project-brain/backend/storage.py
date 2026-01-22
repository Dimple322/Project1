import os
import hashlib
import io
from datetime import datetime
from typing import Optional
from minio import Minio
from minio.error import S3Error
from config import settings
from logger import get_logger

logger = get_logger(__name__)

class MinIOClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(self, file_path: str, object_name: str) -> str:
        """Upload file to MinIO and return object path"""
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as f:
                self.client.put_object(
                    self.bucket,
                    object_name,
                    f,
                    file_size,
                    part_size=10*1024*1024  # 10MB
                )
            logger.info(f"Uploaded file to MinIO: {object_name}")
            return f"{self.bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise
    
    def upload_bytes(self, data: bytes, object_name: str) -> str:
        """Upload bytes to MinIO"""
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(data),
                len(data)
            )
            logger.info(f"Uploaded bytes to MinIO: {object_name}")
            return f"{self.bucket}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading bytes to MinIO: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str) -> None:
        """Download file from MinIO"""
        try:
            response = self.client.get_object(self.bucket, object_name)
            with open(file_path, "wb") as f:
                for data in response.stream(32*1024):
                    f.write(data)
            logger.info(f"Downloaded file from MinIO: {object_name}")
        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise
    
    def download_bytes(self, object_name: str) -> bytes:
        """Download file from MinIO as bytes"""
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            logger.info(f"Downloaded bytes from MinIO: {object_name}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading bytes from MinIO: {e}")
            raise
    
    def delete_file(self, object_name: str) -> None:
        """Delete file from MinIO"""
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info(f"Deleted file from MinIO: {object_name}")
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            raise

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA256 hash of bytes"""
    return hashlib.sha256(data).hexdigest()

minio_client = MinIOClient()
