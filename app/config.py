"""Application configuration settings."""
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "OpenJustice Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # "development" | "production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/openjustice"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ISSUER: str = "openjustice"
    JWT_AUDIENCE: str = "openjustice-api"
    AUTH_COOKIE_NAME: str = "access_token"
    AUTH_COOKIE_SAMESITE: str = "strict"
    AUTH_COOKIE_SECURE: Optional[bool] = None
    RECAPTCHA_SECRET_KEY: Optional[str] = None
    RECAPTCHA_SITE_KEY: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_MAX_TOKENS: int = 1200
    OPENAI_TEMPERATURE: float = 0.2
    
    # Whisper (Speech-to-Text)
    WHISPER_MODEL: str = "gpt-4o-mini-transcribe"
    
    # TTS (Text-to-Speech)
    TTS_MODEL: str = "gpt-4o-mini-tts"
    TTS_VOICE: str = "alloy"
    
    # Audio Processing & Storage Limits
    MAX_AUDIO_DURATION_SECONDS: int = 300
    MAX_AUDIO_FILE_SIZE_MB: int = 25
    AUDIO_TEMP_DIR: str = "temp/audio"
    AUDIO_MEDIA_DIR: str = "media/audio"
    AUDIO_RETENTION_MINUTES: int = 60
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    
    # MinIO (Local Storage)
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET_NAME: str = "openjustice"
    MINIO_SECURE: bool = False

    # Azure Blob Storage
    # Use connection string OR (account name + managed identity).
    # Set AZURE_STORAGE_CONNECTION_STRING in Azure Container App secrets.
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = None
    AZURE_STORAGE_CONTAINER_NAME: str = "openjustice"
    
    # Azure Communication Services
    AZURE_COMMUNICATION_CONNECTION_STRING: Optional[str] = None
    AZURE_SENDER_EMAIL: Optional[str] = None
    
    # WhatsApp (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # Public URL (your ngrok / production domain — Twilio needs this to fetch audio files)
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    
    # Frontend URL (for email links, etc)
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    
    # WhatsApp (Meta Cloud API)
    META_WHATSAPP_TOKEN: Optional[str] = None
    META_WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    META_WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_AUDIO_FORMATS: list[str] = ["mp3", "wav", "ogg", "m4a"]
    ALLOWED_DOCUMENT_FORMATS: list[str] = ["pdf", "txt", "docx"]
    
    # RAG & Semantic Cache Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    VECTOR_SEARCH_TOP_K: int = 5
    CACHE_SIMILARITY_THRESHOLD: float = 0.95
    
    @model_validator(mode="after")
    def _validate_production_settings(self) -> "Settings":
        """Refuse to start in production with unsafe default values."""
        if self.ENVIRONMENT == "production":
            if self.PUBLIC_BASE_URL == "http://localhost:8000":
                raise ValueError(
                    "PUBLIC_BASE_URL must be set to your Azure Container App URL in production. "
                    "Set it via the Azure Container App environment variables."
                )
            if self.SECRET_KEY == "your-secret-key-change-this-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed from the default value in production. "
                    "Generate one with: openssl rand -hex 32"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
