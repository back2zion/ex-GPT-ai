"""
ex-GPT 멀티모달 백엔드 메인 애플리케이션

한국도로공사 ex-GPT 시스템의 멀티모달 기능을 제공하는 FastAPI 서버
- Whisper 기반 STT (Speech-to-Text) 처리
- 이미지 분석 및 임베딩 생성
- Qdrant 벡터 데이터베이스 연동
- H100 GPU 서버 최적화

Author: 곽두일 PM <pm@datastreams.co.kr>
Created: 2025-09-21
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from multimodal.api.endpoints.stt import router as stt_router
from multimodal.api.endpoints.image import router as image_router
from multimodal.api.endpoints.embedding import router as embedding_router
from multimodal.api.endpoints.health import router as health_router
from multimodal.api.endpoints.cctv import router as cctv_router
from multimodal.config.settings import get_settings
from multimodal.services.whisper_service import WhisperService
from multimodal.services.image_service import ImageService
from multimodal.services.embedding_service import EmbeddingService
from multimodal.services.qdrant_service import QdrantService
from multimodal.services.cctv_service import CCTVImageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    settings = get_settings()
    
    # 서비스 초기화
    app.state.whisper_service = WhisperService(settings)
    app.state.image_service = ImageService(settings)
    app.state.embedding_service = EmbeddingService(settings)
    app.state.qdrant_service = QdrantService(settings)
    app.state.cctv_service = CCTVImageService(settings)
    
    # 서비스 시작
    await app.state.whisper_service.initialize()
    await app.state.image_service.initialize()
    await app.state.embedding_service.initialize()
    await app.state.qdrant_service.initialize()
    await app.state.cctv_service.initialize()
    
    print("ex-GPT 멀티모달 백엔드 서비스가 시작되었습니다.")
    print(f"STT 서비스: {settings.STT_MODEL}")
    print(f"이미지 서비스: {settings.IMAGE_MODEL}")
    print(f"임베딩 서비스: {settings.EMBEDDING_MODEL}")
    print(f"Qdrant 연결: {settings.QDRANT_URL}")
    print(f"CCTV 이미지 검색 서비스: 활성화됨")
    
    yield
    
    # 정리 작업
    await app.state.whisper_service.cleanup()
    await app.state.image_service.cleanup()
    await app.state.embedding_service.cleanup()
    await app.state.qdrant_service.cleanup()
    # CCTV 서비스는 별도 정리 불필요
    
    print("ex-GPT 멀티모달 백엔드 서비스가 종료되었습니다.")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    settings = get_settings()
    
    app = FastAPI(
        title="ex-GPT 멀티모달 백엔드",
        description="한국도로공사 ex-GPT 시스템의 멀티모달 기능 제공",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 등록
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(stt_router, prefix="/api/v1/stt", tags=["STT"])
    app.include_router(image_router, prefix="/api/v1/image", tags=["Image"])
    app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["Embedding"])
    app.include_router(cctv_router, prefix="/api/v1/cctv", tags=["CCTV"])
    
    # 전역 예외 처리
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "서버 내부 오류가 발생했습니다.",
                "detail": str(exc) if settings.DEBUG else "자세한 정보는 관리자에게 문의하세요."
            }
        )
    
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        loop="uvloop" if not settings.DEBUG else "asyncio"
    )
