"""Qdrant 벡터 데이터베이스 서비스"""

import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from multimodal.config.settings import Settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        
    async def initialize(self) -> None:
        logger.info(f"Qdrant 연결: {self.settings.QDRANT_URL}")
        self.client = QdrantClient(url=self.settings.QDRANT_URL)
        
        # 컬렉션 생성
        try:
            self.client.create_collection(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except Exception:
            pass  # 이미 존재하는 경우
            
    async def cleanup(self) -> None:
        logger.info("Qdrant 서비스 정리 완료")
        
    async def insert_vectors(self, vectors: List[List[float]], metadata: List[Dict]) -> bool:
        try:
            points = []
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                points.append({
                    "id": i,
                    "vector": vector,
                    "payload": meta
                })
            
            self.client.upsert(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"벡터 삽입 실패: {e}")
            return False
            
    async def search_similar(self, vector: List[float], limit: int = 10) -> List[Dict]:
        try:
            results = self.client.search(
                collection_name=self.settings.QDRANT_COLLECTION_NAME,
                query_vector=vector,
                limit=limit
            )
            return [{"score": hit.score, "payload": hit.payload} for hit in results]
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return []
            
    async def health_check(self) -> Dict[str, Any]:
        try:
            collections = self.client.get_collections()
            return {"status": "healthy", "collections": len(collections.collections)}
        except:
            return {"status": "unhealthy"}
