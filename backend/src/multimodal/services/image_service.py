"""
이미지 처리 서비스

CLIP 기반 이미지 임베딩 및 분석 기능 제공
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import torch
import numpy as np
from PIL import Image
import io

from transformers import CLIPProcessor, CLIPModel

from multimodal.config.settings import Settings

logger = logging.getLogger(__name__)


class ImageService:
    """이미지 처리 서비스"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.processor = None
        self.device = "cuda" if settings.USE_GPU and torch.cuda.is_available() else "cpu"
        
    async def initialize(self) -> None:
        """서비스 초기화"""
        try:
            logger.info(f"이미지 모델 로딩 중: {self.settings.IMAGE_MODEL}")
            
            self.processor = CLIPProcessor.from_pretrained(self.settings.IMAGE_MODEL)
            self.model = CLIPModel.from_pretrained(self.settings.IMAGE_MODEL)
            self.model.to(self.device)
            
            logger.info("이미지 모델 로딩 완료")
            
        except Exception as e:
            logger.error(f"이미지 모델 초기화 실패: {e}")
            raise
    
    async def cleanup(self) -> None:
        """정리 작업"""
        if self.model is not None:
            del self.model
            del self.processor
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        logger.info("이미지 서비스 정리 완료")
    
    async def generate_image_embedding(self, image_bytes: bytes) -> List[float]:
        """이미지 임베딩 생성"""
        try:
            # 이미지 로드 및 전처리
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # CLIP 처리
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # 정규화
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
            
        except Exception as e:
            logger.error(f"이미지 임베딩 생성 실패: {e}")
            raise
    
    async def analyze_image(self, image_bytes: bytes, texts: List[str]) -> Dict[str, Any]:
        """이미지-텍스트 유사도 분석"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            inputs = self.processor(
                text=texts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            results = []
            for i, text in enumerate(texts):
                results.append({
                    "text": text,
                    "similarity": float(probs[0][i]),
                    "confidence": float(probs[0][i])
                })
            
            return {
                "results": results,
                "best_match": max(results, key=lambda x: x["similarity"])
            }
            
        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "status": "healthy" if self.model is not None else "unhealthy",
            "model": self.settings.IMAGE_MODEL,
            "device": self.device,
            "cuda_available": torch.cuda.is_available()
        }
