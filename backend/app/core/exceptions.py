"""
ex-GPT 멀티모달 백엔드 예외 처리
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import traceback
import os

from app.core.config import get_settings

settings = get_settings()


class MultimodalBackendException(Exception):
    """멀티모달 백엔드 기본 예외"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileProcessingException(MultimodalBackendException):
    """파일 처리 예외"""
    def __init__(self, file_name: str, reason: str, processing_type: str = None):
        message = f"파일 처리 실패 '{file_name}': {reason}"
        if processing_type:
            message = f"{processing_type} 처리 실패 '{file_name}': {reason}"
        super().__init__(message, "FILE_PROCESSING_ERROR")
        self.file_name = file_name
        self.reason = reason
        self.processing_type = processing_type


class FileUploadException(MultimodalBackendException):
    """파일 업로드 예외"""
    def __init__(self, reason: str, file_name: str = None):
        message = f"파일 업로드 실패: {reason}"
        if file_name:
            message += f" (파일: {file_name})"
        super().__init__(message, "FILE_UPLOAD_ERROR")
        self.reason = reason
        self.file_name = file_name


class FileNotFoundError(MultimodalBackendException):
    """파일을 찾을 수 없음 예외"""
    def __init__(self, file_id: str, file_path: str = None):
        message = f"파일을 찾을 수 없습니다: {file_id}"
        if file_path:
            message += f" (경로: {file_path})"
        super().__init__(message, "FILE_NOT_FOUND")
        self.file_id = file_id
        self.file_path = file_path


class UnsupportedFileTypeException(MultimodalBackendException):
    """지원하지 않는 파일 형식 예외"""
    def __init__(self, file_extension: str, supported_types: list = None):
        message = f"지원하지 않는 파일 형식: {file_extension}"
        if supported_types:
            message += f" (지원 형식: {', '.join(supported_types)})"
        super().__init__(message, "UNSUPPORTED_FILE_TYPE")
        self.file_extension = file_extension
        self.supported_types = supported_types


class FileSizeException(MultimodalBackendException):
    """파일 크기 예외"""
    def __init__(self, current_size: int, max_size: int, file_name: str = None):
        current_mb = current_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        message = f"파일 크기 초과: {current_mb:.1f}MB (최대: {max_mb:.1f}MB)"
        if file_name:
            message += f" - {file_name}"
        super().__init__(message, "FILE_SIZE_EXCEEDED")
        self.current_size = current_size
        self.max_size = max_size
        self.file_name = file_name


class OCRException(MultimodalBackendException):
    """OCR 처리 예외"""
    def __init__(self, reason: str, engine: str = None, file_name: str = None):
        message = f"OCR 처리 실패: {reason}"
        if engine:
            message += f" (엔진: {engine})"
        if file_name:
            message += f" (파일: {file_name})"
        super().__init__(message, "OCR_ERROR")
        self.reason = reason
        self.engine = engine
        self.file_name = file_name


class STTException(MultimodalBackendException):
    """STT 처리 예외"""
    def __init__(self, reason: str, model: str = None, file_name: str = None):
        message = f"STT 처리 실패: {reason}"
        if model:
            message += f" (모델: {model})"
        if file_name:
            message += f" (파일: {file_name})"
        super().__init__(message, "STT_ERROR")
        self.reason = reason
        self.model = model
        self.file_name = file_name


class VectorSearchException(MultimodalBackendException):
    """벡터 검색 예외"""
    def __init__(self, reason: str, collection: str = None, query: str = None):
        message = f"벡터 검색 실패: {reason}"
        if collection:
            message += f" (컬렉션: {collection})"
        super().__init__(message, "VECTOR_SEARCH_ERROR")
        self.reason = reason
        self.collection = collection
        self.query = query


class QdrantException(MultimodalBackendException):
    """Qdrant 연결/작업 예외"""
    def __init__(self, operation: str, reason: str):
        message = f"Qdrant {operation} 실패: {reason}"
        super().__init__(message, "QDRANT_ERROR")
        self.operation = operation
        self.reason = reason


class ProcessingQueueException(MultimodalBackendException):
    """처리 큐 예외"""
    def __init__(self, reason: str, job_type: str = None):
        message = f"처리 큐 오류: {reason}"
        if job_type:
            message += f" (작업 유형: {job_type})"
        super().__init__(message, "PROCESSING_QUEUE_ERROR")
        self.reason = reason
        self.job_type = job_type


class CacheException(MultimodalBackendException):
    """캐시 예외"""
    def __init__(self, operation: str, reason: str):
        message = f"캐시 {operation} 실패: {reason}"
        super().__init__(message, "CACHE_ERROR")
        self.operation = operation
        self.reason = reason


async def multimodal_backend_exception_handler(request: Request, exc: MultimodalBackendException):
    """멀티모달 백엔드 예외 핸들러"""
    logger.error(f"멀티모달 백엔드 예외: {exc.message} (코드: {exc.error_code})")
    
    # 에러 코드별 HTTP 상태 코드 매핑
    status_code_map = {
        "FILE_PROCESSING_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "FILE_UPLOAD_ERROR": status.HTTP_400_BAD_REQUEST,
        "FILE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "UNSUPPORTED_FILE_TYPE": status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "FILE_SIZE_EXCEEDED": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "OCR_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "STT_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "VECTOR_SEARCH_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "QDRANT_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "PROCESSING_QUEUE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "CACHE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "code": exc.error_code,
                "message": exc.message,
                "timestamp": logger._get_now().isoformat(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.warning(f"HTTP 예외: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "timestamp": logger._get_now().isoformat(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 예외 핸들러"""
    logger.warning(f"요청 검증 실패: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "code": "VALIDATION_ERROR",
                "message": "요청 데이터가 올바르지 않습니다.",
                "details": exc.errors(),
                "timestamp": logger._get_now().isoformat(),
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    error_id = getattr(request.state, "request_id", "unknown")
    
    # 스택 트레이스 로깅
    stack_trace = traceback.format_exc()
    logger.error(f"예상하지 못한 오류 (ID: {error_id}): {str(exc)}\n{stack_trace}")
    
    # 프로덕션 환경에서는 상세 오류 정보 숨김
    if settings.ENVIRONMENT == "production":
        error_message = "내부 서버 오류가 발생했습니다."
        error_details = None
    else:
        error_message = str(exc)
        error_details = {
            "type": exc.__class__.__name__,
            "stack_trace": stack_trace.split("\n") if settings.DEBUG else None
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "code": "INTERNAL_SERVER_ERROR",
                "message": error_message,
                "details": error_details,
                "timestamp": logger._get_now().isoformat(),
                "request_id": error_id
            }
        }
    )


def setup_exception_handlers(app):
    """예외 핸들러 설정"""
    app.add_exception_handler(MultimodalBackendException, multimodal_backend_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("멀티모달 백엔드 예외 핸들러 설정 완료")


# 파일 처리 관련 데코레이터
def handle_file_errors(func):
    """파일 처리 오류를 처리하는 데코레이터"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileNotFoundError(str(e))
        except PermissionError as e:
            raise FileProcessingException("unknown", f"파일 접근 권한 없음: {str(e)}")
        except OSError as e:
            raise FileProcessingException("unknown", f"파일 시스템 오류: {str(e)}")
        except Exception as e:
            raise FileProcessingException("unknown", str(e))
    
    return wrapper


def validate_file_type(allowed_extensions: list):
    """파일 형식 검증 데코레이터"""
    def decorator(func):
        async def wrapper(file, *args, **kwargs):
            if hasattr(file, 'filename') and file.filename:
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in allowed_extensions:
                    raise UnsupportedFileTypeException(file_ext, allowed_extensions)
            return await func(file, *args, **kwargs)
        return wrapper
    return decorator


def validate_file_size(max_size: int):
    """파일 크기 검증 데코레이터"""
    def decorator(func):
        async def wrapper(file, *args, **kwargs):
            if hasattr(file, 'size') and file.size:
                if file.size > max_size:
                    raise FileSizeException(file.size, max_size, getattr(file, 'filename', None))
            return await func(file, *args, **kwargs)
        return wrapper
    return decorator


# OCR/STT 처리 관련 유틸리티
def handle_processing_errors(processing_type: str):
    """처리 작업 오류를 처리하는 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if "memory" in error_msg or "out of memory" in error_msg:
                    raise FileProcessingException(
                        "unknown", 
                        f"메모리 부족: {str(e)}", 
                        processing_type
                    )
                elif "timeout" in error_msg:
                    raise FileProcessingException(
                        "unknown", 
                        f"처리 시간 초과: {str(e)}", 
                        processing_type
                    )
                else:
                    raise FileProcessingException("unknown", str(e), processing_type)
        
        return wrapper
    return decorator
