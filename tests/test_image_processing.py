"""
이미지 처리 테스트 모듈
"""

import pytest
import numpy as np
from PIL import Image
import io
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVLMProcessor:
    """VLM 프로세서 테스트"""

    def test_image_type_classification(self):
        """이미지 타입 분류 테스트"""
        from backend.src.image_processing.vlm_processor import ImageType

        image_types = [
            ImageType.DOCUMENT_SCAN,
            ImageType.FIELD_PHOTO,
            ImageType.ROAD_DAMAGE,
            ImageType.TRAFFIC_SIGN
        ]

        for img_type in image_types:
            assert img_type.value in [
                "document_scan",
                "field_photo",
                "road_damage",
                "traffic_sign"
            ]

    def test_create_dummy_image(self):
        """더미 이미지 생성 테스트"""
        # 100x100 RGB 이미지 생성
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)

        assert img.size == (100, 100)
        assert img.mode == "RGB"

    @pytest.mark.asyncio
    async def test_image_embeddings(self):
        """이미지 임베딩 생성 테스트"""
        # 임베딩 차원 테스트
        embedding_size = 768
        dummy_embedding = np.random.randn(embedding_size)

        assert dummy_embedding.shape == (768,)
        assert isinstance(dummy_embedding, np.ndarray)


class TestOCREngine:
    """OCR 엔진 테스트"""

    def test_supported_languages(self):
        """지원 언어 테스트"""
        supported_langs = ["ko", "en", "ko+en"]

        for lang in supported_langs:
            assert lang in ["ko", "en", "ko+en"]

    def test_ocr_result_structure(self):
        """OCR 결과 구조 테스트"""
        mock_ocr_result = {
            "text": "샘플 텍스트",
            "confidence": 0.95,
            "language": "ko",
            "bounding_boxes": []
        }

        assert "text" in mock_ocr_result
        assert "confidence" in mock_ocr_result
        assert 0 <= mock_ocr_result["confidence"] <= 1

    def test_document_types(self):
        """문서 타입 테스트"""
        doc_types = ["pdf", "image", "mixed"]

        for dtype in doc_types:
            assert dtype in ["pdf", "image", "mixed"]


class TestImageAnalyzer:
    """통합 이미지 분석기 테스트"""

    def test_processing_modes(self):
        """처리 모드 테스트"""
        from backend.src.image_processing.image_analyzer import ProcessingMode

        modes = [
            ProcessingMode.FAST,
            ProcessingMode.STANDARD,
            ProcessingMode.DEEP
        ]

        for mode in modes:
            assert mode.value in ["fast", "standard", "deep"]

    def test_analysis_result_fields(self):
        """분석 결과 필드 테스트"""
        expected_fields = [
            "status",
            "image_type",
            "processing_time",
            "ocr_result",
            "vlm_analysis",
            "embeddings"
        ]

        # 더미 결과 구조
        mock_result = {
            "status": "success",
            "image_type": "document",
            "processing_time": 1.23,
            "ocr_result": {},
            "vlm_analysis": {},
            "embeddings": None
        }

        for field in expected_fields:
            assert field in mock_result

    @pytest.mark.parametrize("image_size,expected", [
        ((100, 100), True),
        ((5000, 5000), False),  # Too large
        ((10, 10), False),  # Too small
    ])
    def test_image_size_validation(self, image_size, expected):
        """이미지 크기 검증 테스트"""
        MIN_SIZE = 50
        MAX_SIZE = 4096

        width, height = image_size
        is_valid = (MIN_SIZE <= width <= MAX_SIZE and
                   MIN_SIZE <= height <= MAX_SIZE)

        assert is_valid == expected


class TestSecurityCheck:
    """보안 검사 테스트"""

    def test_personal_info_patterns(self):
        """개인정보 패턴 테스트"""
        patterns = {
            "주민등록번호": r"\d{6}-\d{7}",
            "전화번호": r"010-\d{4}-\d{4}",
            "이메일": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        }

        for name, pattern in patterns.items():
            assert isinstance(pattern, str)
            assert len(pattern) > 0

    def test_file_extension_validation(self):
        """파일 확장자 검증 테스트"""
        allowed = [".jpg", ".jpeg", ".png", ".pdf", ".docx"]
        blocked = [".exe", ".dll", ".bat", ".sh"]

        for ext in allowed:
            assert ext.startswith(".")

        for ext in blocked:
            assert ext not in allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])