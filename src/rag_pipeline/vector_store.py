"""
Vector Store for ex-GPT RAG Pipeline
Qdrant 벡터 데이터베이스 관리
"""

import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
    UpdateStatus,
    CollectionStatus,
    OptimizersConfig,
    InitFrom
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과"""
    id: str
    score: float
    document: str
    metadata: Dict[str, Any]
    vector: Optional[np.ndarray] = None


@dataclass
class CollectionInfo:
    """컬렉션 정보"""
    name: str
    vector_size: int
    distance_metric: str
    points_count: int
    status: str
    metadata: Dict[str, Any]


class QdrantVectorStore:
    """
    Qdrant 벡터 스토어
    ex-GPT 시스템의 벡터 데이터베이스 관리
    """
    
    def __init__(self,
                 host: str = "localhost",
                 port: int = 6333,
                 collection_name: str = "ex_gpt_vectors",
                 vector_size: int = 768,
                 distance_metric: Distance = Distance.COSINE):
        """
        Qdrant 벡터 스토어 초기화
        
        Args:
            host: Qdrant 서버 호스트
            port: Qdrant 서버 포트
            collection_name: 컬렉션 이름
            vector_size: 벡터 차원
            distance_metric: 거리 메트릭
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance_metric = distance_metric
        
        # 클라이언트 초기화
        self.client = QdrantClient(host=host, port=port)
        
        # 컬렉션 설정
        self.collections = {
            'documents': f"{collection_name}_documents",
            'images': f"{collection_name}_images",
            'chunks': f"{collection_name}_chunks"
        }
        
        logger.info(f"Qdrant 벡터 스토어 초기화 - {host}:{port}")
        
    async def initialize(self):
        """비동기 초기화"""
        try:
            # 컬렉션 생성
            for collection_type, collection_name in self.collections.items():
                await self.create_collection(
                    collection_name,
                    self.vector_size,
                    self.distance_metric
                )
                
            logger.info("모든 컬렉션 초기화 완료")
            
        except Exception as e:
            logger.error(f"초기화 실패: {str(e)}")
            raise
            
    async def create_collection(self,
                               collection_name: str,
                               vector_size: int,
                               distance_metric: Distance = Distance.COSINE):
        """
        컬렉션 생성
        
        Args:
            collection_name: 컬렉션 이름
            vector_size: 벡터 차원
            distance_metric: 거리 메트릭
        """
        try:
            # 컬렉션 존재 확인
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance_metric
                    ),
                    optimizers_config=OptimizersConfig(
                        memmap_threshold=20000,
                        indexing_threshold=10000,
                        flush_interval_sec=5
                    )
                )
                
                # 인덱스 생성
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_type",
                    field_type="keyword"
                )
                
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="timestamp",
                    field_type="float"
                )
                
                logger.info(f"컬렉션 생성 완료: {collection_name}")
                
            else:
                logger.info(f"컬렉션 이미 존재: {collection_name}")
                
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {str(e)}")
            raise
            
    async def add_document(self,
                          document_id: str,
                          embeddings: Union[np.ndarray, List[float]],
                          metadata: Dict[str, Any],
                          collection_type: str = "documents") -> str:
        """
        문서 추가
        
        Args:
            document_id: 문서 ID
            embeddings: 임베딩 벡터
            metadata: 메타데이터
            collection_type: 컬렉션 유형
            
        Returns:
            저장된 문서 ID
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # numpy 배열을 리스트로 변환
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
                
            # 포인트 생성
            point = PointStruct(
                id=document_id or str(uuid.uuid4()),
                vector=embeddings,
                payload={
                    **metadata,
                    "timestamp": datetime.now().timestamp(),
                    "document_type": collection_type
                }
            )
            
            # 업로드
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"문서 추가 완료: {point.id}")
            
            return str(point.id)
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {str(e)}")
            raise
            
    async def add_batch(self,
                       documents: List[Dict[str, Any]],
                       collection_type: str = "documents") -> List[str]:
        """
        배치 문서 추가
        
        Args:
            documents: 문서 리스트 (id, embeddings, metadata)
            collection_type: 컬렉션 유형
            
        Returns:
            저장된 문서 ID 리스트
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            points = []
            document_ids = []
            
            for doc in documents:
                doc_id = doc.get('id', str(uuid.uuid4()))
                embeddings = doc['embeddings']
                
                # numpy 배열을 리스트로 변환
                if isinstance(embeddings, np.ndarray):
                    embeddings = embeddings.tolist()
                    
                point = PointStruct(
                    id=doc_id,
                    vector=embeddings,
                    payload={
                        **doc.get('metadata', {}),
                        "timestamp": datetime.now().timestamp(),
                        "document_type": collection_type
                    }
                )
                
                points.append(point)
                document_ids.append(doc_id)
                
            # 배치 업로드
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"배치 추가 완료: {len(points)}개 문서")
            
            return document_ids
            
        except Exception as e:
            logger.error(f"배치 추가 실패: {str(e)}")
            raise
            
    async def search(self,
                    query_vector: Union[np.ndarray, List[float]],
                    collection_type: str = "documents",
                    top_k: int = 10,
                    filter_conditions: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        벡터 검색
        
        Args:
            query_vector: 쿼리 벡터
            collection_type: 컬렉션 유형
            top_k: 상위 k개 결과
            filter_conditions: 필터 조건
            
        Returns:
            검색 결과 리스트
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # numpy 배열을 리스트로 변환
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
                
            # 필터 생성
            query_filter = None
            if filter_conditions:
                must_conditions = []
                for field, value in filter_conditions.items():
                    must_conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=must_conditions)
                
            # 검색 실행
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # 결과 변환
            results = []
            for hit in search_result:
                result = SearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    document=hit.payload.get('document', ''),
                    metadata=hit.payload
                )
                results.append(result)
                
            logger.info(f"검색 완료: {len(results)}개 결과")
            
            return results
            
        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            raise
            
    async def hybrid_search(self,
                           query_vector: Union[np.ndarray, List[float]],
                           text_query: str,
                           collection_type: str = "documents",
                           top_k: int = 10) -> List[SearchResult]:
        """
        하이브리드 검색 (벡터 + 텍스트)
        
        Args:
            query_vector: 쿼리 벡터
            text_query: 텍스트 쿼리
            collection_type: 컬렉션 유형
            top_k: 상위 k개 결과
            
        Returns:
            검색 결과 리스트
        """
        # 벡터 검색
        vector_results = await self.search(
            query_vector,
            collection_type,
            top_k * 2  # 더 많이 가져와서 필터링
        )
        
        # 텍스트 필터링
        filtered_results = []
        for result in vector_results:
            # 간단한 텍스트 매칭 (실제로는 더 복잡한 로직 필요)
            if text_query.lower() in result.document.lower():
                result.score *= 1.2  # 부스팅
                
            filtered_results.append(result)
            
        # 재정렬
        filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        return filtered_results[:top_k]
        
    async def update_metadata(self,
                             document_id: str,
                             metadata: Dict[str, Any],
                             collection_type: str = "documents"):
        """
        메타데이터 업데이트
        
        Args:
            document_id: 문서 ID
            metadata: 새 메타데이터
            collection_type: 컬렉션 유형
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # 기존 포인트 조회
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=False
            )
            
            if points:
                # 메타데이터 병합
                existing_metadata = points[0].payload
                existing_metadata.update(metadata)
                existing_metadata['last_updated'] = datetime.now().timestamp()
                
                # 업데이트
                self.client.set_payload(
                    collection_name=collection_name,
                    payload=existing_metadata,
                    points=[document_id]
                )
                
                logger.info(f"메타데이터 업데이트 완료: {document_id}")
                
        except Exception as e:
            logger.error(f"메타데이터 업데이트 실패: {str(e)}")
            raise
            
    async def delete_document(self,
                             document_id: str,
                             collection_type: str = "documents"):
        """
        문서 삭제
        
        Args:
            document_id: 문서 ID
            collection_type: 컬렉션 유형
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=[document_id]
            )
            
            logger.info(f"문서 삭제 완료: {document_id}")
            
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            raise
            
    async def get_collection_info(self, collection_type: str = "documents") -> CollectionInfo:
        """
        컬렉션 정보 조회
        
        Args:
            collection_type: 컬렉션 유형
            
        Returns:
            컬렉션 정보
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # 컬렉션 정보 조회
            info = self.client.get_collection(collection_name)
            
            return CollectionInfo(
                name=collection_name,
                vector_size=info.config.params.vectors.size,
                distance_metric=str(info.config.params.vectors.distance),
                points_count=info.points_count,
                status=str(info.status),
                metadata={
                    'segments_count': info.segments_count,
                    'indexed_vectors_count': info.indexed_vectors_count
                }
            )
            
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {str(e)}")
            raise
            
    async def optimize_collection(self, collection_type: str = "documents"):
        """
        컬렉션 최적화
        
        Args:
            collection_type: 컬렉션 유형
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # 인덱스 최적화
            self.client.update_collection(
                collection_name=collection_name,
                optimizer_config=OptimizersConfig(
                    deleted_threshold=0.2,
                    vacuum_min_vector_number=1000,
                    max_segment_size=200000
                )
            )
            
            logger.info(f"컬렉션 최적화 완료: {collection_name}")
            
        except Exception as e:
            logger.error(f"컬렉션 최적화 실패: {str(e)}")
            raise
            
    async def backup_collection(self,
                               collection_type: str = "documents",
                               backup_path: str = "./backups"):
        """
        컬렉션 백업
        
        Args:
            collection_type: 컬렉션 유형
            backup_path: 백업 경로
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # 스냅샷 생성
            snapshot_name = f"{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.client.create_snapshot(
                collection_name=collection_name,
                snapshot_name=snapshot_name
            )
            
            logger.info(f"백업 완료: {snapshot_name}")
            
            return snapshot_name
            
        except Exception as e:
            logger.error(f"백업 실패: {str(e)}")
            raise
            
    async def restore_collection(self,
                                snapshot_name: str,
                                collection_type: str = "documents"):
        """
        컬렉션 복원
        
        Args:
            snapshot_name: 스냅샷 이름
            collection_type: 컬렉션 유형
        """
        try:
            collection_name = self.collections.get(collection_type, self.collection_name)
            
            # 스냅샷에서 복원
            self.client.restore_snapshot(
                collection_name=collection_name,
                snapshot_name=snapshot_name
            )
            
            logger.info(f"복원 완료: {snapshot_name}")
            
        except Exception as e:
            logger.error(f"복원 실패: {str(e)}")
            raise


class MultiModalVectorStore(QdrantVectorStore):
    """
    멀티모달 벡터 스토어
    텍스트와 이미지를 통합 관리
    """
    
    def __init__(self):
        super().__init__()
        
        # 멀티모달 컬렉션 추가
        self.collections.update({
            'multimodal': f"{self.collection_name}_multimodal",
            'cross_modal': f"{self.collection_name}_cross_modal"
        })
        
    async def add_multimodal_document(self,
                                     text_embedding: np.ndarray,
                                     image_embedding: Optional[np.ndarray],
                                     metadata: Dict[str, Any]) -> str:
        """
        멀티모달 문서 추가
        
        Args:
            text_embedding: 텍스트 임베딩
            image_embedding: 이미지 임베딩
            metadata: 메타데이터
            
        Returns:
            문서 ID
        """
        doc_id = str(uuid.uuid4())
        
        # 텍스트 임베딩 저장
        await self.add_document(
            doc_id + "_text",
            text_embedding,
            {**metadata, 'modality': 'text'},
            'multimodal'
        )
        
        # 이미지 임베딩 저장 (있는 경우)
        if image_embedding is not None:
            await self.add_document(
                doc_id + "_image",
                image_embedding,
                {**metadata, 'modality': 'image'},
                'multimodal'
            )
            
            # 크로스모달 임베딩 (평균)
            cross_embedding = (text_embedding + image_embedding) / 2
            await self.add_document(
                doc_id + "_cross",
                cross_embedding,
                {**metadata, 'modality': 'cross'},
                'cross_modal'
            )
            
        return doc_id
        
    async def cross_modal_search(self,
                                query_embedding: np.ndarray,
                                source_modality: str,
                                target_modality: str,
                                top_k: int = 10) -> List[SearchResult]:
        """
        크로스모달 검색
        
        Args:
            query_embedding: 쿼리 임베딩
            source_modality: 소스 모달리티
            target_modality: 타겟 모달리티
            top_k: 상위 k개
            
        Returns:
            검색 결과
        """
        # 크로스모달 공간에서 검색
        results = await self.search(
            query_embedding,
            'cross_modal',
            top_k,
            {'source_modality': source_modality}
        )
        
        # 타겟 모달리티로 필터링
        filtered_results = [
            r for r in results
            if r.metadata.get('target_modality') == target_modality
        ]
        
        return filtered_results


# 테스트 코드
async def main():
    # 벡터 스토어 초기화
    store = MultiModalVectorStore()
    await store.initialize()
    
    print("ex-GPT 벡터 스토어 준비 완료")
    print("\n지원 기능:")
    print("1. 문서/이미지/청크별 벡터 저장")
    print("2. 유사도 기반 검색")
    print("3. 하이브리드 검색 (벡터 + 텍스트)")
    print("4. 멀티모달 통합 관리")
    print("5. 크로스모달 검색")
    print("6. 백업 및 복원")
    
    # 컬렉션 정보
    for collection_type in ['documents', 'images', 'chunks']:
        info = await store.get_collection_info(collection_type)
        print(f"\n{collection_type} 컬렉션:")
        print(f"- 벡터 크기: {info.vector_size}")
        print(f"- 포인트 수: {info.points_count}")
        print(f"- 상태: {info.status}")


if __name__ == "__main__":
    asyncio.run(main())
