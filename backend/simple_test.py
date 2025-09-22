"""
간단한 테스트 백엔드 서버
ex-GPT 프론트엔드 개발용 목 서버
"""

import os
import random
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

app = FastAPI(
    title="ex-GPT Test Backend",
    description="테스트용 백엔드 서버",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 목 이미지 데이터 생성기
def generate_mock_images(query: str, limit: int = 20):
    """테스트용 목 이미지 데이터 생성"""
    images = []
    locations = [
        "경부고속도로 서울IC", "중부고속도로 하남IC", 
        "영동고속도로 강릉IC", "서해안고속도로 목포IC",
        "중앙고속도로 춘천IC", "남해고속도로 부산IC"
    ]
    
    # 실제 이미지 URL 사용 (placeholder 이미지)
    image_urls = [
        "https://via.placeholder.com/400x300/0288d1/ffffff?text=CCTV+해무+이미지",
        "https://via.placeholder.com/400x300/1976d2/ffffff?text=고속도로+안개",
        "https://via.placeholder.com/400x300/0277bd/ffffff?text=시정거리+50m",
        "https://via.placeholder.com/400x300/01579b/ffffff?text=야간+CCTV",
        "https://via.placeholder.com/400x300/006064/ffffff?text=강우+상황",
        "https://picsum.photos/400/300?random=",  # 랜덤 이미지
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=400&h=300&fit=crop",  # 안개 이미지
        "https://images.unsplash.com/photo-1487621167305-5d248087c724?w=400&h=300&fit=crop",  # 도로 이미지
    ]
    
    for i in range(limit):
        # 이미지 URL 순환 사용
        image_url = image_urls[i % len(image_urls)]
        if "picsum" in image_url:
            # 랜덤 이미지를 위해 파라미터 추가
            image_url = f"https://picsum.photos/400/300?random={i}"
        
        images.append({
            "id": f"img_{i+1}",
            "path": f"/images/test_{i+1}.jpg",
            "url": image_url,  # 실제 접근 가능한 URL
            "thumbnail": image_url,  # 썸네일도 같은 URL
            "location": random.choice(locations),
            "description": f"{query} 관련 이미지 {i+1}",
            "timestamp": datetime.now().isoformat(),
            "similarity_score": round(random.uniform(0.6, 1.0), 3),
            "similarity": round(random.uniform(0.6, 1.0), 3),  # 프론트엔드 호환성
            "filename": f"CCTV_{random.randint(1000, 9999)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            "metadata": {
                "weather": random.choice(["해무", "안개", "맑음", "흐림"]),
                "visibility": random.choice(["50m", "100m", "200m", "500m"]),
                "camera_id": f"CAM_{random.randint(1000, 9999)}",
                "highway": random.choice(["경부", "중부", "영동", "서해안", "중앙", "남해"]),
                "direction": random.choice(["상행", "하행"]),
                "time_period": random.choice(["새벽", "오전", "오후", "저녁", "심야"])
            }
        })
    
    return images

# 요청 모델들
class ImageSearchRequest(BaseModel):
    query: str
    limit: int = 20
    offset: int = 0
    filters: Optional[Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]] = None
    history: List[Dict[str, str]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000

# API 엔드포인트들
@app.get("/")
async def root():
    return {
        "service": "ex-GPT Test Backend",
        "version": "1.0.0",
        "status": "running",
        "port": 8201
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "image_search": "available",
            "chat": "available",
            "multimodal": "available"
        }
    }

@app.post("/api/v1/search/images")
async def search_images(request: ImageSearchRequest):
    """이미지 검색 API (테스트용)"""
    try:
        images = generate_mock_images(request.query, request.limit)
        
        return {
            "success": True,
            "query": request.query,
            "images": images,
            "total_count": len(images),
            "has_more": False,
            "search_time_ms": random.randint(100, 500),
            "backend": "test"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """채팅 API (테스트용)"""
    try:
        messages = request.messages or request.history or []
        last_message = messages[-1]["content"] if messages else "안녕하세요"
        
        response = {
            "response": f"테스트 응답입니다: '{last_message}'에 대한 답변입니다. ex-GPT 시스템이 정상 작동 중입니다.",
            "sources": [],
            "suggested_questions": [
                "해무 발생 CCTV 이미지를 보여주세요",
                "최근 고속도로 날씨 상황은?",
                "시스템 상태를 확인해주세요"
            ],
            "metadata": {
                "response_time_ms": random.randint(100, 500),
                "model": "test-model"
            },
            "session_id": request.session_id or "test_session",
            "message_id": f"msg_{random.randint(1000, 9999)}"
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/multimodal")
async def chat_multimodal(request: ChatRequest):
    """멀티모달 채팅 API (테스트용)"""
    try:
        messages = request.messages or request.history or []
        last_message = messages[-1]["content"] if messages else "안녕하세요"
        
        response = {
            "response": f"[멀티모달] 테스트 응답입니다: '{last_message}'에 대한 답변입니다.",
            "type": "multimodal",
            "sources": [],
            "metadata": {
                "response_time_ms": random.randint(100, 500),
                "model": "multimodal-test"
            },
            "session_id": request.session_id or "test_session",
            "message_id": f"msg_{random.randint(1000, 9999)}"
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def api_health():
    """API 헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("=" * 50)
    print("ex-GPT 테스트 백엔드 서버 시작")
    print("포트: 8201")
    print("API 문서: http://localhost:8201/docs")
    print("=" * 50)
    
    uvicorn.run(
        "simple_test:app",
        host="0.0.0.0",
        port=8201,
        reload=True,
        log_level="info"
    )
