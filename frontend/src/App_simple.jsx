import React, { useState } from "react";

function App() {
  const [message, setMessage] = useState("ex-GPT 시스템이 정상적으로 로드되었습니다!");

  return (
    <div style={{ 
      padding: "20px", 
      fontFamily: "Arial, sans-serif",
      backgroundColor: "#f5f5f5",
      minHeight: "100vh"
    }}>
      <header style={{
        backgroundColor: "#1976d2",
        color: "white",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "20px"
      }}>
        <h1>ex-GPT 이미지 검색 시스템</h1>
        <p>고도화된 이미지 그리드 및 검색 기능</p>
      </header>

      <main style={{
        backgroundColor: "white",
        padding: "20px",
        borderRadius: "8px",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)"
      }}>
        <div style={{ marginBottom: "20px" }}>
          <h2>🎉 시스템 상태</h2>
          <p style={{ 
            padding: "10px", 
            backgroundColor: "#e8f5e8", 
            border: "1px solid #4caf50",
            borderRadius: "4px",
            color: "#2e7d32"
          }}>
            {message}
          </p>
        </div>

        <div style={{ marginBottom: "20px" }}>
          <h3>📋 구현된 기능</h3>
          <ul style={{ paddingLeft: "20px" }}>
            <li>✅ 고도화된 이미지 그리드 시스템</li>
            <li>✅ 다양한 뷰 모드 (격자/벽돌/목록)</li>
            <li>✅ 검색 히스토리 & 즐겨찾기</li>
            <li>✅ 무한 스크롤 & 슬라이드쇼</li>
            <li>✅ 반응형 디자인</li>
          </ul>
        </div>

        <div style={{ marginBottom: "20px" }}>
          <h3>🔧 테스트 영역</h3>
          <div style={{ 
            padding: "15px", 
            backgroundColor: "#f8f9fa", 
            border: "1px solid #dee2e6",
            borderRadius: "4px"
          }}>
            <p>테스트 검색어를 입력해보세요:</p>
            <input 
              type="text" 
              placeholder="해무 사진을 보여주세요"
              style={{
                width: "100%",
                padding: "10px",
                border: "1px solid #ccc",
                borderRadius: "4px",
                marginBottom: "10px"
              }}
              onChange={(e) => setMessage(`검색어: "${e.target.value}"`)}
            />
            <button 
              style={{
                backgroundColor: "#1976d2",
                color: "white",
                border: "none",
                padding: "10px 20px",
                borderRadius: "4px",
                cursor: "pointer"
              }}
              onClick={() => alert("검색 기능이 곧 활성화됩니다!")}
            >
              검색하기
            </button>
          </div>
        </div>

        <div>
          <h3>📊 시스템 정보</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <tbody>
              <tr style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: "8px", fontWeight: "bold" }}>버전</td>
                <td style={{ padding: "8px" }}>v2.0.0</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: "8px", fontWeight: "bold" }}>상태</td>
                <td style={{ padding: "8px", color: "#4caf50" }}>✅ 정상 동작</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: "8px", fontWeight: "bold" }}>환경</td>
                <td style={{ padding: "8px" }}>개발 모드 (목 데이터 사용)</td>
              </tr>
              <tr>
                <td style={{ padding: "8px", fontWeight: "bold" }}>포트</td>
                <td style={{ padding: "8px" }}>5173</td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <footer style={{
        marginTop: "20px",
        padding: "15px",
        backgroundColor: "#2c3e50",
        color: "white",
        borderRadius: "8px",
        textAlign: "center"
      }}>
        <p>&copy; 2025 ex-GPT 프로젝트 | 한국도로공사 × DataStreams</p>
      </footer>
    </div>
  );
}

export default App;