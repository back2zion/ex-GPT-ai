import { useState, useEffect } from "react";
// header
import Button from "../common/Button/Button";
import ThemeIcon from "../../assets/components/header/ThemeIcon";
import TextIcon from "../../assets/components/header/TextIcon";
import BookIcon from "../../assets/components/header/BookIcon";
import NoticeIcon from "../../assets/components/header/NoticeIcon";
import StarIcon from "../../assets/components/header/StarIcon";
import "./header.scss";

// 0905 modal
import FontSizeModal from "../../modals/FontSizeModal/FontSizeModal";
import NoticeModal from "../../modals/NoticeModal/NoticeModal";
import SurveyModal from "../../modals/SurveyModal/SurveyModal";

export const Header = ({}) => {
  // BUTTON label 화면 너비 작을 때 숨김 및 title 추가
  // 0905 850 -> 1430 변경
  const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth > 1430);

  // 리사이즈 핸들러
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth > 850;
      setIsLargeScreen(large);
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // 최초 실행

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const getTitleLabel = (isLargeScreen, label) => {
    return isLargeScreen ? "" : label;
  };

  // 0905 - 글자크기 버튼 폰트 사이즈 설정
  // fontSizeModal 열/닫 및 글자 크기 구현
  const [isFontModalOpen, setIsFontModalOpen] = useState(false);
  const [selectedSize, setSelectedSize] = useState(2); // 기본 선택값 (예: 0번)

  // 글자 크기 옵션 (16, 18, 20, 22, 24)
  const fontSizes = [16, 18, 20, 22, 24];

  useEffect(() => {
    // 기본값 20px 설정
    document.documentElement.style.setProperty("--ds-font-size-base", "20px");
  }, []);

  // 확인 버튼 눌렀을 때
  const handleFontsizeConfirm = () => {
    const size = fontSizes[selectedSize];

    // CSS 변수 업데이트
    document.documentElement.style.setProperty(
      "--ds-font-size-base",
      `${size}px`
    );

    setIsFontModalOpen(false);
  };

  // 0905 - 공지사항, 만족도조사 모달 열/닫 구현
  const [isNoticeModalOpen, setIsNoticeModalOpen] = useState(false);
  const [isSurveyModalOpen, setIsSurveyModalOpen] = useState(false);

  return (
    <>
      <header className="header">
        <div className="header__inner">
          <div className="header__util-menu">
            <Button
              iconComponent={<ThemeIcon />}
              className="header__util-button"
              label="테마선택"
              titleLabel={getTitleLabel(isLargeScreen, "테마선택")}
              onClick={() =>
                setTheme((prev) => (prev === "light" ? "dark" : "light"))
              }
            />
            <Button
              iconComponent={<TextIcon />}
              className="header__util-button text-size"
              label="글자크기"
              titleLabel={getTitleLabel(isLargeScreen, "글자크기")}
              // 0905 - 글자크기 모달 열기
              onClick={() => setIsFontModalOpen(true)}
            />
            <Button
              iconComponent={<BookIcon />}
              className="header__util-button"
              label="사용법안내"
              titleLabel={getTitleLabel(isLargeScreen, "사용법안내")}
            />
            <Button
              iconComponent={<NoticeIcon />}
              className="header__util-button"
              label="공지사항"
              titleLabel={getTitleLabel(isLargeScreen, "공지사항")}
              // 0905 - 공지사항 모달 열기
              onClick={() => setIsNoticeModalOpen(true)}
            />
            <Button
              iconComponent={<StarIcon />}
              className="header__util-button"
              label="만족도조사"
              titleLabel={getTitleLabel(isLargeScreen, "만족도 조사")}
              // 0905 - 만족도조사 모달 열기
              onClick={() => setIsSurveyModalOpen(true)}
            />
          </div>
        </div>
      </header>
      {/* 글자크기 모달 */}
      <FontSizeModal
        className="font-size-modal"
        isOpen={isFontModalOpen}
        onCancel={() => setIsFontModalOpen(false)}
        onConfirm={handleFontsizeConfirm}
        selectedSize={selectedSize}
        onSelect={(idx) => setSelectedSize(idx)}
      />
      {/* 공지사항 팝업 */}
      <NoticeModal
        className="notice-modal"
        isOpen={isNoticeModalOpen}
        onCancel={() => setIsNoticeModalOpen(false)}
        onConfirm={() => setIsNoticeModalOpen(false)}
      />
      {/* 만족도 조사 팝업 */}
      <SurveyModal
        className="survey-modal"
        isOpen={isSurveyModalOpen}
        onCancel={() => setIsSurveyModalOpen(false)}
        // 확인 로직 변경 작업 필요
        onConfirm={() => setIsSurveyModalOpen(false)}
      />
    </>
  );
};
