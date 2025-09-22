"""
메모리 기반 캐시 서비스
Redis 대신 cachetools를 사용한 메모리 캐시 구현
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Union
from cachetools import TTLCache
from loguru import logger


class MemoryCache:
    """메모리 기반 캐시 서비스"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        캐시 초기화
        
        Args:
            max_size: 최대 캐시 항목 수
            ttl: TTL(Time To Live) 초 단위
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
        logger.info(f"메모리 캐시 초기화: max_size={max_size}, ttl={ttl}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        try:
            if key in self.cache:
                self.stats["hits"] += 1
                logger.debug(f"캐시 히트: {key}")
                return self.cache[key]
            else:
                self.stats["misses"] += 1
                logger.debug(f"캐시 미스: {key}")
                return None
        except Exception as e:
            logger.error(f"캐시 조회 오류: {key} - {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: 개별 TTL (선택사항)
            
        Returns:
            저장 성공 여부
        """
        try:
            # TTL이 지정된 경우 별도 TTLCache 생성
            if ttl is not None:
                # 기본 캐시에 저장하되, 만료 시간을 현재 시간 + ttl로 설정
                # 단순화를 위해 기본 캐시 사용
                pass
            
            self.cache[key] = value
            self.stats["sets"] += 1
            logger.debug(f"캐시 저장: {key}")
            return True
        except Exception as e:
            logger.error(f"캐시 저장 오류: {key} - {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        캐시에서 값 삭제
        
        Args:
            key: 삭제할 캐시 키
            
        Returns:
            삭제 성공 여부
        """
        try:
            if key in self.cache:
                del self.cache[key]
                self.stats["deletes"] += 1
                logger.debug(f"캐시 삭제: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"캐시 삭제 오류: {key} - {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        키 존재 여부 확인
        
        Args:
            key: 확인할 캐시 키
            
        Returns:
            키 존재 여부
        """
        return key in self.cache
    
    async def clear(self) -> bool:
        """
        모든 캐시 항목 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            self.cache.clear()
            logger.info("모든 캐시 항목 삭제")
            return True
        except Exception as e:
            logger.error(f"캐시 전체 삭제 오류: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 정보 반환
        
        Returns:
            캐시 통계 딕셔너리
        """
        return {
            **self.stats,
            "current_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "hit_rate": self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) 
                       if (self.stats["hits"] + self.stats["misses"]) > 0 else 0.0
        }
    
    async def get_info(self) -> Dict[str, Any]:
        """
        캐시 정보 반환
        
        Returns:
            캐시 정보 딕셔너리
        """
        return {
            "type": "memory",
            "max_size": self.cache.maxsize,
            "ttl": getattr(self.cache, 'ttl', 3600),
            "current_size": len(self.cache),
            "stats": await self.get_stats()
        }


class CacheManager:
    """캐시 매니저 - 싱글톤 패턴"""
    
    _instance: Optional["CacheManager"] = None
    _cache: Optional[MemoryCache] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        if self._cache is None:
            self._cache = MemoryCache(max_size=max_size, ttl=ttl)
    
    @property
    def cache(self) -> MemoryCache:
        """캐시 인스턴스 반환"""
        if self._cache is None:
            self._cache = MemoryCache()
        return self._cache
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        return await self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        return await self.cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        return await self.cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        return await self.cache.exists(key)
    
    async def clear(self) -> bool:
        """모든 캐시 항목 삭제"""
        return await self.cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        return await self.cache.get_stats()
    
    async def get_info(self) -> Dict[str, Any]:
        """캐시 정보 반환"""
        return await self.cache.get_info()


# 전역 캐시 매니저 인스턴스
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """캐시 매니저 인스턴스 반환"""
    global cache_manager
    if cache_manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        cache_manager = CacheManager(
            max_size=settings.MAX_CACHE_SIZE,
            ttl=settings.CACHE_TTL
        )
    return cache_manager


async def init_cache():
    """캐시 초기화"""
    global cache_manager
    cache_manager = get_cache_manager()
    logger.info("메모리 캐시 초기화 완료")


async def cleanup_cache():
    """캐시 정리"""
    global cache_manager
    if cache_manager is not None:
        await cache_manager.clear()
        logger.info("캐시 정리 완료")
