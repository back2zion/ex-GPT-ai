"""
Embeddings Generator for ex-GPT RAG Pipeline
임베딩 생성 모듈
"""

import os
import torch
import numpy as np
from typing import List, Union, Optional, Dict, Any
from transformers import AutoTokenizer, AutoModel
import logging
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """임베딩 결과"""
    embeddings: np.ndarray
    tokens: int
    model: str
    dimension: int
    metadata: Dict[str, Any]


class EmbeddingGenerator:
    """
    임베딩 생성기
    Qwen3-Embedding-0.6B 모델 사용
    """
    
    def __init__(self, 
                 model_name: str = "Qwen/Qwen3-Embedding-0.6B",
                 device: str = "cuda",
                 cache_dir: str = "./embedding_cache"):
        """
        임베딩 생성기 초기화
        
        Args:
            model_name: 사용할 임베딩 모델
            device: 연산 장치
            cache_dir: 캐시 디렉토리
        """
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() else "cpu"
        
        # 캐시 디렉토리
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 모델 로드
        self._load_model()
        
        # 캐시
        self._cache = {}
        self._load_cache()
        
        logger.info(f"임베딩 생성기 초기화 완료 - 모델: {model_name}, 디바이스: {self.device}")
        
    def _load_model(self):
        """모델 로드"""
        try:
            logger.info(f"모델 로드 중: {self.model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 모델 로드
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model = self.model.to(self.device)
            self.model.eval()
            
            # 임베딩 차원
            self.embedding_dim = self.model.config.hidden_size
            
            logger.info(f"모델 로드 완료 - 임베딩 차원: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {str(e)}")
            raise
            
    async def generate(self, 
                      text: Union[str, List[str]],
                      batch_size: int = 32,
                      max_length: int = 512,
                      use_cache: bool = True) -> Union[np.ndarray, List[np.ndarray]]:
        """
        텍스트 임베딩 생성 (비동기)
        
        Args:
            text: 입력 텍스트 (문자열 또는 리스트)
            batch_size: 배치 크기
            max_length: 최대 토큰 길이
            use_cache: 캐시 사용 여부
            
        Returns:
            임베딩 벡터 또는 벡터 리스트
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        # 캐시 확인
        embeddings = []
        texts_to_process = []
        
        for t in texts:
            if use_cache:
                cached = self._get_cached_embedding(t)
                if cached is not None:
                    embeddings.append(cached)
                    continue
                    
            texts_to_process.append(t)
            
        # 처리가 필요한 텍스트가 있는 경우
        if texts_to_process:
            # 비동기 처리
            loop = asyncio.get_event_loop()
            new_embeddings = await loop.run_in_executor(
                None,
                self._generate_batch,
                texts_to_process,
                batch_size,
                max_length
            )
            
            # 캐시 저장
            if use_cache:
                for t, emb in zip(texts_to_process, new_embeddings):
                    self._save_to_cache(t, emb)
                    
            embeddings.extend(new_embeddings)
            
        # 원래 순서로 정렬
        result = []
        cache_idx = 0
        process_idx = 0
        
        for t in texts:
            if use_cache and self._get_cached_embedding(t) is not None:
                result.append(embeddings[cache_idx])
                cache_idx += 1
            else:
                result.append(new_embeddings[process_idx])
                process_idx += 1
                
        return result[0] if is_single else result
        
    def _generate_batch(self, 
                       texts: List[str],
                       batch_size: int,
                       max_length: int) -> List[np.ndarray]:
        """
        배치 임베딩 생성
        
        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기
            max_length: 최대 길이
            
        Returns:
            임베딩 리스트
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 토큰화
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            ).to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Mean pooling
                embeddings = self._mean_pooling(
                    outputs.last_hidden_state,
                    inputs['attention_mask']
                )
                
                # 정규화
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
            # CPU로 이동 및 numpy 변환
            batch_embeddings = embeddings.cpu().numpy()
            all_embeddings.extend(batch_embeddings)
            
        return all_embeddings
        
    def _mean_pooling(self, model_output: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Mean pooling
        
        Args:
            model_output: 모델 출력
            attention_mask: 어텐션 마스크
            
        Returns:
            풀링된 임베딩
        """
        # 어텐션 마스크 확장
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(model_output.size()).float()
        
        # 마스킹된 평균
        sum_embeddings = torch.sum(model_output * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        
        return sum_embeddings / sum_mask
        
    def generate_chunked(self,
                        text: str,
                        chunk_size: int = 512,
                        overlap: int = 50) -> List[np.ndarray]:
        """
        긴 텍스트를 청크로 나누어 임베딩 생성
        
        Args:
            text: 입력 텍스트
            chunk_size: 청크 크기
            overlap: 오버랩 크기
            
        Returns:
            청크별 임베딩 리스트
        """
        # 텍스트를 청크로 분할
        chunks = self._split_text(text, chunk_size, overlap)
        
        # 각 청크에 대해 임베딩 생성
        embeddings = []
        for chunk in chunks:
            embedding = self._generate_batch([chunk], batch_size=1, max_length=chunk_size)[0]
            embeddings.append(embedding)
            
        return embeddings
        
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 입력 텍스트
            chunk_size: 청크 크기
            overlap: 오버랩 크기
            
        Returns:
            청크 리스트
        """
        # 토큰화
        tokens = self.tokenizer.tokenize(text)
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # 토큰을 텍스트로 변환
            chunk_text = self.tokenizer.convert_tokens_to_string(chunk_tokens)
            chunks.append(chunk_text)
            
            # 오버랩을 고려한 다음 시작점
            start = end - overlap if end < len(tokens) else end
            
        return chunks
        
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        두 임베딩 간 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩
            
        Returns:
            유사도 점수 (0~1)
        """
        # 정규화
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)
        
        # 코사인 유사도
        similarity = np.dot(norm1, norm2)
        
        return float(similarity)
        
    def search(self,
              query_embedding: np.ndarray,
              candidate_embeddings: List[np.ndarray],
              top_k: int = 10) -> List[tuple]:
        """
        유사도 검색
        
        Args:
            query_embedding: 쿼리 임베딩
            candidate_embeddings: 후보 임베딩 리스트
            top_k: 상위 k개 반환
            
        Returns:
            (인덱스, 유사도) 튜플 리스트
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            sim = self.similarity(query_embedding, candidate)
            similarities.append((i, sim))
            
        # 유사도 기준 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
        
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """캐시에서 임베딩 조회"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash in self._cache:
            return self._cache[text_hash]
            
        # 파일 캐시 확인
        cache_file = self.cache_dir / f"{text_hash}.npy"
        if cache_file.exists():
            embedding = np.load(cache_file)
            self._cache[text_hash] = embedding
            return embedding
            
        return None
        
    def _save_to_cache(self, text: str, embedding: np.ndarray):
        """캐시에 임베딩 저장"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # 메모리 캐시
        self._cache[text_hash] = embedding
        
        # 파일 캐시
        cache_file = self.cache_dir / f"{text_hash}.npy"
        np.save(cache_file, embedding)
        
    def _load_cache(self):
        """캐시 로드"""
        # 최근 사용한 캐시만 메모리에 로드 (최대 1000개)
        cache_files = sorted(
            self.cache_dir.glob("*.npy"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:1000]
        
        for cache_file in cache_files:
            text_hash = cache_file.stem
            self._cache[text_hash] = np.load(cache_file)
            
        logger.info(f"캐시 로드 완료: {len(self._cache)}개")
        
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        
        # 파일 캐시 삭제
        for cache_file in self.cache_dir.glob("*.npy"):
            cache_file.unlink()
            
        logger.info("캐시 초기화 완료")


class KoreanTextEmbedding(EmbeddingGenerator):
    """
    한국어 특화 텍스트 임베딩
    """
    
    def __init__(self):
        # 한국어 특화 모델 사용 가능
        super().__init__(model_name="Qwen/Qwen3-Embedding-0.6B")
        
        # 한국어 전처리 설정
        self.korean_preprocessor = self._setup_korean_preprocessor()
        
    def _setup_korean_preprocessor(self):
        """한국어 전처리기 설정"""
        # KoNLPy 등 한국어 처리 도구 설정
        # 여기서는 간단한 예시만
        return None
        
    def preprocess_korean(self, text: str) -> str:
        """
        한국어 텍스트 전처리
        
        Args:
            text: 원본 텍스트
            
        Returns:
            전처리된 텍스트
        """
        # 불필요한 공백 제거
        text = ' '.join(text.split())
        
        # 특수문자 정규화
        # 실제로는 더 복잡한 처리 필요
        
        return text
        
    async def generate_korean(self,
                             text: Union[str, List[str]],
                             preprocess: bool = True) -> Union[np.ndarray, List[np.ndarray]]:
        """
        한국어 텍스트 임베딩 생성
        
        Args:
            text: 입력 텍스트
            preprocess: 전처리 수행 여부
            
        Returns:
            임베딩 벡터
        """
        # 전처리
        if preprocess:
            if isinstance(text, str):
                text = self.preprocess_korean(text)
            else:
                text = [self.preprocess_korean(t) for t in text]
                
        # 임베딩 생성
        return await self.generate(text)


# 테스트 코드
if __name__ == "__main__":
    async def test():
        # 임베딩 생성기 초기화
        generator = KoreanTextEmbedding()
        
        # 테스트 텍스트
        texts = [
            "한국도로공사 ex-GPT 시스템입니다.",
            "도로 안전 관리를 위한 AI 솔루션",
            "멀티모달 이미지 검색 기능"
        ]
        
        # 임베딩 생성
        embeddings = await generator.generate(texts)
        
        print(f"임베딩 생성 완료:")
        for i, text in enumerate(texts):
            print(f"- 텍스트 {i+1}: {text[:30]}...")
            print(f"  임베딩 차원: {embeddings[i].shape}")
            
        # 유사도 검색
        query = "도로 관리 시스템"
        query_embedding = await generator.generate(query)
        
        results = generator.search(query_embedding, embeddings, top_k=3)
        
        print(f"\n'{query}' 검색 결과:")
        for idx, score in results:
            print(f"- {texts[idx]}: {score:.3f}")
            
    # asyncio.run(test())
    print("임베딩 생성기 모듈 준비 완료")
