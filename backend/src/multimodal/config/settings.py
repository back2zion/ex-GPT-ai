"""
ex-GPT 멀티모달 백엔드 설정

환경 변수를 통한 설정 관리
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8200, description="서버 포트")
    DEBUG: bool = Field(default=False, description="디버그 모드")
    WORKERS: int = Field(default=4, description="워커 프로세스 수")
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="허용된 오리진 목록"
    )
    
    # 모델 설정 (CPU 최적화)
    STT_MODEL: str = Field(default="openai/whisper-base", description="STT 모델 - CPU 최적화")
    IMAGE_MODEL: str = Field(default="openai/clip-vit-base-patch32", description="이미지 모델 - CPU 최적화")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="임베딩 모델")
    
    # GPU 설정 (CPU 전용 환경)
    CUDA_VISIBLE_DEVICES: str = Field(default="0", description="사용할 GPU 디바이스")
    USE_GPU: bool = Field(default=False, description="GPU 사용 여부 - CPU 전용 환경")
    
    # Qdrant 설정
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant 서버 URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant API 키")
    QDRANT_COLLECTION_NAME: str = Field(default="ex-gpt-multimodal", description="Qdrant 컬렉션 이름")
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, description="최대 파일 크기 (50MB)")
    UPLOAD_PATH: str = Field(default="./uploads", description="업로드 파일 저장 경로")
    ALLOWED_AUDIO_EXTENSIONS: List[str] = Field(
        default=[".wav", ".mp3", ".m4a", ".flac", ".ogg"],
        description="허용된 오디오 파일 확장자"
    )
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
        description="허용된 이미지 파일 확장자"
    )
    
    # Redis 설정 (캐싱용)
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis 서버 URL")
    REDIS_DB: int = Field(default=0, description="Redis 데이터베이스 번호")
    CACHE_TTL: int = Field(default=3600, description="캐시 TTL (초)")
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/exgpt_multimodal",
        description="데이터베이스 URL"
    )
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 형식"
    )
    
    # ex-GPT API 연동 설정
    EXGPT_API_URL: str = Field(default="http://localhost:8080", description="ex-GPT API 서버 URL")
    EXGPT_API_KEY: Optional[str] = Field(default=None, description="ex-GPT API 키")
    
    # CCTV 이미지 검색 설정
    CCTV_DATA_PATH: str = Field(
        default="C:/Users/user/Documents/interim_report/188.해무, 안개 CCTV 데이터/01.데이터",
        description="CCTV 데이터 경로"
    )
    OLLAMA_URL: str = Field(default="http://localhost:11434", description="Ollama 서버 URL")
    OLLAMA_VISION_MODEL: str = Field(default="llava:7b", description="Ollama 비전 모델")
    
    # 성능 설정 (CPU 환경 최적화)
    MAX_CONCURRENT_REQUESTS: int = Field(default=5, description="최대 동시 요청 수 - CPU 환경")
    REQUEST_TIMEOUT: int = Field(default=180, description="요청 타임아웃 (초)")
    
    # CPU 최적화 설정
    CPU_THREADS: int = Field(default=4, description="CPU 스레드 수")
    BATCH_SIZE: int = Field(default=1, description="배치 크기 - CPU 환경")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
