import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import './imageSearch.scss';

const EnhancedImageSearchResults = ({
  results = [],
  isLoading = false,
  error = null,
  onLoadMore = null,
  hasMore = false,
  totalCount = 0,
  hasSearched = false
}) => {
  // 상태 관리
  const [selectedImage, setSelectedImage] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid', 'masonry', 'list'
  const [sortBy, setSortBy] = useState('relevance'); // 'relevance', 'date', 'similarity'
  const [filterBy, setFilterBy] = useState('all'); // 'all', 'recent', 'high-similarity'
  const [gridSize, setGridSize] = useState('medium'); // 'small', 'medium', 'large'
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [selectedImages, setSelectedImages] = useState(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [loadedImages, setLoadedImages] = useState(new Set());
  const [visibleImages, setVisibleImages] = useState(new Set());
  const [slideIndex, setSlideIndex] = useState(0);
  const [isSlideshow, setIsSlideshow] = useState(false);
  const [autoPlay, setAutoPlay] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // Refs
  const gridRef = useRef(null);
  const observerRef = useRef(null);
  const slideshowIntervalRef = useRef(null);

  // 필터링 및 정렬된 결과
  const processedResults = useMemo(() => {
    let filtered = [...results];
    
    // 필터링
    switch (filterBy) {
      case 'recent':
        filtered = filtered.filter(img => {
          if (!img.timestamp && !img.filename) return false;
          const imageDate = new Date(img.timestamp || img.filename);
          const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return imageDate > dayAgo;
        });
        break;
      case 'high-similarity':
        filtered = filtered.filter(img => img.similarity > 0.8);
        break;
      default:
        break;
    }
    
    // 정렬
    switch (sortBy) {
      case 'date':
        filtered.sort((a, b) => {
          const dateA = new Date(a.timestamp || a.filename);
          const dateB = new Date(b.timestamp || b.filename);
          return dateB - dateA;
        });
        break;
      case 'similarity':
        filtered.sort((a, b) => b.similarity - a.similarity);
        break;
      default: // relevance
        break;
    }
    
    return filtered;
  }, [results, filterBy, sortBy]);

  // 페이지네이션
  const paginatedResults = useMemo(() => {
    const startIndex = 0;
    const endIndex = currentPage * itemsPerPage;
    return processedResults.slice(startIndex, endIndex);
  }, [processedResults, currentPage, itemsPerPage]);

  // Intersection Observer for lazy loading
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const imageId = entry.target.dataset.imageId;
            if (imageId) {
              setVisibleImages(prev => new Set(prev).add(imageId));
            }
          }
        });
      },
      { threshold: 0.1, rootMargin: '50px' }
    );

    return () => observerRef.current?.disconnect();
  }, []);

  // 무한 스크롤 처리
  useEffect(() => {
    const handleScroll = () => {
      if (!gridRef.current || isLoading) return;
      
      const { scrollTop, scrollHeight, clientHeight } = gridRef.current;
      const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
      
      if (scrollPercentage > 0.8 && hasMore && onLoadMore) {
        onLoadMore();
      } else if (scrollPercentage > 0.8 && currentPage * itemsPerPage < processedResults.length) {
        setCurrentPage(prev => prev + 1);
      }
    };

    const gridElement = gridRef.current;
    if (gridElement) {
      gridElement.addEventListener('scroll', handleScroll);
      return () => gridElement.removeEventListener('scroll', handleScroll);
    }
  }, [isLoading, hasMore, onLoadMore, currentPage, itemsPerPage, processedResults.length]);

  // 슬라이드쇼 자동재생
  useEffect(() => {
    if (autoPlay && isSlideshow && processedResults.length > 0) {
      slideshowIntervalRef.current = setInterval(() => {
        setSlideIndex(prev => (prev + 1) % processedResults.length);
      }, 3000);
    } else {
      clearInterval(slideshowIntervalRef.current);
    }

    return () => clearInterval(slideshowIntervalRef.current);
  }, [autoPlay, isSlideshow, processedResults.length]);

  // 이벤트 핸들러
  const handleImageClick = useCallback((image, index) => {
    if (isSelectionMode) {
      const newSelected = new Set(selectedImages);
      const imageKey = `${image.filename}-${index}`;
      if (newSelected.has(imageKey)) {
        newSelected.delete(imageKey);
      } else {
        newSelected.add(imageKey);
      }
      setSelectedImages(newSelected);
    } else {
      setSelectedImage(image);
      setSlideIndex(index);
    }
  }, [isSelectionMode, selectedImages]);

  const handleImageLoad = useCallback((imageId) => {
    setLoadedImages(prev => new Set(prev).add(imageId));
  }, []);

  const handleImageError = useCallback((imageId) => {
    console.warn(`이미지 로딩 실패: ${imageId}`);
  }, []);

  const toggleSelectionMode = useCallback(() => {
    setIsSelectionMode(prev => !prev);
    setSelectedImages(new Set());
  }, []);

  const selectAllImages = useCallback(() => {
    const allKeys = paginatedResults.map((img, idx) => `${img.filename}-${idx}`);
    setSelectedImages(new Set(allKeys));
  }, [paginatedResults]);

  const clearSelection = useCallback(() => {
    setSelectedImages(new Set());
  }, []);

  const downloadSelectedImages = useCallback(async () => {
    if (selectedImages.size === 0) return;
    
    try {
      const selectedData = Array.from(selectedImages).map(key => {
        const [filename] = key.split('-');
        return paginatedResults.find(img => img.filename === filename);
      }).filter(Boolean);

      // 다운로드 로직 구현
      for (const image of selectedData) {
        const link = document.createElement('a');
        link.href = image.image_url;
        link.download = image.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 다운로드 간격
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    } catch (error) {
      console.error('이미지 다운로드 실패:', error);
    }
  }, [selectedImages, paginatedResults]);

  const closeModal = useCallback(() => {
    setSelectedImage(null);
    setIsSlideshow(false);
    setAutoPlay(false);
  }, []);

  const nextSlide = useCallback(() => {
    setSlideIndex(prev => (prev + 1) % processedResults.length);
  }, [processedResults.length]);

  const prevSlide = useCallback(() => {
    setSlideIndex(prev => (prev - 1 + processedResults.length) % processedResults.length);
  }, [processedResults.length]);

  const toggleSlideshow = useCallback(() => {
    setIsSlideshow(prev => !prev);
    if (!isSlideshow) {
      setSelectedImage(processedResults[slideIndex]);
    }
  }, [isSlideshow, processedResults, slideIndex]);

  // 키보드 이벤트 처리
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (selectedImage) {
        switch (e.key) {
          case 'Escape':
            closeModal();
            break;
          case 'ArrowLeft':
            prevSlide();
            break;
          case 'ArrowRight':
            nextSlide();
            break;
          case ' ':
            e.preventDefault();
            setAutoPlay(prev => !prev);
            break;
          default:
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedImage, closeModal, prevSlide, nextSlide]);

  // 로딩 상태
  if (isLoading && results.length === 0) {
    return (
      <div className="image-search-loading">
        <div className="loading-spinner"></div>
        <p>이미지를 검색하고 있습니다...</p>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="image-search-error">
        <div className="error-icon">⚠️</div>
        <p>이미지 검색 중 오류가 발생했습니다</p>
        <details>
          <summary>오류 상세</summary>
          <pre>{error}</pre>
        </details>
      </div>
    );
  }

  // 검색 실행 전에는 아무것도 표시하지 않음
  if (!hasSearched) {
    return null;
  }

  // 결과 없음 (검색은 실행됨)
  if (!results || results.length === 0) {
    return (
      <div className="image-search-empty">
        <div className="empty-icon">🔍</div>
        <p>검색된 이미지가 없습니다</p>
        <p className="empty-suggestion">다른 검색어를 시도해보세요</p>
      </div>
    );
  }

  return (
    <div className="enhanced-image-search-results">
      {/* 헤더 */}
      <div className="image-search-header">
        <div className="header-main">
          <h3>검색 결과 ({totalCount || processedResults.length}개)</h3>
          <p className="search-info">해무/안개 CCTV 데이터에서 검색된 결과입니다</p>
        </div>
        
        {/* 컨트롤 버튼들 */}
        <div className="header-controls">
          <div className="view-controls">
            <button
              className={`control-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="격자 보기"
            >
              <GridIcon />
            </button>
            <button
              className={`control-btn ${viewMode === 'masonry' ? 'active' : ''}`}
              onClick={() => setViewMode('masonry')}
              title="벽돌 보기"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <rect x="1" y="1" width="8" height="6"/>
                <rect x="11" y="1" width="8" height="4"/>
                <rect x="1" y="9" width="6" height="4"/>
                <rect x="9" y="7" width="10" height="6"/>
                <rect x="1" y="15" width="8" height="4"/>
                <rect x="11" y="15" width="8" height="4"/>
              </svg>
            </button>
            <button
              className={`control-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
              title="목록 보기"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <rect x="1" y="2" width="18" height="2"/>
                <rect x="1" y="8" width="18" height="2"/>
                <rect x="1" y="14" width="18" height="2"/>
              </svg>
            </button>
          </div>

          <div className="size-controls">
            <select
              value={gridSize}
              onChange={(e) => setGridSize(e.target.value)}
              className="size-select"
            >
              <option value="small">작게</option>
              <option value="medium">보통</option>
              <option value="large">크게</option>
            </select>
          </div>

          <div className="filter-controls">
            <button
              className={`control-btn ${isFilterOpen ? 'active' : ''}`}
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              title="필터"
            >
              <FilterIcon />
            </button>
          </div>

          <div className="selection-controls">
            <button
              className={`control-btn ${isSelectionMode ? 'active' : ''}`}
              onClick={toggleSelectionMode}
              title="선택 모드"
            >
              ✓
            </button>
            {isSelectionMode && (
              <>
                <button
                  className="control-btn"
                  onClick={selectAllImages}
                  title="전체 선택"
                >
                  전체선택
                </button>
                <button
                  className="control-btn"
                  onClick={clearSelection}
                  title="선택 해제"
                >
                  선택해제
                </button>
                <button
                  className="control-btn primary"
                  onClick={downloadSelectedImages}
                  disabled={selectedImages.size === 0}
                  title="다운로드"
                >
                  다운로드 ({selectedImages.size})
                </button>
              </>
            )}
          </div>

          <button
            className="control-btn"
            onClick={toggleSlideshow}
            title="슬라이드쇼"
          >
            📽️
          </button>
        </div>
      </div>

      {/* 필터 패널 */}
      {isFilterOpen && (
        <div className="filter-panel">
          <div className="filter-group">
            <label>정렬:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="relevance">관련도순</option>
              <option value="similarity">유사도순</option>
              <option value="date">날짜순</option>
            </select>
          </div>
          <div className="filter-group">
            <label>필터:</label>
            <select value={filterBy} onChange={(e) => setFilterBy(e.target.value)}>
              <option value="all">전체</option>
              <option value="recent">최근 24시간</option>
              <option value="high-similarity">고유사도 (80% 이상)</option>
            </select>
          </div>
        </div>
      )}

      {/* 이미지 그리드 */}
      <div 
        ref={gridRef}
        className={`image-grid ${viewMode} ${gridSize} ${isSelectionMode ? 'selection-mode' : ''}`}
      >
        {paginatedResults.map((image, index) => {
          const imageKey = `${image.filename}-${index}`;
          const isSelected = selectedImages.has(imageKey);
          const isVisible = visibleImages.has(imageKey);
          const isLoaded = loadedImages.has(imageKey);

          return (
            <div
              key={imageKey}
              className={`image-item ${isSelected ? 'selected' : ''} ${isLoaded ? 'loaded' : ''}`}
              data-image-id={imageKey}
              ref={(el) => {
                if (el && observerRef.current) {
                  observerRef.current.observe(el);
                }
              }}
              onClick={() => handleImageClick(image, index)}
            >
              {isSelectionMode && (
                <div className="selection-checkbox">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleImageClick(image, index)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              )}

              <div className="image-container">
                {isVisible ? (
                  <img
                    src={image.url || image.path || `data:image/jpeg;base64,${image.thumbnail}`}
                    alt={`${image.location} - ${image.filename}`}
                    loading="lazy"
                    onLoad={() => handleImageLoad(imageKey)}
                    onError={() => handleImageError(imageKey)}
                  />
                ) : (
                  <div className="image-placeholder">
                    <div className="placeholder-spinner"></div>
                  </div>
                )}
                
                <div className="image-overlay">
                  <div className="image-info">
                    <p className="location">{image.location}</p>
                    <p className="similarity">
                      유사도: {(image.similarity * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="image-actions">
                    <button
                      className="action-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        // 이미지 정보 모달 열기
                      }}
                      title="정보"
                    >
                      <InfoIcon />
                    </button>
                    <button
                      className="action-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        const link = document.createElement('a');
                        link.href = image.image_url;
                        link.download = image.filename;
                        link.click();
                      }}
                      title="다운로드"
                    >
                      <DownloadIcon />
                    </button>
                  </div>
                </div>
              </div>

              <div className="image-details">
                <p className="filename" title={image.filename}>
                  {image.filename}
                </p>
                {image.timestamp && (
                  <p className="timestamp">
                    {new Date(image.timestamp).toLocaleString('ko-KR')}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 로딩 더보기 */}
      {isLoading && paginatedResults.length > 0 && (
        <div className="load-more-loading">
          <div className="loading-spinner"></div>
          <p>추가 이미지를 불러오는 중...</p>
        </div>
      )}

      {/* 이미지 모달/슬라이드쇼 */}
      {selectedImage && (
        <div className="image-modal" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-nav">
                <button className="nav-btn prev" onClick={prevSlide}>
                  ◀
                </button>
                <span className="slide-counter">
                  {slideIndex + 1} / {processedResults.length}
                </span>
                <button className="nav-btn next" onClick={nextSlide}>
                  ▶
                </button>
              </div>
              
              <div className="modal-controls">
                <button
                  className={`control-btn ${autoPlay ? 'active' : ''}`}
                  onClick={() => setAutoPlay(!autoPlay)}
                  title="자동 재생"
                >
                  {autoPlay ? <PauseIcon /> : <PlayIcon />}
                </button>
                <button
                  className="control-btn"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = selectedImage.image_url;
                    link.download = selectedImage.filename;
                    link.click();
                  }}
                  title="다운로드"
                >
                  <DownloadIcon />
                </button>
                <button className="modal-close" onClick={closeModal}>
                  ×
                </button>
              </div>
            </div>

            <div className="modal-image">
              <img
                src={selectedImage.image_url}
                alt={`${selectedImage.location} - ${selectedImage.filename}`}
              />
            </div>

            <div className="modal-info">
              <div className="info-grid">
                <div className="info-item">
                  <span className="label">위치:</span>
                  <span className="value">{selectedImage.location}</span>
                </div>
                <div className="info-item">
                  <span className="label">파일명:</span>
                  <span className="value">{selectedImage.filename}</span>
                </div>
                <div className="info-item">
                  <span className="label">유사도:</span>
                  <span className="value">
                    {(selectedImage.similarity * 100).toFixed(2)}%
                  </span>
                </div>
                {selectedImage.timestamp && (
                  <div className="info-item">
                    <span className="label">촬영시간:</span>
                    <span className="value">
                      {new Date(selectedImage.timestamp).toLocaleString('ko-KR')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// 아이콘 컴포넌트들 (간단한 SVG 아이콘)
const GridIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <rect x="1" y="1" width="6" height="6" rx="1"/>
    <rect x="9" y="1" width="6" height="6" rx="1"/>
    <rect x="1" y="9" width="6" height="6" rx="1"/>
    <rect x="9" y="9" width="6" height="6" rx="1"/>
  </svg>
);

const FilterIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <path d="M1.5 3a.5.5 0 0 0 0 1h13a.5.5 0 0 0 0-1h-13zM3 6.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm2 3a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
  </svg>
);

const DownloadIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <path d="M8.5 1.5a.5.5 0 0 0-1 0V7H5.707l2.147 2.146a.5.5 0 0 0 .708 0L10.707 7H8.5V1.5zM2 12.5a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"/>
  </svg>
);

const InfoIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
    <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
  </svg>
);

const PlayIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/>
  </svg>
);

const PauseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <path d="M5.5 3.5A1.5 1.5 0 0 1 7 2h1a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 8 14H7a1.5 1.5 0 0 1-1.5-1.5v-9z"/>
    <path d="M10.5 3.5A1.5 1.5 0 0 1 12 2h1a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 13 14h-1a1.5 1.5 0 0 1-1.5-1.5v-9z"/>
  </svg>
);

export default EnhancedImageSearchResults;