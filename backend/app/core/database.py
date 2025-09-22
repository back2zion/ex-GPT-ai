"""
데이터베이스 초기화 (간단한 구현)
"""

import asyncio
from loguru import logger


async def init_db():
    """데이터베이스 초기화"""
    try:
        # 현재는 SQLite를 사용하지 않고 메모리 기반으로 작동
        # 필요시 SQLite 초기화 코드 추가
        logger.info("데이터베이스 초기화 완료 (메모리 기반)")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        return False
