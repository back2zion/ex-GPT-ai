"""
Ollama 클라이언트 서비스
CPU 환경에서 qwen3:8b 모델을 활용한 멀티모달 AI 서비스
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import httpx
from loguru import logger
from app.core.config import settings

class OllamaClient:
    """Ollama API 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model_name = settings.OLLAMA_MODEL_NAME
        self.vlm_model = settings.OLLAMA_VLM_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self._client = None
        
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 인스턴스 반환"""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
        
    async def check_connection(self) -> bool:
        """Ollama 서버 연결 상태 확인"""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 연결 실패: {e}")
            return False
            
    async def list_models(self) -> List[Dict[str, Any]]:
        """사용 가능한 모델 목록 조회"""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            else:
                logger.error(f"모델 목록 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"모델 목록 조회 오류: {e}")
            return []
            
    async def pull_model(self, model_name: str) -> bool:
        """모델 다운로드"""
        try:
            client = await self.get_client()
            
            logger.info(f"모델 다운로드 시작: {model_name}")
            
            response = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=3600  # 1시간 타임아웃
            )
            
            if response.status_code == 200:
                logger.info(f"모델 다운로드 완료: {model_name}")
                return True
            else:
                logger.error(f"모델 다운로드 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"모델 다운로드 오류: {e}")
            return False
            
    async def generate_text(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """텍스트 생성"""
        try:
            client = await self.get_client()
            
            use_model = model or self.model_name
            
            payload = {
                "model": use_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 4096,  # CPU 환경에 맞게 컨텍스트 조정
                    "num_thread": settings.NUM_THREADS
                }
            }
            
            if system:
                payload["system"] = system
                
            logger.debug(f"텍스트 생성 요청: {use_model}")
            
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"텍스트 생성 실패: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"텍스트 생성 오류: {e}")
            return ""
            
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """채팅 완성"""
        try:
            client = await self.get_client()
            
            use_model = model or self.model_name
            
            payload = {
                "model": use_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 4096,
                    "num_thread": settings.NUM_THREADS
                }
            }
            
            logger.debug(f"채팅 완성 요청: {use_model}, 메시지 수: {len(messages)}")
            
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                logger.error(f"채팅 완성 실패: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"채팅 완성 오류: {e}")
            return ""
    
    async def analyze_image_with_vlm(
        self,
        image_path: str,
        prompt: str,
        model_name: Optional[str] = None
    ) -> str:
        """VLM을 사용하여 이미지 분석"""
        try:
            import base64
            from pathlib import Path

            client = await self.get_client()
            use_model = model_name or self.vlm_model

            # 이미지 파일을 base64로 인코딩
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"이미지 파일이 존재하지 않음: {image_path}")
                return ""

            with open(image_file, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Ollama VLM API 호출
            payload = {
                "model": use_model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500,
                    "num_ctx": 2048,
                    "num_thread": settings.NUM_THREADS
                }
            }

            logger.debug(f"VLM 이미지 분석 요청: {use_model}")

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.error(f"VLM 이미지 분석 실패: {response.status_code}, {response.text}")
                return ""

        except Exception as e:
            logger.error(f"VLM 이미지 분석 오류: {e}")
            return ""

    async def analyze_image_with_text(
        self,
        image_path: str,
        query: str,
        model: Optional[str] = None
    ) -> str:
        """이미지와 텍스트를 함께 분석 (VLM 사용)"""
        try:
            # VLM을 사용한 실제 이미지 분석
            vlm_prompt = f"""
이 CCTV 이미지를 분석해주세요.

사용자 질의: "{query}"

다음을 분석해주세요:
1. 이미지에서 보이는 주요 요소들 (도로, 차량, 기상상황 등)
2. 사용자 질의와의 관련성 (0-100 점수)
3. 간단한 설명

응답 형식:
점수: [0-100]
설명: [한 줄 설명]
"""

            response = await self.analyze_image_with_vlm(
                image_path=image_path,
                prompt=vlm_prompt,
                model_name=model
            )

            return response

        except Exception as e:
            logger.error(f"이미지 분석 오류: {e}")
            return "이미지 분석을 수행할 수 없습니다."
    
    async def generate_image_description(self, filename: str, query: str) -> str:
        """파일명 기반 이미지 설명 생성"""
        try:
            prompt = f"""
            파일명: {filename}
            사용자 질의: {query}
            
            이 CCTV 이미지 파일명을 분석하여 다음 정보를 추출해주세요:
            1. 촬영 장소 (지역, 도로명 등)
            2. 촬영 시간 (시간대, 날짜 등)
            3. 기상 상황 (해무, 안개, 맑음 등)
            4. 사용자 질의와의 관련성
            
            간단하고 명확한 설명으로 제공해주세요.
            """
            
            description = await self.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_tokens=300
            )
            
            return description or f"CCTV 이미지: {filename}"
            
        except Exception as e:
            logger.error(f"이미지 설명 생성 오류: {e}")
            return f"CCTV 이미지: {filename}"
    
    async def calculate_relevance_score(self, filename: str, query: str) -> float:
        """파일명과 질의의 관련성 점수 계산"""
        try:
            # 간단한 키워드 매칭 기반 점수 계산
            query_lower = query.lower()
            filename_lower = filename.lower()
            
            # 기본 점수
            score = 0.0
            
            # 날씨 관련 키워드
            weather_keywords = {
                "해무": 0.3, "안개": 0.3, "fog": 0.3, "mist": 0.3,
                "맑음": 0.2, "clear": 0.2, "sunny": 0.2,
                "비": 0.2, "rain": 0.2, "rainy": 0.2,
                "눈": 0.2, "snow": 0.2, "snowy": 0.2,
                "야간": 0.1, "밤": 0.1, "night": 0.1,
                "주간": 0.1, "낮": 0.1, "day": 0.1
            }
            
            # 장소 관련 키워드
            location_keywords = {
                "고속도로": 0.2, "highway": 0.2,
                "경부고속도로": 0.3, "경부": 0.2,
                "중부고속도로": 0.3, "중부": 0.2,
                "서해안고속도로": 0.3, "서해안": 0.2,
                "교량": 0.15, "bridge": 0.15,
                "터널": 0.15, "tunnel": 0.15,
                "ic": 0.1, "인터체인지": 0.1,
                "휴게소": 0.1, "service": 0.1,
                "cctv": 0.2, "영상": 0.1
            }
            
            # 키워드 매칭 점수 계산
            for keyword, weight in weather_keywords.items():
                if keyword in query_lower and keyword in filename_lower:
                    score += weight
                elif keyword in query_lower or keyword in filename_lower:
                    score += weight * 0.5
                    
            for keyword, weight in location_keywords.items():
                if keyword in query_lower and keyword in filename_lower:
                    score += weight
                elif keyword in query_lower or keyword in filename_lower:
                    score += weight * 0.5
            
            # 기본 관련성 (CCTV 이미지라면 최소한의 점수)
            if "ts." in filename_lower or "cctv" in filename_lower:
                score += 0.1
                
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"관련성 점수 계산 오류: {e}")
            return 0.1  # 기본 점수
