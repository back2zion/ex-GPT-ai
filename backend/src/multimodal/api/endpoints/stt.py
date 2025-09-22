"""
STT (Speech-to-Text) API 엔드포인트

Whisper 기반 음성 인식 기능 제공
"""

import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from multimodal.models.stt_models import STTRequest, STTResponse, STTBatchRequest, STTBatchResponse
from multimodal.services.whisper_service import WhisperService
from multimodal.utils.file_utils import validate_audio_file, get_file_extension


logger = logging.getLogger(__name__)
router = APIRouter()


def get_whisper_service(request: Request) -> WhisperService:
    """Whisper 서비스 의존성 주입"""
    return request.app.state.whisper_service


@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="오디오 파일"),
    language: str = Form(default="auto", description="언어 코드"),
    include_segments: bool = Form(default=False, description="세그먼트 포함 여부"),
    enable_vad: bool = Form(default=True, description="VAD 사용 여부"),
    noise_reduction: bool = Form(default=True, description="노이즈 제거 여부"),
    whisper_service: WhisperService = Depends(get_whisper_service)
):
    """
    오디오 파일을 텍스트로 전사
    
    - **file**: 오디오 파일 (wav, mp3, m4a, flac, ogg)
    - **language**: 언어 코드 (auto, ko, en, ja, zh 등)
    - **include_segments**: 세그먼트별 결과 포함 여부
    - **enable_vad**: Voice Activity Detection 사용 여부
    - **noise_reduction**: 노이즈 제거 여부
    """
    try:
        # 파일 유효성 검사
        if not validate_audio_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(['.wav', '.mp3', '.m4a', '.flac', '.ogg'])}"
            )
        
        # 파일 크기 확인
        file_content = await file.read()
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB 제한
            raise HTTPException(status_code=413, detail="파일 크기가 너무 큽니다. (최대 50MB)")
        
        # 요청 객체 생성
        stt_request = STTRequest(
            language=language,
            include_segments=include_segments,
            enable_vad=enable_vad,
            noise_reduction=noise_reduction
        )
        
        # 전사 실행
        result = await whisper_service.transcribe_audio(file_content, stt_request)
        
        logger.info(f"STT 처리 완료: {file.filename}, 언어: {result.language}, 신뢰도: {result.confidence:.3f}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="음성 인식 처리 중 오류가 발생했습니다.")


@router.post("/batch", response_model=STTBatchResponse)
async def batch_transcribe(
    request: STTBatchRequest,
    whisper_service: WhisperService = Depends(get_whisper_service)
):
    """
    배치 음성 인식 작업 시작
    
    - **file_ids**: 처리할 파일 ID 목록
    - **language**: 언어 코드
    - **include_segments**: 세그먼트 포함 여부
    - **callback_url**: 완료 시 콜백 URL
    """
    try:
        # 배치 작업 구현 (Celery 등을 사용)
        # 현재는 기본 응답만 반환
        return STTBatchResponse(
            batch_id="batch_" + "".join(request.file_ids[:5]),
            status="queued",
            total_files=len(request.file_ids),
            processed_files=0,
            estimated_completion=None
        )
        
    except Exception as e:
        logger.error(f"배치 작업 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="배치 작업 시작에 실패했습니다.")


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """배치 작업 상태 조회"""
    try:
        # 실제 구현에서는 데이터베이스에서 상태 조회
        return {
            "batch_id": batch_id,
            "status": "processing",
            "progress": 0.5,
            "results": []
        }
        
    except Exception as e:
        logger.error(f"배치 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="배치 상태 조회에 실패했습니다.")


@router.get("/languages")
async def get_supported_languages(
    whisper_service: WhisperService = Depends(get_whisper_service)
) -> List[str]:
    """지원되는 언어 목록 반환"""
    try:
        languages = await whisper_service.get_supported_languages()
        return languages
        
    except Exception as e:
        logger.error(f"언어 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="언어 목록 조회에 실패했습니다.")


@router.post("/meeting/transcribe")
async def transcribe_meeting(
    file: UploadFile = File(..., description="회의 오디오 파일"),
    meeting_title: str = Form(..., description="회의 제목"),
    participants: str = Form(default="", description="참석자 (쉼표로 구분)"),
    whisper_service: WhisperService = Depends(get_whisper_service)
):
    """
    회의 오디오를 전사하고 구조화된 회의록 생성
    
    - **file**: 회의 오디오 파일
    - **meeting_title**: 회의 제목
    - **participants**: 참석자 목록 (쉼표로 구분)
    """
    try:
        # 기본 전사 수행
        file_content = await file.read()
        stt_request = STTRequest(
            language="ko",  # 한국어 우선
            include_segments=True,
            enable_vad=True,
            noise_reduction=True
        )
        
        transcription_result = await whisper_service.transcribe_audio(file_content, stt_request)
        
        # 회의록 구조화 (실제로는 별도 LLM 서비스 호출)
        participants_list = [p.strip() for p in participants.split(",") if p.strip()]
        
        meeting_result = {
            "title": meeting_title,
            "date": "2025-09-21",  # 실제로는 현재 날짜
            "participants": participants_list,
            "summary": "회의 요약이 여기에 표시됩니다.",  # LLM으로 생성
            "action_items": ["액션 아이템 1", "액션 아이템 2"],  # LLM으로 추출
            "full_transcript": transcription_result.text,
            "key_topics": ["주요 토픽 1", "주요 토픽 2"],  # LLM으로 추출
            "decisions": ["결정 사항 1", "결정 사항 2"],  # LLM으로 추출
            "confidence": transcription_result.confidence,
            "processing_time": transcription_result.processing_time
        }
        
        return meeting_result
        
    except Exception as e:
        logger.error(f"회의록 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="회의록 생성에 실패했습니다.")


@router.get("/health")
async def health_check(
    whisper_service: WhisperService = Depends(get_whisper_service)
):
    """STT 서비스 상태 확인"""
    try:
        status = await whisper_service.health_check()
        return status
        
    except Exception as e:
        logger.error(f"STT 서비스 상태 확인 실패: {e}")
        return {"status": "unhealthy", "error": str(e)}
