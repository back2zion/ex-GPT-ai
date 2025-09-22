"""
CCTV 이미지 검색 API
한국도로공사 해무/안개 CCTV 데이터 검색 서비스
"""

import os
import zipfile
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cctv", tags=["CCTV 이미지 검색"])

class ImageResult(BaseModel):
    id: str
    url: str
    title: str
    region: str
    weather_condition: Optional[str] = None
    time_of_day: Optional[str] = None
    file_size: Optional[int] = None
    similarity_score: Optional[float] = None

class SearchResponse(BaseModel):
    status: str
    query: str
    total_count: int
    images: List[ImageResult]
    has_more: bool = False

class CCTVImageSearcher:
    """CCTV 이미지 검색 클래스 (CPU 최적화)"""
    
    def __init__(self):
        self.data_path = Path("C:/Users/user/Documents/interim_report/188.해무, 안개 CCTV 데이터/01.데이터")
        self.extracted_path = self.data_path.parent / "extracted_images"
        self.image_index = {}
        self.is_initialized = False
        
    async def initialize(self):
        """이미지 데이터 초기화"""
        if self.is_initialized:
            return
            
        logger.info("CCTV 이미지 검색 시스템 초기화 중...")
        
        # ZIP 파일 압축 해제
        await self._extract_zip_files()
        
        # 이미지 인덱싱
        await self._build_image_index()
        
        self.is_initialized = True
        logger.info(f"초기화 완료. 총 {len(self.image_index)}개 이미지 인덱싱됨")
    
    async def _extract_zip_files(self):
        """ZIP 파일들을 압축 해제"""
        train_data_path = self.data_path / "1.Training" / "원천데이터"
        
        if not train_data_path.exists():
            logger.error(f"데이터 경로 없음: {train_data_path}")
            return
            
        self.extracted_path.mkdir(exist_ok=True)
        
        zip_files = list(train_data_path.glob("*.zip"))
        logger.info(f"발견된 ZIP 파일: {len(zip_files)}개")
        
        for zip_file in zip_files:
            region_name = zip_file.stem.replace("TS.", "")
            region_path = self.extracted_path / region_name
            
            # 이미 압축 해제된 경우 스킵
            if region_path.exists() and any(region_path.iterdir()):
                logger.info(f"{region_name} 이미 압축 해제됨")
                continue
                
            try:
                logger.info(f"{region_name} 압축 해제 중...")
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(region_path)
                logger.info(f"{region_name} 압축 해제 완료")
                
            except Exception as e:
                logger.error(f"{zip_file} 압축 해제 실패: {e}")
    
    async def _build_image_index(self):
        """이미지 파일 인덱스 구축"""
        if not self.extracted_path.exists():
            logger.warning("압축 해제된 이미지 없음")
            return
            
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_count = 0
        
        for region_dir in self.extracted_path.iterdir():
            if not region_dir.is_dir():
                continue
                
            region_name = region_dir.name
            logger.info(f"{region_name} 지역 이미지 인덱싱 중...")
            
            for image_file in region_dir.rglob("*"):
                if image_file.suffix.lower() in image_extensions:
                    try:
                        # 이미지 메타데이터 생성
                        metadata = self._extract_metadata(image_file, region_name)
                        
                        image_id = f"{region_name}_{image_file.stem}"
                        self.image_index[image_id] = {
                            "path": str(image_file),
                            "region": region_name,
                            "filename": image_file.name,
                            "size": image_file.stat().st_size,
                            "metadata": metadata
                        }
                        image_count += 1
                        
                    except Exception as e:
                        logger.error(f"이미지 처리 실패 {image_file}: {e}")
        
        logger.info(f"총 {image_count}개 이미지 인덱싱 완료")
    
    def _extract_metadata(self, image_path: Path, region: str) -> Dict:
        """파일명에서 메타데이터 추출"""
        filename = image_path.stem.lower()
        
        # 날씨 상태 감지
        weather_conditions = []
        weather_keywords = {
            "fog": "해무", "mist": "안개", "clear": "맑음",
            "rain": "강우", "snow": "강설", "cloudy": "흐림"
        }
        
        for keyword, korean in weather_keywords.items():
            if keyword in filename:
                weather_conditions.append(korean)
        
        # 시간대 감지
        time_of_day = "주간"
        night_indicators = ["night", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"]
        if any(indicator in filename for indicator in night_indicators):
            time_of_day = "야간"
        
        return {
            "weather": weather_conditions,
            "time_of_day": time_of_day,
            "description": f"{region} 지역 {', '.join(weather_conditions) if weather_conditions else '일반'} CCTV 영상"
        }
    
    async def search(self, query: str, limit: int = 12) -> List[Dict]:
        """텍스트 쿼리로 이미지 검색"""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.image_index:
            return []
        
        query_lower = query.lower()
        results = []
        
        # 키워드 기반 검색 (간단한 구현)
        search_keywords = {
            "해무": ["fog", "해무"],
            "안개": ["mist", "fog", "안개"],
            "맑음": ["clear", "맑음"],
            "강우": ["rain", "강우"],
            "강설": ["snow", "강설"],
            "야간": ["night", "야간"],
            "주간": ["day", "주간"],
            "흐림": ["cloudy", "흐림"]
        }
        
        # 지역명 키워드
        region_keywords = {
            "강화도": ["강화도", "ganghwa"],
            "대부도": ["대부도", "daebu"],
            "영종도": ["영종도", "yeongjong"],
            "인천항": ["인천항", "incheon"]
        }
        
        for image_id, image_data in self.image_index.items():
            score = 0
            
            # 날씨 키워드 매칭
            for keyword, variants in search_keywords.items():
                if any(variant in query_lower for variant in variants):
                    if keyword in str(image_data["metadata"].get("weather", [])):
                        score += 2
                    if keyword in image_data["metadata"].get("description", "").lower():
                        score += 1
            
            # 지역 키워드 매칭
            for region, variants in region_keywords.items():
                if any(variant in query_lower for variant in variants):
                    if region in image_data["region"]:
                        score += 3
            
            # 일반 텍스트 매칭
            if query_lower in image_data["metadata"].get("description", "").lower():
                score += 1
            
            if query_lower in image_data["filename"].lower():
                score += 1
            
            if score > 0:
                results.append({
                    "image_data": image_data,
                    "score": score,
                    "id": image_id
                })
        
        # 점수별 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit]

# 전역 검색 인스턴스
searcher = CCTVImageSearcher()

@router.get("/search", response_model=SearchResponse)
async def search_cctv_images(
    query: str = Query(..., description="검색 쿼리"),
    limit: int = Query(12, ge=1, le=50, description="검색 결과 수"),
    page: int = Query(1, ge=1, description="페이지 번호")
):
    """CCTV 이미지 검색"""
    try:
        # 백그라운드에서 초기화 (첫 호출시에만)
        if not searcher.is_initialized:
            logger.info("첫 검색 요청 - 백그라운드에서 초기화 중...")
        
        search_results = await searcher.search(query, limit)
        
        images = []
        for i, result in enumerate(search_results):
            image_data = result["image_data"]
            
            # 이미지 URL 생성 (개발용 - 실제로는 정적 파일 서빙 필요)
            image_url = f"http://localhost:8200/static/images/{image_data['region']}/{image_data['filename']}"
            
            images.append(ImageResult(
                id=result["id"],
                url=image_url,
                title=f"{image_data['region']} - {image_data['metadata'].get('description', '이미지')}",
                region=image_data["region"],
                weather_condition=", ".join(image_data["metadata"].get("weather", [])) or None,
                time_of_day=image_data["metadata"].get("time_of_day"),
                file_size=image_data.get("size"),
                similarity_score=result["score"] / 10.0  # 정규화된 점수
            ))
        
        return SearchResponse(
            status="success",
            query=query,
            total_count=len(images),
            images=images,
            has_more=len(search_results) >= limit
        )
        
    except Exception as e:
        logger.error(f"이미지 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@router.get("/regions")
async def get_regions():
    """사용 가능한 지역 목록 조회"""
    try:
        if not searcher.is_initialized:
            await searcher.initialize()
        
        regions = set()
        for image_data in searcher.image_index.values():
            regions.add(image_data["region"])
        
        return {
            "status": "success",
            "regions": sorted(list(regions))
        }
        
    except Exception as e:
        logger.error(f"지역 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="지역 목록을 가져올 수 없습니다")

@router.get("/stats")
async def get_search_stats():
    """검색 시스템 통계"""
    try:
        if not searcher.is_initialized:
            await searcher.initialize()
        
        # 지역별 이미지 수 집계
        region_counts = {}
        weather_counts = {}
        
        for image_data in searcher.image_index.values():
            region = image_data["region"]
            region_counts[region] = region_counts.get(region, 0) + 1
            
            for weather in image_data["metadata"].get("weather", []):
                weather_counts[weather] = weather_counts.get(weather, 0) + 1
        
        return {
            "status": "success",
            "total_images": len(searcher.image_index),
            "regions": region_counts,
            "weather_conditions": weather_counts,
            "initialized": searcher.is_initialized
        }
        
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="통계를 가져올 수 없습니다")
