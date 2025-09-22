"""
STT (Speech-to-Text) 관련 데이터 모델

Pydantic 모델을 사용한 요청/응답 스키마 정의
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class STTRequest(BaseModel):
    """STT 요청 모델"""
    
    language: str = Field(
        default="auto",
        description="언어 코드 (auto, ko, en, ja, zh 등)"
    )
    include_segments: bool = Field(
        default=False,
        description="세그먼트 정보 포함 여부"
    )
    enable_vad: bool = Field(
        default=True,
        description="Voice Activity Detection 사용 여부"
    )
    noise_reduction: bool = Field(
        default=True,
        description="노이즈 제거 여부"
    )


class TranscriptionSegment(BaseModel):
    """전사 세그먼트"""
    
    start: float = Field(description="시작 시간 (초)")
    end: float = Field(description="종료 시간 (초)")
    text: str = Field(description="전사된 텍스트")
    confidence: float = Field(description="신뢰도 (0.0-1.0)")


class STTResponse(BaseModel):
    """STT 응답 모델"""
    
    text: str = Field(description="전사된 전체 텍스트")
    language: str = Field(description="감지된 언어")
    confidence: float = Field(description="전체 신뢰도")
    segments: Optional[List[TranscriptionSegment]] = Field(
        default=None,
        description="세그먼트별 전사 결과"
    )
    processing_time: float = Field(description="처리 시간 (초)")
    model_version: str = Field(description="사용된 모델 버전")


class STTBatchRequest(BaseModel):
    """STT 배치 요청 모델"""
    
    file_ids: List[str] = Field(description="처리할 파일 ID 목록")
    language: str = Field(default="auto", description="언어 코드")
    include_segments: bool = Field(default=False, description="세그먼트 포함 여부")
    callback_url: Optional[str] = Field(default=None, description="완료 시 콜백 URL")


class STTBatchResponse(BaseModel):
    """STT 배치 응답 모델"""
    
    batch_id: str = Field(description="배치 작업 ID")
    status: str = Field(description="작업 상태")
    total_files: int = Field(description="전체 파일 수")
    processed_files: int = Field(description="처리된 파일 수")
    estimated_completion: Optional[str] = Field(
        default=None,
        description="예상 완료 시간"
    )


class MeetingTranscription(BaseModel):
    """회의록 전사 결과"""
    
    title: str = Field(description="회의 제목")
    date: str = Field(description="회의 날짜")
    participants: List[str] = Field(description="참석자 목록")
    summary: str = Field(description="회의 요약")
    action_items: List[str] = Field(description="액션 아이템")
    full_transcript: str = Field(description="전체 전사 내용")
    key_topics: List[str] = Field(description="주요 토픽")
    decisions: List[str] = Field(description="결정 사항")
