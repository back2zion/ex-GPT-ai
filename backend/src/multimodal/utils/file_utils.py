"""파일 유틸리티 함수"""

from pathlib import Path
from typing import List

ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

def validate_audio_file(filename: str) -> bool:
    """오디오 파일 유효성 검사"""
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_AUDIO_EXTENSIONS

def validate_image_file(filename: str) -> bool:
    """이미지 파일 유효성 검사"""
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def get_file_extension(filename: str) -> str:
    """파일 확장자 반환"""
    return Path(filename).suffix.lower()

def get_safe_filename(filename: str) -> str:
    """안전한 파일명 생성"""
    import re
    # 한글, 영문, 숫자, 일부 특수문자만 허용
    safe_name = re.sub(r'[^\w\-_\.\u3131-\u3163\uac00-\ud7a3]', '_', filename)
    return safe_name[:100]  # 길이 제한
