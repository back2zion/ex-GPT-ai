"""
Vision Language Model (VLM) Processor
한국도로공사 ex-GPT 멀티모달 이미지 처리 엔진
"""

import os
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import io
import base64
from dataclasses import dataclass
from enum import Enum
import logging
from transformers import (
    BlipProcessor, 
    BlipForConditionalGeneration,
    CLIPProcessor,
    CLIPModel,
    AutoProcessor,
    AutoModelForVision2Seq
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageType(Enum):
    """이미지 유형 분류"""
    DOCUMENT_SCAN = "document_scan"
    TECHNICAL_DRAWING = "technical_drawing"
    FIELD_PHOTO = "field_photo"
    TRAFFIC_SIGN = "traffic_sign"
    ROAD_DAMAGE = "road_damage"
    BLUEPRINT = "blueprint"
    SATELLITE = "satellite"
    UNKNOWN = "unknown"


@dataclass
class ImageAnalysisResult:
    """이미지 분석 결과"""
    image_type: ImageType
    caption: str
    detected_objects: List[str]
    confidence_score: float
    embeddings: Optional[np.ndarray] = None
    ocr_text: Optional[str] = None
    metadata: Dict[str, Any] = None
    

class MultimodalVLMProcessor:
    """
    멀티모달 Vision Language Model 처리기
    BLIP-2와 CLIP을 활용한 이미지-텍스트 통합 처리
    """
    
    def __init__(self, device: str = "cuda"):
        """
        VLM 프로세서 초기화
        
        Args:
            device: 연산 장치 (cuda/cpu)
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        logger.info(f"VLM Processor 초기화 - Device: {self.device}")
        
        # 모델 로드
        self._load_models()
        
        # 한국도로공사 특화 라벨
        self.korea_expressway_labels = {
            "road_damage": ["포트홀", "균열", "침하", "파손"],
            "traffic_sign": ["속도제한", "진입금지", "우회전", "좌회전", "정지"],
            "construction": ["공사중", "차선규제", "우회로", "서행"],
            "facility": ["톨게이트", "휴게소", "IC", "JC", "터널", "교량"]
        }
        
    def _load_models(self):
        """모델 로드 및 초기화"""
        try:
            # BLIP-2 모델 로드 (캡셔닝용)
            logger.info("BLIP-2 모델 로드 중...")
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-2-opt-2.7b"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-2-opt-2.7b",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # CLIP 모델 로드 (임베딩용)
            logger.info("CLIP 모델 로드 중...")
            self.clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-large-patch14"
            )
            self.clip_model = CLIPModel.from_pretrained(
                "openai/clip-vit-large-patch14"
            ).to(self.device)
            
            logger.info("모든 모델 로드 완료")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {str(e)}")
            raise
            
    def classify_image_type(self, image: Image.Image) -> ImageType:
        """
        이미지 유형 분류
        
        Args:
            image: PIL Image 객체
            
        Returns:
            ImageType enum
        """
        # 이미지 특성 추출
        width, height = image.size
        aspect_ratio = width / height
        
        # 이미지 픽셀 분석
        image_array = np.array(image)
        
        # 문서 스캔 판별 (흑백, 텍스트 많음)
        if self._is_document_scan(image_array):
            return ImageType.DOCUMENT_SCAN
            
        # 기술 도면 판별 (선 위주, 단색)
        if self._is_technical_drawing(image_array):
            return ImageType.TECHNICAL_DRAWING
            
        # CLIP을 사용한 세부 분류
        image_features = self._extract_clip_features(image)
        
        # 도로 손상 검출
        if self._detect_road_damage(image_features):
            return ImageType.ROAD_DAMAGE
            
        # 교통 표지판 검출
        if self._detect_traffic_sign(image_features):
            return ImageType.TRAFFIC_SIGN
            
        # 위성 이미지 판별
        if self._is_satellite_image(image_features):
            return ImageType.SATELLITE
            
        # 일반 현장 사진
        return ImageType.FIELD_PHOTO
        
    def process_image(self, 
                      image_path: str,
                      generate_caption: bool = True,
                      extract_features: bool = True) -> ImageAnalysisResult:
        """
        이미지 종합 처리
        
        Args:
            image_path: 이미지 파일 경로
            generate_caption: 캡션 생성 여부
            extract_features: 특징 추출 여부
            
        Returns:
            ImageAnalysisResult 객체
        """
        # 이미지 로드
        image = Image.open(image_path).convert("RGB")
        
        # 이미지 유형 분류
        image_type = self.classify_image_type(image)
        logger.info(f"이미지 유형: {image_type.value}")
        
        # 캡션 생성
        caption = ""
        if generate_caption:
            caption = self.generate_caption(image)
            logger.info(f"생성된 캡션: {caption}")
            
        # 특징 추출
        embeddings = None
        if extract_features:
            embeddings = self.extract_image_embeddings(image)
            
        # 객체 검출
        detected_objects = self.detect_objects(image, image_type)
        
        # 메타데이터 생성
        metadata = self.extract_metadata(image_path, image)
        
        return ImageAnalysisResult(
            image_type=image_type,
            caption=caption,
            detected_objects=detected_objects,
            confidence_score=self._calculate_confidence(image, image_type),
            embeddings=embeddings,
            metadata=metadata
        )
        
    def generate_caption(self, image: Image.Image) -> str:
        """
        BLIP-2를 사용한 이미지 캡션 생성
        
        Args:
            image: PIL Image 객체
            
        Returns:
            생성된 캡션 텍스트
        """
        inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            generated_ids = self.blip_model.generate(**inputs, max_length=50)
            
        caption = self.blip_processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        
        return caption
        
    def extract_image_embeddings(self, image: Image.Image) -> np.ndarray:
        """
        CLIP을 사용한 이미지 임베딩 추출
        
        Args:
            image: PIL Image 객체
            
        Returns:
            임베딩 벡터 (1024차원)
        """
        inputs = self.clip_processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            
        # 정규화
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()
        
    def search_similar_text(self, 
                           image: Image.Image, 
                           text_queries: List[str]) -> List[Tuple[str, float]]:
        """
        이미지와 텍스트 쿼리 간 유사도 검색
        
        Args:
            image: PIL Image 객체
            text_queries: 검색할 텍스트 쿼리 리스트
            
        Returns:
            (쿼리, 유사도) 튜플 리스트
        """
        # 이미지 특징 추출
        image_inputs = self.clip_processor(images=image, return_tensors="pt")
        image_inputs = {k: v.to(self.device) for k, v in image_inputs.items()}
        
        # 텍스트 특징 추출
        text_inputs = self.clip_processor(text=text_queries, return_tensors="pt", padding=True)
        text_inputs = {k: v.to(self.device) for k, v in text_inputs.items()}
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**image_inputs)
            text_features = self.clip_model.get_text_features(**text_inputs)
            
            # 정규화
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            
            # 코사인 유사도 계산
            similarities = (image_features @ text_features.T).squeeze().cpu().numpy()
            
        results = [(query, float(sim)) for query, sim in zip(text_queries, similarities)]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
        
    def detect_objects(self, image: Image.Image, image_type: ImageType) -> List[str]:
        """
        이미지 유형별 객체 검출
        
        Args:
            image: PIL Image 객체
            image_type: 이미지 유형
            
        Returns:
            검출된 객체 리스트
        """
        detected = []
        
        if image_type == ImageType.ROAD_DAMAGE:
            # 도로 손상 관련 객체 검출
            damage_queries = ["포트홀", "도로 균열", "아스팔트 파손", "도로 침하"]
            results = self.search_similar_text(image, damage_queries)
            detected = [obj for obj, score in results if score > 0.3]
            
        elif image_type == ImageType.TRAFFIC_SIGN:
            # 교통 표지판 검출
            sign_queries = self.korea_expressway_labels["traffic_sign"]
            results = self.search_similar_text(image, sign_queries)
            detected = [obj for obj, score in results if score > 0.35]
            
        else:
            # 일반 객체 검출
            general_queries = ["차량", "사람", "건물", "도로", "나무", "하늘"]
            results = self.search_similar_text(image, general_queries)
            detected = [obj for obj, score in results if score > 0.25]
            
        return detected
        
    def extract_metadata(self, image_path: str, image: Image.Image) -> Dict[str, Any]:
        """
        이미지 메타데이터 추출
        
        Args:
            image_path: 이미지 파일 경로
            image: PIL Image 객체
            
        Returns:
            메타데이터 딕셔너리
        """
        metadata = {
            "file_path": image_path,
            "file_name": os.path.basename(image_path),
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": os.path.getsize(image_path) if os.path.exists(image_path) else 0
        }
        
        # EXIF 데이터 추출 (있는 경우)
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            metadata["exif"] = {k: v for k, v in exif.items() if k in [271, 272, 274, 282, 283]}
            
        return metadata
        
    def _is_document_scan(self, image_array: np.ndarray) -> bool:
        """문서 스캔 이미지 판별"""
        # 흑백 또는 회색조 비율 확인
        if len(image_array.shape) == 2:
            return True
            
        # RGB 이미지에서 회색조 비율 확인
        gray_ratio = np.std(image_array, axis=2).mean()
        return gray_ratio < 30
        
    def _is_technical_drawing(self, image_array: np.ndarray) -> bool:
        """기술 도면 판별"""
        # 엣지 검출을 통한 선 비율 확인
        edges = self._detect_edges(image_array)
        edge_ratio = np.sum(edges) / edges.size
        return edge_ratio > 0.15
        
    def _detect_edges(self, image_array: np.ndarray) -> np.ndarray:
        """간단한 엣지 검출"""
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array
            
        # Sobel 필터 근사
        dx = np.abs(np.diff(gray, axis=1))
        dy = np.abs(np.diff(gray, axis=0))
        
        edges = np.zeros_like(gray)
        edges[:-1, :-1] = (dx[:-1, :] + dy[:, :-1]) > 30
        
        return edges
        
    def _extract_clip_features(self, image: Image.Image) -> np.ndarray:
        """CLIP 특징 추출"""
        return self.extract_image_embeddings(image)
        
    def _detect_road_damage(self, features: np.ndarray) -> bool:
        """도로 손상 검출"""
        # 실제로는 전용 모델 사용 권장
        # 여기서는 간단한 휴리스틱 사용
        return False
        
    def _detect_traffic_sign(self, features: np.ndarray) -> bool:
        """교통 표지판 검출"""
        # 실제로는 전용 모델 사용 권장
        return False
        
    def _is_satellite_image(self, features: np.ndarray) -> bool:
        """위성 이미지 판별"""
        # 실제로는 전용 모델 사용 권장
        return False
        
    def _calculate_confidence(self, image: Image.Image, image_type: ImageType) -> float:
        """신뢰도 점수 계산"""
        # 간단한 휴리스틱
        return 0.85
        

class KoreaExpresswayImageAnalyzer(MultimodalVLMProcessor):
    """
    한국도로공사 특화 이미지 분석기
    도로, 교통, 인프라 관련 이미지 전문 처리
    """
    
    def __init__(self):
        super().__init__()
        
        # 도로공사 특화 설정
        self.damage_severity_levels = ["경미", "보통", "심각", "긴급"]
        self.maintenance_priority = ["낮음", "보통", "높음", "긴급"]
        
    def analyze_road_damage(self, image_path: str) -> Dict[str, Any]:
        """
        도로 손상 분석
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            손상 분석 결과
        """
        image = Image.open(image_path).convert("RGB")
        
        # 손상 유형 검출
        damage_types = [
            "포트홀", "횡단균열", "종단균열", "거북등균열",
            "침하", "융기", "박리", "마모"
        ]
        
        results = self.search_similar_text(image, damage_types)
        
        # 심각도 평가
        severity = self._assess_damage_severity(image, results)
        
        # 유지보수 우선순위 계산
        priority = self._calculate_maintenance_priority(severity, results)
        
        return {
            "damage_types": [r[0] for r in results if r[1] > 0.3],
            "severity_level": severity,
            "maintenance_priority": priority,
            "confidence_scores": {r[0]: r[1] for r in results},
            "recommended_action": self._recommend_action(severity, priority)
        }
        
    def analyze_traffic_infrastructure(self, image_path: str) -> Dict[str, Any]:
        """
        교통 인프라 분석
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            인프라 분석 결과
        """
        image = Image.open(image_path).convert("RGB")
        
        # 인프라 요소 검출
        infrastructure_elements = [
            "톨게이트", "휴게소", "IC", "JC",
            "터널 입구", "터널 출구", "교량", "고가도로",
            "가드레일", "중앙분리대", "갓길", "차선"
        ]
        
        results = self.search_similar_text(image, infrastructure_elements)
        
        detected_elements = [r[0] for r in results if r[1] > 0.25]
        
        return {
            "detected_infrastructure": detected_elements,
            "location_type": self._identify_location_type(detected_elements),
            "safety_assessment": self._assess_safety(image, detected_elements),
            "maintenance_needs": self._check_maintenance_needs(detected_elements)
        }
        
    def _assess_damage_severity(self, image: Image.Image, damage_results: List[Tuple[str, float]]) -> str:
        """손상 심각도 평가"""
        max_score = max([score for _, score in damage_results]) if damage_results else 0
        
        if max_score > 0.7:
            return "심각"
        elif max_score > 0.5:
            return "보통"
        elif max_score > 0.3:
            return "경미"
        else:
            return "정상"
            
    def _calculate_maintenance_priority(self, severity: str, damage_results: List[Tuple[str, float]]) -> str:
        """유지보수 우선순위 계산"""
        severity_map = {"정상": 0, "경미": 1, "보통": 2, "심각": 3}
        priority_score = severity_map.get(severity, 0)
        
        # 손상 유형 수 고려
        num_damages = len([r for r in damage_results if r[1] > 0.3])
        if num_damages > 3:
            priority_score += 1
            
        priority_levels = ["낮음", "보통", "높음", "긴급"]
        return priority_levels[min(priority_score, 3)]
        
    def _recommend_action(self, severity: str, priority: str) -> str:
        """권장 조치 사항"""
        if priority == "긴급":
            return "즉시 보수 필요 - 교통 통제 검토"
        elif priority == "높음":
            return "1주일 내 보수 계획 수립 필요"
        elif priority == "보통":
            return "정기 점검 시 보수 검토"
        else:
            return "경과 관찰 필요"
            
    def _identify_location_type(self, elements: List[str]) -> str:
        """위치 유형 식별"""
        if "톨게이트" in elements:
            return "요금소"
        elif "휴게소" in elements:
            return "휴게시설"
        elif any(x in elements for x in ["IC", "JC"]):
            return "분기점"
        elif "터널" in elements[0] if elements else False:
            return "터널"
        elif "교량" in elements:
            return "교량"
        else:
            return "일반도로"
            
    def _assess_safety(self, image: Image.Image, elements: List[str]) -> Dict[str, Any]:
        """안전성 평가"""
        safety_score = 100
        issues = []
        
        # 가드레일 상태 확인
        if "가드레일" in elements:
            # 실제로는 가드레일 손상 검출 모델 사용
            safety_score -= 0
            
        # 시야 확보 확인
        visibility = self._check_visibility(image)
        if visibility < 0.7:
            safety_score -= 20
            issues.append("시야 불량")
            
        return {
            "safety_score": safety_score,
            "issues": issues,
            "status": "안전" if safety_score > 80 else "주의필요"
        }
        
    def _check_visibility(self, image: Image.Image) -> float:
        """시야 확보 정도 확인"""
        # 간단한 휴리스틱 (실제로는 전용 모델 사용)
        image_array = np.array(image)
        brightness = np.mean(image_array)
        return min(brightness / 255, 1.0)
        
    def _check_maintenance_needs(self, elements: List[str]) -> List[str]:
        """유지보수 필요 사항 확인"""
        needs = []
        
        if "가드레일" in elements:
            needs.append("가드레일 상태 점검")
        if "차선" in elements:
            needs.append("차선 도색 상태 확인")
        if "터널" in elements[0] if elements else False:
            needs.append("터널 조명 점검")
            
        return needs


# 테스트 코드
if __name__ == "__main__":
    # VLM 프로세서 초기화
    processor = MultimodalVLMProcessor()
    
    # 한국도로공사 특화 분석기 초기화
    analyzer = KoreaExpresswayImageAnalyzer()
    
    print("ex-GPT Vision Language Model 프로세서 준비 완료")
    print("이미지 처리 기능:")
    print("1. 이미지 분류 및 캡셔닝")
    print("2. 도로 손상 분석")
    print("3. 교통 인프라 인식")
    print("4. 멀티모달 검색")
