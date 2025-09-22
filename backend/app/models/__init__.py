"""
ex-GPT 멀티모달 백엔드 데이터베이스 모델
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class UploadedFile(Base):
    """업로드된 파일 정보"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), unique=True, index=True)
    original_filename = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=True, index=True)
    description = Column(Text, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    checksum = Column(String(255), nullable=True)
    is_processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    processing_results = Column(JSON, nullable=True)
    upload_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OCRResult(Base):
    """OCR 처리 결과"""
    __tablename__ = "ocr_results"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), nullable=False, index=True)
    language = Column(String(20), nullable=False, index=True)
    engine = Column(String(50), nullable=False, index=True)  # tesseract, easyocr
    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    bounding_boxes = Column(JSON, nullable=True)  # 텍스트 위치 정보
    file_metadata = Column(JSON, nullable=True)
    status = Column(String(50), default="completed", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class STTResult(Base):
    """STT 처리 결과"""
    __tablename__ = "stt_results"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)  # whisper-large-v3
    language = Column(String(20), nullable=True, index=True)
    transcription = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    audio_duration = Column(Float, nullable=True)
    segments = Column(JSON, nullable=True)  # 시간 세그먼트별 텍스트
    speaker_info = Column(JSON, nullable=True)  # 화자 정보 (향후 확장)
    file_metadata = Column(JSON, nullable=True)
    status = Column(String(50), default="completed", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class VectorDocument(Base):
    """벡터 데이터베이스 문서 정보"""
    __tablename__ = "vector_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True)
    file_id = Column(String(255), nullable=True, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(100), nullable=False, index=True)  # text, ocr, stt
    language = Column(String(20), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=True)
    total_chunks = Column(Integer, nullable=True)
    embedding_model = Column(String(255), nullable=False)
    vector_collection = Column(String(255), nullable=False, index=True)
    qdrant_point_id = Column(String(255), nullable=True, index=True)
    file_metadata = Column(JSON, nullable=True)
    is_indexed = Column(Boolean, default=False, index=True)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SearchQuery(Base):
    """검색 쿼리 로그"""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(255), unique=True, index=True)
    query_text = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False, index=True)  # semantic, keyword, hybrid
    collection_name = Column(String(255), nullable=True, index=True)
    limit = Column(Integer, nullable=True)
    score_threshold = Column(Float, nullable=True)
    results_count = Column(Integer, nullable=True)
    search_time = Column(Float, nullable=True)
    results = Column(JSON, nullable=True)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class ProcessingJob(Base):
    """처리 작업 큐"""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True)
    job_type = Column(String(50), nullable=False, index=True)  # ocr, stt, vector_index, image_analysis
    file_id = Column(String(255), nullable=True, index=True)
    priority = Column(Integer, default=5, index=True)  # 1-10 (높을수록 우선순위)
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed, cancelled
    parameters = Column(JSON, nullable=True)
    progress = Column(Float, default=0.0)  # 0.0 - 1.0
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    worker_id = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration = Column(Float, nullable=True)
    actual_duration = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ImageAnalysis(Base):
    """이미지 분석 결과"""
    __tablename__ = "image_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(255), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False, index=True)  # classification, detection, segmentation
    model_name = Column(String(255), nullable=False)
    results = Column(JSON, nullable=False)  # 분석 결과
    confidence_scores = Column(JSON, nullable=True)
    processing_time = Column(Float, nullable=True)
    image_dimensions = Column(JSON, nullable=True)  # {"width": 1920, "height": 1080}
    color_analysis = Column(JSON, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    status = Column(String(50), default="completed", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SystemLog(Base):
    """시스템 로그"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    component = Column(String(100), nullable=False, index=True)  # API, PROCESSING, SEARCH, etc
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    client_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True, index=True)
    file_id = Column(String(255), nullable=True, index=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class CacheStats(Base):
    """캐시 통계"""
    __tablename__ = "cache_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    cache_type = Column(String(50), nullable=False, index=True)  # memory
    total_size = Column(Integer, nullable=True)
    hit_count = Column(Integer, nullable=True)
    miss_count = Column(Integer, nullable=True)
    hit_rate = Column(Float, nullable=True)
    eviction_count = Column(Integer, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    average_key_size = Column(Float, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
