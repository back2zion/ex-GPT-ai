"""
이미지 검색 서비스
CCTV 이미지 데이터를 기반으로 한 멀티모달 검색 시스템
"""

import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from PIL import Image

from app.core.config import settings
from app.services.ollama_client import OllamaClient

@dataclass
class ImageResult:
    """이미지 검색 결과"""
    file_path: str
    relative_path: str
    filename: str
    description: str
    relevance_score: float
    file_size: int
    image_dimensions: Optional[Tuple[int, int]] = None
    timestamp: Optional[datetime] = None
    location: Optional[str] = None
    weather_condition: Optional[str] = None

class ImageSearchService:
    """이미지 검색 서비스"""
    
    def __init__(self, image_folder: str, ollama_client: OllamaClient):
        self.image_folder = Path(image_folder)
        self.ollama_client = ollama_client
        self.supported_formats = settings.SUPPORTED_IMAGE_FORMATS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.temp_dir = Path("temp/extracted_images")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 이미지 캐시
        self._image_cache: Dict[str, List[ImageResult]] = {}
        self._cache_initialized = False
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def initialize(self):
        """서비스 초기화"""
        logger.info("이미지 검색 서비스 초기화 시작")
        
        if not self.image_folder.exists():
            logger.error(f"이미지 폴더가 존재하지 않습니다: {self.image_folder}")
            return
            
        # 이미지 캐시 구축 (JPG 파일만)
        await self._build_image_cache()
        
        self._cache_initialized = True
        logger.info("이미지 검색 서비스 초기화 완료")
        
    async def _extract_zip_files(self):
        """ZIP 파일들을 메모리에서 직접 처리 (디스크 공간 절약)"""
        try:
            zip_files = list(self.image_folder.rglob("*.zip"))
            logger.info(f"발견된 ZIP 파일 수: {len(zip_files)}")

            # ZIP 파일을 추출하지 않고 직접 읽을 수 있도록 정보만 저장
            self.zip_file_info = {}

            for zip_path in zip_files:
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # ZIP 내부의 이미지 파일 목록만 저장
                        image_files = []
                        for file_info in zip_ref.filelist:
                            if any(file_info.filename.lower().endswith(ext)
                                   for ext in ['.jpg', '.jpeg', '.png', '.bmp']):
                                image_files.append(file_info.filename)

                        self.zip_file_info[str(zip_path)] = image_files
                        logger.debug(f"ZIP 파일 스캔 완료: {zip_path.name} ({len(image_files)}개 이미지)")

                except Exception as e:
                    logger.error(f"ZIP 파일 스캔 실패 {zip_path}: {e}")

        except Exception as e:
            logger.error(f"ZIP 파일 스캔 과정 오류: {e}")
            
    async def _build_image_cache(self):
        """이미지 파일 캐시 구축 (JPG 파일만)"""
        try:
            total_images = 0

            # JPG 이미지 파일들만 스캔
            if self.image_folder.exists():
                logger.info(f"JPG 이미지 파일 스캔 시작: {self.image_folder}")

                # JPG 확장자 패턴들
                jpg_patterns = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]

                # 각 패턴에 대해 재귀적으로 검색
                all_image_files = []
                for pattern in jpg_patterns:
                    pattern_files = list(self.image_folder.rglob(pattern))
                    all_image_files.extend(pattern_files)

                # 중복 제거
                all_image_files = list(set(all_image_files))
                total_files = len(all_image_files)
                logger.info(f"총 {total_files}개의 JPG 파일 발견, 처리 시작...")

                processed_count = 0
                for image_path in all_image_files:
                    try:
                        # 이미지 파일 정보 처리
                        result = await self._process_image_file(image_path)
                        if result:
                            # 지역별 캐시에 저장
                            location_key = self._extract_location_from_filename(result.filename)
                            if location_key not in self._image_cache:
                                self._image_cache[location_key] = []
                            self._image_cache[location_key].append(result)
                            total_images += 1

                        processed_count += 1

                        # 진행률 로깅 (10,000개마다)
                        if processed_count % 10000 == 0:
                            progress = (processed_count / total_files) * 100
                            logger.info(f"처리 진행률: {processed_count}/{total_files} ({progress:.1f}%)")

                    except Exception as e:
                        logger.debug(f"JPG 이미지 파일 처리 실패 {image_path}: {e}")
                        processed_count += 1

            logger.info(f"발견된 JPG 이미지 파일 수: {total_images}")
            logger.info(f"이미지 캐시 구축 완료. 지역 수: {len(self._image_cache)}")

        except Exception as e:
            logger.error(f"이미지 캐시 구축 오류: {e}")
            
    async def _process_image_file(self, image_path: Path) -> Optional[ImageResult]:
        """개별 이미지 파일 처리 (최적화됨)"""
        try:
            # 파일 정보 수집
            stat = image_path.stat()
            file_size = stat.st_size

            # 파일명에서 정보 추출
            filename = image_path.name
            location = self._extract_location_from_filename(filename)
            weather = self._extract_weather_from_filename(filename)
            timestamp = self._extract_timestamp_from_filename(filename)

            # 상대 경로 계산 (IMAGE_FOLDER_PATH 기준)
            try:
                relative_path = str(image_path.relative_to(self.image_folder))
            except ValueError:
                # temp_dir에 있는 경우, temp_dir 기준으로 계산
                relative_path = str(image_path.relative_to(self.temp_dir))

            return ImageResult(
                file_path=str(image_path),
                relative_path=relative_path,
                filename=filename,
                description=f"CCTV 이미지 - {location}",
                relevance_score=0.0,  # 검색 시 계산
                file_size=file_size,
                image_dimensions=None,  # 성능을 위해 이미지 크기는 나중에 필요할 때 로드
                timestamp=timestamp,
                location=location,
                weather_condition=weather
            )

        except Exception as e:
            logger.debug(f"이미지 파일 처리 오류 {image_path}: {e}")
            return None

    def _quick_relevance_score(self, filename: str, query: str) -> float:
        """빠른 키워드 기반 관련성 점수 계산 (VLM 사용 안함)"""
        try:
            query_lower = query.lower()
            filename_lower = filename.lower()

            score = 0.0

            # 날씨 관련 키워드
            weather_keywords = {
                "해무": 0.4, "안개": 0.4, "fog": 0.4, "mist": 0.4,
                "맑음": 0.3, "clear": 0.3, "sunny": 0.3,
                "비": 0.3, "rain": 0.3, "rainy": 0.3,
                "눈": 0.3, "snow": 0.3, "snowy": 0.3,
                "야간": 0.2, "밤": 0.2, "night": 0.2,
                "주간": 0.2, "낮": 0.2, "day": 0.2
            }

            # 도로/장소 관련 키워드
            location_keywords = {
                "경부고속도로": 0.5, "경부": 0.4,
                "중부고속도로": 0.5, "중부": 0.4,
                "서해안고속도로": 0.5, "서해안": 0.4,
                "고속도로": 0.3, "highway": 0.3,
                "교량": 0.3, "bridge": 0.3,
                "터널": 0.3, "tunnel": 0.3,
                "ic": 0.2, "인터체인지": 0.2,
                "휴게소": 0.2, "service": 0.2
            }

            # CCTV/영상 관련 키워드
            video_keywords = {
                "cctv": 0.3, "영상": 0.2, "카메라": 0.2,
                "이미지": 0.2, "사진": 0.2
            }

            # 키워드 매칭 점수 계산
            for keyword, weight in weather_keywords.items():
                if keyword in query_lower and keyword in filename_lower:
                    score += weight
                elif keyword in query_lower or keyword in filename_lower:
                    score += weight * 0.3

            for keyword, weight in location_keywords.items():
                if keyword in query_lower and keyword in filename_lower:
                    score += weight
                elif keyword in query_lower or keyword in filename_lower:
                    score += weight * 0.3

            for keyword, weight in video_keywords.items():
                if keyword in query_lower and keyword in filename_lower:
                    score += weight
                elif keyword in query_lower or keyword in filename_lower:
                    score += weight * 0.3

            # 기본 CCTV 파일 점수
            if "ts." in filename_lower or "cctv" in filename_lower:
                score += 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"빠른 관련성 점수 계산 오류: {e}")
            return 0.0

    def _extract_location_from_filename(self, filename: str) -> str:
        """파일명에서 위치 정보 추출"""
        filename_lower = filename.lower()
        
        # 알려진 지역명 매핑
        location_mapping = {
            "강화도": "강화도",
            "대부도": "대부도", 
            "대산항": "대산항",
            "덕적도": "덕적도",
            "백령도": "백령도",
            "송도": "송도",
            "연안부두": "연안부두",
            "연평도": "연평도",
            "영종도": "영종도",
            "영흥도": "영흥도",
            "인천항": "인천항",
            "지도": "지도",
            "평택당진항": "평택당진항"
        }
        
        for key, location in location_mapping.items():
            if key in filename_lower:
                return location
                
        return "알 수 없는 지역"
        
    def _extract_weather_from_filename(self, filename: str) -> Optional[str]:
        """파일명에서 날씨 정보 추출"""
        filename_lower = filename.lower()
        
        weather_keywords = {
            "fog": "안개",
            "mist": "해무", 
            "clear": "맑음",
            "rain": "비",
            "snow": "눈",
            "night": "야간",
            "day": "주간"
        }
        
        for keyword, weather in weather_keywords.items():
            if keyword in filename_lower:
                return weather
                
        return None
        
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[datetime]:
        """파일명에서 타임스탬프 추출"""
        import re
        
        # 다양한 날짜/시간 패턴 시도
        patterns = [
            r'(\d{4})(\d{2})(\d{2})[\-_]?(\d{2})(\d{2})(\d{2})',
            r'(\d{4})\-(\d{2})\-(\d{2})[\-_]?(\d{2})\-(\d{2})\-(\d{2})',
            r'(\d{2})(\d{2})(\d{2})[\-_]?(\d{2})(\d{2})(\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 6:
                        year, month, day, hour, minute, second = map(int, groups)
                        if year < 100:  # 2자리 연도를 4자리로 변환
                            year += 2000
                        return datetime(year, month, day, hour, minute, second)
                except ValueError:
                    continue
                    
        return None
        
    async def search_images(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> "ImageSearchResponse":
        """이미지 검색 수행"""
        try:
            if not self._cache_initialized:
                await self.initialize()
                
            logger.info(f"이미지 검색 수행: '{query}', limit={limit}, offset={offset}")
            
            start_time = asyncio.get_event_loop().time()
            
            # 모든 이미지 결과 수집
            all_results = []
            for location_images in self._image_cache.values():
                all_results.extend(location_images)
                
            # 성능 최적화: 키워드 기반 사전 필터링
            logger.info(f"총 {len(all_results)}개 이미지에서 검색 시작")

            # 1단계: 빠른 키워드 매칭으로 후보 추림 (임시로 모든 이미지 포함)
            candidate_results = []
            for image_result in all_results:
                # 빠른 키워드 기반 점수 계산 (VLM 사용 안함)
                quick_score = self._quick_relevance_score(image_result.filename, query)
                if quick_score > 0.01:  # 임계값을 매우 낮게 설정
                    image_result.relevance_score = quick_score
                    candidate_results.append(image_result)
                else:
                    # 키워드 점수가 낮아도 기본 점수 부여
                    image_result.relevance_score = 0.1
                    candidate_results.append(image_result)

            logger.info(f"키워드 필터링 후 {len(candidate_results)}개 후보 선택")

            # 2단계: 상위 후보만 VLM으로 정밀 분석 (최대 200개)
            max_vlm_candidates = min(200, len(candidate_results))
            candidate_results.sort(key=lambda x: x.relevance_score, reverse=True)
            vlm_candidates = candidate_results[:max_vlm_candidates]

            logger.info(f"VLM 분석 대상: {len(vlm_candidates)}개")

            # 3단계: VLM을 사용한 정밀 이미지 분석 (활성화됨)
            scored_results = []
            for i, image_result in enumerate(vlm_candidates):
                try:
                    # VLM을 사용하여 이미지 분석 및 관련성 점수 계산
                    vlm_score, vlm_description = await self._analyze_image_with_vlm(
                        image_result.file_path, query
                    )

                    # 키워드 점수와 VLM 점수 결합 (가중 평균)
                    keyword_weight = 0.3
                    vlm_weight = 0.7
                    final_score = (image_result.relevance_score * keyword_weight) + (vlm_score * vlm_weight)

                    # 임계값 통과 시 결과에 포함
                    if final_score > self.similarity_threshold:
                        # VLM 분석 결과로 설명 업데이트
                        image_result.description = vlm_description if vlm_description else f"CCTV 영상 - {self._extract_location_from_filename(image_result.filename)}"
                        image_result.relevance_score = final_score
                        scored_results.append(image_result)

                    # 진행 상황 로그 (10개마다 - VLM 분석은 더 느리므로)
                    if (i + 1) % 10 == 0:
                        logger.info(f"VLM 분석 진행: {i + 1}/{len(vlm_candidates)} (점수: {final_score:.3f})")

                except Exception as e:
                    logger.warning(f"VLM 분석 실패 {image_result.filename}: {e}")
                    # VLM 분석 실패 시 키워드 점수만으로 판단
                    if image_result.relevance_score > self.similarity_threshold:
                        image_result.description = f"CCTV 영상 - {self._extract_location_from_filename(image_result.filename)} (VLM 분석 실패)"
                        scored_results.append(image_result)
                    
            # 관련성 점수로 정렬
            scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # 필터 적용
            if filters:
                scored_results = self._apply_filters(scored_results, filters)
                
            # 페이징 적용
            total_count = len(scored_results)
            paginated_results = scored_results[offset:offset + limit]
            
            # 결과 변환
            image_dicts = []
            for result in paginated_results:
                image_dict = {
                    "id": result.relative_path,
                    "filename": result.filename,
                    "description": result.description,
                    "relevance_score": result.relevance_score,
                    "file_size": result.file_size,
                    "location": result.location,
                    "weather_condition": result.weather_condition,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                    "image_url": f"/api/v1/images/{result.relative_path}",
                    "thumbnail_url": f"/api/v1/images/{result.relative_path}?size=thumbnail",
                    "dimensions": result.image_dimensions
                }
                image_dicts.append(image_dict)
                
            end_time = asyncio.get_event_loop().time()
            search_time_ms = (end_time - start_time) * 1000
            
            # 응답 생성
            from app.models.schemas import ImageSearchResponse
            
            response = ImageSearchResponse(
                success=True,
                query=query,
                images=image_dicts,
                total_count=total_count,
                returned_count=len(image_dicts),
                has_more=offset + limit < total_count,
                page_info={
                    "offset": offset,
                    "limit": limit,
                    "current_page": (offset // limit) + 1,
                    "total_pages": (total_count + limit - 1) // limit
                },
                search_time_ms=search_time_ms,
                filters_applied=filters or {}
            )
            
            logger.info(f"검색 완료: {len(image_dicts)}개 결과, {search_time_ms:.2f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"이미지 검색 오류: {e}")
            from app.models.schemas import ImageSearchResponse
            
            return ImageSearchResponse(
                success=False,
                query=query,
                images=[],
                total_count=0,
                returned_count=0,
                has_more=False,
                page_info={"offset": offset, "limit": limit, "current_page": 1, "total_pages": 0},
                search_time_ms=0,
                filters_applied={},
                error=str(e)
            )
            
    def _apply_filters(self, results: List[ImageResult], filters: Dict[str, Any]) -> List[ImageResult]:
        """검색 결과에 필터 적용"""
        filtered_results = results
        
        # 위치 필터
        if "location" in filters and filters["location"]:
            location_filter = filters["location"].lower()
            filtered_results = [
                r for r in filtered_results 
                if r.location and location_filter in r.location.lower()
            ]
            
        # 날씨 조건 필터
        if "weather" in filters and filters["weather"]:
            weather_filter = filters["weather"].lower()
            filtered_results = [
                r for r in filtered_results
                if r.weather_condition and weather_filter in r.weather_condition.lower()
            ]
            
        # 파일 크기 필터
        if "min_file_size" in filters:
            min_size = filters["min_file_size"]
            filtered_results = [r for r in filtered_results if r.file_size >= min_size]
            
        if "max_file_size" in filters:
            max_size = filters["max_file_size"]
            filtered_results = [r for r in filtered_results if r.file_size <= max_size]
            
        # 관련성 점수 필터
        if "min_relevance" in filters:
            min_relevance = filters["min_relevance"]
            filtered_results = [r for r in filtered_results if r.relevance_score >= min_relevance]
            
        return filtered_results
        
    async def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """특정 이미지의 상세 정보 조회"""
        try:
            full_path = self.temp_dir / image_path
            
            if not full_path.exists():
                return None
                
            # 캐시에서 검색
            for location_images in self._image_cache.values():
                for image_result in location_images:
                    if image_result.relative_path == image_path:
                        return {
                            "filename": image_result.filename,
                            "description": image_result.description,
                            "file_size": image_result.file_size,
                            "location": image_result.location,
                            "weather_condition": image_result.weather_condition,
                            "timestamp": image_result.timestamp.isoformat() if image_result.timestamp else None,
                            "dimensions": image_result.image_dimensions,
                            "file_path": image_result.file_path
                        }
                        
            return None
            
        except Exception as e:
            logger.error(f"이미지 정보 조회 오류: {e}")
            return None
            
    async def _analyze_image_with_vlm(self, image_path: str, query: str) -> Tuple[float, str]:
        """VLM을 사용하여 이미지 분석 및 관련성 점수 계산"""
        try:
            # 이미지 파일이 존재하는지 확인
            if not Path(image_path).exists():
                logger.warning(f"이미지 파일이 존재하지 않음: {image_path}")
                return 0.0, ""

            # VLM 프롬프트 구성
            vlm_prompt = f"""
이 CCTV 이미지를 분석해주세요.

검색 질의: "{query}"

다음 사항들을 분석해주세요:
1. 이미지에서 보이는 주요 요소들 (도로, 차량, 기상상황 등)
2. 검색 질의와의 관련성 (0-1 점수)
3. 간단한 설명 (한 줄)

응답 형식:
점수: [0.0-1.0]
설명: [간단한 한 줄 설명]
"""

            # Ollama VLM 모델로 이미지 분석
            vlm_response = await self.ollama_client.analyze_image_with_vlm(
                image_path=image_path,
                prompt=vlm_prompt,
                model_name=settings.OLLAMA_VLM_MODEL
            )

            if not vlm_response:
                logger.warning(f"VLM 응답이 없음: {image_path}")
                return 0.0, ""

            # 응답에서 점수와 설명 추출
            score, description = self._parse_vlm_response(vlm_response, query)

            return score, description

        except Exception as e:
            logger.error(f"VLM 이미지 분석 오류 {image_path}: {e}")
            return 0.0, ""

    def _parse_vlm_response(self, vlm_response: str, query: str) -> Tuple[float, str]:
        """VLM 응답에서 점수와 설명 파싱"""
        try:
            import re

            # 점수 추출 (0.0-1.0)
            score_match = re.search(r'점수[:：]\s*([0-9]*\.?[0-9]+)', vlm_response)
            score = 0.0
            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(1.0, score))  # 0-1 범위로 제한
            else:
                # 점수가 명시되지 않은 경우 키워드 기반으로 추정
                if any(keyword in vlm_response.lower() for keyword in query.lower().split()):
                    score = 0.5
                else:
                    score = 0.1

            # 설명 추출
            description_match = re.search(r'설명[:：]\s*(.+)', vlm_response)
            if description_match:
                description = description_match.group(1).strip()
            else:
                # 설명이 없으면 전체 응답의 첫 번째 문장 사용
                sentences = vlm_response.split('.')
                description = sentences[0].strip() if sentences else "CCTV 이미지"

            # 설명이 너무 길면 자르기
            if len(description) > 100:
                description = description[:97] + "..."

            return score, description

        except Exception as e:
            logger.error(f"VLM 응답 파싱 오류: {e}")
            return 0.1, "CCTV 이미지 (분석 오류)"

    async def cleanup(self):
        """리소스 정리"""
        try:
            # 임시 폴더 정리
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

            # 스레드 풀 종료
            self.executor.shutdown(wait=True)

            logger.info("이미지 검색 서비스 정리 완료")

        except Exception as e:
            logger.error(f"이미지 검색 서비스 정리 오류: {e}")
