"""
멀티모달 백엔드 파일 업로드 API 라우터
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from loguru import logger
# import aiofiles  # 임시 주석 처리

# from app.core.config import get_settings  # 임시 주석
# from app.services.cache_service import get_cache_manager  # 임시 주석

router = APIRouter(prefix="/files", tags=["파일 관리"])
# settings = get_settings()  # 임시 주석


class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""
    file_id: str = Field(..., description="파일 고유 ID")
    filename: str = Field(..., description="원본 파일명")
    file_path: str = Field(..., description="저장된 파일 경로")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    content_type: str = Field(..., description="파일 콘텐츠 타입")
    upload_time: datetime = Field(..., description="업로드 시간")
    metadata: Dict[str, Union[str, int, float]] = Field(default_factory=dict, description="파일 메타데이터")


class FileInfo(BaseModel):
    """파일 정보"""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_time: datetime
    metadata: Dict[str, Union[str, int, float]] = Field(default_factory=dict)


def validate_file_extension(filename: str) -> bool:
    """파일 확장자 검증"""
    if not hasattr(settings, 'ALLOWED_EXTENSIONS'):
        return True
    
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in settings.ALLOWED_EXTENSIONS


def get_file_path(file_id: str, filename: str) -> str:
    """파일 저장 경로 생성"""
    # 날짜별 디렉토리 구조 생성
    today = datetime.now().strftime("%Y/%m/%d")
    upload_dir = os.path.join(settings.UPLOAD_PATH, today)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 고유한 파일명 생성
    file_ext = os.path.splitext(filename)[1]
    unique_filename = f"{file_id}{file_ext}"
    
    return os.path.join(upload_dir, unique_filename)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """
    파일 업로드
    
    Args:
        file: 업로드할 파일
        description: 파일 설명
        
    Returns:
        업로드 결과
    """
    try:
        # 파일 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 허용된 확장자: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # 파일 크기 확인
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # 고유 파일 ID 생성
        file_id = str(uuid.uuid4())
        
        # 파일 저장 경로 생성
        file_path = get_file_path(file_id, file.filename)
        
        # 파일 저장
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 메타데이터 생성
        metadata = {
            "description": description or "",
            "original_name": file.filename,
            "content_type": file.content_type or "application/octet-stream"
        }
        
        # 파일 정보 생성
        file_info = FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            upload_time=datetime.now(),
            metadata=metadata
        )
        
        # 캐시에 파일 정보 저장
        cache_manager = get_cache_manager()
        await cache_manager.set(f"file_info:{file_id}", file_info.dict(), ttl=86400)  # 24시간
        
        logger.info(f"파일 업로드 완료: {file.filename} -> {file_path}")
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 업로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.get("/info/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """
    파일 정보 조회
    
    Args:
        file_id: 파일 ID
        
    Returns:
        파일 정보
    """
    try:
        cache_manager = get_cache_manager()
        file_info = await cache_manager.get(f"file_info:{file_id}")
        
        if not file_info:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        return FileInfo(**file_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 정보 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    파일 다운로드
    
    Args:
        file_id: 파일 ID
        
    Returns:
        파일 응답
    """
    try:
        # 파일 정보 조회
        cache_manager = get_cache_manager()
        file_info = await cache_manager.get(f"file_info:{file_id}")
        
        if not file_info:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        file_path = file_info["file_path"]
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
        
        return FileResponse(
            path=file_path,
            filename=file_info["filename"],
            media_type=file_info["content_type"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_id}")
async def delete_file(file_id: str):
    """
    파일 삭제
    
    Args:
        file_id: 파일 ID
        
    Returns:
        삭제 결과
    """
    try:
        # 파일 정보 조회
        cache_manager = get_cache_manager()
        file_info = await cache_manager.get(f"file_info:{file_id}")
        
        if not file_info:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        file_path = file_info["file_path"]
        
        # 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 캐시에서 파일 정보 삭제
        await cache_manager.delete(f"file_info:{file_id}")
        
        logger.info(f"파일 삭제 완료: {file_path}")
        return {"message": "파일이 성공적으로 삭제되었습니다.", "file_id": file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 삭제 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[FileInfo])
async def list_files(
    limit: int = 50,
    offset: int = 0
):
    """
    업로드된 파일 목록 조회
    
    Args:
        limit: 조회할 파일 수
        offset: 시작 위치
        
    Returns:
        파일 목록
    """
    try:
        # 실제 구현에서는 데이터베이스에서 조회해야 함
        # 여기서는 캐시에서 파일 정보들을 조회하는 간단한 예시
        cache_manager = get_cache_manager()
        
        # 캐시에서 파일 정보들을 조회 (실제로는 DB 쿼리 필요)
        # 이는 데모용 구현이며, 실제로는 데이터베이스 쿼리가 필요합니다
        files = []
        
        # TODO: 데이터베이스에서 파일 목록 조회 로직 구현
        logger.warning("파일 목록 조회는 데이터베이스 구현이 필요합니다.")
        
        return files
        
    except Exception as e:
        logger.error(f"파일 목록 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_upload_stats():
    """
    업로드 통계 조회
    
    Returns:
        업로드 통계
    """
    try:
        # 업로드 디렉토리 통계
        upload_dir = settings.UPLOAD_PATH
        total_files = 0
        total_size = 0
        
        if os.path.exists(upload_dir):
            for root, dirs, files in os.walk(upload_dir):
                total_files += len(files)
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        
        # 캐시 통계
        cache_manager = get_cache_manager()
        cache_stats = await cache_manager.get_stats()
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "upload_directory": upload_dir,
            "cache_stats": cache_stats,
            "allowed_extensions": getattr(settings, 'ALLOWED_EXTENSIONS', []),
            "max_file_size_bytes": settings.MAX_FILE_SIZE
        }
        
    except Exception as e:
        logger.error(f"업로드 통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
