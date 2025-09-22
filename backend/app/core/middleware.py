"""
ex-GPT 멀티모달 백엔드 미들웨어
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from loguru import logger
import psutil

from app.core.config import get_settings
from app.core.logging import api_logger, file_logger, processing_logger

settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 클라이언트 정보
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 요청 로깅
        logger.info(
            f"요청 시작 - {request.method} {request.url.path} "
            f"클라이언트={client_ip} ID={request_id}"
        )
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간 계산
        process_time = time.time() - start_time
        
        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # 응답 로깅
        api_logger.log_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration=process_time
        )
        
        return response


class FileUploadMiddleware(BaseHTTPMiddleware):
    """파일 업로드 모니터링 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 파일 업로드 요청인지 확인
        if "/files/upload" in str(request.url.path) and request.method == "POST":
            start_time = time.time()
            
            # Content-Length 헤더에서 파일 크기 확인
            content_length = request.headers.get("content-length")
            if content_length:
                file_size_mb = int(content_length) / (1024 * 1024)
                
                # 큰 파일 업로드 로깅
                if file_size_mb > 50:
                    logger.info(f"대용량 파일 업로드 시작: {file_size_mb:.1f}MB")
            
            response = await call_next(request)
            
            # 업로드 완료 시간 로깅
            process_time = time.time() - start_time
            if content_length:
                upload_speed = int(content_length) / process_time / 1024 / 1024  # MB/s
                file_logger.logger.info(
                    f"파일 업로드 완료 - 크기: {file_size_mb:.1f}MB, "
                    f"시간: {process_time:.2f}s, 속도: {upload_speed:.1f}MB/s"
                )
            
            return response
        else:
            return await call_next(request)


class ProcessingQueueMiddleware(BaseHTTPMiddleware):
    """처리 큐 모니터링 미들웨어"""
    
    def __init__(self, app, max_concurrent_tasks: int = None):
        super().__init__(app)
        self.max_concurrent_tasks = max_concurrent_tasks or settings.MAX_CONCURRENT_TASKS
        self.active_tasks = {
            "ocr": 0,
            "stt": 0,
            "vector_index": 0,
            "image_analysis": 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 처리 작업 요청인지 확인
        task_type = None
        if "/ocr" in str(request.url.path):
            task_type = "ocr"
        elif "/stt" in str(request.url.path):
            task_type = "stt"
        elif "/search" in str(request.url.path):
            task_type = "vector_index"
        elif "/analyze" in str(request.url.path):
            task_type = "image_analysis"
        
        if task_type:
            # 동시 작업 수 확인
            total_active = sum(self.active_tasks.values())
            if total_active >= self.max_concurrent_tasks:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=503,
                    detail=f"처리 서버가 과부하 상태입니다. 잠시 후 다시 시도해주세요."
                )
            
            self.active_tasks[task_type] += 1
            processing_logger.logger.info(
                f"처리 작업 시작 - {task_type}, 활성 작업: {self.active_tasks}"
            )
            
            try:
                response = await call_next(request)
                return response
            finally:
                self.active_tasks[task_type] -= 1
                processing_logger.logger.info(
                    f"처리 작업 완료 - {task_type}, 활성 작업: {self.active_tasks}"
                )
        else:
            return await call_next(request)


class CacheMiddleware(BaseHTTPMiddleware):
    """캐시 모니터링 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 캐시 가능한 요청인지 확인 (GET 요청)
        if request.method == "GET" and "/api/" in str(request.url.path):
            # 캐시 히트/미스 정보를 응답에 추가
            response = await call_next(request)
            
            # 캐시 상태 정보 추가 (실제 구현은 각 API에서 수행)
            response.headers["X-Cache-Status"] = "DYNAMIC"  # 기본값
            
            return response
        else:
            return await call_next(request)


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 처리
        response = await call_next(request)
        
        # 보안 헤더 설정
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 파일 다운로드 보안 헤더
        if "/files/download/" in str(request.url.path):
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["X-Download-Options"] = "noopen"
        
        # CORS 헤더 (개발 환경에서만)
        if settings.ENVIRONMENT == "development":
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """성능 모니터링 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 시스템 리소스 체크 (시작 시점)
        cpu_before = psutil.cpu_percent()
        memory_before = psutil.virtual_memory().percent
        
        start_time = time.time()
        
        # 요청 처리
        response = await call_next(request)
        
        # 처리 시간 및 리소스 사용량 계산
        process_time = time.time() - start_time
        cpu_after = psutil.cpu_percent()
        memory_after = psutil.virtual_memory().percent
        
        # 성능 정보를 응답 헤더에 추가
        response.headers["X-CPU-Usage"] = f"{cpu_after:.1f}%"
        response.headers["X-Memory-Usage"] = f"{memory_after:.1f}%"
        
        # 느린 요청 감지 (10초 이상 - 파일 처리 고려)
        if process_time > 10.0:
            logger.warning(
                f"느린 요청 감지 - {request.method} {request.url.path} "
                f"처리시간: {process_time:.2f}s"
            )
        
        # 높은 리소스 사용량 감지
        if cpu_after > 80:
            logger.warning(f"높은 CPU 사용률: {cpu_after:.1f}%")
        
        if memory_after > 85:
            logger.warning(f"높은 메모리 사용률: {memory_after:.1f}%")
        
        return response


class FileSizeValidationMiddleware(BaseHTTPMiddleware):
    """파일 크기 검증 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 파일 업로드 요청인지 확인
        if request.method == "POST" and (
            "/files/upload" in str(request.url.path) or 
            "/ocr" in str(request.url.path) or 
            "/stt" in str(request.url.path)
        ):
            content_length = request.headers.get("content-length")
            if content_length:
                file_size = int(content_length)
                
                # 최대 파일 크기 확인
                if file_size > settings.MAX_FILE_SIZE:
                    from fastapi import HTTPException
                    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                    current_size_mb = file_size / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"파일 크기가 너무 큽니다. 최대 크기: {max_size_mb:.1f}MB, "
                               f"현재 크기: {current_size_mb:.1f}MB"
                    )
        
        return await call_next(request)


def setup_middleware(app):
    """미들웨어 설정"""
    # 요청 로깅 미들웨어
    app.add_middleware(RequestLoggingMiddleware)
    
    # 파일 크기 검증 미들웨어
    app.add_middleware(FileSizeValidationMiddleware)
    
    # 파일 업로드 모니터링 미들웨어
    app.add_middleware(FileUploadMiddleware)
    
    # 처리 큐 모니터링 미들웨어
    app.add_middleware(ProcessingQueueMiddleware)
    
    # 캐시 미들웨어
    app.add_middleware(CacheMiddleware)
    
    # 성능 모니터링 미들웨어
    app.add_middleware(PerformanceMiddleware)
    
    # 보안 미들웨어
    app.add_middleware(SecurityMiddleware)
    
    logger.info("멀티모달 백엔드 미들웨어 설정 완료")
