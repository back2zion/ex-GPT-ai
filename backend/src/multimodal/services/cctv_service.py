"""
CCTV 이미지 검색 서비스

해무/안개 CCTV 데이터를 기반으로 한 이미지 검색 및 분석 기능
"""

import asyncio
import logging
import os
import zipfile
import base64
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import io
import tempfile

import torch
import numpy as np
from PIL import Image
import httpx
from transformers import CLIPProcessor, CLIPModel

from multimodal.config.settings import Settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    async def check_model(self, model_name: str) -> bool:
        """모델 존재 여부 확인"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(model["name"].startswith(model_name) for model in models)
                return False
        except Exception as e:
            logger.error(f"Ollama 모델 확인 실패: {e}")
            return False
    
    async def pull_model(self, model_name: str) -> bool:
        """모델 다운로드"""
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"모델 다운로드 실패: {e}")
            return False
    
    async def generate_vision(self, model_name: str, prompt: str, image_base64: str) -> str:
        """비전 모델로 이미지 분석"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "분석 결과를 가져올 수 없습니다")
                else:
                    return f"API 오류: {response.status_code}"
        except Exception as e:
            logger.error(f"Ollama 비전 분석 실패: {e}")
            return f"분석 중 오류 발생: {str(e)}"


class CCTVImageService:
    """CCTV 이미지 검색 및 분석 서비스"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = "cpu"  # CPU 전용 설정
        self.model = None
        self.processor = None
        self.ollama_client = OllamaClient()
        self.vision_model = "llava:7b"  # CPU에서 실행 가능한 모델
        
        # CCTV 데이터 경로
        self.cctv_data_path = Path("C:/Users/user/Documents/interim_report/188.해무, 안개 CCTV 데이터/01.데이터")
        self.image_index = {}
        
    async def initialize(self) -> None:
        """서비스 초기화"""
        try:
            logger.info("CCTV 이미지 서비스 초기화 시작")
            
            # CLIP 모델 로드 (CPU 최적화된 가벼운 모델)
            model_name = "openai/clip-vit-base-patch32"
            logger.info(f"CLIP 모델 로딩: {model_name}")
            
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Ollama 비전 모델 확인 및 설치
            await self._setup_ollama_model()
            
            # 이미지 인덱스 구축
            await self._build_image_index()
            
            logger.info("CCTV 이미지 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"CCTV 이미지 서비스 초기화 실패: {e}")
            raise
    
    async def _setup_ollama_model(self):
        """Ollama 비전 모델 설정"""
        try:
            # 모델 존재 확인
            if not await self.ollama_client.check_model(self.vision_model):
                logger.info(f"Ollama 모델 {self.vision_model} 다운로드 중...")
                success = await self.ollama_client.pull_model(self.vision_model)
                if not success:
                    logger.warning("Ollama 모델 다운로드 실패, 기본 CLIP만 사용")
                    self.vision_model = None
            else:
                logger.info(f"Ollama 모델 {self.vision_model} 준비됨")
        except Exception as e:
            logger.warning(f"Ollama 설정 실패: {e}, CLIP만 사용")
            self.vision_model = None
    
    async def _build_image_index(self):
        """이미지 인덱스 구축"""
        try:
            logger.info("CCTV 이미지 인덱스 구축 시작")
            
            # Training 데이터
            training_path = self.cctv_data_path / "1.Training" / "원천데이터"
            validation_path = self.cctv_data_path / "2.Validation"
            
            # ZIP 파일 스캔
            all_zip_files = []
            if training_path.exists():
                all_zip_files.extend(list(training_path.glob("*.zip")))
            if validation_path.exists():
                all_zip_files.extend(list(validation_path.glob("*.zip")))
            
            logger.info(f"발견된 ZIP 파일: {len(all_zip_files)}개")
            
            # 각 ZIP 파일 처리 (성능을 위해 처음 5개만)
            for zip_path in all_zip_files[:5]:
                location_name = zip_path.stem.replace("TS.", "")
                logger.info(f"인덱싱 중: {location_name}")
                
                try:
                    image_files = await self._scan_zip_images(zip_path)
                    self.image_index[location_name] = {
                        "zip_path": str(zip_path),
                        "image_count": len(image_files),
                        "sample_images": image_files[:20]  # 샘플 이미지만 저장
                    }
                    logger.info(f"{location_name}: {len(image_files)}개 이미지")
                except Exception as e:
                    logger.error(f"ZIP 파일 처리 실패 {zip_path}: {e}")
            
            logger.info(f"이미지 인덱스 구축 완료: {len(self.image_index)}개 위치")
            
        except Exception as e:
            logger.error(f"이미지 인덱스 구축 실패: {e}")
    
    async def _scan_zip_images(self, zip_path: Path) -> List[str]:
        """ZIP 파일 내 이미지 파일 스캔"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                image_files = [
                    filename for filename in zip_ref.namelist()
                    if Path(filename).suffix.lower() in image_extensions
                ]
                return image_files
        except Exception as e:
            logger.error(f"ZIP 스캔 실패 {zip_path}: {e}")
            return []
    
    async def search_images(self, query: str, location: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """이미지 검색"""
        try:
            logger.info(f"이미지 검색 시작: '{query}', 위치: {location}")
            
            # 검색 대상 위치 결정
            search_locations = [location] if location and location in self.image_index else list(self.image_index.keys())
            
            results = []
            
            # 텍스트 임베딩 생성
            text_inputs = self.processor(text=[query], return_tensors="pt", padding=True)
            text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}
            
            with torch.no_grad():
                text_features = self.model.get_text_features(**text_inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # 각 위치별 이미지 검색
            for loc in search_locations:
                if loc not in self.image_index:
                    continue
                
                zip_path = Path(self.image_index[loc]["zip_path"])
                sample_images = self.image_index[loc]["sample_images"]
                
                # 샘플 이미지들과 유사도 계산
                for img_file in sample_images[:min(10, len(sample_images))]:  # 성능 고려
                    try:
                        # 이미지 로드
                        image_data = await self._load_image_from_zip(zip_path, img_file)
                        if not image_data:
                            continue
                        
                        # 유사도 계산
                        similarity = await self._calculate_similarity(image_data, text_features)
                        
                        # 결과 추가
                        results.append({
                            "location": loc,
                            "filename": img_file,
                            "similarity": float(similarity),
                            "image_data": base64.b64encode(image_data).decode(),
                            "zip_path": str(zip_path)
                        })
                        
                    except Exception as e:
                        logger.warning(f"이미지 처리 실패 {img_file}: {e}")
                        continue
            
            # 유사도 순으로 정렬 후 상위 결과 반환
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"이미지 검색 실패: {e}")
            return []
    
    async def _load_image_from_zip(self, zip_path: Path, image_filename: str) -> Optional[bytes]:
        """ZIP 파일에서 이미지 로드"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                with zip_ref.open(image_filename) as img_file:
                    return img_file.read()
        except Exception as e:
            logger.warning(f"이미지 로드 실패 {image_filename}: {e}")
            return None
    
    async def _calculate_similarity(self, image_data: bytes, text_features: torch.Tensor) -> float:
        """이미지-텍스트 유사도 계산"""
        try:
            # 이미지 전처리
            image = Image.open(io.BytesIO(image_data))
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # 크기 조정 (성능 최적화)
            image.thumbnail((224, 224), Image.Resampling.LANCZOS)
            
            # 이미지 임베딩 생성
            image_inputs = self.processor(images=image, return_tensors="pt")
            image_inputs = {k: v.to(self.device) for k, v in image_inputs.items()}
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # 코사인 유사도 계산
                similarity = torch.cosine_similarity(text_features, image_features)
                return similarity.item()
        
        except Exception as e:
            logger.warning(f"유사도 계산 실패: {e}")
            return 0.0
    
    async def analyze_with_ollama(self, image_data: bytes, query: str) -> str:
        """Ollama를 이용한 상세 이미지 분석"""
        try:
            if not self.vision_model:
                return "Ollama 비전 모델을 사용할 수 없습니다."
            
            # 이미지를 base64로 인코딩
            image_b64 = base64.b64encode(image_data).decode()
            
            # 분석용 프롬프트
            prompt = f"""
이 CCTV 이미지를 자세히 분석해주세요.

질문: {query}

다음 항목들을 확인하여 한국어로 답변해주세요:
1. 날씨 상태 (맑음, 흐림, 비, 눈, 안개, 해무 등)
2. 가시거리 (좋음, 보통, 나쁨)
3. 도로 상황
4. 교통량
5. 시간대 (주간/야간)
6. 특이사항

구체적이고 정확하게 설명해주세요.
"""
            
            return await self.ollama_client.generate_vision(self.vision_model, prompt, image_b64)
            
        except Exception as e:
            logger.error(f"Ollama 이미지 분석 실패: {e}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """사용 가능한 위치 목록 반환"""
        return [
            {
                "name": location,
                "image_count": data["image_count"],
                "zip_path": data["zip_path"]
            }
            for location, data in self.image_index.items()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "status": "healthy" if self.model is not None else "unhealthy",
            "device": self.device,
            "locations_indexed": len(self.image_index),
            "total_sample_images": sum(len(data["sample_images"]) for data in self.image_index.values()),
            "ollama_model": self.vision_model,
            "clip_model": "openai/clip-vit-base-patch32"
        }
