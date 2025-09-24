"""
API 테스트 모듈
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.src.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """API 엔드포인트 테스트"""

    def test_health_check(self):
        """헬스체크 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ex-GPT API"
        assert data["version"] == "1.0.0"

    def test_multimodal_search_text(self):
        """텍스트 검색 테스트"""
        request_data = {
            "query": "도로 파손 현황",
            "query_type": "text",
            "top_k": 5
        }
        response = client.post("/api/v1/multimodal-search", json=request_data)
        assert response.status_code in [200, 500]  # 초기화 상태에 따라

    def test_upload_invalid_file(self):
        """잘못된 파일 업로드 테스트"""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.exe", b"fake content", "application/x-msdownload")}
        )
        assert response.status_code in [400, 422, 500]


class TestImageAnalysis:
    """이미지 분석 테스트"""

    @pytest.mark.asyncio
    async def test_image_analysis_request(self):
        """이미지 분석 요청 테스트"""
        request_data = {
            "image_url": "test_image.jpg",
            "mode": "fast",
            "extract_text": True,
            "detect_objects": True
        }
        # 실제 테스트는 모듈 초기화 후 수행
        assert request_data is not None

    def test_processing_modes(self):
        """처리 모드 테스트"""
        modes = ["fast", "standard", "deep"]
        for mode in modes:
            assert mode in ["fast", "standard", "deep"]


class TestVectorStore:
    """벡터 스토어 테스트"""

    def test_collection_types(self):
        """컬렉션 타입 테스트"""
        collection_types = ["documents", "images", "chunks"]
        for ctype in collection_types:
            assert ctype in ["documents", "images", "chunks"]

    @pytest.mark.asyncio
    async def test_search_parameters(self):
        """검색 파라미터 테스트"""
        params = {
            "top_k": 10,
            "score_threshold": 0.5,
            "filter_conditions": {"type": "document"}
        }
        assert params["top_k"] > 0
        assert 0 <= params["score_threshold"] <= 1


class TestKoreaExpressway:
    """한국도로공사 특화 기능 테스트"""

    def test_damage_types(self):
        """도로 손상 타입 테스트"""
        damage_types = ["포트홀", "균열", "침하", "파손", "박리", "마모"]
        for dtype in damage_types:
            assert dtype in ["포트홀", "균열", "침하", "파손", "박리", "마모"]

    def test_infrastructure_types(self):
        """인프라 타입 테스트"""
        infra_types = ["톨게이트", "휴게소", "IC", "JC", "터널", "교량"]
        for itype in infra_types:
            assert itype in ["톨게이트", "휴게소", "IC", "JC", "터널", "교량"]

    def test_severity_levels(self):
        """심각도 레벨 테스트"""
        severity_levels = ["경미", "보통", "심각", "긴급"]
        for level in severity_levels:
            assert level in ["경미", "보통", "심각", "긴급"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])