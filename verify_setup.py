"""
프로젝트 구조 및 설정 검증 스크립트
"""

import os
import sys
import json
import yaml

print("=" * 60)
print("ex-GPT Project Structure Verification")
print("=" * 60)

# 1. 디렉토리 구조 확인
print("\n[1] Directory Structure Check")
required_dirs = [
    "backend",
    "frontend",
    "services",
    "tests",
    "config",
    "docs",
    "data",
    "services/traffic-analysis",
    "services/damage-detection"
]

for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"  [OK] {dir_path}/")
    else:
        print(f"  [MISSING] {dir_path}/")

# 2. 중요 파일 확인
print("\n[2] Important Files Check")
important_files = [
    ".gitignore",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    "config/development.yaml",
    "config/production.yaml",
    "requirements.txt",
    "backend/requirements.txt",
    "frontend/package.json",
    "tests/pytest.ini",
    "services/traffic-analysis/traffic_analyzer.py",
    "services/damage-detection/damage_detector.py"
]

for file_path in important_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"  [OK] {file_path} ({size:,} bytes)")
    else:
        print(f"  [MISSING] {file_path}")

# 3. 백엔드 구조 확인
print("\n[3] Backend Structure Check")
backend_structure = {
    "backend/src": os.path.exists("backend/src"),
    "backend/main.py": os.path.exists("backend/main.py"),
    "backend/simple_test.py": os.path.exists("backend/simple_test.py"),
}

for path, exists in backend_structure.items():
    status = "[OK]" if exists else "[MISSING]"
    print(f"  {status} {path}")

# 4. 설정 파일 검증
print("\n[4] Configuration Validation")
try:
    with open("config/development.yaml", "r", encoding="utf-8") as f:
        dev_config = yaml.safe_load(f)
        print(f"  [OK] Development config loaded")
        print(f"      - Environment: {dev_config.get('environment')}")
        print(f"      - Debug: {dev_config.get('debug')}")
        print(f"      - API Port: {dev_config.get('api', {}).get('port')}")
except Exception as e:
    print(f"  [ERROR] Failed to load dev config: {e}")

try:
    with open("config/production.yaml", "r", encoding="utf-8") as f:
        prod_config = yaml.safe_load(f)
        print(f"  [OK] Production config loaded")
        print(f"      - Environment: {prod_config.get('environment')}")
        print(f"      - Workers: {prod_config.get('api', {}).get('workers')}")
except Exception as e:
    print(f"  [ERROR] Failed to load prod config: {e}")

# 5. 프론트엔드 확인
print("\n[5] Frontend Check")
if os.path.exists("frontend/package.json"):
    with open("frontend/package.json", "r", encoding="utf-8") as f:
        package = json.load(f)
        print(f"  [OK] Frontend package.json exists")
        print(f"      - Name: {package.get('name')}")
        print(f"      - Version: {package.get('version')}")

        # 스크립트 확인
        scripts = package.get('scripts', {})
        if 'dev' in scripts:
            print(f"      - Dev script: Available")
        if 'build' in scripts:
            print(f"      - Build script: Available")
else:
    print(f"  [MISSING] frontend/package.json")

# 6. Docker 설정 확인
print("\n[6] Docker Configuration")
docker_files = {
    "docker-compose.yml": "Main compose file",
    "docker-compose.dev.yml": "Development override",
    "docker-compose.prod.yml": "Production override",
    "Dockerfile": "API Dockerfile",
    "Dockerfile.admin": "Admin UI Dockerfile"
}

for file, desc in docker_files.items():
    if os.path.exists(file):
        print(f"  [OK] {file} - {desc}")
    else:
        print(f"  [MISSING] {file} - {desc}")

# 7. 실행 가능 여부 요약
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_checks = []

# Backend 실행 가능
backend_ready = (
    os.path.exists("backend/simple_test.py") and
    os.path.exists("backend/main.py")
)
all_checks.append(("Backend API", backend_ready))
print(f"  Backend API: {'[READY]' if backend_ready else '[NOT READY]'}")

# Frontend 실행 가능
frontend_ready = os.path.exists("frontend/package.json")
all_checks.append(("Frontend", frontend_ready))
print(f"  Frontend: {'[READY]' if frontend_ready else '[NOT READY]'}")

# Services 실행 가능
services_ready = (
    os.path.exists("services/traffic-analysis/traffic_analyzer.py") and
    os.path.exists("services/damage-detection/damage_detector.py")
)
all_checks.append(("Services", services_ready))
print(f"  Services: {'[READY]' if services_ready else '[NOT READY]'}")

# Docker 실행 가능
docker_ready = (
    os.path.exists("docker-compose.yml") and
    os.path.exists("Dockerfile")
)
all_checks.append(("Docker", docker_ready))
print(f"  Docker: {'[READY]' if docker_ready else '[NOT READY]'}")

# 전체 상태
all_ready = all(status for _, status in all_checks)
print("\n" + "=" * 60)
if all_ready:
    print("[SUCCESS] PROJECT IS READY TO RUN")
    print("\nHow to run:")
    print("  1. Backend: cd backend && python simple_test.py")
    print("  2. Frontend: cd frontend && npm install && npm run dev")
    print("  3. Services: python test_services.py")
    print("  4. Docker: docker-compose up")
else:
    print("[WARNING] PROJECT NEEDS CONFIGURATION")
    print("\nMissing components:")
    for component, ready in all_checks:
        if not ready:
            print(f"  - {component}")

print("=" * 60)