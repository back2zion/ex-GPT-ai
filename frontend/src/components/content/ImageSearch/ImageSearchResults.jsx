import React, { useState } from 'react';
import './imageSearch.scss';

const ImageSearchResults = ({ results, isLoading, error }) => {
  const [selectedImage, setSelectedImage] = useState(null);

  if (isLoading) {
    return (
      <div className="image-search-loading">
        <div className="loading-spinner"></div>
        <p>이미지를 검색하고 있습니다...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="image-search-error">
        <p>이미지 검색 중 오류가 발생했습니다: {error}</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return null;
  }

  const handleImageClick = (image) => {
    setSelectedImage(image);
  };

  const closeModal = () => {
    setSelectedImage(null);
  };

  return (
    <div className="image-search-results">
      <div className="image-search-header">
        <h3>관련 이미지 ({results.length}개)</h3>
        <p className="search-info">해무/안개 CCTV 데이터에서 검색된 결과입니다</p>
      </div>
      
      <div className="image-grid">
        {results.map((image, index) => (
          <div key={index} className="image-item" onClick={() => handleImageClick(image)}>
            <div className="image-container">
              <img 
                src={`data:image/jpeg;base64,${image.thumbnail}`}
                alt={`${image.location} - ${image.filename}`}
                loading="lazy"
              />
              <div className="image-overlay">
                <div className="image-info">
                  <p className="location">{image.location}</p>
                  <p className="similarity">유사도: {(image.similarity * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>
            <div className="image-details">
              <p className="filename">{image.filename}</p>
            </div>
          </div>
        ))}
      </div>

      {/* 이미지 모달 */}
      {selectedImage && (
        <div className="image-modal" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal}>×</button>
            <div className="modal-image">
              <img 
                src={selectedImage.image_url}
                alt={`${selectedImage.location} - ${selectedImage.filename}`}
              />
            </div>
            <div className="modal-info">
              <h4>{selectedImage.location}</h4>
              <p><strong>파일명:</strong> {selectedImage.filename}</p>
              <p><strong>유사도:</strong> {(selectedImage.similarity * 100).toFixed(2)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageSearchResults;