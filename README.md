# ex-GPT AI System
## 한국도로공사 차세대 AI 어시스턴트 시스템

### 프로젝트 개요
ex-GPT는 한국도로공사의 업무 효율성 증대를 위한 통합 AI 시스템입니다.
멀티모달 검색, 이미지 처리, RAG 기반 질의응답 등의 기능을 제공합니다.

### 시스템 아키텍처
```
ex-GPT-ai/
├── src/
│   ├── image_processing/     # 이미지 처리 모듈
│   │   ├── vlm_processor.py  # Vision Language Model 처리
│   │   ├── ocr_engine.py     # OCR 엔진
│   │   └── image_analyzer.py # 이미지 분석
│   ├── admin_tools/          # 관리도구
│   │   ├── upload_handler.py # 업로드 처리
│   │   └── admin_ui.py       # 관리자 UI
│   ├── rag_pipeline/         # RAG 파이프라인
│   │   ├── embeddings.py     # 임베딩 생성
│   │   └── vector_store.py   # 벡터 저장소
│   └── api/                  # API 엔드포인트
│       └── main.py           # FastAPI 메인
├── config/                   # 설정 파일
│   └── settings.py
├── tests/                    # 테스트
└── docker-compose.yml        # 도커 구성
```

### 주요 기능
1. **멀티모달 이미지 검색**
   - Vision Language Model (VLM) 기반 이미지-텍스트 통합 검색
   - CLIP/BLIP-2 모델 활용
   - 도로공사 특화 이미지 인식 (도로 손상, 교통 표지판 등)

2. **관리도구 이미지 업로드**
   - 자동 OCR 처리
   - 개인정보 자동 검출 및 처리
   - 중복 이미지 필터링
   - 메타데이터 자동 생성

3. **RAG 기반 지능형 검색**
   - Qdrant 벡터 데이터베이스
   - BGE Reranker 활용
   - 실시간 임베딩 생성

### 기술 스택
- **LLM**: Qwen3-32B/235B
- **Vision Model**: BLIP-2, CLIP
- **Vector DB**: Qdrant
- **Framework**: FastAPI, Flask
- **GPU**: H100 (4대 할당)
- **Container**: Docker, Docker Compose

### R&R (역할과 책임)
- **DataStreams**: 전처리, 보안 검사, LLM 추론
- **NeoAli**: 문서 파싱, RAG 파이프라인, 벡터 저장

### 실행 방법
```bash
# 환경 설정
cp config/.env.example config/.env

# Docker 컨테이너 실행
docker-compose up -d

# API 서버 직접 실행
python src/api/main.py
```

### 환경 변수
```
CHAT_MODEL_ENDPOINT=http://vllm:8000/v1
EMBEDDING_MODEL_ENDPOINT=http://vllm-embeddings:8100/v1
RERANK_MODEL_ENDPOINT=http://vllm-rerank:8101/v1
QDRANT_URL=http://qdrant:6333
FLAGS__ENABLE_VLM=True
```

### 라이센스
Copyright (c) 2025 한국도로공사
