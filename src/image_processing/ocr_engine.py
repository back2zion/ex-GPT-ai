"""
OCR Engine for ex-GPT System
문서 이미지에서 텍스트 추출 및 구조화
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import pytesseract
import easyocr
from dataclasses import dataclass
import logging
import re
from datetime import datetime
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR 처리 결과"""
    text: str
    confidence: float
    language: str
    bounding_boxes: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    personal_info_detected: bool = False
    redacted_text: Optional[str] = None


class KoreanOCREngine:
    """
    한국어 특화 OCR 엔진
    EasyOCR과 Tesseract를 결합한 하이브리드 방식
    """
    
    def __init__(self, use_gpu: bool = True):
        """
        OCR 엔진 초기화
        
        Args:
            use_gpu: GPU 사용 여부
        """
        self.use_gpu = use_gpu
        
        # EasyOCR 리더 초기화 (한국어, 영어)
        logger.info("EasyOCR 초기화 중...")
        self.reader = easyocr.Reader(['ko', 'en'], gpu=use_gpu)
        
        # Tesseract 경로 설정 (Windows)
        if os.name == 'nt':
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                
        # 개인정보 패턴 정규식
        self.personal_info_patterns = {
            'phone': r'\d{3}-\d{3,4}-\d{4}',
            'mobile': r'01[0-9]-\d{3,4}-\d{4}',
            'rrn': r'\d{6}-[1-4]\d{6}',  # 주민등록번호
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'card': r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
            'account': r'\d{3,6}-\d{2,6}-\d{6,}',  # 계좌번호
            'car_number': r'\d{2,3}[가-힣]\d{4}'  # 차량번호
        }
        
        logger.info("OCR 엔진 초기화 완료")
        
    def extract_text(self, 
                     image_path: str,
                     preprocess: bool = True,
                     detect_personal_info: bool = True) -> OCRResult:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            preprocess: 전처리 수행 여부
            detect_personal_info: 개인정보 검출 여부
            
        Returns:
            OCRResult 객체
        """
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
            
        # 전처리
        if preprocess:
            image = self._preprocess_image(image)
            
        # EasyOCR로 텍스트 추출
        ocr_results = self.reader.readtext(image)
        
        # 결과 정리
        full_text = []
        bounding_boxes = []
        total_confidence = 0
        
        for bbox, text, confidence in ocr_results:
            full_text.append(text)
            bounding_boxes.append({
                'bbox': bbox,
                'text': text,
                'confidence': confidence
            })
            total_confidence += confidence
            
        extracted_text = ' '.join(full_text)
        avg_confidence = total_confidence / len(ocr_results) if ocr_results else 0
        
        # 개인정보 검출 및 마스킹
        personal_info_detected = False
        redacted_text = None
        
        if detect_personal_info:
            personal_info_detected, redacted_text = self._detect_and_redact_personal_info(
                extracted_text
            )
            
        # 메타데이터 생성
        metadata = self._generate_metadata(image_path, image, ocr_results)
        
        return OCRResult(
            text=extracted_text,
            confidence=avg_confidence,
            language='ko',
            bounding_boxes=bounding_boxes,
            metadata=metadata,
            personal_info_detected=personal_info_detected,
            redacted_text=redacted_text
        )
        
    def extract_structured_text(self, image_path: str) -> Dict[str, Any]:
        """
        구조화된 텍스트 추출 (테이블, 양식 등)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            구조화된 데이터 딕셔너리
        """
        image = cv2.imread(image_path)
        
        # 테이블 검출
        tables = self._detect_tables(image)
        
        # 양식 필드 검출
        form_fields = self._detect_form_fields(image)
        
        # 각 영역별 OCR 수행
        structured_data = {
            'tables': [],
            'form_fields': {},
            'paragraphs': []
        }
        
        # 테이블 데이터 추출
        for table in tables:
            table_data = self._extract_table_data(image, table)
            structured_data['tables'].append(table_data)
            
        # 양식 필드 데이터 추출
        for field_name, field_bbox in form_fields.items():
            field_text = self._extract_region_text(image, field_bbox)
            structured_data['form_fields'][field_name] = field_text
            
        # 일반 문단 추출
        paragraphs = self._extract_paragraphs(image)
        structured_data['paragraphs'] = paragraphs
        
        return structured_data
        
    def process_document_batch(self, 
                              image_paths: List[str],
                              output_format: str = 'json') -> List[OCRResult]:
        """
        문서 배치 처리
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            output_format: 출력 형식 (json, text, csv)
            
        Returns:
            OCRResult 리스트
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"처리 중: {i+1}/{len(image_paths)} - {image_path}")
            
            try:
                result = self.extract_text(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"처리 실패: {image_path} - {str(e)}")
                continue
                
        # 출력 형식에 따른 변환
        if output_format == 'json':
            return self._to_json(results)
        elif output_format == 'text':
            return self._to_text(results)
        else:
            return results
            
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        이미지 전처리
        
        Args:
            image: 원본 이미지
            
        Returns:
            전처리된 이미지
        """
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 이진화 (Otsu's method)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 기울기 보정
        corrected = self._deskew(binary)
        
        return corrected
        
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        이미지 기울기 보정
        
        Args:
            image: 입력 이미지
            
        Returns:
            기울기 보정된 이미지
        """
        # 엣지 검출
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # 허프 변환으로 선 검출
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            # 각도 계산
            angles = []
            for rho, theta in lines[:, 0]:
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)
                    
            if angles:
                # 중간값 각도로 회전
                median_angle = np.median(angles)
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), 
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
                return rotated
                
        return image
        
    def _detect_and_redact_personal_info(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        개인정보 검출 및 마스킹
        
        Args:
            text: 원본 텍스트
            
        Returns:
            (개인정보 검출 여부, 마스킹된 텍스트)
        """
        detected = False
        redacted = text
        
        for info_type, pattern in self.personal_info_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected = True
                # 마스킹 처리
                masked = '*' * len(match.group())
                redacted = redacted.replace(match.group(), masked)
                logger.warning(f"개인정보 검출: {info_type} - 위치: {match.span()}")
                
        return detected, redacted if detected else None
        
    def _detect_tables(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        테이블 영역 검출
        
        Args:
            image: 입력 이미지
            
        Returns:
            테이블 영역 좌표 리스트 [(x, y, w, h), ...]
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # 형태학적 연산으로 테이블 구조 강조
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        # 수평선 검출
        horizontal = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 수직선 검출
        vertical = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # 테이블 그리드 생성
        table_grid = cv2.add(horizontal, vertical)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(table_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 최소 크기 필터링
            if w > 100 and h > 100:
                tables.append((x, y, w, h))
                
        return tables
        
    def _detect_form_fields(self, image: np.ndarray) -> Dict[str, Tuple[int, int, int, int]]:
        """
        양식 필드 검출
        
        Args:
            image: 입력 이미지
            
        Returns:
            필드명과 좌표 딕셔너리
        """
        # 간단한 휴리스틱 기반 필드 검출
        # 실제로는 딥러닝 모델 사용 권장
        fields = {}
        
        # 예시 필드 위치 (실제로는 동적 검출 필요)
        common_fields = {
            'title': (50, 50, 500, 100),
            'date': (550, 50, 200, 50),
            'content': (50, 150, 700, 400),
            'signature': (50, 600, 200, 100)
        }
        
        return common_fields
        
    def _extract_table_data(self, 
                           image: np.ndarray, 
                           table_bbox: Tuple[int, int, int, int]) -> List[List[str]]:
        """
        테이블 데이터 추출
        
        Args:
            image: 입력 이미지
            table_bbox: 테이블 영역 좌표
            
        Returns:
            2차원 테이블 데이터
        """
        x, y, w, h = table_bbox
        table_image = image[y:y+h, x:x+w]
        
        # 셀 분할 (간단한 그리드 기반)
        rows = []
        row_height = h // 10  # 예시: 10행으로 가정
        col_width = w // 5   # 예시: 5열로 가정
        
        for i in range(10):
            row = []
            for j in range(5):
                cell_y = i * row_height
                cell_x = j * col_width
                cell = table_image[cell_y:cell_y+row_height, cell_x:cell_x+col_width]
                
                # 셀에서 텍스트 추출
                cell_text = self._extract_region_text(image, 
                                                      (x+cell_x, y+cell_y, col_width, row_height))
                row.append(cell_text)
            rows.append(row)
            
        return rows
        
    def _extract_region_text(self, 
                            image: np.ndarray, 
                            bbox: Tuple[int, int, int, int]) -> str:
        """
        특정 영역에서 텍스트 추출
        
        Args:
            image: 입력 이미지
            bbox: 영역 좌표 (x, y, w, h)
            
        Returns:
            추출된 텍스트
        """
        x, y, w, h = bbox
        region = image[y:y+h, x:x+w]
        
        # EasyOCR로 텍스트 추출
        try:
            results = self.reader.readtext(region)
            texts = [text for _, text, _ in results]
            return ' '.join(texts)
        except:
            return ""
            
    def _extract_paragraphs(self, image: np.ndarray) -> List[str]:
        """
        문단 단위 텍스트 추출
        
        Args:
            image: 입력 이미지
            
        Returns:
            문단 리스트
        """
        # 전체 텍스트 추출
        results = self.reader.readtext(image)
        
        # Y 좌표 기준 정렬
        results.sort(key=lambda x: x[0][0][1])
        
        # 문단 구분 (Y 좌표 차이 기준)
        paragraphs = []
        current_paragraph = []
        prev_y = 0
        
        for bbox, text, _ in results:
            current_y = bbox[0][1]
            
            # 줄 간격이 크면 새 문단
            if prev_y > 0 and current_y - prev_y > 50:
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                    
            current_paragraph.append(text)
            prev_y = bbox[2][1]  # 하단 Y 좌표
            
        # 마지막 문단 추가
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
            
        return paragraphs
        
    def _generate_metadata(self, 
                          image_path: str, 
                          image: np.ndarray,
                          ocr_results: List) -> Dict[str, Any]:
        """
        메타데이터 생성
        
        Args:
            image_path: 이미지 파일 경로
            image: 이미지 배열
            ocr_results: OCR 결과
            
        Returns:
            메타데이터 딕셔너리
        """
        height, width = image.shape[:2]
        
        return {
            'file_path': image_path,
            'file_name': os.path.basename(image_path),
            'image_size': (width, height),
            'total_text_regions': len(ocr_results),
            'processing_timestamp': datetime.now().isoformat(),
            'ocr_engine': 'EasyOCR',
            'languages': ['ko', 'en']
        }
        
    def _to_json(self, results: List[OCRResult]) -> str:
        """결과를 JSON으로 변환"""
        data = []
        for result in results:
            data.append({
                'text': result.text,
                'confidence': result.confidence,
                'language': result.language,
                'personal_info_detected': result.personal_info_detected,
                'redacted_text': result.redacted_text,
                'metadata': result.metadata
            })
        return json.dumps(data, ensure_ascii=False, indent=2)
        
    def _to_text(self, results: List[OCRResult]) -> str:
        """결과를 텍스트로 변환"""
        texts = []
        for result in results:
            texts.append(f"=== {result.metadata.get('file_name', 'Unknown')} ===")
            texts.append(result.redacted_text if result.personal_info_detected else result.text)
            texts.append(f"신뢰도: {result.confidence:.2f}")
            texts.append("")
        return '\n'.join(texts)


class DocumentProcessor:
    """
    문서 이미지 전문 처리기
    한국도로공사 공문서 특화
    """
    
    def __init__(self):
        self.ocr_engine = KoreanOCREngine()
        
        # 문서 템플릿 패턴
        self.document_patterns = {
            '공문': {
                'header': ['문서번호', '시행일자', '수신', '참조'],
                'footer': ['담당자', '전화번호', '팩스']
            },
            '보고서': {
                'header': ['제목', '작성일', '작성자', '부서'],
                'sections': ['개요', '내용', '결론', '첨부']
            },
            '회의록': {
                'header': ['회의명', '일시', '장소', '참석자'],
                'content': ['안건', '논의사항', '결정사항', '향후계획']
            }
        }
        
    def process_official_document(self, image_path: str) -> Dict[str, Any]:
        """
        공문서 처리
        
        Args:
            image_path: 문서 이미지 경로
            
        Returns:
            구조화된 문서 데이터
        """
        # OCR 수행
        ocr_result = self.ocr_engine.extract_text(image_path)
        
        # 문서 유형 판별
        doc_type = self._identify_document_type(ocr_result.text)
        
        # 구조화된 데이터 추출
        structured_data = self._extract_structured_data(ocr_result.text, doc_type)
        
        # 개인정보 처리
        if ocr_result.personal_info_detected:
            structured_data['has_personal_info'] = True
            structured_data['redacted_content'] = ocr_result.redacted_text
            
        return {
            'document_type': doc_type,
            'structured_data': structured_data,
            'raw_text': ocr_result.text,
            'confidence': ocr_result.confidence,
            'metadata': ocr_result.metadata
        }
        
    def _identify_document_type(self, text: str) -> str:
        """문서 유형 식별"""
        for doc_type, patterns in self.document_patterns.items():
            match_count = 0
            for section, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in text:
                        match_count += 1
                        
            if match_count >= 3:
                return doc_type
                
        return '일반문서'
        
    def _extract_structured_data(self, text: str, doc_type: str) -> Dict[str, Any]:
        """구조화된 데이터 추출"""
        structured = {}
        
        if doc_type in self.document_patterns:
            patterns = self.document_patterns[doc_type]
            
            for section, keywords in patterns.items():
                structured[section] = {}
                for keyword in keywords:
                    # 키워드 뒤의 내용 추출
                    pattern = f"{keyword}\\s*[:：]\\s*([^\\n]+)"
                    match = re.search(pattern, text)
                    if match:
                        structured[section][keyword] = match.group(1).strip()
                        
        return structured


# 테스트 코드
if __name__ == "__main__":
    # OCR 엔진 초기화
    ocr_engine = KoreanOCREngine(use_gpu=False)
    
    # 문서 처리기 초기화
    doc_processor = DocumentProcessor()
    
    print("ex-GPT OCR 엔진 준비 완료")
    print("지원 기능:")
    print("1. 한국어/영어 텍스트 추출")
    print("2. 개인정보 자동 검출 및 마스킹")
    print("3. 테이블/양식 구조 인식")
    print("4. 공문서 자동 분류 및 구조화")
