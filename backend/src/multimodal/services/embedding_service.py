"""임베딩 서비스"""

import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from multimodal.config.settings import Settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        
    async def initialize(self) -> None:
        logger.info(f"임베딩 모델 로딩: {self.settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(self.settings.EMBEDDING_MODEL)
        
    async def cleanup(self) -> None:
        logger.info("임베딩 서비스 정리 완료")
        
    async def encode_text(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
        
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy" if self.model else "unhealthy"}
