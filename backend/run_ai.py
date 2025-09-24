"""
실제 AI 백엔드 실행 스크립트
"""

import sys
import os
from pathlib import Path

# 모듈 경로 추가
backend_root = Path(__file__).parent
src_path = backend_root / "src"
sys.path.insert(0, str(src_path))

try:
    # 필요한 라이브러리 확인
    print("=" * 50)
    print("ex-GPT AI Backend Startup")
    print("=" * 50)

    print("[INFO] Checking dependencies...")

    # PyTorch 확인
    try:
        import torch
        print(f"[OK] PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"[OK] CUDA available: {torch.cuda.device_count()} GPU(s)")
        else:
            print("[WARNING] CUDA not available, using CPU")
    except ImportError:
        print("[ERROR] PyTorch not installed")

    # Transformers 확인
    try:
        import transformers
        print(f"[OK] Transformers: {transformers.__version__}")
    except ImportError:
        print("[ERROR] Transformers not installed")

    # FastAPI 확인
    try:
        import fastapi
        print(f"[OK] FastAPI: {fastapi.__version__}")
    except ImportError:
        print("[ERROR] FastAPI not installed")

    print("\n[INFO] Starting AI services...")

    # 실제 AI 백엔드 시작
    from multimodal.main import app
    import uvicorn

    print("[SUCCESS] AI Backend loaded successfully!")
    print("\nStarting server...")
    print("- API: http://localhost:8200")
    print("- Docs: http://localhost:8200/docs")

    # 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8200,
        reload=True,
        log_level="info"
    )

except ImportError as e:
    print(f"\n[ERROR] Module import failed: {e}")
    print("\nThis looks like a dependency issue. Options:")
    print("1. Install missing packages: pip install torch transformers")
    print("2. Use the simple test server: python simple_test.py")
    print("3. Use Docker mode: docker-compose up")

except Exception as e:
    print(f"\n[ERROR] Failed to start AI backend: {e}")
    print("\nFallback to simple test server...")

    # 폴백: 간단한 테스트 서버
    try:
        import simple_test
        print("[INFO] Starting simple test server instead...")
    except:
        print("[ERROR] Could not start any server")

print("\nPress Enter to exit...")
input()