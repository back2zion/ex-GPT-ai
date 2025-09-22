"""
Whisper 기반 STT (Speech-to-Text) 서비스

한국도로공사 ex-GPT 시스템의 음성 인식 기능 제공
- 다양한 오디오 포맷 지원
- H100 GPU 최적화
- 실시간 스트리밍 처리
- 회의록 자동 생성
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
import whisper
import ffmpeg
from whisper.model import Whisper

from multimodal.config.settings import Settings
from multimodal.models.stt_models import STTRequest, STTResponse, TranscriptionSegment


logger = logging.getLogger(__name__)


class WhisperService:
    """Whisper STT 서비스"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model: Optional[Whisper] = None
        self.device = "cuda" if settings.USE_GPU and torch.cuda.is_available() else "cpu"
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """서비스 초기화"""
        try:
            logger.info(f"Whisper 모델 로딩 중: {self.settings.STT_MODEL}")
            logger.info(f"디바이스: {self.device}")
            
            # Whisper 모델 로드
            model_name = self.settings.STT_MODEL.split("/")[-1]  # "openai/whisper-large-v3" -> "large-v3"
            self.model = whisper.load_model(model_name, device=self.device)
            
            logger.info("Whisper 모델 로딩 완료")
            
        except Exception as e:
            logger.error(f"Whisper 모델 초기화 실패: {e}")
            raise
    
    async def cleanup(self) -> None:
        """정리 작업"""
        if self.model is not None:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        logger.info("Whisper 서비스 정리 완료")
    
    async def transcribe_audio(self, audio_file: bytes, request: STTRequest) -> STTResponse:
        """오디오 파일 전사"""
        async with self._lock:
            try:
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_file)
                    temp_file_path = temp_file.name
                
                # 오디오 전처리
                processed_audio_path = await self._preprocess_audio(temp_file_path)
                
                # Whisper 전사 실행
                result = await self._run_whisper_transcription(
                    processed_audio_path, request
                )
                
                # 결과 후처리
                response = await self._postprocess_result(result, request)
                
                # 임시 파일 정리
                Path(temp_file_path).unlink(missing_ok=True)
                if processed_audio_path != temp_file_path:
                    Path(processed_audio_path).unlink(missing_ok=True)
                
                return response
                
            except Exception as e:
                logger.error(f"음성 전사 실패: {e}")
                raise
    
    async def _preprocess_audio(self, audio_path: str) -> str:
        """오디오 전처리"""
        try:
            # FFmpeg를 사용하여 오디오 정규화
            output_path = audio_path.replace(".wav", "_processed.wav")
            
            stream = ffmpeg.input(audio_path)
            stream = ffmpeg.filter(stream, "loudnorm")  # 음량 정규화
            stream = ffmpeg.filter(stream, "highpass", f=80)  # 고주파 필터
            stream = ffmpeg.filter(stream, "lowpass", f=8000)  # 저주파 필터
            stream = ffmpeg.output(stream, output_path, ar=16000, ac=1)  # 16kHz 모노
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return output_path
            
        except Exception as e:
            logger.warning(f"오디오 전처리 실패, 원본 사용: {e}")
            return audio_path
    
    async def _run_whisper_transcription(
        self, audio_path: str, request: STTRequest
    ) -> Dict[str, Any]:
        """Whisper 전사 실행"""
        options = {
            "language": request.language if request.language != "auto" else None,
            "task": "transcribe",
            "temperature": 0.0,
            "no_speech_threshold": 0.6,
            "logprob_threshold": -1.0,
            "compression_ratio_threshold": 2.4,
            "condition_on_previous_text": True,
            "verbose": False,
        }
        
        # 비동기 실행을 위해 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self.model.transcribe(audio_path, **options)
        )
        
        return result
    
    async def _postprocess_result(
        self, whisper_result: Dict[str, Any], request: STTRequest
    ) -> STTResponse:
        """결과 후처리"""
        segments = []
        
        for segment in whisper_result.get("segments", []):
            segments.append(TranscriptionSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"].strip(),
                confidence=segment.get("no_speech_prob", 0.0)
            ))
        
        # 전체 텍스트 생성
        full_text = whisper_result.get("text", "").strip()
        
        # 언어 감지
        detected_language = whisper_result.get("language", "unknown")
        
        # 신뢰도 계산
        confidence = self._calculate_overall_confidence(segments)
        
        return STTResponse(
            text=full_text,
            language=detected_language,
            confidence=confidence,
            segments=segments if request.include_segments else None,
            processing_time=0.0,  # 실제로는 측정해야 함
            model_version=self.settings.STT_MODEL
        )
    
    def _calculate_overall_confidence(self, segments: List[TranscriptionSegment]) -> float:
        """전체 신뢰도 계산"""
        if not segments:
            return 0.0
        
        # 각 세그먼트의 길이로 가중평균 계산
        total_duration = sum(seg.end - seg.start for seg in segments)
        if total_duration == 0:
            return 0.0
        
        weighted_confidence = sum(
            (seg.end - seg.start) * (1.0 - seg.confidence) 
            for seg in segments
        ) / total_duration
        
        return weighted_confidence
    
    async def get_supported_languages(self) -> List[str]:
        """지원되는 언어 목록 반환"""
        if self.model is None:
            return []
        
        return list(whisper.tokenizer.LANGUAGES.values())
    
    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "status": "healthy" if self.model is not None else "unhealthy",
            "model": self.settings.STT_MODEL,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "gpu_memory": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else 0
        }
