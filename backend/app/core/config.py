"""
애플리케이션 설정 관리
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8201, description="서버 포트")
    DEBUG: bool = Field(default=True, description="디버그 모드")
    
    # Ollama 설정
    OLLAMA_HOST: str = Field(default="http://localhost:11434", description="Ollama 서버 주소")
    OLLAMA_MODEL_NAME: str = Field(default="qwen3:8b", description="기본 LLM 모델")
    OLLAMA_VLM_MODEL: str = Field(default="llava:7b", description="비전-언어 모델")
    OLLAMA_TIMEOUT: int = Field(default=300, description="Ollama 요청 타임아웃(초)")
    
    # 이미지 관련 설정
    IMAGE_FOLDER_PATH: str = Field(
        default=r"C:\Users\user\Documents\ex-GPT-ai\data\1.Training\원천데이터\이미지데이터",
        description="이미지 폴더 경로"
    )
    OBSERVATION_DATA_PATH: str = Field(
        default=r"C:\Users\user\Documents\ex-GPT-ai\data\1.Training\원천데이터\관측데이터",
        description="관측데이터 폴더 경로 (CSV 파일)"
    )
    SUPPORTED_IMAGE_FORMATS: list = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"],
        description="지원하는 이미지 형식"
    )
    MAX_IMAGE_SIZE: int = Field(default=10 * 1024 * 1024, description="최대 이미지 크기(바이트)")
    
    # 검색 설정
    DEFAULT_SEARCH_LIMIT: int = Field(default=20, description="기본 검색 결과 수")
    MAX_SEARCH_LIMIT: int = Field(default=100, description="최대 검색 결과 수")
    SIMILARITY_THRESHOLD: float = Field(default=0.1, description="유사도 임계값")
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(default="sqlite:///./multimodal.db", description="데이터베이스 URL")
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    LOG_FILE: Optional[str] = Field(default="logs/multimodal.log", description="로그 파일 경로")
    
    # 보안 설정
    SECRET_KEY: str = Field(default="ex-gpt-multimodal-secret-key-2025", description="JWT 시크릿 키")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="액세스 토큰 만료 시간(분)")
    
    # API 설정
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    
    # CPU 전용 설정 (GPU 없는 환경)
    DEVICE: str = Field(default="cpu", description="연산 장치")
    NUM_THREADS: int = Field(default=4, description="CPU 스레드 수")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 필드 무시

# 전역 설정 인스턴스
settings = Settings()

# 필요한 디렉토리 생성
def create_directories():
    """필요한 디렉토리들을 생성"""
    directories = [
        Path("logs"),
        Path("temp"),
        Path("cache"),
        Path(settings.IMAGE_FOLDER_PATH).parent if settings.IMAGE_FOLDER_PATH else None
    ]
    
    for directory in directories:
        if directory and not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

# 초기화 시 디렉토리 생성
create_directories()
