# ex-GPT Quick Start Guide

## 🚀 한 번에 실행하기 (권장)

```bash
# Python 스크립트로 실행 (인코딩 문제 없음)
python START_SIMPLE.py

# 또는 배치 파일로 실행 (Windows)
START_SYSTEM.bat
```

## 📋 실행 옵션

1. **Quick Test Mode** - 백엔드만 빠르게 테스트
2. **Full System** - 프론트엔드 + 백엔드 전체 실행
3. **Docker Mode** - Docker로 모든 서비스 실행
4. **Service Test** - 서비스 모듈만 테스트

## 🌐 접속 주소

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8201
- **API 문서**: http://localhost:8201/docs
- **Qdrant 대시보드**: http://localhost:6333
- **MinIO 콘솔**: http://localhost:9001

## 🔧 수동 실행 방법

```bash
# 백엔드만 실행
cd backend && python simple_test.py

# 프론트엔드만 실행
cd frontend && npm install && npm run dev

# 서비스 테스트
python test_services.py

# Docker 실행
docker-compose up -d
```

## 📁 프로젝트 구조

```
ex-GPT-ai/
├── START_SIMPLE.py         # 🚀 Python 기반 시작 스크립트 (권장)
├── START_SYSTEM.bat        # 🚀 Windows 배치 스크립트
├── backend/                # 백엔드 API
├── frontend/               # React 프론트엔드
├── services/               # 도메인 서비스
│   ├── traffic-analysis/   # 교통 분석
│   └── damage-detection/   # 손상 감지
├── tests/                  # 테스트 코드
├── config/                 # 환경 설정
├── docker-compose.yml      # Docker 구성
└── verify_setup.py         # 설치 검증
```

## 🛠 문제 해결

### 인코딩 오류 해결
- **문제**: PowerShell에서 배치 파일 실행 시 인코딩 오류
- **해결**: `python START_SIMPLE.py` 사용 (권장)

### 포트 충돌 해결
- **문제**: 포트가 이미 사용 중
- **해결**: 자동으로 기존 프로세스 종료됨

### Node.js 없을 때
- **문제**: Node.js 미설치
- **해결**: 백엔드만 실행되며, Node.js 설치 후 재시도

## 📊 시스템 확인

```bash
# 전체 시스템 상태 확인
python verify_setup.py

# 서비스 테스트
python test_services.py
```

## 🎯 개발 워크플로우

1. **개발 시작**: `python START_SIMPLE.py` → 옵션 2 선택
2. **API 테스트**: http://localhost:8201/docs 접속
3. **프론트엔드 개발**: http://localhost:5173 접속
4. **서비스 테스트**: 옵션 4로 기능 확인
5. **Docker 배포**: 옵션 3으로 전체 시스템 테스트