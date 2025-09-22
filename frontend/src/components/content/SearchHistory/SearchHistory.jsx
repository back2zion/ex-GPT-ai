import React, { useState, useEffect } from 'react';
import './searchHistory.scss';

const SearchHistory = ({ 
  onSearchSelect, 
  currentQuery = '',
  className = '' 
}) => {
  const [searchHistory, setSearchHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState('recent'); // 'recent' or 'favorites'

  // 로컬 스토리지에서 검색 히스토리 및 즐겨찾기 로드
  useEffect(() => {
    const savedHistory = JSON.parse(localStorage.getItem('ex-gpt-search-history') || '[]');
    const savedFavorites = JSON.parse(localStorage.getItem('ex-gpt-search-favorites') || '[]');
    
    setSearchHistory(savedHistory);
    setFavorites(savedFavorites);
  }, []);

  // 검색 히스토리 저장
  const saveHistory = (history) => {
    localStorage.setItem('ex-gpt-search-history', JSON.stringify(history));
  };

  // 즐겨찾기 저장
  const saveFavorites = (favs) => {
    localStorage.setItem('ex-gpt-search-favorites', JSON.stringify(favs));
  };

  // 새 검색어 추가
  const addToHistory = (query) => {
    if (!query.trim()) return;

    const newHistory = [
      query,
      ...searchHistory.filter(item => item !== query)
    ].slice(0, 10); // 최대 10개 유지

    setSearchHistory(newHistory);
    saveHistory(newHistory);
  };

  // 즐겨찾기 토글
  const toggleFavorite = (query) => {
    const newFavorites = favorites.includes(query)
      ? favorites.filter(item => item !== query)
      : [...favorites, query].slice(0, 5); // 최대 5개 유지

    setFavorites(newFavorites);
    saveFavorites(newFavorites);
  };

  // 히스토리에서 항목 제거
  const removeFromHistory = (query) => {
    const newHistory = searchHistory.filter(item => item !== query);
    setSearchHistory(newHistory);
    saveHistory(newHistory);
  };

  // 전체 히스토리 클리어
  const clearHistory = () => {
    setSearchHistory([]);
    saveHistory([]);
  };

  // 검색어 선택 핸들러
  const handleSearchSelect = (query) => {
    addToHistory(query);
    onSearchSelect(query);
    setIsExpanded(false);
  };

  // 외부에서 호출할 수 있도록 히스토리 추가 함수 노출
  useEffect(() => {
    if (currentQuery) {
      addToHistory(currentQuery);
    }
  }, [currentQuery]);

  // 인기 검색어 (정적 데이터, 실제로는 서버에서 가져와야 함)
  const popularSearches = [
    '해무 안개 사진',
    '고속도로 CCTV',
    '강우 시 도로상황',
    '야간 톨게이트',
    '경부고속도로 서울IC'
  ];

  if (!isExpanded && searchHistory.length === 0 && favorites.length === 0) {
    return null;
  }

  return (
    <div className={`search-history ${className}`}>
      {/* 토글 버튼 */}
      <button
        className="search-history-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        title="검색 히스토리"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
          <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
        </svg>
        {searchHistory.length > 0 && (
          <span className="history-count">{searchHistory.length}</span>
        )}
      </button>

      {/* 히스토리 패널 */}
      {isExpanded && (
        <div className="search-history-panel">
          {/* 탭 헤더 */}
          <div className="history-tabs">
            <button
              className={`tab-button ${activeTab === 'recent' ? 'active' : ''}`}
              onClick={() => setActiveTab('recent')}
            >
              최근 검색
            </button>
            <button
              className={`tab-button ${activeTab === 'favorites' ? 'active' : ''}`}
              onClick={() => setActiveTab('favorites')}
            >
              즐겨찾기
            </button>
            <button
              className={`tab-button ${activeTab === 'popular' ? 'active' : ''}`}
              onClick={() => setActiveTab('popular')}
            >
              인기 검색
            </button>
          </div>

          {/* 탭 컨텐츠 */}
          <div className="history-content">
            {/* 최근 검색 */}
            {activeTab === 'recent' && (
              <div className="recent-searches">
                {searchHistory.length > 0 ? (
                  <>
                    <div className="history-header">
                      <span>최근 검색어</span>
                      <button 
                        className="clear-button"
                        onClick={clearHistory}
                        title="전체 삭제"
                      >
                        전체삭제
                      </button>
                    </div>
                    <div className="history-list">
                      {searchHistory.map((query, index) => (
                        <div key={index} className="history-item">
                          <button
                            className="search-query"
                            onClick={() => handleSearchSelect(query)}
                            title={`"${query}" 다시 검색`}
                          >
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                            </svg>
                            <span className="query-text">{query}</span>
                          </button>
                          <div className="item-actions">
                            <button
                              className={`favorite-button ${favorites.includes(query) ? 'active' : ''}`}
                              onClick={() => toggleFavorite(query)}
                              title={favorites.includes(query) ? '즐겨찾기 해제' : '즐겨찾기 추가'}
                            >
                              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                              </svg>
                            </button>
                            <button
                              className="remove-button"
                              onClick={() => removeFromHistory(query)}
                              title="히스토리에서 제거"
                            >
                              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <svg width="32" height="32" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
                      <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
                    </svg>
                    <p>최근 검색 내역이 없습니다</p>
                  </div>
                )}
              </div>
            )}

            {/* 즐겨찾기 */}
            {activeTab === 'favorites' && (
              <div className="favorite-searches">
                {favorites.length > 0 ? (
                  <>
                    <div className="history-header">
                      <span>즐겨찾기</span>
                    </div>
                    <div className="history-list">
                      {favorites.map((query, index) => (
                        <div key={index} className="history-item favorite">
                          <button
                            className="search-query"
                            onClick={() => handleSearchSelect(query)}
                            title={`"${query}" 검색`}
                          >
                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                              <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                            </svg>
                            <span className="query-text">{query}</span>
                          </button>
                          <div className="item-actions">
                            <button
                              className="remove-button"
                              onClick={() => toggleFavorite(query)}
                              title="즐겨찾기에서 제거"
                            >
                              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <svg width="32" height="32" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                    </svg>
                    <p>즐겨찾기한 검색어가 없습니다</p>
                    <p className="empty-hint">★ 버튼을 눌러 자주 사용하는 검색어를 저장하세요</p>
                  </div>
                )}
              </div>
            )}

            {/* 인기 검색 */}
            {activeTab === 'popular' && (
              <div className="popular-searches">
                <div className="history-header">
                  <span>인기 검색어</span>
                </div>
                <div className="history-list">
                  {popularSearches.map((query, index) => (
                    <div key={index} className="history-item popular">
                      <button
                        className="search-query"
                        onClick={() => handleSearchSelect(query)}
                        title={`"${query}" 검색`}
                      >
                        <span className="rank-number">{index + 1}</span>
                        <span className="query-text">{query}</span>
                      </button>
                      <div className="item-actions">
                        <button
                          className={`favorite-button ${favorites.includes(query) ? 'active' : ''}`}
                          onClick={() => toggleFavorite(query)}
                          title={favorites.includes(query) ? '즐겨찾기 해제' : '즐겨찾기 추가'}
                        >
                          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchHistory;