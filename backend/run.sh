#!/bin/bash

# ex-GPT 멀티모달 백엔드 실행 스크립트 (메모리 캐시 기반)

set -e

echo "=== ex-GPT 멀티모달 백엔드 시작 ==="

# 환경변수 체크
if [ ! -f .env ]; then
    echo "환경설정 파일(.env)을 생성하는 중..."
    cp .env.example .env
    echo "⚠️  .env 파일을 편집하여 필요한 설정값을 입력하세요."
fi

# UV 설치 확인
if ! command -v uv &> /dev/null; then
    echo "UV를 설치하는 중..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 가상환경 확인 및 생성
if [ ! -d ".venv" ]; then
    echo "가상환경을 생성하는 중..."
    uv venv
fi

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
echo "의존성을 설치하는 중..."
uv pip install -e ".[dev]"

# 필요한 디렉토리 생성
mkdir -p uploads logs

# PostgreSQL 상태 확인 (선택사항)
if command -v psql &> /dev/null; then
    echo "PostgreSQL 연결 확인 중..."
    if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
        echo "✅ PostgreSQL 연결 성공"
    else
        echo "⚠️  PostgreSQL 연결 실패 - Docker로 PostgreSQL을 시작하세요"
        echo "   docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15"
    fi
fi

# Qdrant 상태 확인 (선택사항)
if command -v curl &> /dev/null; then
    echo "Qdrant 연결 확인 중..."
    if curl -s http://localhost:6333/health &> /dev/null; then
        echo "✅ Qdrant 연결 성공"
    else
        echo "⚠️  Qdrant 연결 실패 - Docker로 Qdrant를 시작하세요"
        echo "   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant"
    fi
fi

# 데이터베이스 마이그레이션 (선택사항)
if command -v alembic &> /dev/null; then
    echo "데이터베이스 마이그레이션 실행 중..."
    alembic upgrade head
fi

echo "✅ 메모리 캐시 기반 멀티모달 백엔드 준비 완료"

# 개발 모드 또는 프로덕션 모드 선택
if [ "$1" = "prod" ]; then
    echo "프로덕션 모드로 서버 시작... (포트: 8001)"
    uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
else
    echo "개발 모드로 서버 시작... (포트: 8001)"
    echo "📖 API 문서: http://localhost:8001/docs"
    echo "❤️  헬스체크: http://localhost:8001/health"
    echo "📊 캐시 상태: http://localhost:8001/cache/status"
    uvicorn main:app --reload --host 0.0.0.0 --port 8001
fi
