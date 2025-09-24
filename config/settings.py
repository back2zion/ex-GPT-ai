"""
Configuration Settings for ex-GPT System
시스템 설정 관리
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import yaml
import json

# .env 파일 로드
load_dotenv()


@dataclass
class ModelConfig:
    """모델 설정"""
    chat_model_endpoint: str
    chat_model_name: str
    embedding_model_endpoint: str
    embedding_model_name: str
    rerank_model_endpoint: str
    rerank_model_name: str
    vlm_model_name: str
    ocr_engine: str
    
    
@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    qdrant_host: str
    qdrant_port: int
    qdrant_collection_prefix: str
    vector_size: int
    
    
@dataclass
class StorageConfig:
    """저장소 설정"""
    upload_dir: str
    processed_dir: str
    temp_dir: str
    cache_dir: str
    backup_dir: str
    max_file_size: int
    
    
@dataclass
class SecurityConfig:
    """보안 설정"""
    enable_personal_info_detection: bool
    enable_duplicate_check: bool
    enable_virus_scan: bool
    allowed_file_extensions: list
    session_timeout: int
    
    
@dataclass
class PerformanceConfig:
    """성능 설정"""
    batch_size: int
    max_workers: int
    gpu_memory_fraction: float
    cache_size: int
    enable_profiling: bool


class Settings:
    """
    ex-GPT 시스템 통합 설정
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        설정 초기화
        
        Args:
            config_file: 설정 파일 경로
        """
        self.config_file = config_file or os.getenv("CONFIG_FILE", "config/settings.yaml")
        
        # 기본 설정 로드
        self.load_defaults()
        
        # 파일에서 설정 로드
        if os.path.exists(self.config_file):
            self.load_from_file()
            
        # 환경 변수에서 오버라이드
        self.load_from_env()
        
    def load_defaults(self):
        """기본 설정 로드"""
        # 모델 설정
        self.model = ModelConfig(
            chat_model_endpoint=os.getenv("CHAT_MODEL_ENDPOINT", "http://vllm:8000/v1"),
            chat_model_name=os.getenv("CHAT_MODEL_NAME", "Qwen/Qwen3-32B"),
            embedding_model_endpoint=os.getenv("EMBEDDING_MODEL_ENDPOINT", "http://vllm-embeddings:8100/v1"),
            embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-0.6B"),
            rerank_model_endpoint=os.getenv("RERANK_MODEL_ENDPOINT", "http://vllm-rerank:8101/v1"),
            rerank_model_name=os.getenv("RERANK_MODEL_NAME", "BAAI/bge-reranker-v2-m3"),
            vlm_model_name=os.getenv("VLM_MODEL_NAME", "Salesforce/blip-2-opt-2.7b"),
            ocr_engine=os.getenv("OCR_ENGINE", "easyocr")
        )
        
        # 데이터베이스 설정
        self.database = DatabaseConfig(
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            qdrant_collection_prefix=os.getenv("QDRANT_COLLECTION_PREFIX", "ex_gpt"),
            vector_size=int(os.getenv("VECTOR_SIZE", "768"))
        )
        
        # 저장소 설정
        self.storage = StorageConfig(
            upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
            processed_dir=os.getenv("PROCESSED_DIR", "./processed"),
            temp_dir=os.getenv("TEMP_DIR", "./temp"),
            cache_dir=os.getenv("CACHE_DIR", "./cache"),
            backup_dir=os.getenv("BACKUP_DIR", "./backups"),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024)))
        )
        
        # 보안 설정
        self.security = SecurityConfig(
            enable_personal_info_detection=os.getenv("ENABLE_PERSONAL_INFO_DETECTION", "true").lower() == "true",
            enable_duplicate_check=os.getenv("ENABLE_DUPLICATE_CHECK", "true").lower() == "true",
            enable_virus_scan=os.getenv("ENABLE_VIRUS_SCAN", "false").lower() == "true",
            allowed_file_extensions=[
                ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif",
                ".pdf", ".doc", ".docx", ".hwp", ".hwpx",
                ".xls", ".xlsx", ".csv", ".txt", ".md"
            ],
            session_timeout=int(os.getenv("SESSION_TIMEOUT", "3600"))
        )
        
        # 성능 설정
        self.performance = PerformanceConfig(
            batch_size=int(os.getenv("BATCH_SIZE", "32")),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            gpu_memory_fraction=float(os.getenv("GPU_MEMORY_FRACTION", "0.9")),
            cache_size=int(os.getenv("CACHE_SIZE", "1000")),
            enable_profiling=os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        )
        
        # 서비스별 설정
        self.services = {
            "image_processing": {
                "enable_vlm": os.getenv("FLAGS__ENABLE_VLM", "true").lower() == "true",
                "enable_ocr": True,
                "enable_security": True
            },
            "rag_pipeline": {
                "retriever_max_documents": int(os.getenv("SEARCH__RETRIEVER_MAX_DOCUMENTS", "10")),
                "retriever_score_threshold": float(os.getenv("SEARCH__RETRIEVER_SCORE_THRESHOLD", "0.0")),
                "reranker_max_documents": int(os.getenv("SEARCH__RERANKER_MAX_DOCUMENTS", "10")),
                "reranker_score_threshold": float(os.getenv("SEARCH__RERANKER_SCORE_THRESHOLD", "0.01")),
                "enable_rerank": os.getenv("FLAGS__ENABLE_RERANK", "true").lower() == "true"
            },
            "admin_tools": {
                "session_file_multiplier": float(os.getenv("SEARCH__SESSION_FILE_MULTIPLIER", "1.5")),
                "ga_file_multiplier": float(os.getenv("SEARCH__GA_FILE_MULTIPLIER", "1.1")),
                "enable_file_context_generation": os.getenv("FLAGS__ENABLE_FILE_CONTEXT_GENERATION", "true").lower() == "true"
            }
        }
        
        # 로깅 설정
        self.logging = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": os.getenv("LOG_FILE", "logs/ex-gpt.log"),
            "max_bytes": int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
        }
        
        # 한국도로공사 특화 설정
        self.korea_expressway = {
            "damage_types": [
                "포트홀", "균열", "침하", "파손", "박리", "마모"
            ],
            "infrastructure_types": [
                "톨게이트", "휴게소", "IC", "JC", "터널", "교량"
            ],
            "severity_levels": ["경미", "보통", "심각", "긴급"],
            "maintenance_priority": ["낮음", "보통", "높음", "긴급"]
        }
        
    def load_from_file(self):
        """파일에서 설정 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif self.config_file.endswith('.json'):
                    config = json.load(f)
                else:
                    return
                    
            # 설정 업데이트
            self._update_config(config)
            
        except Exception as e:
            print(f"설정 파일 로드 실패: {str(e)}")
            
    def load_from_env(self):
        """환경 변수에서 설정 오버라이드"""
        # 환경 변수는 이미 기본 설정에서 로드됨
        pass
        
    def _update_config(self, config: Dict[str, Any]):
        """설정 업데이트"""
        if 'model' in config:
            for key, value in config['model'].items():
                if hasattr(self.model, key):
                    setattr(self.model, key, value)
                    
        if 'database' in config:
            for key, value in config['database'].items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
                    
        if 'storage' in config:
            for key, value in config['storage'].items():
                if hasattr(self.storage, key):
                    setattr(self.storage, key, value)
                    
        if 'security' in config:
            for key, value in config['security'].items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
                    
        if 'performance' in config:
            for key, value in config['performance'].items():
                if hasattr(self.performance, key):
                    setattr(self.performance, key, value)
                    
        if 'services' in config:
            self.services.update(config['services'])
            
        if 'logging' in config:
            self.logging.update(config['logging'])
            
        if 'korea_expressway' in config:
            self.korea_expressway.update(config['korea_expressway'])
            
    def save_to_file(self, file_path: Optional[str] = None):
        """설정을 파일로 저장"""
        file_path = file_path or self.config_file
        
        config = {
            'model': self.model.__dict__,
            'database': self.database.__dict__,
            'storage': self.storage.__dict__,
            'security': self.security.__dict__,
            'performance': self.performance.__dict__,
            'services': self.services,
            'logging': self.logging,
            'korea_expressway': self.korea_expressway
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
                elif file_path.endswith('.json'):
                    json.dump(config, f, indent=2, ensure_ascii=False)
                    
            print(f"설정 저장 완료: {file_path}")
            
        except Exception as e:
            print(f"설정 저장 실패: {str(e)}")
            
    def validate(self) -> bool:
        """설정 검증"""
        errors = []
        
        # 필수 디렉토리 확인
        for dir_path in [self.storage.upload_dir, self.storage.processed_dir, 
                        self.storage.temp_dir, self.storage.cache_dir]:
            if not os.path.exists(dir_path):
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                except:
                    errors.append(f"디렉토리 생성 실패: {dir_path}")
                    
        # 포트 검증
        if not 1 <= self.database.qdrant_port <= 65535:
            errors.append(f"잘못된 포트 번호: {self.database.qdrant_port}")
            
        # 벡터 크기 검증
        if self.database.vector_size <= 0:
            errors.append(f"잘못된 벡터 크기: {self.database.vector_size}")
            
        if errors:
            for error in errors:
                print(f"설정 오류: {error}")
            return False
            
        return True
        
    def get_gpu_config(self) -> Dict[str, Any]:
        """GPU 설정 반환"""
        return {
            "device": "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu",
            "gpu_memory_fraction": self.performance.gpu_memory_fraction,
            "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES", "0"),
            "use_fp16": True,
            "use_flash_attention": True
        }
        
    def get_model_endpoints(self) -> Dict[str, str]:
        """모델 엔드포인트 반환"""
        return {
            "chat": self.model.chat_model_endpoint,
            "embedding": self.model.embedding_model_endpoint,
            "rerank": self.model.rerank_model_endpoint
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            'model': self.model.__dict__,
            'database': self.database.__dict__,
            'storage': self.storage.__dict__,
            'security': self.security.__dict__,
            'performance': self.performance.__dict__,
            'services': self.services,
            'logging': self.logging,
            'korea_expressway': self.korea_expressway,
            'gpu': self.get_gpu_config(),
            'endpoints': self.get_model_endpoints()
        }


# 싱글톤 인스턴스
settings = Settings()


# 테스트 코드
if __name__ == "__main__":
    # 설정 로드
    config = Settings()
    
    # 검증
    if config.validate():
        print("설정 검증 성공")
        
    # 설정 출력
    print("\n=== ex-GPT 시스템 설정 ===")
    print(f"\n[모델 설정]")
    print(f"Chat Model: {config.model.chat_model_name}")
    print(f"Embedding Model: {config.model.embedding_model_name}")
    print(f"VLM Model: {config.model.vlm_model_name}")
    
    print(f"\n[데이터베이스 설정]")
    print(f"Qdrant: {config.database.qdrant_host}:{config.database.qdrant_port}")
    print(f"Vector Size: {config.database.vector_size}")
    
    print(f"\n[저장소 설정]")
    print(f"Upload Dir: {config.storage.upload_dir}")
    print(f"Max File Size: {config.storage.max_file_size / (1024*1024):.2f}MB")
    
    print(f"\n[보안 설정]")
    print(f"개인정보 검출: {config.security.enable_personal_info_detection}")
    print(f"중복 검사: {config.security.enable_duplicate_check}")
    
    print(f"\n[성능 설정]")
    print(f"Batch Size: {config.performance.batch_size}")
    print(f"Max Workers: {config.performance.max_workers}")
    print(f"GPU Memory: {config.performance.gpu_memory_fraction}")
    
    # 설정 저장
    # config.save_to_file("config/settings_export.yaml")
