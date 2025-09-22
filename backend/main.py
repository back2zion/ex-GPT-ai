"""
ex-GPT 멀티모달 백엔드 메인 애플리케이션
한국도로공사 전용 이미지 검색 및 멀티모달 AI 서비스
"""

import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from loguru import logger

# 기존 API 라우터가 있다면 사용
try:
    from app.api.v1.router import api_router
    HAS_EXISTING_API = True
except ImportError:
    HAS_EXISTING_API = False

# 새로 추가한 서비스들
try:
    from app.services.image_search import ImageSearchService
    from app.services.multimodal_chat import MultimodalChatService
    from app.services.ollama_client import OllamaClient
    from app.models.schemas import (
        ImageSearchRequest, 
        ImageSearchResponse, 
        MultimodalChatRequest, 
        MultimodalChatResponse,
        HealthCheckResponse
    )
    from app.core.config import settings
    HAS_NEW_SERVICES = True
except ImportError as e:
    logger.error(f"새 서비스 로드 실패: {e}")
    HAS_NEW_SERVICES = False
    # 기본 설정 fallback
    class Settings:
        HOST = "0.0.0.0"
        PORT = 8001
        DEBUG = True
        IMAGE_FOLDER_PATH = r"C:\Users\user\Documents\interim_report\188.해무, 안개 CCTV 데이터"
        OLLAMA_MODEL_NAME = "qwen3:8b"
        OLLAMA_VLM_MODEL = "llava:7b"
    settings = Settings()

# 전역 서비스 인스턴스
image_search_service: Optional[ImageSearchService] = None
multimodal_chat_service: Optional[MultimodalChatService] = None
ollama_client: Optional[OllamaClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("ex-GPT 멀티모달 백엔드 시작")
    
    global image_search_service, multimodal_chat_service, ollama_client
    
    try:
        if HAS_NEW_SERVICES:
            # Ollama 클라이언트 초기화
            ollama_client = OllamaClient()
            connection_ok = await ollama_client.check_connection()
            if not connection_ok:
                logger.warning("Ollama 서버에 연결할 수 없습니다. Ollama가 설치되어 있고 실행 중인지 확인하세요.")
            
            # 이미지 검색 서비스 초기화
            if os.path.exists(settings.IMAGE_FOLDER_PATH):
                image_search_service = ImageSearchService(
                    image_folder=settings.IMAGE_FOLDER_PATH,
                    ollama_client=ollama_client
                )
                await image_search_service.initialize()
                logger.info("이미지 검색 서비스 초기화 완료")
            else:
                logger.warning(f"이미지 폴더가 존재하지 않습니다: {settings.IMAGE_FOLDER_PATH}")
            
            # 멀티모달 채팅 서비스 초기화
            multimodal_chat_service = MultimodalChatService(
                ollama_client=ollama_client
            )
            logger.info("멀티모달 채팅 서비스 초기화 완료")
        
        logger.info("모든 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        # 초기화 실패해도 서버는 시작되도록 함
    
    yield
    
    # 종료 시 정리
    logger.info("ex-GPT 멀티모달 백엔드 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="ex-GPT 멀티모달 백엔드",
    description="한국도로공사 ex-GPT 시스템의 멀티모달 AI 백엔드 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],  # 프론트엔드 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기존 API 라우터가 있으면 포함
if HAS_EXISTING_API:
    app.include_router(api_router, prefix="/api/v1")
    logger.info("기존 API 라우터 포함됨")

# 의존성 함수들
def get_image_search_service() -> ImageSearchService:
    if not HAS_NEW_SERVICES:
        raise HTTPException(status_code=503, detail="이미지 검색 서비스가 활성화되지 않았습니다")
    if image_search_service is None:
        raise HTTPException(status_code=503, detail="이미지 검색 서비스를 초기화할 수 없습니다. 이미지 폴더 경로를 확인하세요.")
    return image_search_service

def get_multimodal_chat_service() -> MultimodalChatService:
    if not HAS_NEW_SERVICES or multimodal_chat_service is None:
        raise HTTPException(status_code=503, detail="멀티모달 채팅 서비스가 사용할 수 없습니다")
    return multimodal_chat_service

def get_ollama_client() -> OllamaClient:
    if not HAS_NEW_SERVICES or ollama_client is None:
        raise HTTPException(status_code=503, detail="Ollama 클라이언트가 사용할 수 없습니다")
    return ollama_client

# API 엔드포인트들

@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
    return {
        "service": "ex-GPT 멀티모달 백엔드",
        "version": "1.0.0",
        "status": "running",
        "description": "한국도로공사 멀티모달 AI 서비스",
        "features": [
            "CCTV 이미지 검색",
            "멀티모달 채팅",
            "이미지 분석",
            "기존 API 호환"
        ]
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        status = {
            "status": "healthy",
            "timestamp": None,
            "services": {
                "main_server": "running",
                "new_services": "available" if HAS_NEW_SERVICES else "not_available",
                "existing_api": "available" if HAS_EXISTING_API else "not_available"
            }
        }

        if HAS_NEW_SERVICES and ollama_client:
            # Ollama 연결 상태 확인
            ollama_status = await ollama_client.check_connection()
            status["services"]["ollama"] = "connected" if ollama_status else "disconnected"
            status["services"]["model"] = settings.OLLAMA_MODEL_NAME

            # 이미지 폴더 접근 가능성 확인
            image_folder_accessible = Path(settings.IMAGE_FOLDER_PATH).exists()
            status["services"]["image_folder"] = "accessible" if image_folder_accessible else "inaccessible"

        return status

    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return {
            "status": "unhealthy",
            "services": {"error": str(e)}
        }

@app.get("/api/v1/health")
async def mcp_health_check():
    """MCP용 헬스체크 엔드포인트"""
    return await health_check()

# 새로운 멀티모달 API 엔드포인트들 (새 서비스가 있을 때만 활성화)
if HAS_NEW_SERVICES:
    
    @app.post("/api/v1/search/images", response_model=ImageSearchResponse)
    async def search_images(
        request: ImageSearchRequest,
        service: ImageSearchService = Depends(get_image_search_service)
    ):
        """이미지 검색 API"""
        try:
            logger.info(f"[검색 API 호출] 이미지 검색 요청: '{request.query}', limit={request.limit}, offset={request.offset}")

            results = await service.search_images(
                query=request.query,
                limit=request.limit,
                offset=request.offset,
                filters=request.filters
            )

            logger.info(f"[검색 API 응답] 검색 완료: {len(results.images)}개 이미지 발견, 전체: {results.total_count}개")

            return results

        except Exception as e:
            logger.error(f"[검색 API 오류] 이미지 검색 실패: {e}")
            raise HTTPException(status_code=500, detail=f"이미지 검색 중 오류가 발생했습니다: {str(e)}")

    @app.get("/api/v1/images/{image_path:path}")
    async def serve_image(image_path: str):
        """이미지 파일 서빙 (ZIP 파일에서 추출)"""
        try:
            logger.info(f"이미지 요청: {image_path}")

            # 먼저 이미지 검색 서비스에서 이미지 정보 찾기
            if image_search_service and hasattr(image_search_service, '_image_cache'):
                found_result = None

                # 캐시에서 해당 이미지 찾기
                for location_images in image_search_service._image_cache.values():
                    for result in location_images:
                        if result.filename == image_path or result.relative_path == image_path:
                            found_result = result
                            break
                    if found_result:
                        break

                if found_result and '#' in found_result.file_path:
                    # ZIP 파일에서 이미지 추출
                    zip_path, image_filename = found_result.file_path.split('#', 1)
                    logger.info(f"ZIP에서 이미지 추출: {zip_path} -> {image_filename}")

                    try:
                        import zipfile
                        import tempfile

                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            # 임시 파일에 이미지 추출
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                                # ZIP에서 이미지 데이터 읽기
                                image_data = zip_ref.read(image_filename)
                                temp_file.write(image_data)
                                temp_file_path = temp_file.name

                        logger.info(f"이미지 임시 파일 생성: {temp_file_path}")

                        return FileResponse(
                            path=temp_file_path,
                            media_type="image/jpeg",
                            headers={"Cache-Control": "max-age=3600"},
                            # 임시 파일은 응답 후 삭제되도록 설정
                            background=None
                        )

                    except Exception as e:
                        logger.error(f"ZIP에서 이미지 추출 실패: {e}")

            # ZIP에서 찾지 못한 경우 기존 방식으로 검색
            search_paths = [
                Path(settings.IMAGE_FOLDER_PATH) / image_path,  # 메인 이미지 폴더
                Path("temp/extracted_images") / image_path,     # 추출된 이미지 폴더
                Path(settings.IMAGE_FOLDER_PATH) / Path(image_path).name,  # 파일명만으로 검색
                Path.cwd() / "temp" / "extracted_images" / image_path,  # 절대 경로로 추출된 이미지
                Path.cwd() / "temp" / "extracted_images" / Path(image_path).name,  # 절대 경로 + 파일명만
            ]

            full_path = None
            for path in search_paths:
                abs_path = path.resolve()
                if abs_path.exists() and abs_path.is_file():
                    full_path = abs_path
                    logger.info(f"이미지 발견: {full_path}")
                    break

            if not full_path:
                logger.error(f"이미지를 찾을 수 없음: {image_path}")
                raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")

            return FileResponse(
                path=str(full_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "max-age=3600"}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"이미지 서빙 실패: {e}")
            raise HTTPException(status_code=500, detail="이미지 서빙 중 오류가 발생했습니다")

    @app.post("/api/v1/chat/multimodal")
    async def multimodal_chat(request: dict = Body(...)):
        """멀티모달 채팅 API"""
        try:
            logger.info(f"멀티모달 채팅 요청: {request}")

            if not HAS_NEW_SERVICES or multimodal_chat_service is None:
                return {
                    "success": False,
                    "response": "멀티모달 채팅 서비스가 사용할 수 없습니다.",
                    "error": "Service not available"
                }

            # 요청에서 메시지 추출
            messages = []
            for msg in request.get("messages", []):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "image_url": msg.get("image_url")
                })

            response = await multimodal_chat_service.process_chat(
                messages=messages,
                session_id=request.get("session_id"),
                user_id=request.get("user_id"),
                temperature=request.get("temperature", 0.7),
                max_tokens=request.get("max_tokens", 1000)
            )

            logger.info("멀티모달 채팅 응답 생성 완료")

            # ChatResponse를 dict로 변환하여 반환
            return {
                "success": response.success,
                "response": response.response,
                "session_id": response.session_id,
                "message_id": response.message_id,
                "sources": response.sources,
                "suggested_questions": response.suggested_questions,
                "metadata": response.metadata,
                "error": response.error
            }

        except Exception as e:
            logger.error(f"멀티모달 채팅 실패: {e}")
            return {
                "success": False,
                "response": "처리 중 오류가 발생했습니다.",
                "error": str(e)
            }

    @app.get("/api/v1/models")
    async def list_models(
        ollama_client: OllamaClient = Depends(get_ollama_client)
    ):
        """사용 가능한 모델 목록 조회"""
        try:
            models = await ollama_client.list_models()
            return {"models": models}
        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {e}")
            raise HTTPException(status_code=500, detail="모델 목록 조회 중 오류가 발생했습니다")

    @app.post("/api/v1/models/pull")
    async def pull_model(
        model_name: str = Query(..., description="다운로드할 모델명")
    ):
        """모델 다운로드"""
        try:
            ollama_client_instance = get_ollama_client()
            await ollama_client_instance.pull_model(model_name)
            return {"success": True, "message": f"모델 {model_name} 다운로드 완료"}
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            raise HTTPException(status_code=500, detail=f"모델 다운로드 중 오류가 발생했습니다: {str(e)}")

    class MCPChatRequest(BaseModel):
        history: List[Dict[str, str]]
        session_id: Optional[str] = None
        user_id: Optional[str] = None
        department_id: Optional[str] = None
        stream: bool = False
        search_documents: bool = True
        suggest_questions: bool = False
        generate_search_query: bool = True

    @app.post("/api/v1/chat")
    async def mcp_chat(request: dict = Body(...)):
        """MCP 호환 채팅 API"""
        try:
            logger.info(f"MCP 채팅 요청: {request}")

            if not HAS_NEW_SERVICES or multimodal_chat_service is None:
                return {
                    "response": "죄송합니다. 채팅 서비스가 현재 사용할 수 없습니다.",
                    "error": "Service not available"
                }

            # MCP 형식에서 멀티모달 형식으로 변환
            messages = []
            for msg in request.get("history", []):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            response = await multimodal_chat_service.process_chat(
                messages=messages,
                session_id=request.get("session_id"),
                user_id=request.get("user_id"),
                temperature=0.7,
                max_tokens=1000
            )

            # MCP 응답 형식으로 변환
            return {
                "response": response.response,
                "session_id": response.session_id,
                "message_id": response.message_id,
                "sources": getattr(response, 'sources', []),
                "suggested_questions": getattr(response, 'suggested_questions', []),
                "metadata": {
                    "model": settings.OLLAMA_MODEL_NAME if HAS_NEW_SERVICES else "none",
                    "response_time_ms": getattr(response, 'processing_time_ms', 0)
                }
            }

        except Exception as e:
            logger.error(f"MCP 채팅 실패: {e}")
            return {
                "response": "죄송합니다. 처리 중 오류가 발생했습니다.",
                "error": str(e)
            }

# 정적 파일 서빙 (이미지 제공용)
static_path = settings.IMAGE_FOLDER_PATH
if os.path.exists(static_path):
    app.mount("/static/images", StaticFiles(directory=static_path), name="images")
    logger.info(f"정적 파일 서빙 설정: {static_path}")
else:
    logger.warning(f"정적 파일 경로 없음: {static_path}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
