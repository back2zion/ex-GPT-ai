"""임베딩 API 엔드포인트"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List

from multimodal.services.embedding_service import EmbeddingService

router = APIRouter()

class EmbeddingRequest(BaseModel):
    texts: List[str]

def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service

@router.post("/encode")
async def encode_texts(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """텍스트 임베딩 생성"""
    try:
        embeddings = await embedding_service.encode_text(request.texts)
        return {"embeddings": embeddings, "count": len(embeddings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(embedding_service: EmbeddingService = Depends(get_embedding_service)):
    return await embedding_service.health_check()
