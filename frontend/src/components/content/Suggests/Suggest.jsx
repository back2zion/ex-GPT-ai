// 0905 슬라이드 변경 및 미디어 쿼리 추가
import { useState, useEffect } from "react";

// slick
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";

import "./suggests.scss";

const suggestList = [
  { title: "해무 발생 CCTV 이미지 검색" },
  { title: "안개 낀 도로 사진 보여줘" },
  { title: "경부고속도로 CCTV 영상" },
  { title: "우천 시 도로 상황 이미지" },
  { title: "야간 도로 CCTV 사진" },
  { title: "교통사고 현장 이미지 검색" },
];

const Suggests = ({ onSuggestClick }) => {
  const [slidesToShow, setSlidesToShow] = useState(4);

  useEffect(() => {
    const updateSlides = () => {
      const width = window.innerWidth;

      if (width <= 575) setSlidesToShow(1);
      else if (width <= 670) setSlidesToShow(1);
      else if (width <= 770) setSlidesToShow(2);
      else if (width <= 1000) setSlidesToShow(3);
      else if (width <= 1065) setSlidesToShow(3);
      else if (width <= 1680) setSlidesToShow(3);
      else setSlidesToShow(4);
    };

    updateSlides(); // 첫 로딩 시 실행
    window.addEventListener("resize", updateSlides);
    return () => window.removeEventListener("resize", updateSlides);
  }, []);

  const settings = {
    dots: false,
    infinite: false,
    speed: 500,
    slidesToShow,
    slidesToScroll: 1,
    arrows: true,
    centerPadding: "12px",
    responsive: [
      { breakpoint: 1680, settings: { slidesToShow: 3 } },
      { breakpoint: 1065, settings: { slidesToShow: 3 } },
      { breakpoint: 1000, settings: { slidesToShow: 3 } },
      { breakpoint: 770, settings: { slidesToShow: 2 } },
      { breakpoint: 670, settings: { slidesToShow: 1 } },
      { breakpoint: 575, settings: { slidesToShow: 1 } },
    ],
  };

  // content__suggests__list tag 삭제
  return (
    <div className="content__suggests_wrapper">
      <div className="content__inner">
        <div className="content__suggests">
          <Slider {...settings}>
            {suggestList.map((item, index) => (
              <div key={index}>
                <div
                  className="content__suggests__item"
                  onClick={() => onSuggestClick && onSuggestClick(item.title)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="content__suggests__text">{item.title}</div>
                </div>
              </div>
            ))}
          </Slider>
        </div>
      </div>
    </div>
  );
};

export default Suggests;
