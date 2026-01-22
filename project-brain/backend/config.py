import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://brain_user:brain_password@localhost:5432/project_brain"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = "qdrant_key"
    
    # Neo4j
    NEO4J_URL: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"
    
    # MinIO
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "project-brain"
    MINIO_SECURE: bool = False
    
    # LM Studio
    LM_STUDIO_URL: str = "http://localhost:1234"
    LM_STUDIO_MODEL: str = "lm-studio"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # API
    API_TITLE: str = "Project Brain"
    API_VERSION: str = "0.1.0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()
