# ex-GPT AI System
## 한국도로공사 차세대 멀티모달 AI 어시스턴트 시스템

### 🌟 프로젝트 개요
ex-GPT는 한국도로공사의 업무 효율성 증대를 위한 통합 AI 시스템입니다.
최신 멀티모달 모델을 활용한 이미지-텍스트 통합 처리, RAG 기반 지능형 검색, 도로 인프라 특화 분석 기능을 제공합니다.

### 🏗 시스템 아키텍처
```
ex-GPT-ai/
├── START_SIMPLE.py           # 🚀 통합 시작 스크립트 (권장)
├── START_SYSTEM.bat          # Windows 배치 스크립트
├── backend/                  # 백엔드 API 서버
│   ├── src/                  # 소스 코드
│   │   ├── multimodal/       # 멀티모달 처리
│   │   ├── image_processing/ # 이미지 처리 모듈
│   │   ├── admin_tools/      # 관리도구
│   │   └── rag_pipeline/     # RAG 파이프라인
│   ├── simple_test.py        # 빠른 테스트 서버
│   └── run_ai.py            # 실제 AI 백엔드 실행
├── frontend/                 # React 프론트엔드
│   ├── src/                  # React 컴포넌트 (47개)
│   └── package.json         # React 19.1.1
├── services/                 # 도메인 특화 서비스
│   ├── traffic-analysis/     # 교통 분석 서비스
│   └── damage-detection/     # 손상 감지 서비스
├── config/                   # 환경별 설정
│   ├── settings.py          # 통합 설정
│   ├── development.yaml     # 개발환경
│   └── production.yaml      # 운영환경
├── tests/                    # 통합 테스트
├── docker-compose.yml        # Docker 구성
└── verify_setup.py          # 시스템 검증
```

### 🚀 주요 기능

#### 1. **멀티모달 AI 처리**
   - **Microsoft Florence-2** 기반 차세대 Vision Language Model
   - 이미지 캡션 생성, 객체 감지, OCR 통합 처리
   - 도로 인프라 특화 분석 (포트홀, 균열, 교통표지판 등)
   - CLIP 모델을 활용한 고품질 이미지 임베딩

#### 2. **한국도로공사 특화 서비스**
   - **교통 분석**: 실시간 교통 패턴 분석 및 예측
   - **손상 감지**: AI 기반 도로 손상 자동 분류 및 우선순위 설정
   - **인프라 관리**: 톨게이트, 휴게소, IC/JC, 터널, 교량 모니터링

#### 3. **관리도구 및 업로드**
   - 자동 OCR 처리 (한국어/영어)
   - 개인정보 자동 검출 및 보안 처리
   - 중복 이미지 필터링 및 메타데이터 생성
   - 바이러스 스캔 및 파일 검증

#### 4. **RAG 기반 지능형 검색**
   - Qdrant 벡터 데이터베이스 활용
   - BGE Reranker v2-m3 기반 정확도 향상
   - 세션별 컨텍스트 관리

### 🛠 기술 스택

#### AI 모델
- **LLM**: Qwen3-32B (Chat & Generation)
- **Vision Model**: Microsoft Florence-2-base + CLIP-ViT-Large
- **Embedding**: Qwen3-Embedding-0.6B
- **Reranker**: BGE-reranker-v2-m3

#### 프레임워크 & 인프라
- **Backend**: FastAPI + Python 3.11+
- **Frontend**: React 19.1.1 + Vite + TypeScript
- **Vector DB**: Qdrant
- **Cache**: Redis
- **Database**: PostgreSQL
- **Storage**: MinIO (S3 호환)
- **Container**: Docker + Docker Compose

### 🚀 빠른 시작

#### 1️⃣ 원클릭 실행 (권장)
```bash
# Python 통합 스크립트 실행
python START_SIMPLE.py

# 또는 Windows 배치 파일
START_SYSTEM.bat
```

#### 2️⃣ 실행 옵션 선택
1. **Quick Test** - 백엔드만 빠르게 테스트
2. **Full System** - 프론트엔드 + 백엔드 전체 실행
3. **Docker Mode** - Docker로 전체 서비스 실행
4. **Service Test** - 도메인 서비스 테스트

#### 3️⃣ 접속 주소
- **Frontend**: http://localhost:5173 (React UI)
- **Backend API**: http://localhost:8201
- **API 문서**: http://localhost:8201/docs
- **Real AI Backend**: http://localhost:8200 (실제 AI 모델)
- **Admin UI**: http://localhost:5000

### 🐳 Docker 실행 (고성능 AI)
```bash
# 실제 AI 모델 실행 (GPU 필요)
START_REAL_AI.bat

# 또는 Docker Compose 직접 실행
docker-compose up -d
```

### 🔧 수동 설치 및 실행
```bash
# 백엔드 의존성 설치
pip install -r requirements.txt
pip install torch transformers accelerate
pip install einops timm  # Florence-2용

# 백엔드 실행 (Mock 모드)
cd backend && python simple_test.py

# 프론트엔드 실행
cd frontend && npm install && npm run dev

# 시스템 검증
python verify_setup.py
```

### 📊 시스템 요구사항
- **개발환경**: Python 3.11+, Node.js 18+
- **AI 모델**: 8GB+ GPU (CUDA), Docker Desktop
- **메모리**: 16GB+ RAM 권장
- **저장공간**: 50GB+ (모델 다운로드용)

### 🌐 환경 변수
```bash
# AI 모델 엔드포인트
CHAT_MODEL_ENDPOINT=http://vllm:8000/v1
EMBEDDING_MODEL_ENDPOINT=http://vllm-embeddings:8100/v1
VLM_MODEL_NAME=microsoft/Florence-2-base

# 데이터베이스
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 기능 플래그
FLAGS__ENABLE_VLM=True
FLAGS__ENABLE_RERANK=True
```

### 🛠 문제 해결

#### 인코딩 오류
```bash
# PowerShell에서 배치 파일 실행 시 오류
# 해결: Python 스크립트 사용
python START_SIMPLE.py
```

#### 포트 충돌
```bash
# 포트 사용 중 오류
# 해결: 자동으로 기존 프로세스 종료됨
```

#### AI 모델 의존성
```bash
# Florence-2 모델 오류 (flash_attn 필요)
# 해결: WSL 또는 Docker 사용 권장
pip install flash-attn  # Linux/WSL에서
```

### 📁 프로젝트 구조 (상세)
```
ex-GPT-ai/
├── 🚀 실행 스크립트
│   ├── START_SIMPLE.py         # Python 통합 런처
│   ├── START_SYSTEM.bat        # Windows 배치
│   └── START_REAL_AI.bat       # Docker AI 실행
├── 🖥 백엔드 (Python)
│   ├── backend/src/
│   │   ├── multimodal/         # 실제 AI 처리
│   │   │   ├── main.py         # FastAPI 서버
│   │   │   └── whisper/        # STT 처리
│   │   ├── image_processing/   # VLM & OCR
│   │   │   ├── vlm_processor.py (Florence-2)
│   │   │   └── ocr_engine.py
│   │   └── rag_pipeline/       # RAG 검색
│   └── simple_test.py          # Mock 서버
├── 🌐 프론트엔드 (React)
│   ├── src/components/         # 47개 컴포넌트
│   ├── src/pages/              # 페이지 라우팅
│   └── package.json           # React 19.1.1
├── 🏢 비즈니스 서비스
│   ├── services/traffic-analysis/  # 교통 분석
│   └── services/damage-detection/  # 손상 감지
├── ⚙️ 설정 & 배포
│   ├── config/                 # 환경별 설정
│   ├── docker-compose.yml      # 서비스 오케스트레이션
│   └── Dockerfile             # 컨테이너 이미지
└── 🧪 테스트 & 검증
    ├── tests/                  # 통합 테스트
    ├── verify_setup.py         # 시스템 검증
    └── test_services.py        # 서비스 테스트
```

### 📋 개발 워크플로우
1. **개발 시작**: `python START_SIMPLE.py` → 옵션 2 선택
2. **API 테스트**: http://localhost:8201/docs 에서 테스트
3. **프론트엔드 개발**: http://localhost:5173 에서 확인
4. **서비스 테스트**: 옵션 4로 도메인 기능 검증
5. **AI 모델 테스트**: `START_REAL_AI.bat`로 실제 모델 실행
6. **배포 준비**: Docker Compose로 전체 시스템 검증

### 📈 성능 최적화
- **GPU 가속**: CUDA 지원 시 자동으로 GPU 활용
- **배치 처리**: 대량 이미지 처리 시 배치 단위로 처리
- **캐싱**: Redis 기반 결과 캐싱으로 응답 속도 향상
- **벡터 인덱싱**: Qdrant의 HNSW 인덱스로 빠른 유사도 검색

### 🔐 보안 기능
- **개인정보 보호**: 자동 개인정보 감지 및 마스킹
- **파일 검증**: 업로드 파일 바이러스 스캔
- **접근 제어**: 세션 기반 인증 및 권한 관리
- **데이터 암호화**: 민감 데이터 암호화 저장

### 🌍 다국어 지원
- **한국어**: 주 언어, OCR 및 텍스트 처리 최적화
- **영어**: 기술 문서 및 국제 표준 지원
- **다국어 임베딩**: 다양한 언어로 작성된 문서 검색 지원

### 📞 기술 지원
- **GitHub**: https://github.com/back2zion/ex-GPT-ai
- **이슈 리포팅**: GitHub Issues 활용
- **문서**: `/docs` 폴더 참조

### 📄 라이센스
Copyright (c) 2025 한국도로공사
본 프로젝트는 한국도로공사의 내부 사용을 위한 AI 시스템입니다.
