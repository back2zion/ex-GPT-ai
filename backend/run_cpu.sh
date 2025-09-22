#!/bin/bash

# ex-GPT 멀티모달 백엔드 실행 스크립트 (CPU 환경)

echo "ex-GPT 멀티모달 백엔드를 시작합니다..."

# UV 가상환경 활성화 및 의존성 설치
echo "UV 가상환경 설정 중..."
uv venv --python 3.11
source .venv/bin/activate

echo "의존성 설치 중..."
uv pip install -e .

# Ollama 서버 상태 확인
echo "Ollama 서버 상태 확인 중..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Ollama 서버가 실행되지 않았습니다. 별도로 실행해주세요:"
    echo "   ollama serve"
    echo "   ollama pull llava:7b"
fi

# 업로드 디렉토리 생성
mkdir -p uploads

# CPU 최적화 환경 변수 설정
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export TORCH_NUM_THREADS=4

echo "서버 시작 중... (포트: 8200)"
echo "API 문서: http://localhost:8200/docs"
echo "CCTV 이미지 검색: http://localhost:8200/api/v1/cctv/search"

# FastAPI 서버 실행
uvicorn src.multimodal.main:app \
    --host 0.0.0.0 \
    --port 8200 \
    --reload \
    --workers 1 \
    --loop asyncio
