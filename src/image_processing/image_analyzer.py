"""
Image Analyzer for ex-GPT System
통합 이미지 분석 모듈
"""

import os
import hashlib
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image
import logging
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from dataclasses import dataclass, asdict

# 로컬 모듈 임포트
from .vlm_processor import (
    MultimodalVLMProcessor, 
    KoreaExpresswayImageAnalyzer,
    ImageType,
    ImageAnalysisResult
)
from .ocr_engine import (
    KoreanOCREngine,
    DocumentProcessor,
    OCRResult
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """처리 모드"""
    FAST = "fast"          # 빠른 처리 (기본 OCR만)
    STANDARD = "standard"  # 표준 처리 (OCR + 기본 분석)
    DEEP = "deep"         # 심층 처리 (OCR + VLM + 전체 분석)


@dataclass
class ComprehensiveImageAnalysis:
    """종합 이미지 분석 결과"""
    file_info: Dict[str, Any]
    image_type: str
    ocr_result: Optional[Dict[str, Any]]
    vlm_analysis: Optional[Dict[str, Any]]
    security_check: Dict[str, Any]
    embeddings: Optional[np.ndarray]
    processing_time: float
    status: str
    errors: List[str]


class IntegratedImageAnalyzer:
    """
    통합 이미지 분석기
    VLM, OCR, 보안 검사를 통합한 종합 분석 시스템
    """
    
    def __init__(self, 
                 enable_vlm: bool = True,
                 enable_ocr: bool = True,
                 enable_security: bool = True,
                 cache_dir: str = "./cache"):
        """
        통합 분석기 초기화
        
        Args:
            enable_vlm: Vision Language Model 사용 여부
            enable_ocr: OCR 사용 여부
            enable_security: 보안 검사 사용 여부
            cache_dir: 캐시 디렉토리
        """
        self.enable_vlm = enable_vlm
        self.enable_ocr = enable_ocr
        self.enable_security = enable_security
        
        # 캐시 디렉토리 생성
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 모듈 초기화
        if enable_vlm:
            self.vlm_processor = MultimodalVLMProcessor()
            self.korea_analyzer = KoreaExpresswayImageAnalyzer()
            
        if enable_ocr:
            self.ocr_engine = KoreanOCREngine()
            self.doc_processor = DocumentProcessor()
            
        # 중복 검사용 해시 저장소
        self.processed_hashes = set()
        self._load_hash_cache()
        
        logger.info(f"통합 이미지 분석기 초기화 완료 - VLM: {enable_vlm}, OCR: {enable_ocr}")
        
    async def analyze_image(self, 
                           image_path: str,
                           mode: ProcessingMode = ProcessingMode.STANDARD) -> ComprehensiveImageAnalysis:
        """
        이미지 종합 분석 (비동기)
        
        Args:
            image_path: 이미지 파일 경로
            mode: 처리 모드
            
        Returns:
            ComprehensiveImageAnalysis 객체
        """
        start_time = datetime.now()
        errors = []
        
        try:
            # 파일 정보 추출
            file_info = self._get_file_info(image_path)
            
            # 중복 검사
            is_duplicate = await self._check_duplicate(image_path)
            if is_duplicate:
                logger.info(f"중복 이미지 검출: {image_path}")
                return ComprehensiveImageAnalysis(
                    file_info=file_info,
                    image_type="duplicate",
                    ocr_result=None,
                    vlm_analysis=None,
                    security_check={"is_duplicate": True},
                    embeddings=None,
                    processing_time=0,
                    status="duplicate",
                    errors=[]
                )
                
            # 이미지 로드
            image = Image.open(image_path).convert("RGB")
            
            # 병렬 처리 태스크
            tasks = []
            
            # OCR 처리
            ocr_result = None
            if self.enable_ocr and mode != ProcessingMode.FAST:
                ocr_result = await self._process_ocr_async(image_path)
                
            # VLM 분석
            vlm_analysis = None
            if self.enable_vlm and mode == ProcessingMode.DEEP:
                vlm_analysis = await self._process_vlm_async(image_path)
                
            # 보안 검사
            security_check = {}
            if self.enable_security:
                security_check = await self._security_check_async(image_path, ocr_result)
                
            # 임베딩 생성
            embeddings = None
            if self.enable_vlm and mode in [ProcessingMode.STANDARD, ProcessingMode.DEEP]:
                embeddings = self._generate_embeddings(image)
                
            # 이미지 유형 결정
            if vlm_analysis:
                image_type = vlm_analysis.get('image_type', 'unknown')
            elif ocr_result:
                image_type = 'document'
            else:
                image_type = self._simple_classify(image)
                
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 해시 저장
            self._save_hash(image_path)
            
            return ComprehensiveImageAnalysis(
                file_info=file_info,
                image_type=image_type,
                ocr_result=ocr_result,
                vlm_analysis=vlm_analysis,
                security_check=security_check,
                embeddings=embeddings,
                processing_time=processing_time,
                status="success",
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"이미지 분석 실패: {str(e)}")
            errors.append(str(e))
            
            return ComprehensiveImageAnalysis(
                file_info=self._get_file_info(image_path) if os.path.exists(image_path) else {},
                image_type="error",
                ocr_result=None,
                vlm_analysis=None,
                security_check={},
                embeddings=None,
                processing_time=(datetime.now() - start_time).total_seconds(),
                status="error",
                errors=errors
            )
            
    def analyze_batch(self,
                     image_paths: List[str],
                     mode: ProcessingMode = ProcessingMode.STANDARD,
                     max_workers: int = 4) -> List[ComprehensiveImageAnalysis]:
        """
        배치 이미지 분석 (동기)
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            mode: 처리 모드
            max_workers: 최대 워커 수
            
        Returns:
            분석 결과 리스트
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 비동기 태스크를 동기로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            futures = []
            for image_path in image_paths:
                future = executor.submit(
                    loop.run_until_complete,
                    self.analyze_image(image_path, mode)
                )
                futures.append(future)
                
            # 결과 수집
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"배치 처리 중 오류: {str(e)}")
                    
        return results
        
    async def _process_ocr_async(self, image_path: str) -> Dict[str, Any]:
        """OCR 비동기 처리"""
        loop = asyncio.get_event_loop()
        
        # OCR을 별도 스레드에서 실행
        ocr_result = await loop.run_in_executor(
            None,
            self.ocr_engine.extract_text,
            image_path,
            True,  # preprocess
            True   # detect_personal_info
        )
        
        # 문서 유형별 추가 처리
        doc_analysis = await loop.run_in_executor(
            None,
            self.doc_processor.process_official_document,
            image_path
        )
        
        return {
            'text': ocr_result.text,
            'confidence': ocr_result.confidence,
            'personal_info_detected': ocr_result.personal_info_detected,
            'redacted_text': ocr_result.redacted_text,
            'document_type': doc_analysis.get('document_type'),
            'structured_data': doc_analysis.get('structured_data')
        }
        
    async def _process_vlm_async(self, image_path: str) -> Dict[str, Any]:
        """VLM 비동기 처리"""
        loop = asyncio.get_event_loop()
        
        # VLM 분석 실행
        vlm_result = await loop.run_in_executor(
            None,
            self.vlm_processor.process_image,
            image_path,
            True,  # generate_caption
            True   # extract_features
        )
        
        # 도로공사 특화 분석 (필요시)
        korea_analysis = None
        if vlm_result.image_type == ImageType.ROAD_DAMAGE:
            korea_analysis = await loop.run_in_executor(
                None,
                self.korea_analyzer.analyze_road_damage,
                image_path
            )
        elif vlm_result.image_type in [ImageType.TRAFFIC_SIGN, ImageType.FIELD_PHOTO]:
            korea_analysis = await loop.run_in_executor(
                None,
                self.korea_analyzer.analyze_traffic_infrastructure,
                image_path
            )
            
        return {
            'image_type': vlm_result.image_type.value,
            'caption': vlm_result.caption,
            'detected_objects': vlm_result.detected_objects,
            'confidence': vlm_result.confidence_score,
            'korea_analysis': korea_analysis
        }
        
    async def _security_check_async(self, 
                                   image_path: str,
                                   ocr_result: Optional[Dict]) -> Dict[str, Any]:
        """보안 검사 비동기 처리"""
        security_issues = []
        
        # 개인정보 검사
        if ocr_result and ocr_result.get('personal_info_detected'):
            security_issues.append({
                'type': 'personal_info',
                'severity': 'high',
                'action': 'redacted'
            })
            
        # 파일 크기 검사
        file_size = os.path.getsize(image_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            security_issues.append({
                'type': 'large_file',
                'severity': 'medium',
                'size_mb': file_size / (1024 * 1024)
            })
            
        # 파일 확장자 검사
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf'}
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in allowed_extensions:
            security_issues.append({
                'type': 'invalid_extension',
                'severity': 'high',
                'extension': file_ext
            })
            
        return {
            'passed': len(security_issues) == 0,
            'issues': security_issues,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _check_duplicate(self, image_path: str) -> bool:
        """중복 이미지 검사"""
        # 파일 해시 생성
        file_hash = self._calculate_file_hash(image_path)
        
        # 이미지 내용 해시 (perceptual hash)
        image = Image.open(image_path)
        content_hash = self._calculate_image_hash(image)
        
        # 중복 확인
        is_duplicate = (file_hash in self.processed_hashes or 
                       content_hash in self.processed_hashes)
        
        if not is_duplicate:
            self.processed_hashes.add(file_hash)
            self.processed_hashes.add(content_hash)
            
        return is_duplicate
        
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def _calculate_image_hash(self, image: Image.Image, hash_size: int = 8) -> str:
        """이미지 perceptual hash 계산"""
        # 이미지 리사이즈
        image = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        
        # 그레이스케일 변환
        image = image.convert('L')
        
        # 픽셀 값 가져오기
        pixels = list(image.getdata())
        
        # 평균 계산
        avg = sum(pixels) / len(pixels)
        
        # 해시 생성
        bits = ''.join(['1' if pixel > avg else '0' for pixel in pixels])
        
        # 16진수로 변환
        hex_hash = hex(int(bits, 2))[2:].rjust(hash_size * hash_size // 4, '0')
        
        return hex_hash
        
    def _generate_embeddings(self, image: Image.Image) -> Optional[np.ndarray]:
        """이미지 임베딩 생성"""
        if self.enable_vlm:
            return self.vlm_processor.extract_image_embeddings(image)
        return None
        
    def _simple_classify(self, image: Image.Image) -> str:
        """간단한 이미지 분류"""
        # 이미지 특성 기반 간단 분류
        width, height = image.size
        aspect_ratio = width / height
        
        # 문서 형태 (A4 비율 근처)
        if 0.7 < aspect_ratio < 0.8 or 1.3 < aspect_ratio < 1.5:
            return "document"
            
        # 파노라마/위성 이미지
        if aspect_ratio > 2 or aspect_ratio < 0.5:
            return "panorama"
            
        return "photo"
        
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 정보 추출"""
        stat = os.stat(file_path)
        
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size_bytes': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': Path(file_path).suffix.lower()
        }
        
    def _save_hash(self, image_path: str):
        """처리된 이미지 해시 저장"""
        cache_file = self.cache_dir / "processed_hashes.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(list(self.processed_hashes), f)
        except Exception as e:
            logger.error(f"해시 저장 실패: {str(e)}")
            
    def _load_hash_cache(self):
        """해시 캐시 로드"""
        cache_file = self.cache_dir / "processed_hashes.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.processed_hashes = set(json.load(f))
            except Exception as e:
                logger.error(f"해시 캐시 로드 실패: {str(e)}")
                self.processed_hashes = set()
                
    def export_results(self, 
                      results: List[ComprehensiveImageAnalysis],
                      output_path: str,
                      format: str = 'json'):
        """
        분석 결과 내보내기
        
        Args:
            results: 분석 결과 리스트
            output_path: 출력 파일 경로
            format: 출력 형식 (json, csv, html)
        """
        if format == 'json':
            self._export_json(results, output_path)
        elif format == 'csv':
            self._export_csv(results, output_path)
        elif format == 'html':
            self._export_html(results, output_path)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
            
    def _export_json(self, results: List[ComprehensiveImageAnalysis], output_path: str):
        """JSON 형식으로 내보내기"""
        data = []
        for result in results:
            # numpy 배열은 리스트로 변환
            result_dict = asdict(result)
            if result_dict['embeddings'] is not None:
                result_dict['embeddings'] = result_dict['embeddings'].tolist()
            data.append(result_dict)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _export_csv(self, results: List[ComprehensiveImageAnalysis], output_path: str):
        """CSV 형식으로 내보내기"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if not results:
                return
                
            # 헤더 작성
            fieldnames = ['file_name', 'image_type', 'status', 'processing_time',
                         'has_text', 'has_personal_info', 'security_passed']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # 데이터 작성
            for result in results:
                row = {
                    'file_name': result.file_info.get('name', ''),
                    'image_type': result.image_type,
                    'status': result.status,
                    'processing_time': result.processing_time,
                    'has_text': bool(result.ocr_result),
                    'has_personal_info': result.ocr_result.get('personal_info_detected', False) if result.ocr_result else False,
                    'security_passed': result.security_check.get('passed', True)
                }
                writer.writerow(row)
                
    def _export_html(self, results: List[ComprehensiveImageAnalysis], output_path: str):
        """HTML 형식으로 내보내기"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ex-GPT 이미지 분석 결과</title>
            <style>
                body { font-family: 'Malgun Gothic', sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .success { color: green; }
                .error { color: red; }
                .warning { color: orange; }
            </style>
        </head>
        <body>
            <h1>ex-GPT 이미지 분석 결과</h1>
            <p>총 {count}개 이미지 처리</p>
            <table>
                <tr>
                    <th>파일명</th>
                    <th>유형</th>
                    <th>상태</th>
                    <th>처리시간</th>
                    <th>텍스트</th>
                    <th>개인정보</th>
                    <th>보안</th>
                </tr>
        """.format(count=len(results))
        
        for result in results:
            status_class = 'success' if result.status == 'success' else 'error'
            has_text = '✓' if result.ocr_result else '-'
            has_pi = '⚠️' if result.ocr_result and result.ocr_result.get('personal_info_detected') else '✓'
            security = '✓' if result.security_check.get('passed', True) else '⚠️'
            
            html_content += f"""
                <tr>
                    <td>{result.file_info.get('name', '')}</td>
                    <td>{result.image_type}</td>
                    <td class="{status_class}">{result.status}</td>
                    <td>{result.processing_time:.2f}s</td>
                    <td>{has_text}</td>
                    <td>{has_pi}</td>
                    <td>{security}</td>
                </tr>
            """
            
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


# 테스트 코드
if __name__ == "__main__":
    # 통합 분석기 초기화
    analyzer = IntegratedImageAnalyzer(
        enable_vlm=True,
        enable_ocr=True,
        enable_security=True
    )
    
    print("ex-GPT 통합 이미지 분석기 준비 완료")
    print("\n지원 기능:")
    print("1. 멀티모달 이미지 분석 (VLM)")
    print("2. 한국어 OCR 및 문서 구조화")
    print("3. 개인정보 자동 검출 및 마스킹")
    print("4. 중복 이미지 필터링")
    print("5. 보안 검사")
    print("6. 배치 처리")
    print("7. 다양한 형식 내보내기 (JSON/CSV/HTML)")
    
    # 비동기 테스트 예시
    async def test_analyze():
        # 테스트 이미지 경로
        test_image = "test_image.jpg"
        
        if os.path.exists(test_image):
            result = await analyzer.analyze_image(test_image, ProcessingMode.DEEP)
            print(f"\n분석 결과:")
            print(f"- 이미지 유형: {result.image_type}")
            print(f"- 처리 시간: {result.processing_time:.2f}초")
            print(f"- 상태: {result.status}")
            
    # asyncio.run(test_analyze())
