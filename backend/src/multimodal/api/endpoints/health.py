"""헬스 체크 API 엔드포인트"""

from fastapi import APIRouter, Request
import psutil
import torch

router = APIRouter()

@router.get("/")
async def health_check():
    """전체 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "ex-gpt-multimodal-backend",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(request: Request):
    """상세 서비스 상태 확인"""
    try:
        # 시스템 리소스
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # GPU 정보
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "memory_allocated": torch.cuda.memory_allocated(),
                "memory_cached": torch.cuda.memory_reserved()
            }
        
        # 서비스 상태
        services = {}
        if hasattr(request.app.state, 'whisper_service'):
            services['stt'] = await request.app.state.whisper_service.health_check()
        if hasattr(request.app.state, 'image_service'):
            services['image'] = await request.app.state.image_service.health_check()
        if hasattr(request.app.state, 'embedding_service'):
            services['embedding'] = await request.app.state.embedding_service.health_check()
        if hasattr(request.app.state, 'qdrant_service'):
            services['qdrant'] = await request.app.state.qdrant_service.health_check()
        
        return {
            "status": "healthy",
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available
            },
            "gpu": gpu_info,
            "services": services
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
