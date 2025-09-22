# ex-GPT 멀티모달 백엔드 Dockerfile (메모리 캐시 기반)
FROM nvidia/cuda:12.0-devel-ubuntu20.04

LABEL maintainer="DataStreams <dev@datastreams.co.kr>"
LABEL description="ex-GPT 멀티모달 백엔드 서비스 - 한국도로공사 전용 AI 시스템"

# 환경변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0,1
ENV TORCH_USE_CUDA_DSA=1

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python 기본 버전 설정
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# pip 업그레이드
RUN python -m pip install --upgrade pip

# UV 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 작업 디렉토리 설정
WORKDIR /app

# pyproject.toml과 의존성 파일 복사
COPY pyproject.toml ./
COPY .env.example .env

# UV로 의존성 설치
RUN uv venv && \
    uv pip install -e "."

# 필요한 디렉토리 생성
RUN mkdir -p uploads logs

# 애플리케이션 코드 복사
COPY . .

# 환경변수 활성화 스크립트
RUN echo "source .venv/bin/activate" >> ~/.bashrc

# 포트 노출
EXPOSE 8001

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 실행 명령
CMD ["sh", "-c", "source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8001"]
