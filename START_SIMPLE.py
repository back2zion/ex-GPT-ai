"""
간단한 Python 기반 시작 스크립트
배치 파일 인코딩 문제 해결을 위한 대안
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def print_header():
    print("=" * 50)
    print("    ex-GPT AI System - Python Launcher")
    print("=" * 50)

def check_requirements():
    """시스템 요구사항 확인"""
    print("\n[INFO] Checking system requirements...")

    # Python 확인
    print(f"[OK] Python {sys.version.split()[0]}")

    # 필요한 디렉토리 생성
    dirs = ["logs", "uploads", "temp", "cache"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)

    # .env 파일 확인
    if not Path(".env").exists() and Path(".env.example").exists():
        try:
            import shutil
            shutil.copy(".env.example", ".env")
            print("[OK] .env file created from example")
        except Exception as e:
            print(f"[WARNING] Could not create .env: {e}")

    return True

def kill_port_process(port):
    """특정 포트의 프로세스 종료"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[INFO] Port {port} is in use, attempting to free it...")
            # PID 추출 및 종료 시도
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if f':{port} ' in line:
                    try:
                        pid = line.split()[-1]
                        subprocess.run(f'taskkill /F /PID {pid}',
                                     shell=True, capture_output=True)
                        print(f"[OK] Freed port {port}")
                        break
                    except:
                        pass
    except:
        pass

def start_backend():
    """백엔드 서버 시작"""
    print("\n[INFO] Starting backend server...")

    if not Path("backend/simple_test.py").exists():
        print("[ERROR] Backend files not found!")
        return False

    kill_port_process(8201)

    try:
        # 백엔드 서버 시작
        cmd = [sys.executable, "simple_test.py"]
        process = subprocess.Popen(
            cmd,
            cwd="backend",
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("[OK] Backend server started")

        # 잠시 대기
        time.sleep(2)

        # 서버 상태 확인
        try:
            import requests
            response = requests.get("http://localhost:8201/health", timeout=5)
            if response.status_code == 200:
                print("[OK] Backend is responding")
                return True
        except:
            print("[INFO] Backend is starting...")
            return True

    except Exception as e:
        print(f"[ERROR] Failed to start backend: {e}")
        return False

def start_frontend():
    """프론트엔드 서버 시작"""
    print("\n[INFO] Starting frontend...")

    if not Path("frontend/package.json").exists():
        print("[ERROR] Frontend package.json not found!")
        return False

    # Node.js 확인
    try:
        result = subprocess.run(["node", "--version"],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print("[ERROR] Node.js not found!")
            return False
        print(f"[OK] Node.js {result.stdout.strip()}")
    except:
        print("[ERROR] Node.js not available!")
        return False

    kill_port_process(5173)

    try:
        # npm install 실행 (조용히)
        print("[INFO] Installing dependencies...")
        subprocess.run(["npm", "install"],
                      cwd="frontend",
                      capture_output=True)

        # 프론트엔드 서버 시작
        cmd = ["npm", "run", "dev"]
        process = subprocess.Popen(
            cmd,
            cwd="frontend",
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print("[OK] Frontend server started")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to start frontend: {e}")
        return False

def run_tests():
    """서비스 테스트 실행"""
    print("\n[INFO] Running service tests...")
    try:
        result = subprocess.run([sys.executable, "test_services.py"],
                               capture_output=True, text=True)
        if "Test Completed!" in result.stdout:
            print("[OK] Service tests passed")
            return True
        else:
            print("[WARNING] Service tests had issues")
            print(result.stdout[-200:] if result.stdout else "No output")
            return False
    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        return False

def start_docker():
    """Docker 모드 실행"""
    print("\n[INFO] Starting Docker services...")

    # Docker 확인
    try:
        result = subprocess.run(["docker", "--version"],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print("[ERROR] Docker not found!")
            return False
        print(f"[OK] {result.stdout.strip()}")
    except:
        print("[ERROR] Docker not available!")
        return False

    try:
        # Docker Compose 실행
        subprocess.run(["docker-compose", "down"],
                      capture_output=True)
        result = subprocess.run(["docker-compose", "up", "-d"],
                               capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] Docker services started")

            # 서비스 상태 확인
            time.sleep(5)
            subprocess.run(["docker-compose", "ps"])
            return True
        else:
            print(f"[ERROR] Docker failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Docker execution failed: {e}")
        return False

def main():
    """메인 함수"""
    print_header()

    if not check_requirements():
        print("[ERROR] System requirements not met!")
        input("Press Enter to exit...")
        return

    print("\nSelect startup option:")
    print("1) Quick Test Mode (Backend only)")
    print("2) Full System (Backend + Frontend)")
    print("3) Docker Mode (All services)")
    print("4) Service Test Only")
    print("5) Exit")

    choice = input("\nEnter your choice [1-5]: ").strip()

    if choice == "1":
        print("\n" + "=" * 50)
        print("      Quick Test Mode - Backend Only")
        print("=" * 50)

        if start_backend():
            run_tests()
            print("\n[SUCCESS] Quick test completed!")
            print("Backend API: http://localhost:8201")
            print("API Docs: http://localhost:8201/docs")

            # 브라우저 열기
            try:
                webbrowser.open("http://localhost:8201/docs")
            except:
                pass

    elif choice == "2":
        print("\n" + "=" * 50)
        print("        Full System Mode")
        print("=" * 50)

        backend_ok = start_backend()
        frontend_ok = start_frontend()

        if backend_ok or frontend_ok:
            time.sleep(3)
            print("\n[SUCCESS] System started!")
            if frontend_ok:
                print("Frontend: http://localhost:5173")
                try:
                    webbrowser.open("http://localhost:5173")
                except:
                    pass
            if backend_ok:
                print("Backend: http://localhost:8201")
                print("API Docs: http://localhost:8201/docs")

    elif choice == "3":
        print("\n" + "=" * 50)
        print("           Docker Mode")
        print("=" * 50)

        if start_docker():
            print("\n[SUCCESS] Docker services started!")
            print("API Server: http://localhost:8080")
            print("Admin UI: http://localhost:5000")
            print("Qdrant: http://localhost:6333")
            print("MinIO Console: http://localhost:9001")

    elif choice == "4":
        print("\n" + "=" * 50)
        print("        Service Test Mode")
        print("=" * 50)

        run_tests()

        try:
            subprocess.run([sys.executable, "verify_setup.py"])
        except:
            print("[WARNING] Could not run verification")

        print("\n[SUCCESS] Service tests completed!")

    elif choice == "5":
        print("Goodbye!")
        return

    else:
        print("Invalid choice. Starting Quick Test Mode...")
        choice = "1"
        # 재귀 호출 대신 quick test 실행
        start_backend()
        run_tests()

    print("\n" + "=" * 50)
    print("      Services Running")
    print("=" * 50)
    print("\nTo stop services:")
    print("- Close the opened console windows")
    print("- For Docker: run 'docker-compose down'")
    print("\nPress Enter to exit this launcher...")
    input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutdown requested by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")