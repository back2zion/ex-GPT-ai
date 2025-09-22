# ex-GPT 시스템 복구 가이드

## 현재 상황
- 기본 테스트 페이지로 전환 완료
- 복잡한 컴포넌트들을 일시 비활성화

## 단계별 복구 방법

### 1단계: 기본 동작 확인 ✅
- App_simple.jsx로 기본 페이지 표시
- React 앱 정상 동작 확인

### 2단계: 전체 기능 활성화
기본 테스트가 성공하면 main.jsx를 다시 수정:

```javascript
// main.jsx 수정
import App from './App.jsx'  // App_simple.jsx -> App.jsx로 변경
```

### 3단계: 컴포넌트별 점진적 활성화
만약 전체 App.jsx에서 오류가 발생하면:

1. **SearchHistory 컴포넌트 비활성화**
```jsx
// App.jsx에서 임시 주석 처리
{/* <SearchHistory
  onSearchSelect={handleHistorySearchSelect}
  currentQuery={inputValue}
  className="search-history-widget"
/> */}
```

2. **EnhancedImageSearchResults 단순화**
```jsx
// 기존 컴포넌트 대신 단순 버전 사용
import ImageSearchResults from "./components/content/ImageSearch/ImageSearchResults";
```

### 4단계: 오류 진단
브라우저 콘솔에서 확인할 오류들:

- **Module not found**: 파일 경로 오류
- **Syntax error**: 문법 오류  
- **Cannot read property**: undefined 변수 접근
- **SCSS compilation error**: 스타일 시트 오류

### 5단계: 개발 서버 재시작
```bash
# Ctrl+C로 서버 중지 후
npm run dev
```

## 일반적인 해결책

### 포트 변경
```bash
npm run dev -- --port 3000
```

### 캐시 클리어
```bash
npm run build
rm -rf node_modules/.vite
npm run dev
```

### 종속성 재설치
```bash
npm install --force
```

## 현재 테스트 상태
✅ App_simple.jsx 활성화됨
⏳ 전체 기능 대기 중
📱 http://localhost:5173 접속 가능