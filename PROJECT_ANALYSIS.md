# ex-GPT AI 프로젝트 분석

## 프로젝트 개요

**한국도로공사 전용 멀티모달 AI 시스템**
- 목표: UI에서 질의를 통해 CCTV 이미지를 검색하고 출력창에 표시
- 주요 기능: 이미지 검색, 멀티모달 채팅, 관리자 시스템 연동

## 전체 폴더 구조

```
ex-GPT-ai/
├── admin/                  # Spring Boot 관리자 패널 (Java 17)
│   ├── src/
│   │   └── main/
│   │       ├── java/       # Java 소스 코드
│   │       └── resources/
│   │           └── templates/  # Thymeleaf 템플릿
│   │               ├── html/   # 관리 페이지들
│   │               ├── js/     # JavaScript 파일들
│   │               └── *.html  # 메인 페이지들
│   ├── target/             # 빌드 결과물
│   └── pom.xml            # Maven 설정
│
├── backend/               # FastAPI 백엔드 서버 (Python)
│   ├── app/              # 애플리케이션 코드
│   │   ├── __init__.py
│   │   ├── services/     # 비즈니스 로직
│   │   ├── models/       # 데이터 모델
│   │   ├── api/          # API 라우터
│   │   └── core/         # 핵심 설정
│   ├── .venv/            # Python 가상환경
│   ├── main.py           # FastAPI 메인 애플리케이션
│   ├── .env              # 환경 변수
│   └── tests/            # 테스트 파일
│
├── frontend/             # React 프론트엔드 (Vite)
│   ├── src/
│   │   ├── App.jsx       # 메인 React 컴포넌트
│   │   ├── components/   # UI 컴포넌트들
│   │   │   ├── common/   # 공통 컴포넌트
│   │   │   ├── content/  # 컨텐츠 컴포넌트
│   │   │   └── modals/   # 모달 컴포넌트
│   │   ├── assets/       # 아이콘, 이미지
│   │   └── utils/        # 유틸리티 함수
│   ├── node_modules/     # Node.js 의존성
│   ├── package.json      # npm 설정
│   └── index.html        # HTML 엔트리 포인트
│
├── data/                 # 데이터 폴더 (CCTV 이미지 등)
├── .claude/              # Claude Code 설정
├── README.md             # 프로젝트 문서
├── SETUP_AND_RUN.bat     # 설치 스크립트
└── START.bat             # 시작 스크립트
```

## 기술 스택 분석

### 1. 백엔드 (backend/)
- **프레임워크**: FastAPI (Python)
- **포트**: 8001
- **주요 기능**:
  - 이미지 검색 API (`/api/v1/search/images`)
  - 멀티모달 채팅 API (`/api/v1/chat/multimodal`)
  - 헬스체크 API (`/health`, `/api/v1/health`)
  - 이미지 서빙 (`/api/v1/images/{image_path}`)
- **AI 모델**: Ollama 클라이언트 (qwen3:8b, llava:7b)
- **이미지 폴더**: `C:\Users\user\Documents\interim_report\188.해무, 안개 CCTV 데이터`

### 2. 프론트엔드 (frontend/)
- **프레임워크**: React 19.1.1 + Vite
- **포트**: 5173 (개발 서버)
- **주요 컴포넌트**:
  - `EnhancedImageSearchResults`: 이미지 검색 결과 표시
  - `SearchHistory`: 검색 기록 관리
  - `FontSizeModal`, `NoticeModal`, `SurveyModal`: 각종 모달
- **UI 라이브러리**:
  - react-slick (이미지 슬라이더)
  - Sass (스타일링)
- **API 연동**: ExGPTAPI 유틸리티로 백엔드 통신

### 3. 관리자 패널 (admin/)
- **프레임워크**: Spring Boot 3.5.4
- **언어**: Java 17
- **템플릿 엔진**: Thymeleaf
- **보안**: Spring Security
- **주요 기능**:
  - 문서권한관리
  - 문서등록관리
  - 로그인 시스템
- **UI 라이브러리**: ag-Grid, jQuery

## 핵심 기능 구현 현황

### ✅ 이미지 검색 기능
- **백엔드**: `ImageSearchService`로 Ollama 기반 이미지 검색
- **프론트엔드**: `EnhancedImageSearchResults` 컴포넌트로 검색 결과 표시
- **API**: POST `/api/v1/search/images`

### ✅ 멀티모달 채팅
- **백엔드**: `MultimodalChatService`로 텍스트+이미지 처리
- **AI 모델**: llava:7b (비전 언어 모델)
- **API**: POST `/api/v1/chat/multimodal`

### ✅ 관리자 시스템
- **Spring Boot** 기반 독립적인 관리 시스템
- **문서 관리** 및 **권한 관리** 기능
- **Thymeleaf** 템플릿으로 웹 UI 제공

## 시스템 아키텍처

```
[사용자]
    ↓ (질의)
[React Frontend:5173]
    ↓ (API 호출)
[FastAPI Backend:8001]
    ↓ (AI 처리)
[Ollama Client] → [qwen3:8b / llava:7b]
    ↓ (이미지 검색)
[CCTV 이미지 데이터베이스]

[관리자]
    ↓
[Spring Boot Admin] → [문서/권한 관리]
```

## 목표 달성을 위한 현재 상태

### ✅ 완료된 기능
1. **UI에서 질의 입력**: React 프론트엔드에서 검색 쿼리 입력 가능
2. **이미지 검색**: 백엔드에서 Ollama 기반 이미지 검색 구현
3. **출력창 표시**: `EnhancedImageSearchResults` 컴포넌트로 검색 결과 표시
4. **Admin 연동**: Spring Boot 관리자 패널 독립 운영

### 🔄 개선 필요 사항
1. **검색 정확도 향상**: AI 모델 튜닝 및 검색 알고리즘 최적화
2. **UI/UX 개선**: 이미지 그리드 레이아웃 및 검색 인터페이스 개선
3. **Admin 연동 강화**: 관리자 패널과 메인 시스템 간 데이터 연동
4. **성능 최적화**: 대용량 이미지 처리 및 검색 속도 개선

## 실행 방법

1. **전체 시스템 시작**: `START.bat` 실행
2. **개별 서비스**:
   - Frontend: `cd frontend && npm run dev`
   - Backend: `cd backend && python main.py`
   - Admin: Spring Boot 애플리케이션 실행

## 포트 정보
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8001
- **Admin**: 별도 포트 (Spring Boot 기본 설정)

---
*한국도로공사 디지털기획부 내부 사용*