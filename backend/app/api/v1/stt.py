"""
멀티모달 백엔드 음성 STT API 라우터
"""

import time
import asyncio
import tempfile
import os
from typing import Dict, List, Optional, Union
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel, Field
from loguru import logger
# import whisper  # 임시 주석
# import librosa  # 임시 주석
# import soundfile as sf  # 임시 주석
# from pydub import AudioSegment  # 임시 주석
# import numpy as np  # 임시 주석

# from app.core.config import get_settings  # 임시 주석
# from app.core.exceptions import STTException, FileProcessingException, handle_file_errors  # 임시 주석
# from app.services.cache_service import get_cache_manager  # 임시 주석

router = APIRouter(prefix="/stt", tags=["STT 음성 텍스트 변환"])
# settings = get_settings()  # 임시 주석


class STTRequest(BaseModel):
    """STT 요청"""
    model: str = Field(default="large-v3", description="Whisper 모델 (tiny, base, small, medium, large, large-v3)")
    language: Optional[str] = Field(default=None, description="음성 언어 (자동 감지 시 None)")
    task: str = Field(default="transcribe", description="작업 유형 (transcribe, translate)")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="샘플링 온도")
    no_speech_threshold: float = Field(default=0.6, description="무음 구간 임계값")
    logprob_threshold: float = Field(default=-1.0, description="로그 확률 임계값")


class STTSegment(BaseModel):
    """STT 세그먼트"""
    id: int = Field(..., description="세그먼트 ID")
    start: float = Field(..., description="시작 시간(초)")
    end: float = Field(..., description="종료 시간(초)")
    text: str = Field(..., description="텍스트")
    tokens: List[int] = Field(default_factory=list, description="토큰 목록")
    temperature: float = Field(..., description="사용된 온도")
    avg_logprob: float = Field(..., description="평균 로그 확률")
    compression_ratio: float = Field(..., description="압축 비율")
    no_speech_prob: float = Field(..., description="무음 확률")


class STTResponse(BaseModel):
    """STT 응답"""
    transcription: str = Field(..., description="전체 변환 텍스트")
    language: str = Field(..., description="감지된 언어")
    language_probability: float = Field(..., description="언어 감지 확률")
    duration: float = Field(..., description="오디오 지속 시간(초)")
    processing_time: float = Field(..., description="처리 시간(초)")
    model: str = Field(..., description="사용된 모델")
    task: str = Field(..., description="수행된 작업")
    segments: List[STTSegment] = Field(default_factory=list, description="세그먼트 목록")
    metadata: Dict = Field(default_factory=dict, description="추가 메타데이터")


# Whisper 모델 캐시
_whisper_models = {}


def get_whisper_model(model_name: str):
    """Whisper 모델 로드 (캐시됨)"""
    if model_name not in _whisper_models:
        try:
            logger.info(f"Whisper 모델 로드 중: {model_name}")
            _whisper_models[model_name] = whisper.load_model(model_name)
            logger.info(f"Whisper 모델 로드 완료: {model_name}")
        except Exception as e:
            raise STTException(f"Whisper 모델 로드 실패: {str(e)}", model_name)
    
    return _whisper_models[model_name]


def preprocess_audio(audio_path: str, target_sr: int = 16000) -> np.ndarray:
    """오디오 전처리"""
    try:
        # librosa로 오디오 로드
        audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
        
        # 정규화
        audio = librosa.util.normalize(audio)
        
        # 무음 구간 제거 (선택사항)
        audio, _ = librosa.effects.trim(audio, top_db=20)
        
        return audio
        
    except Exception as e:
        logger.warning(f"오디오 전처리 실패, 원본 사용: {e}")
        # 기본적인 로드만 수행
        audio, _ = librosa.load(audio_path, sr=target_sr, mono=True)
        return audio


def convert_audio_format(input_path: str, output_path: str) -> bool:
    """오디오 형식 변환"""
    try:
        # pydub으로 다양한 형식 지원
        audio = AudioSegment.from_file(input_path)
        
        # WAV 형식으로 변환 (Whisper가 선호하는 형식)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        
        return True
        
    except Exception as e:
        logger.error(f"오디오 형식 변환 실패: {e}")
        return False


async def perform_whisper_stt(
    audio_path: str,
    model_name: str,
    language: Optional[str] = None,
    task: str = "transcribe",
    temperature: float = 0.0,
    no_speech_threshold: float = 0.6,
    logprob_threshold: float = -1.0
) -> Dict:
    """Whisper STT 수행"""
    try:
        # 모델 로드
        model = get_whisper_model(model_name)
        
        # STT 옵션 설정
        options = {
            "language": language,
            "task": task,
            "temperature": temperature,
            "no_speech_threshold": no_speech_threshold,
            "logprob_threshold": logprob_threshold,
            "verbose": False
        }
        
        # 언어가 지정되지 않은 경우 자동 감지
        if language is None:
            options.pop("language")
        
        # STT 실행
        result = model.transcribe(audio_path, **options)
        
        # 세그먼트 정보 처리
        segments = []
        for seg in result.get("segments", []):
            segments.append(STTSegment(
                id=seg["id"],
                start=seg["start"],
                end=seg["end"],
                text=seg["text"],
                tokens=seg.get("tokens", []),
                temperature=seg.get("temperature", temperature),
                avg_logprob=seg.get("avg_logprob", 0.0),
                compression_ratio=seg.get("compression_ratio", 0.0),
                no_speech_prob=seg.get("no_speech_prob", 0.0)
            ))
        
        return {
            "text": result["text"],
            "language": result["language"],
            "language_probability": result.get("language_probability", 0.0),
            "segments": segments
        }
        
    except Exception as e:
        raise STTException(f"Whisper STT 실행 실패: {str(e)}", model_name)


@router.post("/transcribe", response_model=STTResponse)
@handle_file_errors
async def transcribe_audio(
    audio: UploadFile = File(..., description="STT를 수행할 오디오 파일"),
    model: str = Form(default="large-v3", description="Whisper 모델"),
    language: Optional[str] = Form(default=None, description="음성 언어 (자동 감지 시 비워둠)"),
    task: str = Form(default="transcribe", description="작업 유형"),
    temperature: float = Form(default=0.0, description="샘플링 온도"),
    no_speech_threshold: float = Form(default=0.6, description="무음 구간 임계값"),
    logprob_threshold: float = Form(default=-1.0, description="로그 확률 임계값")
):
    """
    오디오 파일을 텍스트로 변환합니다.
    
    지원 형식: MP3, WAV, M4A, FLAC, OGG 등
    """
    start_time = time.time()
    
    try:
        # 지원 형식 확인
        supported_formats = [
            "audio/mpeg", "audio/wav", "audio/wave", "audio/x-wav",
            "audio/mp4", "audio/m4a", "audio/flac", "audio/ogg"
        ]
        
        if audio.content_type not in supported_formats:
            raise HTTPException(
                status_code=415,
                detail=f"지원하지 않는 오디오 형식입니다. 지원 형식: MP3, WAV, M4A, FLAC, OGG"
            )
        
        # 캐시 키 생성
        audio_content = await audio.read()
        cache_key = f"stt:{hash(audio_content)}:{model}:{language}:{task}:{temperature}"
        await audio.seek(0)  # 파일 포인터 리셋
        
        cache_manager = get_cache_manager()
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.info(f"STT 캐시 히트: {audio.filename}")
            return STTResponse(**cached_result)
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
            tmp_file.write(audio_content)
            tmp_path = tmp_file.name
        
        try:
            # 오디오 정보 가져오기
            try:
                audio_info = AudioSegment.from_file(tmp_path)
                duration = len(audio_info) / 1000.0  # 초 단위
            except:
                duration = 0.0
            
            # WAV 형식으로 변환 (필요한 경우)
            wav_path = tmp_path + ".wav"
            if not convert_audio_format(tmp_path, wav_path):
                # 변환 실패 시 원본 사용
                wav_path = tmp_path
            
            # STT 수행
            stt_result = await perform_whisper_stt(
                wav_path,
                model,
                language,
                task,
                temperature,
                no_speech_threshold,
                logprob_threshold
            )
            
            # 처리 시간 계산
            processing_time = time.time() - start_time
            
            # 응답 생성
            response = STTResponse(
                transcription=stt_result["text"],
                language=stt_result["language"],
                language_probability=stt_result["language_probability"],
                duration=duration,
                processing_time=processing_time,
                model=model,
                task=task,
                segments=stt_result["segments"],
                metadata={
                    "word_count": len(stt_result["text"].split()),
                    "character_count": len(stt_result["text"]),
                    "segment_count": len(stt_result["segments"]),
                    "original_filename": audio.filename,
                    "file_size_mb": len(audio_content) / (1024 * 1024),
                    "average_confidence": sum(
                        seg.avg_logprob for seg in stt_result["segments"]
                    ) / len(stt_result["segments"]) if stt_result["segments"] else 0.0
                }
            )
            
            # 캐시에 결과 저장
            await cache_manager.set(cache_key, response.dict(), ttl=3600)
            
            logger.info(
                f"STT 완료 - {audio.filename}: "
                f"모델={model}, 언어={stt_result['language']}, "
                f"텍스트={len(stt_result['text'])}자, "
                f"지속시간={duration:.1f}s, "
                f"처리시간={processing_time:.2f}s"
            )
            
            return response
            
        finally:
            # 임시 파일 정리
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(wav_path) and wav_path != tmp_path:
                os.unlink(wav_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT 처리 중 오류: {str(e)}")
        raise STTException(str(e), model, audio.filename)


@router.get("/models")
async def get_available_models():
    """
    사용 가능한 Whisper 모델 목록을 반환합니다.
    """
    models = [
        {
            "name": "tiny",
            "size": "39 MB",
            "description": "가장 빠른 모델, 낮은 정확도",
            "languages": "다국어",
            "speed": "매우 빠름"
        },
        {
            "name": "base",
            "size": "74 MB", 
            "description": "빠른 모델, 중간 정확도",
            "languages": "다국어",
            "speed": "빠름"
        },
        {
            "name": "small",
            "size": "244 MB",
            "description": "균형잡힌 속도와 정확도",
            "languages": "다국어",
            "speed": "보통"
        },
        {
            "name": "medium",
            "size": "769 MB",
            "description": "높은 정확도, 느린 속도",
            "languages": "다국어",
            "speed": "느림"
        },
        {
            "name": "large",
            "size": "1550 MB",
            "description": "최고 정확도, 가장 느림",
            "languages": "다국어",
            "speed": "매우 느림"
        },
        {
            "name": "large-v3",
            "size": "1550 MB",
            "description": "최신 대형 모델, 최고 성능",
            "languages": "다국어",
            "speed": "매우 느림"
        }
    ]
    
    return {
        "models": models,
        "default_model": settings.WHISPER_MODEL,
        "supported_languages": [
            "ko", "en", "ja", "zh", "es", "fr", "de", "ru", "it", "pt"
        ],
        "supported_tasks": ["transcribe", "translate"]
    }


@router.post("/batch")
async def batch_stt_processing(
    audio_files: List[UploadFile] = File(..., description="STT를 수행할 오디오 파일들"),
    model: str = Form(default="large-v3"),
    language: Optional[str] = Form(default=None),
    task: str = Form(default="transcribe")
):
    """
    여러 오디오 파일에 대해 배치 STT 처리를 수행합니다.
    """
    if len(audio_files) > 5:
        raise HTTPException(
            status_code=400,
            detail="한 번에 최대 5개의 오디오 파일만 처리할 수 있습니다."
        )
    
    results = []
    
    for audio_file in audio_files:
        try:
            # 개별 STT 처리
            result = await transcribe_audio(
                audio=audio_file,
                model=model,
                language=language,
                task=task
            )
            
            results.append({
                "filename": audio_file.filename,
                "status": "success",
                "result": result
            })
            
        except Exception as e:
            results.append({
                "filename": audio_file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_files": len(audio_files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }


@router.post("/segment-search")
async def search_in_transcription(
    query: str = Form(..., description="검색할 텍스트"),
    transcription_segments: List[Dict] = Form(..., description="검색할 세그먼트 목록")
):
    """
    변환된 텍스트 세그먼트에서 특정 단어나 구문을 검색합니다.
    """
    matching_segments = []
    
    for segment in transcription_segments:
        if query.lower() in segment.get("text", "").lower():
            matching_segments.append({
                "segment_id": segment.get("id"),
                "start_time": segment.get("start"),
                "end_time": segment.get("end"),
                "text": segment.get("text"),
                "match_context": segment.get("text")  # 전체 텍스트를 컨텍스트로 제공
            })
    
    return {
        "query": query,
        "total_matches": len(matching_segments),
        "matching_segments": matching_segments
    }
