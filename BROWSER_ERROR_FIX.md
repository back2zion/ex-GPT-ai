# 브라우저 확장 프로그램 에러 해결 가이드

## 에러 분석
```
content.js:246 Uncaught TypeError: Cannot read properties of undefined (reading 'sendMessage')
```

이 에러는 **ex-GPT 프로젝트와 무관한 브라우저 확장 프로그램 에러**입니다.

## 에러 원인
- Chrome/Edge 브라우저에 설치된 확장 프로그램 충돌
- 특히 `sendMessage` API를 사용하는 확장 프로그램의 문제
- 가능성 있는 확장 프로그램:
  - 번역 확장 프로그램
  - 광고 차단기
  - VPN 확장 프로그램
  - 개발자 도구 확장 프로그램
  - AI 어시스턴트 확장 프로그램

## 해결 방법

### 방법 1: 시크릿/프라이빗 모드 사용 (즉시 해결)
1. Chrome: `Ctrl+Shift+N` (시크릿 모드)
2. Edge: `Ctrl+Shift+N` (InPrivate 모드)
3. Firefox: `Ctrl+Shift+P` (프라이빗 창)
4. http://localhost:5173 접속

### 방법 2: 문제 확장 프로그램 찾기
1. Chrome 주소창에 `chrome://extensions/` 입력 (Edge는 `edge://extensions/`)
2. 모든 확장 프로그램 비활성화
3. ex-GPT 테스트
4. 하나씩 활성화하며 문제 확장 프로그램 찾기

### 방법 3: 특정 확장 프로그램 비활성화
충돌 가능성이 높은 확장 프로그램들:
- Grammarly
- Google Translate
- LastPass
- Honey
- AdBlock/uBlock Origin
- React Developer Tools (가끔 충돌)
- Any AI Assistant extensions

### 방법 4: 개발자 모드로 실행 (권장)
```bash
# 새 Chrome 프로필로 실행
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%TEMP%\chrome_dev" --disable-extensions

# Edge의 경우
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --user-data-dir="%TEMP%\edge_dev" --disable-extensions
```

## ex-GPT 프로젝트에 영향이 없음을 확인

### 테스트 방법
1. 브라우저 콘솔 열기 (F12)
2. Console 탭에서 필터 설정:
   - `content.js` 메시지 필터링 (제외)
   - ex-GPT 관련 메시지만 표시

### 콘솔 필터 설정
```javascript
// 콘솔에서 실행
console.clear();
console.log('%c ex-GPT 시스템 로그만 표시', 'color: green; font-weight: bold');
```

## 개발 환경 최적화

### VS Code 설정 (브라우저 충돌 방지)
`.vscode/launch.json` 파일:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome for ex-GPT",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/frontend",
      "runtimeArgs": [
        "--disable-extensions",
        "--disable-web-security",
        "--user-data-dir=${workspaceFolder}/.chrome"
      ]
    }
  ]
}
```

## 프로젝트 실행 확인

### 정상 동작 확인 체크리스트
- [ ] 프론트엔드 로딩 완료 (http://localhost:5173)
- [ ] 백엔드 연결 상태 표시
- [ ] 이미지 검색 기능 작동
- [ ] 채팅 기능 작동
- [ ] 콘솔에 ex-GPT 관련 에러 없음

### 무시해도 되는 에러들
- `content.js` 관련 모든 에러
- 확장 프로그램 관련 에러
- `chrome-extension://` 로 시작하는 URL 에러

## 추가 도움

이 에러는 ex-GPT 시스템 동작에 영향을 주지 않습니다.
계속 에러가 거슬린다면:

1. 브라우저 콘솔에서 우클릭
2. "Hide messages from content.js" 선택
3. 또는 Filter에 `-content.js` 입력

## 문의사항
프로젝트 관련 실제 에러가 있다면:
- `App.jsx` 에러
- `exgptAPI.js` 에러  
- `main.py` 에러
- 위 파일들의 에러만 보고해주세요.
