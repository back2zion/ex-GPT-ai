"""
ex-GPT 통합 백엔드 - 멀티모달 + 채팅 서비스
한국도로공사 전용 AI 시스템
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str
    image_url: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False

class ChatResponse(BaseModel):
    success: bool
    response: str
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    suggested_questions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class MultimodalChatService:
    """멀티모달 채팅 서비스 (기존 채팅 기능 통합)"""
    
    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client
        self.sessions = {}
        
    async def process_chat(
        self,
        messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        multimodal: bool = False
    ) -> ChatResponse:
        """채팅 처리 (텍스트 및 멀티모달)"""
        try:
            # 세션 관리
            if not session_id:
                session_id = str(uuid.uuid4())
                
            message_id = str(uuid.uuid4())
            
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "messages": []
                }
            
            # 세션에 새 메시지 추가
            self.sessions[session_id]["messages"].extend(messages)

            # Ollama를 통한 응답 생성 (전체 대화 히스토리 사용)
            response_text = ""
            if self.ollama_client:
                try:
                    # 세션의 전체 대화 히스토리를 Ollama에 전달
                    ollama_messages = []
                    for msg in self.sessions[session_id]["messages"]:
                        ollama_msg = {
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        }
                        ollama_messages.append(ollama_msg)

                    logger.info(f"Ollama에 전달할 메시지 히스토리: {len(ollama_messages)}개")

                    response_text = await self.ollama_client.chat_completion(
                        messages=ollama_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    if not response_text:
                        response_text = self._get_default_response()
                except Exception as e:
                    logger.error(f"Ollama 처리 오류: {e}")
                    response_text = self._get_default_response()
            else:
                response_text = self._get_default_response()

            # 응답 메시지를 세션에 추가
            self.sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": response_text
            })
            
            # 응답 생성
            return ChatResponse(
                success=True,
                response=response_text,
                session_id=session_id,
                message_id=message_id,
                sources=None,  # 추후 RAG 구현 시 추가
                suggested_questions=self._generate_suggestions(response_text),
                metadata={
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "model": "qwen3:8b" if self.ollama_client else "none",
                    "multimodal": multimodal
                }
            )
            
        except Exception as e:
            logger.error(f"채팅 처리 오류: {e}")
            return ChatResponse(
                success=False,
                response="죄송합니다. 처리 중 오류가 발생했습니다.",
                error=str(e)
            )
    
    def _get_default_response(self) -> str:
        """기본 응답 메시지"""
        return """안녕하세요! 한국도로공사 ex-GPT 시스템입니다.
        
다음과 같은 기능을 제공합니다:
• CCTV 이미지 검색: '해무', '안개', '날씨' 등의 키워드로 도로 상황 이미지를 검색할 수 있습니다.
• 업무 지원: 한국도로공사 업무 관련 질문에 답변해 드립니다.
• 문서 분석: 업무 문서에 대한 질의응답을 지원합니다.

무엇을 도와드릴까요?"""
    
    def _generate_suggestions(self, response: str) -> List[str]:
        """추천 질문 생성"""
        # 간단한 키워드 기반 추천
        suggestions = []
        
        if "이미지" in response or "사진" in response:
            suggestions.append("해무가 있는 도로 사진을 보여주세요")
            suggestions.append("야간 CCTV 이미지를 검색해주세요")
        
        if "도로" in response or "고속도로" in response:
            suggestions.append("고속도로 통행료 계산 방법은?")
            suggestions.append("도로 안전 관리 규정은 무엇인가요?")
            
        if not suggestions:
            suggestions = [
                "오늘의 도로 상황은 어떤가요?",
                "안개 발생 시 대응 절차는?",
                "통행료 면제 대상은 누구인가요?"
            ]
            
        return suggestions[:3]  # 최대 3개
