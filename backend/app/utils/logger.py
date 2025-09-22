"""
로거 설정 유틸리티
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger():
    """로거 설정"""
    # 기본 로거 제거
    logger.remove()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # 파일 출력 설정
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        log_path / "multimodal.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days"
    )
    
    return logger
