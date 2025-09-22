"""
멀티모달 백엔드 API v1 라우터
"""

from fastapi import APIRouter

# from .files import router as files_router  # 임시 비활성화
# from .ocr import router as ocr_router  # 임시 비활성화
# from .stt import router as stt_router  # 임시 비활성화
from .cctv_search import router as cctv_router

api_router = APIRouter()

# 파일 관리 라우터 등록 (임시 비활성화)
# api_router.include_router(files_router)

# OCR 라우터 등록 (임시 비활성화)
# api_router.include_router(ocr_router)

# STT 라우터 등록 (임시 비활성화)
# api_router.include_router(stt_router)

# CCTV 이미지 검색 라우터 등록
api_router.include_router(cctv_router)

# 추가 라우터들 (필요시 확장)
# api_router.include_router(images_router)
# api_router.include_router(tts_router)
