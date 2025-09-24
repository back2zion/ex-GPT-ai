"""
Main API for ex-GPT System
FastAPI 기반 메인 API 서버
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import asyncio
import logging
from datetime import datetime

# 로컬 모듈
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_processing import IntegratedImageAnalyzer, ProcessingMode
from admin_tools.upload_handler import AdminUploadHandler, UploadType
from rag_pipeline.embeddings import EmbeddingGenerator
from rag_pipeline.vector_store import QdrantVectorStore

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="ex-GPT API",
    description="한국도로공사 AI 어시스턴트 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
image_analyzer = None
upload_handler = None
embedding_generator = None
vector_store = None


# Pydantic 모델
class MultimodalSearchRequest(BaseModel):
    query: Optional[str] = None
    image_url: Optional[str] = None
    query_type: str = "text"  # text, image, hybrid
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None


class ImageAnalysisRequest(BaseModel):
    image_url: str
    mode: str = "standard"  # fast, standard, deep
    extract_text: bool = True
    detect_objects: bool = True


class UploadResponse(BaseModel):
    file_id: str
    status: str
    message: str
    processing_time: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    processing_time: float


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    global image_analyzer, upload_handler, embedding_generator, vector_store
    
    logger.info("ex-GPT API 서버 초기화 중...")
    
    try:
        # 모듈 초기화
        image_analyzer = IntegratedImageAnalyzer()
        upload_handler = AdminUploadHandler()
        embedding_generator = EmbeddingGenerator()
        vector_store = QdrantVectorStore()
        
        # 비동기 초기화
        await upload_handler.initialize_modules()
        await vector_store.initialize()
        
        logger.info("모든 모듈 초기화 완료")
        
    except Exception as e:
        logger.error(f"초기화 실패: {str(e)}")
        raise


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "ex-GPT API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "modules": {
            "image_analyzer": image_analyzer is not None,
            "upload_handler": upload_handler is not None,
            "embedding_generator": embedding_generator is not None,
            "vector_store": vector_store is not None
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Query("admin", description="업로드 유형"),
    user_id: str = Query("default", description="사용자 ID")
):
    """
    파일 업로드 및 처리
    
    - **file**: 업로드할 파일
    - **upload_type**: admin, user, batch, ga 중 선택
    - **user_id**: 사용자 식별자
    """
    start_time = datetime.now()
    
    try:
        # 파일 저장
        result = await upload_handler.upload_file(
            file,
            UploadType[upload_type.upper()],
            user_id
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return UploadResponse(
            file_id=result.file_id,
            status=result.processing_status,
            message="파일 업로드 성공",
            processing_time=processing_time,
            metadata={
                "original_name": result.original_name,
                "file_type": result.file_type.value,
                "stored_path": result.stored_path
            }
        )
        
    except Exception as e:
        logger.error(f"업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze", response_model=Dict[str, Any])
async def analyze_image(request: ImageAnalysisRequest):
    """
    이미지 분석
    
    이미지를 분석하여 텍스트 추출, 객체 검출 등을 수행합니다.
    """
    try:
        # 처리 모드 변환
        mode_map = {
            "fast": ProcessingMode.FAST,
            "standard": ProcessingMode.STANDARD,
            "deep": ProcessingMode.DEEP
        }
        mode = mode_map.get(request.mode, ProcessingMode.STANDARD)
        
        # 이미지 분석
        result = await image_analyzer.analyze_image(
            request.image_url,
            mode
        )
        
        return {
            "status": result.status,
            "image_type": result.image_type,
            "ocr_text": result.ocr_result.get("text") if result.ocr_result else None,
            "detected_objects": result.vlm_analysis.get("detected_objects") if result.vlm_analysis else [],
            "caption": result.vlm_analysis.get("caption") if result.vlm_analysis else None,
            "processing_time": result.processing_time,
            "errors": result.errors
        }
        
    except Exception as e:
        logger.error(f"분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/multimodal-search", response_model=SearchResponse)
async def multimodal_search(request: MultimodalSearchRequest):
    """
    멀티모달 검색
    
    텍스트 또는 이미지를 사용하여 관련 문서를 검색합니다.
    """
    start_time = datetime.now()
    
    try:
        results = []
        
        if request.query_type == "text" and request.query:
            # 텍스트 검색
            query_embedding = await embedding_generator.generate(request.query)
            search_results = await vector_store.search(
                query_embedding,
                collection_type="documents",
                top_k=request.top_k,
                filter_conditions=request.filters
            )
            
            results = [
                {
                    "id": r.id,
                    "score": r.score,
                    "document": r.document,
                    "metadata": r.metadata
                }
                for r in search_results
            ]
            
        elif request.query_type == "image" and request.image_url:
            # 이미지 검색
            # 이미지 처리 및 임베딩 생성
            analysis = await image_analyzer.analyze_image(
                request.image_url,
                ProcessingMode.FAST
            )
            
            if analysis.embeddings is not None:
                search_results = await vector_store.search(
                    analysis.embeddings,
                    collection_type="images",
                    top_k=request.top_k,
                    filter_conditions=request.filters
                )
                
                results = [
                    {
                        "id": r.id,
                        "score": r.score,
                        "document": r.document,
                        "metadata": r.metadata
                    }
                    for r in search_results
                ]
                
        elif request.query_type == "hybrid":
            # 하이브리드 검색
            # 텍스트와 이미지 모두 사용
            pass
            
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.query or request.image_url or "",
            results=results,
            total_found=len(results),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/statistics")
async def get_statistics():
    """시스템 통계 조회"""
    try:
        upload_stats = await upload_handler.get_upload_statistics()
        
        # 벡터 스토어 통계
        vector_stats = {}
        for collection_type in ["documents", "images", "chunks"]:
            info = await vector_store.get_collection_info(collection_type)
            vector_stats[collection_type] = {
                "count": info.points_count,
                "status": info.status
            }
            
        return {
            "uploads": upload_stats,
            "vectors": vector_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/cleanup")
async def cleanup_old_files(days: int = Query(7, description="보관 일수")):
    """오래된 파일 정리"""
    try:
        await upload_handler.cleanup_old_files(days)
        return {"message": f"{days}일 이상된 파일 정리 완료"}
        
    except Exception as e:
        logger.error(f"정리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/document/{document_id}")
async def delete_document(
    document_id: str,
    collection_type: str = Query("documents", description="컬렉션 유형")
):
    """문서 삭제"""
    try:
        await vector_store.delete_document(document_id, collection_type)
        return {"message": f"문서 삭제 완료: {document_id}"}
        
    except Exception as e:
        logger.error(f"삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/optimize")
async def optimize_collections():
    """컬렉션 최적화"""
    try:
        for collection_type in ["documents", "images", "chunks"]:
            await vector_store.optimize_collection(collection_type)
            
        return {"message": "모든 컬렉션 최적화 완료"}
        
    except Exception as e:
        logger.error(f"최적화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backup")
async def backup_system():
    """시스템 백업"""
    try:
        backups = {}
        
        for collection_type in ["documents", "images", "chunks"]:
            snapshot_name = await vector_store.backup_collection(collection_type)
            backups[collection_type] = snapshot_name
            
        return {
            "message": "백업 완료",
            "backups": backups,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"백업 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("="*50)
    print("ex-GPT API 서버 시작")
    print("URL: http://localhost:8000")
    print("문서: http://localhost:8000/docs")
    print("="*50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
