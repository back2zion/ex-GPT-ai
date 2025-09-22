"""이미지 API 엔드포인트"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from typing import List

from multimodal.services.image_service import ImageService

router = APIRouter()

def get_image_service(request: Request) -> ImageService:
    return request.app.state.image_service

@router.post("/embedding")
async def generate_image_embedding(
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service)
):
    """이미지 임베딩 생성"""
    try:
        content = await file.read()
        embedding = await image_service.generate_image_embedding(content)
        return {"embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    texts: str = "도로, 건물, 자동차, 사람",
    image_service: ImageService = Depends(get_image_service)
):
    """이미지-텍스트 유사도 분석"""
    try:
        content = await file.read()
        text_list = [t.strip() for t in texts.split(",")]
        result = await image_service.analyze_image(content, text_list)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(image_service: ImageService = Depends(get_image_service)):
    return await image_service.health_check()
