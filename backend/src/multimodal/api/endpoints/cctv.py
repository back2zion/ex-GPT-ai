"""CCTV 이미지 검색 API 엔드포인트"""

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File, Depends
from typing import List, Optional, Dict, Any
import logging

from multimodal.services.cctv_service import CCTVImageService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_cctv_service(request: Request) -> CCTVImageService:
    """CCTV 서비스 인스턴스 가져오기"""
    return request.app.state.cctv_service


@router.get("/locations")
async def get_cctv_locations(
    cctv_service: CCTVImageService = Depends(get_cctv_service)
) -> Dict[str, Any]:
    """사용 가능한 CCTV 위치 목록 조회"""
    try:
        locations = await cctv_service.get_locations()
        return {
            "success": True,
            "locations": locations,
            "total_count": len(locations)
        }
    except Exception as e:
        logger.error(f"위치 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_cctv_images(
    query: str = Query(..., description="검색 쿼리"),
    location: Optional[str] = Query(None, description="특정 위치로 제한"),
    limit: int = Query(10, description="최대 결과 수", ge=1, le=50),
    cctv_service: CCTVImageService = Depends(get_cctv_service)
) -> Dict[str, Any]:
    """CCTV 이미지 검색"""
    try:
        # 이미지 검색 실행
        results = await cctv_service.search_images(query, location, limit)
        
        # 응답 데이터 구성
        response_data = {
            "success": True,
            "query": query,
            "location": location,
            "total_results": len(results),
            "results": []
        }
        
        # 결과 데이터 변환
        for result in results:
            response_data["results"].append({
                "location": result["location"],
                "filename": result["filename"],
                "similarity": result["similarity"],
                "image_url": f"/api/v1/cctv/image/{result['location']}/{result['filename']}",
                "thumbnail": result["image_data"][:1000] + "..." if len(result["image_data"]) > 1000 else result["image_data"]  # 썸네일용 축약
            })
        
        return response_data
        
    except Exception as e:
        logger.error(f"CCTV 이미지 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.get("/image/{location}/{filename}")
async def get_cctv_image(
    location: str,
    filename: str,
    cctv_service: CCTVImageService = Depends(get_cctv_service)
) -> Dict[str, Any]:
    """특정 CCTV 이미지 조회"""
    try:
        # 이미지 로드
        if location not in cctv_service.image_index:
            raise HTTPException(status_code=404, detail="위치를 찾을 수 없습니다")
        
        from pathlib import Path
        zip_path = Path(cctv_service.image_index[location]["zip_path"])
        image_data = await cctv_service._load_image_from_zip(zip_path, filename)
        
        if not image_data:
            raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
        
        import base64
        return {
            "success": True,
            "location": location,
            "filename": filename,
            "image_data": base64.b64encode(image_data).decode(),
            "size": len(image_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_cctv_image(
    query: str = Query(..., description="분석 질문"),
    file: UploadFile = File(..., description="분석할 이미지 파일"),
    use_ollama: bool = Query(False, description="Ollama 상세 분석 사용 여부"),
    cctv_service: CCTVImageService = Depends(get_cctv_service)
) -> Dict[str, Any]:
    """업로드된 이미지 분석"""
    try:
        # 파일 검증
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다")
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        
        # 기본 CLIP 분석
        text_inputs = cctv_service.processor(text=[query], return_tensors="pt", padding=True)
        text_inputs = {k: v.to(cctv_service.device) for k, v in text_inputs.items()}
        
        import torch
        with torch.no_grad():
            text_features = cctv_service.model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        similarity = await cctv_service._calculate_similarity(image_data, text_features)
        
        response = {
            "success": True,
            "query": query,
            "filename": file.filename,
            "clip_similarity": similarity,
            "clip_analysis": f"이미지와 '{query}'의 유사도: {similarity:.3f}"
        }
        
        # Ollama 상세 분석 (옵션)
        if use_ollama:
            ollama_result = await cctv_service.analyze_with_ollama(image_data, query)
            response["ollama_analysis"] = ollama_result
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check_cctv(
    cctv_service: CCTVImageService = Depends(get_cctv_service)
) -> Dict[str, Any]:
    """CCTV 서비스 상태 확인"""
    try:
        health_status = await cctv_service.health_check()
        return {
            "success": True,
            "service": "CCTV Image Search",
            **health_status
        }
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return {
            "success": False,
            "service": "CCTV Image Search",
            "status": "unhealthy",
            "error": str(e)
        }
