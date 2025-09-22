/**
 * ex-GPT API 서비스
 * 멀티모달 백엔드와 MCP 백엔드와의 통신을 담당
 */

// API 설정
const API_CONFIG = {
  // 통합 백엔드 (실제 VLM 백엔드 사용)
  BACKEND_BASE_URL: 'http://localhost:8201',  // 메인 백엔드 포트 수정
  TEST_BACKEND_URL: 'http://localhost:8200',  // 테스트 백엔드 추가

  // 기존 호환성을 위한 별칭
  MULTIMODAL_BASE_URL: 'http://localhost:8201',  // 메인 백엔드 포트 수정
  MCP_BASE_URL: 'http://localhost:8201',  // 메인 백엔드 포트 수정
  
  // 요청 타임아웃 설정
  TIMEOUT: 120000, // 120초로 증가 (VLM 모델 처리 시간 고려)
  HEALTH_CHECK_TIMEOUT: 5000, // 헬스 체크는 5초로 증가
  RETRY_COUNT: 1, // 재시도 횟수 감소 (타임아웃 증가로 보상)
  RETRY_DELAY: 2000, // 재시도 대기 시간 증가 (ms)
  
  // 기본 헤더
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  }
};

/**
 * CCTV 이미지 검색 API
 */
export class ImageSearchAPI {
  static async searchImages(query, page = 1, limit = 20) {
    let lastError;
    let useTestBackend = false;
    
    // 메인 백엔드로 시도, 실패 시 테스트 백엔드로 전환
    const backendUrls = [
      API_CONFIG.MULTIMODAL_BASE_URL,
      API_CONFIG.TEST_BACKEND_URL
    ];
    
    for (const baseUrl of backendUrls) {
      const backendType = baseUrl === API_CONFIG.TEST_BACKEND_URL ? '테스트' : '메인';
      
      for (let attempt = 0; attempt <= API_CONFIG.RETRY_COUNT; attempt++) {
        try {
          console.log(`이미지 검색 API 호출 [${backendType} 백엔드]: "${query}", 페이지: ${page}, 시도: ${attempt + 1}`);
          
          // 새로운 멀티모달 백엔드 API 엔드포인트 사용
          const url = `${baseUrl}/api/v1/search/images`;
        
        const requestBody = {
          query: query,
          limit: limit,
          offset: (page - 1) * limit,
          filters: {}
        };
          
          const response = await fetch(url, {
            method: 'POST',
            headers: API_CONFIG.DEFAULT_HEADERS,
            body: JSON.stringify(requestBody),
            signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log(`${backendType} 백엔드 이미지 검색 응답:`, data);
          
          // 성공한 경우 즉시 반환
          return {
            success: data.success !== false,
            backend: backendType,  // 사용된 백엔드 표시
            images: data.images || [],
            total_count: data.total_count || 0,
            has_more: data.has_more || false,
            page: page,
            processing_time: data.search_time_ms ? data.search_time_ms / 1000 : 0,
            query: data.query || query
          };
          
        } catch (error) {
          lastError = error;
          console.error(`${backendType} 백엔드 이미지 검색 API 오류 (시도 ${attempt + 1}):`, error);
          
          // 연결 거부나 네트워크 오류인 경우
          if (error.message.includes('Failed to fetch') || 
              error.message.includes('ERR_CONNECTION_REFUSED') ||
              error.name === 'TimeoutError') {
            console.log(`${backendType} 백엔드 서버에 연결할 수 없습니다. ${baseUrl === API_CONFIG.MULTIMODAL_BASE_URL && API_CONFIG.TEST_BACKEND_URL ? '테스트 백엔드로 전환합니다.' : ''}`);
            break;  // 현재 백엔드에서의 재시도 중단
          }
          
          // 마지막 시도가 아니면 대기 후 재시도
          if (attempt < API_CONFIG.RETRY_COUNT) {
            await new Promise(resolve => setTimeout(resolve, API_CONFIG.RETRY_DELAY));
          }
        }
      }
    }
    
    // 모든 시도 실패
    throw new Error(`이미지 검색 실패: ${lastError?.message || '알 수 없는 오류'}`);
  }

  static async uploadImageForSearch(file, description = '') {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', description);
      
      const response = await fetch(`${API_CONFIG.MULTIMODAL_BASE_URL}/api/v1/upload/image`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('이미지 업로드 API 오류:', error);
      throw new Error(`이미지 업로드 실패: ${error.message}`);
    }
  }
}

/**
 * 텍스트 채팅 API (멀티모달 백엔드 또는 MCP 백엔드)
 */
export class ChatAPI {
  static async sendMessage(messages, options = {}) {
    try {
      console.log('채팅 API 호출:', messages);
      
      // 먼저 멀티모달 백엔드 시도
      try {
        const requestBody = {
          messages: messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            image_url: msg.image_url || null
          })),
          session_id: options.session_id || null,
          user_id: options.user_id || null,
          temperature: options.temperature || 0.7,
          max_tokens: options.max_tokens || 1000
        };
        
        const response = await fetch(`${API_CONFIG.MULTIMODAL_BASE_URL}/api/v1/chat/multimodal`, {
          method: 'POST',
          headers: API_CONFIG.DEFAULT_HEADERS,
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('멀티모달 채팅 응답:', data);
          return data;
        }
      } catch (multimodalError) {
        console.log('멀티모달 백엔드 사용 불가, MCP 백엔드로 시도:', multimodalError.message);
      }
      
      // 멀티모달 백엔드 실패 시 MCP 백엔드 시도
      const requestBody = {
        stream: options.stream || false,
        history: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        message_id: options.message_id || null,
        session_id: options.session_id || null,
        user_id: options.user_id || null,
        department_id: options.department_id || null,
        search_documents: options.search_documents !== false,
        suggest_questions: options.suggest_questions || false,
        generate_search_query: options.generate_search_query !== false
      };
      
      console.log('보내는 요청 데이터:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(`${API_CONFIG.MCP_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS,
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });

      console.log('API 응답 상태:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('MCP 채팅 응답:', data);
      
      return data;
      
    } catch (error) {
      console.error('채팅 API 오류:', error);

      // 타임아웃 에러 특별 처리
      if (error.name === 'TimeoutError' || error.message.includes('timeout')) {
        throw new Error('요청 시간이 초과되었습니다. 서버가 응답하는데 시간이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.');
      }

      throw new Error(`채팅 요청 실패: ${error.message}`);
    }
  }

  static async sendStreamingMessage(messages, options = {}) {
    try {
      console.log('스트리밍 채팅 API 호출:', messages);
      
      const requestBody = {
        stream: true,
        history: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        session_id: options.session_id || null,
        user_id: options.user_id || null,
        department_id: options.department_id || null
      };
      
      console.log('스트리밍 요청 데이터:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(`${API_CONFIG.MCP_BASE_URL}/api/v1/chat`, {
        method: 'POST',
        headers: API_CONFIG.DEFAULT_HEADERS,
        body: JSON.stringify(requestBody),
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });

      console.log('스트리밍 응답 상태:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response; // EventSource 스트림 반환
      
    } catch (error) {
      console.error('스트리밍 채팅 API 오류:', error);
      throw new Error(`스트리밍 채팅 요청 실패: ${error.message}`);
    }
  }

  static async uploadFile(file, userId = null) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (userId) {
        formData.append('user_id', userId);
      }
      
      // 먼저 멀티모달 백엔드 시도
      try {
        const response = await fetch(`${API_CONFIG.MULTIMODAL_BASE_URL}/api/v1/upload/image`, {
          method: 'POST',
          body: formData,
          signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
        });
        
        if (response.ok) {
          return await response.json();
        }
      } catch (multimodalError) {
        console.log('멀티모달 백엔드 파일 업로드 실패, MCP 백엔드로 시도');
      }
      
      // MCP 백엔드 시도
      const response = await fetch(`${API_CONFIG.MCP_BASE_URL}/api/v1/files/upload`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('파일 업로드 API 오류:', error);
      throw new Error(`파일 업로드 실패: ${error.message}`);
    }
  }
}

/**
 * 헬스 체크 API
 */
export class HealthAPI {
  static async checkBackendHealth(baseUrl, backendName) {
    try {
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(API_CONFIG.HEALTH_CHECK_TIMEOUT)
      });
      
      if (response.ok) {
        const data = await response.json();
        return { status: 'healthy', backend: backendName, ...data };
      } else {
        return { status: 'error', backend: backendName, message: `${backendName} backend not responding` };
      }
    } catch (error) {
      // 연결 거부 에러를 더 명확하게 처리
      if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        return { status: 'offline', backend: backendName, message: `${backendName} 서버가 실행되지 않습니다` };
      }
      if (error.name === 'TimeoutError') {
        return { status: 'timeout', backend: backendName, message: `${backendName} 서버 응답 시간 초과` };
      }
      return { status: 'error', backend: backendName, message: error.message };
    }
  }

  static async checkMultimodalBackend() {
    // 메인 백엔드로 먼저 시도
    const mainResult = await this.checkBackendHealth(API_CONFIG.MULTIMODAL_BASE_URL, '메인');
    if (mainResult.status === 'healthy') {
      return mainResult;
    }
    
    // 메인 백엔드 실패 시 테스트 백엔드 시도
    console.log('메인 백엔드 상태:', mainResult.status, '- 테스트 백엔드로 전환');
    const testResult = await this.checkBackendHealth(API_CONFIG.TEST_BACKEND_URL, '테스트');
    
    // 테스트 백엔드가 정상이면 그 결과 반환, 아니면 메인 백엔드 결과 반환
    return testResult.status === 'healthy' ? testResult : mainResult;
  }

  static async checkMCPBackend() {
    try {
      const response = await fetch(`${API_CONFIG.MCP_BASE_URL}/api/v1/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(API_CONFIG.HEALTH_CHECK_TIMEOUT)
      });
      
      if (response.ok) {
        const data = await response.json();
        return { status: 'healthy', ...data };
      } else {
        return { status: 'error', message: 'MCP backend not responding' };
      }
    } catch (error) {
      // 연결 거부 에러를 더 명확하게 처리
      if (error.message.includes('Failed to fetch')) {
        return { status: 'offline', message: '백엔드 서버가 실행되지 않습니다' };
      }
      return { status: 'error', message: error.message };
    }
  }

  static async checkAllServices() {
    const [multimodal, mcp] = await Promise.allSettled([
      this.checkMultimodalBackend(),
      this.checkMCPBackend()
    ]);

    return {
      multimodal: multimodal.status === 'fulfilled' ? multimodal.value : { status: 'error', message: multimodal.reason.message },
      mcp: mcp.status === 'fulfilled' ? mcp.value : { status: 'error', message: mcp.reason.message }
    };
  }
}

/**
 * 통합 API 서비스
 */
export class ExGPTAPI {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.userId = null;
    this.departmentId = null;
  }

  generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  setUserInfo(userId, departmentId) {
    this.userId = userId;
    this.departmentId = departmentId;
  }

  /**
   * 통합 검색 함수 - 이미지와 텍스트를 모두 처리
   */
  async search(query, options = {}) {
    try {
      // 이미지 검색 키워드 감지
      const imageKeywords = [
        '사진', '이미지', '그림', '해무', '안개', 'cctv', '카메라', 
        '날씨', '시야', '가시거리', '강우', '강설', '야간', '맑음',
        '경부고속도로', '중부고속도로', '서해안고속도로'
      ];
      
      const hasImageKeyword = imageKeywords.some(keyword => 
        query.toLowerCase().includes(keyword.toLowerCase())
      );
      
      if (hasImageKeyword) {
        // 이미지 검색 실행
        console.log('이미지 검색 모드');
        return await ImageSearchAPI.searchImages(
          query, 
          options.page || 1, 
          options.limit || 20
        );
      } else {
        // 텍스트 채팅 실행
        console.log('텍스트 채팅 모드');
        const messages = [
          { role: 'user', content: query }
        ];
        
        const response = await ChatAPI.sendMessage(messages, {
          session_id: this.sessionId,
          user_id: this.userId,
          department_id: this.departmentId,
          ...options
        });
        
        return {
          success: true,
          type: 'chat',
          response: response.response,
          sources: response.sources,
          suggested_questions: response.suggested_questions,
          metadata: response.metadata,
          session_id: response.session_id,
          message_id: response.message_id
        };
      }
    } catch (error) {
      console.error('통합 검색 오류:', error);
      throw error;
    }
  }
}

// 기본 내보내기
export default ExGPTAPI;

// API 설정 내보내기
export { API_CONFIG };

// 개발 모드에서 사용할 목 데이터 호환 함수
export const simulateApiCall = async (query, page = 1, limit = 20) => {
  console.warn('simulateApiCall은 개발 모드 전용입니다. 실제 API를 사용하세요.');
  
  try {
    const api = new ExGPTAPI();
    const result = await api.search(query, { page, limit });
    
    // 목 데이터 형식으로 변환
    if (result.type === 'chat') {
      return {
        success: true,
        results: [],
        total: 0,
        hasMore: false,
        page: page,
        limit: limit,
        query: query,
        processingTime: result.metadata?.response_time_ms / 1000 || 0
      };
    } else {
      return {
        success: true,
        results: result.images || [],
        total: result.total_count || 0,
        hasMore: result.has_more || false,
        page: result.page || page,
        limit: limit,
        query: query,
        processingTime: result.processing_time || 0
      };
    }
  } catch (error) {
    throw new Error(`API 호출 실패: ${error.message}`);
  }
};
