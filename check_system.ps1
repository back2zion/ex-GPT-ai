# ex-GPT 시스템 진단 스크립트
# PowerShell 실행: powershell -ExecutionPolicy Bypass -File check_system.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   ex-GPT 시스템 상태 진단 도구" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 색상 정의
$Success = "Green"
$Warning = "Yellow"
$Error = "Red"
$Info = "Cyan"

# 포트 확인 함수
function Test-Port {
    param($hostname, $port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient($hostname, $port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# 1. Python 확인
Write-Host "[1/6] Python 설치 확인..." -ForegroundColor $Info
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python 설치됨: $pythonVersion" -ForegroundColor $Success
} catch {
    Write-Host "  ✗ Python이 설치되지 않았습니다" -ForegroundColor $Error
    Write-Host "    → python.org에서 Python 3.10+ 설치 필요" -ForegroundColor $Warning
}

# 2. Node.js 확인
Write-Host "[2/6] Node.js 설치 확인..." -ForegroundColor $Info
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js 설치됨: $nodeVersion" -ForegroundColor $Success
} catch {
    Write-Host "  ✗ Node.js가 설치되지 않았습니다" -ForegroundColor $Error
    Write-Host "    → nodejs.org에서 Node.js 18+ 설치 필요" -ForegroundColor $Warning
}

# 3. 프론트엔드 포트 확인 (5173)
Write-Host "[3/6] 프론트엔드 서버 확인 (포트 5173)..." -ForegroundColor $Info
if (Test-Port "localhost" 5173) {
    Write-Host "  ✓ 프론트엔드 실행 중" -ForegroundColor $Success
    Write-Host "    URL: http://localhost:5173" -ForegroundColor $Info
} else {
    Write-Host "  ✗ 프론트엔드가 실행되지 않음" -ForegroundColor $Warning
}

# 4. 메인 백엔드 포트 확인 (8200)
Write-Host "[4/6] 메인 백엔드 서버 확인 (포트 8200)..." -ForegroundColor $Info
if (Test-Port "localhost" 8200) {
    Write-Host "  ✓ 메인 백엔드 실행 중" -ForegroundColor $Success
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8200/health" -UseBasicParsing -TimeoutSec 2
        Write-Host "    상태: 정상" -ForegroundColor $Success
    } catch {
        Write-Host "    상태: 초기화 중..." -ForegroundColor $Warning
    }
} else {
    Write-Host "  ✗ 메인 백엔드가 실행되지 않음" -ForegroundColor $Warning
}

# 5. 테스트 백엔드 포트 확인 (8201)
Write-Host "[5/6] 테스트 백엔드 서버 확인 (포트 8201)..." -ForegroundColor $Info
if (Test-Port "localhost" 8201) {
    Write-Host "  ✓ 테스트 백엔드 실행 중" -ForegroundColor $Success
    Write-Host "    URL: http://localhost:8201/docs" -ForegroundColor $Info
} else {
    Write-Host "  ✗ 테스트 백엔드가 실행되지 않음" -ForegroundColor $Error
}

# 6. Ollama 서버 확인 (11434)
Write-Host "[6/6] Ollama 서버 확인 (포트 11434)..." -ForegroundColor $Info
if (Test-Port "localhost" 11434) {
    Write-Host "  ✓ Ollama 서버 실행 중" -ForegroundColor $Success
} else {
    Write-Host "  ○ Ollama 서버 미실행 (선택사항)" -ForegroundColor $Warning
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "            진단 결과 요약" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

# 시스템 상태 판단
$frontendRunning = Test-Port "localhost" 5173
$testBackendRunning = Test-Port "localhost" 8201
$mainBackendRunning = Test-Port "localhost" 8200

if ($frontendRunning -and $testBackendRunning) {
    Write-Host ""
    Write-Host "✅ 시스템이 정상적으로 작동 중입니다!" -ForegroundColor $Success
    Write-Host ""
    Write-Host "접속 URL: http://localhost:5173" -ForegroundColor $Info
    Write-Host "API 문서: http://localhost:8201/docs" -ForegroundColor $Info
} elseif (-not $frontendRunning -and -not $testBackendRunning) {
    Write-Host ""
    Write-Host "⚠️ 시스템이 실행되지 않았습니다." -ForegroundColor $Warning
    Write-Host ""
    Write-Host "시작 방법:" -ForegroundColor $Info
    Write-Host "  1. ex-GPT-ai 폴더에서" -ForegroundColor White
    Write-Host "  2. START_QUICK.bat 실행" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️ 일부 서비스만 실행 중입니다." -ForegroundColor $Warning
    Write-Host ""
    if (-not $frontendRunning) {
        Write-Host "프론트엔드 시작:" -ForegroundColor $Info
        Write-Host "  cd frontend && npm run dev" -ForegroundColor White
    }
    if (-not $testBackendRunning) {
        Write-Host "백엔드 시작:" -ForegroundColor $Info
        Write-Host "  cd backend && python simple_test.py" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "브라우저 에러 해결:" -ForegroundColor $Info
Write-Host "  content.js 에러는 브라우저 확장 프로그램 문제입니다." -ForegroundColor White
Write-Host "  시크릿/프라이빗 모드로 실행하면 해결됩니다." -ForegroundColor White
Write-Host ""

# 대기
Write-Host "종료하려면 아무 키나 누르세요..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
