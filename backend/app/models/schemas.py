"""
Pydantic 스키마 모델들
API 요청/응답 데이터 구조 정의
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# 공통 응답 모델
class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = Field(description="요청 성공 여부")
    message: Optional[str] = Field(default=None, description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

# 이미지 검색 관련
class ImageSearchRequest(BaseModel):
    """이미지 검색 요청"""
    query: str = Field(description="검색 질의")
    limit: int = Field(default=20, ge=1, le=100, description="반환할 결과 수")
    offset: int = Field(default=0, ge=0, description="결과 오프셋")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="검색 필터")

class ImageItem(BaseModel):
    """이미지 항목"""
    id: str = Field(description="이미지 고유 ID")
    filename: str = Field(description="파일명")
    description: str = Field(description="이미지 설명")
    relevance_score: float = Field(description="관련성 점수 (0-1)")
    file_size: int = Field(description="파일 크기 (바이트)")
    location: Optional[str] = Field(default=None, description="촬영 위치")
    weather_condition: Optional[str] = Field(default=None, description="날씨 조건")
    timestamp: Optional[str] = Field(default=None, description="촬영 시간")
    image_url: str = Field(description="이미지 URL")
    thumbnail_url: str = Field(description="썸네일 URL")
    dimensions: Optional[List[int]] = Field(default=None, description="이미지 크기 [width, height]")

class PageInfo(BaseModel):
    """페이징 정보"""
    offset: int = Field(description="현재 오프셋")
    limit: int = Field(description="페이지 크기")
    current_page: int = Field(description="현재 페이지")
    total_pages: int = Field(description="전체 페이지 수")

class ImageSearchResponse(BaseResponse):
    """이미지 검색 응답"""
    query: str = Field(description="검색 질의")
    images: List[ImageItem] = Field(description="검색된 이미지 목록")
    total_count: int = Field(description="전체 결과 수")
    returned_count: int = Field(description="반환된 결과 수")
    has_more: bool = Field(description="추가 결과 존재 여부")
    page_info: PageInfo = Field(description="페이징 정보")
    search_time_ms: float = Field(description="검색 소요 시간 (밀리초)")
    filters_applied: Dict[str, Any] = Field(description="적용된 필터")
    error: Optional[str] = Field(default=None, description="오류 메시지")

# 멀티모달 채팅 관련
class ChatMessage(BaseModel):
    """채팅 메시지"""
    role: str = Field(description="메시지 역할 (user, assistant, system)")
    content: str = Field(description="메시지 내용")
    image_url: Optional[str] = Field(default=None, description="첨부 이미지 URL")
    timestamp: Optional[datetime] = Field(default=None, description="메시지 시간")

class MultimodalChatRequest(BaseModel):
    """멀티모달 채팅 요청"""
    messages: List[ChatMessage] = Field(description="채팅 메시지 목록")
    session_id: Optional[str] = Field(default=None, description="세션 ID")
    user_id: Optional[str] = Field(default=None, description="사용자 ID")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="응답 창의성")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="최대 토큰 수")
    include_image_analysis: bool = Field(default=True, description="이미지 분석 포함 여부")

class MultimodalChatResponse(BaseResponse):
    """멀티모달 채팅 응답"""
    response: str = Field(description="AI 응답")
    session_id: str = Field(description="세션 ID")
    message_id: str = Field(description="메시지 ID")
    model_used: str = Field(description="사용된 모델")
    processing_time_ms: float = Field(description="처리 시간 (밀리초)")
    images_analyzed: int = Field(default=0, description="분석된 이미지 수")
    suggested_actions: List[str] = Field(default_factory=list, description="제안된 액션")

# 파일 업로드 관련
class FileUploadResponse(BaseResponse):
    """파일 업로드 응답"""
    file_id: str = Field(description="업로드된 파일 ID")
    filename: str = Field(description="파일명")
    file_size: int = Field(description="파일 크기")
    file_type: str = Field(description="파일 타입")
    upload_url: str = Field(description="업로드된 파일 URL")
    analysis_result: Optional[str] = Field(default=None, description="자동 분석 결과")

# 모델 관리 관련
class ModelInfo(BaseModel):
    """모델 정보"""
    name: str = Field(description="모델명")
    size: Optional[str] = Field(default=None, description="모델 크기")
    modified: Optional[datetime] = Field(default=None, description="수정 시간")
    digest: Optional[str] = Field(default=None, description="모델 해시")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="상세 정보")

class ModelListResponse(BaseResponse):
    """모델 목록 응답"""
    models: List[ModelInfo] = Field(description="사용 가능한 모델 목록")

class ModelPullRequest(BaseModel):
    """모델 다운로드 요청"""
    model_name: str = Field(description="다운로드할 모델명")
    force: bool = Field(default=False, description="강제 다운로드 여부")

class ModelPullResponse(BaseResponse):
    """모델 다운로드 응답"""
    model_name: str = Field(description="다운로드된 모델명")
    status: str = Field(description="다운로드 상태")
    progress: Optional[float] = Field(default=None, description="다운로드 진행률 (0-100)")

# 헬스체크 관련
class ServiceStatus(BaseModel):
    """서비스 상태"""
    name: str = Field(description="서비스명")
    status: str = Field(description="상태 (healthy, unhealthy, unknown)")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="상세 정보")
    last_check: datetime = Field(default_factory=datetime.now, description="마지막 확인 시간")

class HealthCheckResponse(BaseResponse):
    """헬스체크 응답"""
    status: str = Field(description="전체 시스템 상태")
    version: str = Field(description="서비스 버전")
    uptime: float = Field(description="가동 시간 (초)")
    services: List[ServiceStatus] = Field(description="개별 서비스 상태")
    system_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="시스템 정보")

# 통계 관련
class SearchStats(BaseModel):
    """검색 통계"""
    total_searches: int = Field(description="전체 검색 수")
    avg_response_time_ms: float = Field(description="평균 응답 시간")
    popular_queries: List[str] = Field(description="인기 검색어")
    error_rate: float = Field(description="오류율")

class UsageStats(BaseModel):
    """사용량 통계"""
    total_requests: int = Field(description="전체 요청 수")
    active_sessions: int = Field(description="활성 세션 수")
    peak_concurrent_users: int = Field(description="최대 동시 사용자 수")
    data_processed_gb: float = Field(description="처리된 데이터량 (GB)")

class StatsResponse(BaseResponse):
    """통계 응답"""
    period: str = Field(description="통계 기간")
    search_stats: SearchStats = Field(description="검색 통계")
    usage_stats: UsageStats = Field(description="사용량 통계")
    system_performance: Dict[str, Any] = Field(description="시스템 성능 지표")

# 오류 응답
class ErrorResponse(BaseModel):
    """오류 응답"""
    success: bool = Field(default=False, description="요청 성공 여부")
    error_code: str = Field(description="오류 코드")
    error_message: str = Field(description="오류 메시지")
    details: Optional[Dict[str, Any]] = Field(default=None, description="오류 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="오류 발생 시간")
    request_id: Optional[str] = Field(default=None, description="요청 ID")

# 배치 처리 관련
class BatchProcessRequest(BaseModel):
    """배치 처리 요청"""
    operation: str = Field(description="수행할 작업")
    items: List[str] = Field(description="처리할 항목 목록")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="처리 옵션")

class BatchProcessResponse(BaseResponse):
    """배치 처리 응답"""
    job_id: str = Field(description="작업 ID")
    total_items: int = Field(description="전체 항목 수")
    processed_items: int = Field(description="처리된 항목 수")
    failed_items: int = Field(description="실패한 항목 수")
    status: str = Field(description="작업 상태")
    results: List[Dict[str, Any]] = Field(description="처리 결과")

# 설정 관련
class ConfigUpdateRequest(BaseModel):
    """설정 업데이트 요청"""
    settings: Dict[str, Any] = Field(description="업데이트할 설정")
    apply_immediately: bool = Field(default=True, description="즉시 적용 여부")

class ConfigResponse(BaseResponse):
    """설정 응답"""
    current_settings: Dict[str, Any] = Field(description="현재 설정")
    modifiable_settings: List[str] = Field(description="수정 가능한 설정 목록")
    last_modified: datetime = Field(description="마지막 수정 시간")
