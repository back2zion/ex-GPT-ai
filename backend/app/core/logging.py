"""
ex-GPT 멀티모달 백엔드 로깅 설정
"""

import sys
from pathlib import Path
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """로깅 설정 초기화"""
    # 기본 로거 제거
    logger.remove()
    
    # 로그 디렉토리 생성
    log_dir = Path(settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 콘솔 로그 설정 (개발 환경)
    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True
        )
    
    # 파일 로그 설정
    logger.add(
        settings.LOG_FILE_PATH,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        serialize=False
    )
    
    # 에러 로그 별도 파일
    error_log_path = str(settings.LOG_FILE_PATH).replace(".log", "_error.log")
    logger.add(
        error_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        serialize=False
    )
    
    # 파일 처리 로그
    file_log_path = str(settings.LOG_FILE_PATH).replace(".log", "_files.log")
    logger.add(
        file_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | FILES | {message}",
        level="INFO",
        rotation="50 MB",
        retention="30 days",
        filter=lambda record: any(keyword in record["message"].lower() 
                                for keyword in ["upload", "download", "file", "ocr", "stt", "processing"]),
        serialize=False
    )
    
    # OCR/STT 처리 로그
    processing_log_path = str(settings.LOG_FILE_PATH).replace(".log", "_processing.log")
    logger.add(
        processing_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | PROCESSING | {message}",
        level="INFO",
        rotation="100 MB",
        retention="30 days",
        filter=lambda record: any(keyword in record["message"].lower() 
                                for keyword in ["ocr", "stt", "tts", "whisper", "tesseract", "processing"]),
        serialize=False
    )
    
    # 벡터 검색 로그
    search_log_path = str(settings.LOG_FILE_PATH).replace(".log", "_search.log")
    logger.add(
        search_log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | SEARCH | {message}",
        level="INFO",
        rotation="50 MB",
        retention="30 days",
        filter=lambda record: any(keyword in record["message"].lower() 
                                for keyword in ["qdrant", "vector", "search", "embedding", "rag"]),
        serialize=False
    )
    
    logger.info(f"멀티모달 백엔드 로깅 설정 완료 - 레벨: {settings.LOG_LEVEL}, 환경: {settings.ENVIRONMENT}")


def get_logger(name: str = None):
    """
    로거 인스턴스 반환
    
    Args:
        name: 로거 이름
        
    Returns:
        loguru logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


def log_file_processing(file_type: str, file_name: str, processing_time: float, success: bool):
    """파일 처리 로깅"""
    status = "성공" if success else "실패"
    logger.info(
        f"파일 처리 - {file_type} '{file_name}': "
        f"상태={status}, 소요시간={processing_time:.2f}s"
    )


def log_ocr_results(file_name: str, text_length: int, confidence: float, processing_time: float):
    """OCR 결과 로깅"""
    logger.info(
        f"OCR 처리 완료 - '{file_name}': "
        f"텍스트길이={text_length}자, 신뢰도={confidence:.2%}, "
        f"소요시간={processing_time:.2f}s"
    )


def log_stt_results(file_name: str, transcript_length: int, processing_time: float):
    """STT 결과 로깅"""
    logger.info(
        f"STT 처리 완료 - '{file_name}': "
        f"변환텍스트길이={transcript_length}자, "
        f"소요시간={processing_time:.2f}s"
    )


def log_vector_search(query: str, results_count: int, search_time: float):
    """벡터 검색 로깅"""
    logger.info(
        f"벡터 검색 - 쿼리='{query[:50]}...': "
        f"결과수={results_count}, 소요시간={search_time:.3f}s"
    )


def log_cache_operation(operation: str, key: str, success: bool, cache_type: str = "memory"):
    """캐시 작업 로깅"""
    status = "성공" if success else "실패"
    logger.debug(f"캐시 작업 - {operation} '{key}': {status} ({cache_type})")


class StructuredLogger:
    """구조화된 로깅을 위한 클래스"""
    
    def __init__(self, name: str):
        self.logger = logger.bind(component=name)
    
    def log_request(self, method: str, path: str, status_code: int, duration: float):
        """API 요청 로깅"""
        self.logger.info(
            f"API 요청 - {method} {path} "
            f"상태코드={status_code} 소요시간={duration:.3f}s"
        )
    
    def log_error(self, error: Exception, context: dict = None):
        """에러 로깅"""
        error_info = f"에러 발생 - {type(error).__name__}: {str(error)}"
        if context:
            error_info += f" 컨텍스트={context}"
        self.logger.error(error_info)
    
    def log_file_upload(self, filename: str, file_size: int, content_type: str, success: bool):
        """파일 업로드 로깅"""
        status = "성공" if success else "실패"
        size_mb = file_size / (1024 * 1024)
        self.logger.info(
            f"파일 업로드 - '{filename}' ({content_type}): "
            f"크기={size_mb:.2f}MB, 상태={status}"
        )
    
    def log_multimodal_processing(self, file_type: str, operation: str, duration: float, success: bool):
        """멀티모달 처리 로깅"""
        status = "성공" if success else "실패"
        self.logger.info(
            f"멀티모달 처리 - {file_type} {operation}: "
            f"상태={status}, 소요시간={duration:.2f}s"
        )


# 컴포넌트별 로거 인스턴스
api_logger = StructuredLogger("API")
file_logger = StructuredLogger("FILES")
processing_logger = StructuredLogger("PROCESSING")
search_logger = StructuredLogger("SEARCH")
cache_logger = StructuredLogger("CACHE")
