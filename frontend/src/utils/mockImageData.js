// 테스트용 목 데이터 생성기
export const generateMockImageData = (count = 50) => {
  const locations = [
    '경부고속도로 서울IC',
    '중부고속도로 하남IC',
    '영동고속도로 강릉IC',
    '서해안고속도로 목포IC',
    '중앙고속도로 춘천IC',
    '남해고속도로 부산IC',
    '호남고속도로 광주IC',
    '서울외곽순환고속도로 판교IC',
    '인천국제공항고속도로 공항IC',
    '제2경인고속도로 부천IC'
  ];

  const imageTypes = [
    { type: 'fog', description: '해무/안개' },
    { type: 'rain', description: '강우' },
    { type: 'snow', description: '강설' },
    { type: 'clear', description: '맑음' },
    { type: 'night', description: '야간' }
  ];

  const mockImages = [];

  for (let i = 0; i < count; i++) {
    const location = locations[Math.floor(Math.random() * locations.length)];
    const imageType = imageTypes[Math.floor(Math.random() * imageTypes.length)];
    const similarity = 0.6 + Math.random() * 0.4; // 0.6-1.0 범위
    const timestamp = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000); // 최근 30일

    // 간단한 색상 기반 썸네일 생성 (실제 환경에서는 실제 이미지 사용)
    const colors = {
      fog: '#808080',
      rain: '#4a90e2',
      snow: '#ffffff',
      clear: '#87ceeb',
      night: '#2c3e50'
    };

    const thumbnailSvg = `
      <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="300" height="200" fill="${colors[imageType.type]}"/>
        <text x="150" y="100" text-anchor="middle" fill="white" font-family="Arial" font-size="14">
          ${imageType.description}
        </text>
        <text x="150" y="120" text-anchor="middle" fill="white" font-family="Arial" font-size="12">
          ${location}
        </text>
        <text x="150" y="140" text-anchor="middle" fill="white" font-family="Arial" font-size="10">
          유사도: ${(similarity * 100).toFixed(1)}%
        </text>
      </svg>
    `;

    const thumbnail = btoa(unescape(encodeURIComponent(thumbnailSvg)));

    mockImages.push({
      filename: `CCTV_${timestamp.getFullYear()}${(timestamp.getMonth() + 1).toString().padStart(2, '0')}${timestamp.getDate().toString().padStart(2, '0')}_${i.toString().padStart(3, '0')}.jpg`,
      location: location,
      similarity: similarity,
      thumbnail: thumbnail,
      image_url: `data:image/svg+xml;base64,${thumbnail}`,
      timestamp: timestamp.toISOString(),
      weather_condition: imageType.description,
      camera_id: `CAM_${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`,
      coordinates: {
        lat: 37.5665 + (Math.random() - 0.5) * 2,
        lng: 126.9780 + (Math.random() - 0.5) * 2
      }
    });
  }

  return mockImages.sort((a, b) => b.similarity - a.similarity);
};

// API 응답 시뮬레이터
export const simulateApiCall = async (query, page = 1, limit = 20) => {
  // 실제 API 호출과 유사한 지연 시간
  await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

  const allImages = generateMockImageData(200);
  
  // 쿼리에 따른 필터링 시뮬레이션
  let filteredImages = allImages;
  
  if (query) {
    const queryLower = query.toLowerCase();
    filteredImages = allImages.filter(img => 
      img.location.toLowerCase().includes(queryLower) ||
      img.weather_condition.toLowerCase().includes(queryLower) ||
      img.filename.toLowerCase().includes(queryLower)
    );
  }

  // 페이지네이션
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const paginatedResults = filteredImages.slice(startIndex, endIndex);

  // 에러 시뮬레이션 (5% 확률)
  if (Math.random() < 0.05) {
    throw new Error('네트워크 연결 오류: 잠시 후 다시 시도해주세요.');
  }

  return {
    success: true,
    results: paginatedResults,
    total: filteredImages.length,
    hasMore: endIndex < filteredImages.length,
    page: page,
    limit: limit,
    query: query,
    processingTime: Math.random() * 2 + 0.5 // 0.5-2.5초 범위
  };
};

// 실시간 검색 시뮬레이터
export class MockSearchService {
  constructor() {
    this.cache = new Map();
    this.searchHistory = [];
  }

  async search(query, options = {}) {
    const { page = 1, limit = 20, sortBy = 'relevance', filterBy = 'all' } = options;
    
    // 캐시 확인
    const cacheKey = `${query}-${page}-${limit}-${sortBy}-${filterBy}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    try {
      const result = await simulateApiCall(query, page, limit);
      
      // 정렬 적용
      if (sortBy === 'similarity') {
        result.results.sort((a, b) => b.similarity - a.similarity);
      } else if (sortBy === 'date') {
        result.results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      }

      // 필터 적용
      if (filterBy === 'recent') {
        const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
        result.results = result.results.filter(img => new Date(img.timestamp) > dayAgo);
      } else if (filterBy === 'high-similarity') {
        result.results = result.results.filter(img => img.similarity > 0.8);
      }

      // 캐시 저장 (최대 100개 항목)
      if (this.cache.size >= 100) {
        const firstKey = this.cache.keys().next().value;
        this.cache.delete(firstKey);
      }
      this.cache.set(cacheKey, result);

      // 검색 히스토리 업데이트
      if (query && !this.searchHistory.includes(query)) {
        this.searchHistory.unshift(query);
        this.searchHistory = this.searchHistory.slice(0, 10); // 최근 10개만 유지
      }

      return result;
    } catch (error) {
      console.error('검색 중 오류 발생:', error);
      throw error;
    }
  }

  getSearchHistory() {
    return this.searchHistory;
  }

  clearCache() {
    this.cache.clear();
  }
}

// 글로벌 목 서비스 인스턴스
export const mockSearchService = new MockSearchService();

export default {
  generateMockImageData,
  simulateApiCall,
  MockSearchService,
  mockSearchService
};