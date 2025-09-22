# ex-GPT 멀티모달 백엔드

한국도로공사 전용 AI 시스템의 멀티모달 처리 서비스 (메모리 캐시 기반)

## 개요

ex-GPT 멀티모달 백엔드는 한국도로공사의 업무 특성에 맞춰 설계된 멀티모달 AI 처리 시스템입니다. 이미지, 음성, 비디오, 문서 등 다양한 형태의 데이터를 처리하고 분석하여 업무 효율성을 향상시킵니다.

## 주요 기능

### 🖼️ 이미지 처리
- **OCR (광학 문자 인식)**: 한국어/영어 문서 텍스트 추출
- **이미지 분석**: 도로 시설물, 교통 상황 자동 분석
- **문서 스캔**: 법령, 규정 문서 디지털화

### 🎵 음성 처리
- **STT (Speech-to-Text)**: 회의록 자동 생성
- **TTS (Text-to-Speech)**: 음성 안내 시스템
- **음성 분석**: 통화 내용 요약 및 분석

### 🎬 비디오 처리
- **영상 분석**: CCTV 영상 자동 분석
- **장면 인식**: 교통 상황, 사고 감지
- **하이라이트 추출**: 중요 장면 자동 추출

### 📄 문서 처리
- **문서 파싱**: PDF, DOCX, XLSX 파일 처리
- **내용 추출**: 구조화된 데이터 변환
- **메타데이터 추출**: 문서 속성 정보 수집

### 🔍 벡터 검색
- **RAG (Retrieval Augmented Generation)**: 문서 기반 질의응답
- **의미 검색**: 자연어 쿼리로 문서 검색
- **유사도 검색**: 관련 문서 추천

## 기술 스택

- **Backend Framework**: FastAPI 0.104+
- **AI/ML**: PyTorch, Transformers, Whisper
- **Computer Vision**: OpenCV, PIL, EasyOCR
- **Vector Database**: Qdrant
- **Database**: PostgreSQL
- **Cache**: 메모리 기반 캐시 (cachetools)
- **Monitoring**: Prometheus, Grafana

## 시스템 요구사항

### 하드웨어
- **GPU**: NVIDIA RTX 4090 또는 H100 권장
- **RAM**: 32GB 이상
- **Storage**: SSD 500GB 이상

### 소프트웨어
- **OS**: Ubuntu 20.04+ / Windows 10+
- **Python**: 3.11+
- **CUDA**: 11.8+
- **Docker**: 20.10+

## 설치 및 실행

### 1. 리포지토리 클론
\`\`\`bash
git clone <repository-url>
cd ex-gpt-multimodal-backend
\`\`\`

### 2. UV 가상환경 설정
\`\`\`bash
# UV 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows

# 의존성 설치
uv pip install -e ".[dev]"
\`\`\`

### 3. 환경변수 설정
\`\`\`bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정값 입력
\`\`\`

### 4. 데이터베이스 설정
\`\`\`bash
# PostgreSQL 시작
docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15

# 데이터베이스 마이그레이션 (선택사항)
alembic upgrade head
\`\`\`

### 5. Qdrant 벡터 데이터베이스 시작
\`\`\`bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
\`\`\`

### 6. 서버 실행
\`\`\`bash
# 개발 모드
./run.sh                # Linux/Mac
run.bat                 # Windows

# 프로덕션 모드
./run.sh prod          # Linux/Mac
run.bat prod           # Windows
\`\`\`

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 주요 API 엔드포인트

### 파일 업로드
\`\`\`http
POST /api/v1/files/upload
Content-Type: multipart/form-data

{
  "file": "<파일>",
  "description": "파일 설명"
}
\`\`\`

### 이미지 OCR
\`\`\`http
POST /api/v1/images/ocr
Content-Type: multipart/form-data

{
  "image": "<이미지 파일>",
  "languages": "kor+eng"
}
\`\`\`

### 음성 STT
\`\`\`http
POST /api/v1/audio/stt
Content-Type: multipart/form-data

{
  "audio": "<음성 파일>",
  "model": "large-v3"
}
\`\`\`

### 문서 검색
\`\`\`http
POST /api/v1/search/semantic
Content-Type: application/json

{
  "query": "도로 안전 관련 규정",
  "limit": 10
}
\`\`\`

### 캐시 상태 확인
\`\`\`http
GET /cache/status

Response:
{
  "type": "memory",
  "max_size": 1000,
  "current_size": 45,
  "stats": {
    "hits": 120,
    "misses": 30,
    "hit_rate": 0.8
  }
}
\`\`\`

## 캐시 시스템

### 메모리 기반 캐시
- **라이브러리**: cachetools TTLCache
- **특징**: Redis 없이 경량화된 메모리 캐시
- **설정**: TTL, 최대 크기 설정 가능
- **성능**: 빠른 접근 속도, 프로세스 종료 시 데이터 소실

### 캐시 설정
\`\`\`.env
CACHE_TYPE=memory
CACHE_TTL=3600        # 1시간
MAX_CACHE_SIZE=1000   # 최대 1000개 항목
\`\`\`

## MCP 백엔드 연동

### 연동 설정
\`\`\`.env
MCP_BACKEND_URL=http://localhost:8002
MCP_API_KEY=your-api-key
ENABLE_MCP_INTEGRATION=true
\`\`\`

### 연동 기능
- 모델 추론 요청 전달
- 실시간 상태 동기화
- 부하 분산 및 큐잉

## 개발 가이드

### 코드 스타일
\`\`\`bash
# 코드 포맷팅
black .
isort .

# 린팅
flake8
mypy .
\`\`\`

### 테스트 실행
\`\`\`bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html
\`\`\`

## 배포

### Docker 배포
\`\`\`bash
# 이미지 빌드
docker build -t ex-gpt-multimodal-backend .

# 컨테이너 실행
docker run -p 8001:8001 ex-gpt-multimodal-backend
\`\`\`

## 모니터링

### 메트릭 확인
- **Prometheus**: http://localhost:8001/metrics
- **헬스체크**: http://localhost:8001/health
- **캐시 상태**: http://localhost:8001/cache/status

### 로그 확인
\`\`\`bash
# 실시간 로그
tail -f logs/multimodal.log

# 특정 레벨 로그 필터링
grep "ERROR" logs/multimodal.log
\`\`\`

## 문제 해결

### 일반적인 문제

1. **GPU 메모리 부족**
   - `CUDA_VISIBLE_DEVICES` 환경변수로 GPU 선택
   - 배치 크기 조정

2. **Qdrant 연결 실패**
   - Qdrant 서버 상태 확인
   - 포트 및 호스트 설정 검증

3. **캐시 메모리 부족**
   - `MAX_CACHE_SIZE` 설정 조정
   - TTL 시간 단축

4. **파일 업로드 실패**
   - 파일 크기 제한 확인
   - 허용된 확장자 목록 확인

## 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 라이선스

이 프로젝트는 한국도로공사의 내부 시스템으로 제한됩니다.

## 지원

기술 지원이 필요한 경우:
- **이메일**: dev@datastreams.co.kr
- **내부 위키**: [링크]
- **Slack**: #ex-gpt-support
