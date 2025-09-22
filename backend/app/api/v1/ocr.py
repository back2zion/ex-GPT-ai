"""
멀티모달 백엔드 이미지 OCR API 라우터
"""

import time
import asyncio
from typing import Dict, List, Optional, Union
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel, Field
from loguru import logger
# import cv2  # 임시 주석
# import numpy as np  # 임시 주석
# from PIL import Image  # 임시 주석
# import pytesseract  # 임시 주석
# import easyocr  # 임시 주석
import io

# from app.core.config import get_settings  # 임시 주석
# from app.core.exceptions import OCRException, FileProcessingException, handle_file_errors  # 임시 주석
# from app.services.cache_service import get_cache_manager  # 임시 주석

router = APIRouter(prefix="/ocr", tags=["OCR 이미지 텍스트 인식"])
# settings = get_settings()  # 임시 주석


class OCRRequest(BaseModel):
    """OCR 요청"""
    languages: str = Field(default="kor+eng", description="인식할 언어 (kor, eng, kor+eng)")
    engine: str = Field(default="tesseract", description="OCR 엔진 (tesseract, easyocr)")
    preprocess: bool = Field(default=True, description="이미지 전처리 여부")
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="신뢰도 임계값")


class OCRResponse(BaseModel):
    """OCR 응답"""
    extracted_text: str = Field(..., description="추출된 텍스트")
    confidence_score: float = Field(..., description="평균 신뢰도")
    word_count: int = Field(..., description="단어 수")
    character_count: int = Field(..., description="문자 수")
    processing_time: float = Field(..., description="처리 시간(초)")
    engine: str = Field(..., description="사용된 OCR 엔진")
    languages: str = Field(..., description="인식 언어")
    bounding_boxes: List[Dict] = Field(default_factory=list, description="텍스트 위치 정보")
    metadata: Dict = Field(default_factory=dict, description="추가 메타데이터")


def preprocess_image(image_array: np.ndarray) -> np.ndarray:
    """이미지 전처리"""
    try:
        # 그레이스케일 변환
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # 노이즈 제거
        denoised = cv2.medianBlur(gray, 3)
        
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 이진화 (적응적 임계값)
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    except Exception as e:
        logger.warning(f"이미지 전처리 실패, 원본 사용: {e}")
        return image_array


async def perform_tesseract_ocr(
    image_array: np.ndarray, 
    languages: str, 
    confidence_threshold: float
) -> Dict:
    """Tesseract OCR 수행"""
    try:
        # 언어 코드 변환
        lang_map = {"kor": "kor", "eng": "eng", "kor+eng": "kor+eng"}
        tesseract_lang = lang_map.get(languages, "eng")
        
        # OCR 설정
        config = f"--oem 3 --psm 6 -l {tesseract_lang}"
        
        # 텍스트 추출
        extracted_text = pytesseract.image_to_string(image_array, config=config)
        
        # 상세 정보 추출 (단어별 신뢰도 포함)
        data = pytesseract.image_to_data(
            image_array, 
            config=config, 
            output_type=pytesseract.Output.DICT
        )
        
        # 신뢰도 필터링 및 바운딩 박스 생성
        bounding_boxes = []
        confidences = []
        
        for i in range(len(data['text'])):
            conf = int(data['conf'][i])
            text = data['text'][i].strip()
            
            if conf > confidence_threshold * 100 and text:
                bounding_boxes.append({
                    "text": text,
                    "confidence": conf / 100.0,
                    "bbox": {
                        "x": int(data['left'][i]),
                        "y": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i])
                    }
                })
                confidences.append(conf / 100.0)
        
        # 평균 신뢰도 계산
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "text": extracted_text.strip(),
            "confidence": avg_confidence,
            "bounding_boxes": bounding_boxes,
            "metadata": {
                "total_words": len([t for t in data['text'] if t.strip()]),
                "high_confidence_words": len(confidences)
            }
        }
        
    except Exception as e:
        raise OCRException(f"Tesseract OCR 실행 실패: {str(e)}", "tesseract")


async def perform_easyocr_ocr(
    image_array: np.ndarray, 
    languages: str, 
    confidence_threshold: float
) -> Dict:
    """EasyOCR 수행"""
    try:
        # 언어 코드 변환
        lang_map = {
            "kor": ["ko"],
            "eng": ["en"],
            "kor+eng": ["ko", "en"]
        }
        easyocr_langs = lang_map.get(languages, ["en"])
        
        # EasyOCR 리더 생성 (캐시됨)
        reader = easyocr.Reader(easyocr_langs, gpu=False)  # CPU 사용 (더 안정적)
        
        # OCR 수행
        results = reader.readtext(image_array)
        
        # 결과 처리
        bounding_boxes = []
        confidences = []
        extracted_texts = []
        
        for (bbox, text, conf) in results:
            if conf > confidence_threshold:
                # 바운딩 박스 좌표 변환
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                
                bounding_boxes.append({
                    "text": text,
                    "confidence": float(conf),
                    "bbox": {
                        "x": int(min(x_coords)),
                        "y": int(min(y_coords)),
                        "width": int(max(x_coords) - min(x_coords)),
                        "height": int(max(y_coords) - min(y_coords))
                    }
                })
                confidences.append(float(conf))
                extracted_texts.append(text)
        
        # 텍스트 결합
        full_text = " ".join(extracted_texts)
        
        # 평균 신뢰도 계산
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "text": full_text,
            "confidence": avg_confidence,
            "bounding_boxes": bounding_boxes,
            "metadata": {
                "total_detections": len(results),
                "high_confidence_detections": len(confidences)
            }
        }
        
    except Exception as e:
        raise OCRException(f"EasyOCR 실행 실패: {str(e)}", "easyocr")


@router.post("/extract", response_model=OCRResponse)
@handle_file_errors
async def extract_text_from_image(
    image: UploadFile = File(..., description="OCR을 수행할 이미지 파일"),
    languages: str = Form(default="kor+eng", description="인식할 언어"),
    engine: str = Form(default="tesseract", description="OCR 엔진"),
    preprocess: bool = Form(default=True, description="이미지 전처리 여부"),
    confidence_threshold: float = Form(default=0.6, description="신뢰도 임계값")
):
    """
    이미지에서 텍스트를 추출합니다.
    
    지원 형식: JPG, PNG, GIF, BMP, TIFF
    """
    start_time = time.time()
    
    try:
        # 파일 형식 검증
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=415,
                detail="이미지 파일만 지원됩니다."
            )
        
        # 캐시 키 생성
        cache_key = f"ocr:{hash(await image.read())}:{languages}:{engine}:{preprocess}:{confidence_threshold}"
        await image.seek(0)  # 파일 포인터 리셋
        
        cache_manager = get_cache_manager()
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.info(f"OCR 캐시 히트: {image.filename}")
            return OCRResponse(**cached_result)
        
        # 이미지 읽기
        image_bytes = await image.read()
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # PIL을 numpy 배열로 변환
        image_array = np.array(image_pil)
        
        # 이미지 전처리
        if preprocess:
            image_array = preprocess_image(image_array)
        
        # OCR 수행
        if engine == "tesseract":
            ocr_result = await perform_tesseract_ocr(image_array, languages, confidence_threshold)
        elif engine == "easyocr":
            ocr_result = await perform_easyocr_ocr(image_array, languages, confidence_threshold)
        else:
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 OCR 엔진입니다. (tesseract, easyocr만 지원)"
            )
        
        # 처리 시간 계산
        processing_time = time.time() - start_time
        
        # 응답 생성
        response = OCRResponse(
            extracted_text=ocr_result["text"],
            confidence_score=ocr_result["confidence"],
            word_count=len(ocr_result["text"].split()),
            character_count=len(ocr_result["text"]),
            processing_time=processing_time,
            engine=engine,
            languages=languages,
            bounding_boxes=ocr_result["bounding_boxes"],
            metadata={
                **ocr_result["metadata"],
                "image_size": f"{image_pil.width}x{image_pil.height}",
                "preprocessed": preprocess,
                "original_filename": image.filename
            }
        )
        
        # 캐시에 결과 저장
        await cache_manager.set(cache_key, response.dict(), ttl=3600)
        
        logger.info(
            f"OCR 완료 - {image.filename}: "
            f"엔진={engine}, 언어={languages}, "
            f"텍스트={len(ocr_result['text'])}자, "
            f"신뢰도={ocr_result['confidence']:.2%}, "
            f"처리시간={processing_time:.2f}s"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR 처리 중 오류: {str(e)}")
        raise OCRException(str(e), engine, image.filename)


@router.get("/engines")
async def get_available_engines():
    """
    사용 가능한 OCR 엔진 목록을 반환합니다.
    """
    engines = []
    
    # Tesseract 가용성 확인
    try:
        pytesseract.get_tesseract_version()
        engines.append({
            "name": "tesseract",
            "description": "Google Tesseract OCR",
            "languages": ["kor", "eng", "kor+eng"],
            "features": ["바운딩 박스", "신뢰도 점수", "전처리"]
        })
    except:
        logger.warning("Tesseract이 설치되지 않았습니다.")
    
    # EasyOCR 가용성 확인
    try:
        import easyocr
        engines.append({
            "name": "easyocr",
            "description": "EasyOCR (딥러닝 기반)",
            "languages": ["kor", "eng", "kor+eng"],
            "features": ["고정밀도", "다국어 지원", "자동 텍스트 감지"]
        })
    except ImportError:
        logger.warning("EasyOCR이 설치되지 않았습니다.")
    
    return {
        "engines": engines,
        "default_engine": "tesseract" if engines and engines[0]["name"] == "tesseract" else "easyocr",
        "supported_languages": ["kor", "eng", "kor+eng"]
    }


@router.post("/batch")
async def batch_ocr_processing(
    images: List[UploadFile] = File(..., description="OCR을 수행할 이미지 파일들"),
    languages: str = Form(default="kor+eng"),
    engine: str = Form(default="tesseract"),
    preprocess: bool = Form(default=True),
    confidence_threshold: float = Form(default=0.6)
):
    """
    여러 이미지에 대해 배치 OCR 처리를 수행합니다.
    """
    if len(images) > 10:
        raise HTTPException(
            status_code=400,
            detail="한 번에 최대 10개의 이미지만 처리할 수 있습니다."
        )
    
    results = []
    
    for image in images:
        try:
            # 개별 OCR 처리 (단일 처리 엔드포인트 재사용)
            result = await extract_text_from_image(
                image=image,
                languages=languages,
                engine=engine,
                preprocess=preprocess,
                confidence_threshold=confidence_threshold
            )
            
            results.append({
                "filename": image.filename,
                "status": "success",
                "result": result
            })
            
        except Exception as e:
            results.append({
                "filename": image.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_images": len(images),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }
