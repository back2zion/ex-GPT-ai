import { useState, useEffect } from "react";

// toggle button icon
import { ToggleCloseIcon } from "../../../assets/components/aside/ToggleCloseIcon";
import { ToggleOpenIcon } from "../../../assets/components/aside/ToggleOpenIcon";
// proflie icon
import userDefaultIconLight from "./assets/icons/aside/userDefaultIcon_light.svg";
import userDefaultIconDark from "./assets/icons/aside/userDefaultIcon_dark.svg";
// department icon
import userDeptProfile from "../../assets/icons/aside/userDeptProfile.svg";
// logo icon
import Logo from "../../assets/components/header/Logo";
// 새 대화
import { PlusIcon } from "../../assets/components/aside/PlusIcon";
import { NewChatGliterIcon } from "../../assets/components/aside/NewChatGliterIcon";
// 대화 지우기
import { DeleteChatIcon } from "../../assets/components/aside/DeleteChatIcon";
// 국정 감사 AI
import { GovInspctionIcon } from "../../assets/components/aside/GovInspctionIcon";
// 메뉴 우측 화살표
import { ChevronRightIcon } from "../../assets/components/aside/ChevronRightIcon";

import Button from "../common/Button/Button";

import "./aside.scss";

export const Aside = () => {
  // aside 열/닫
  const [isOpen, setIsOpen] = useState(true); // 기본은 큰 화면 열림
  // 0905 850 -> 1430 변경
  const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth > 1430);
  const [manualClosed, setManualClosed] = useState(false); // 큰 화면에서 닫았는지 기억

  // 버튼 토글
  const toggleAside = () => {
    if (isLargeScreen) {
      setIsOpen(!isOpen);
      setManualClosed(!isOpen === false); // 열린 상태에서 누르면 -> 닫은 걸 기록
    } else {
      setIsOpen(!isOpen);
    }
  };

  // 리사이즈 핸들러
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth > 1430; // 0905 850 -> 1430 변경
      setIsLargeScreen(large);

      if (large) {
        // 큰 화면으로 돌아왔을 때
        setIsOpen(!manualClosed); // 닫은 적 있으면 닫힘 유지, 아니면 열림
      } else {
        // 작은 화면은 항상 닫힘 기본
        setIsOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // 최초 실행

    return () => window.removeEventListener("resize", handleResize);
  }, [manualClosed]);

  return (
    <>
      <aside className={`aside ${isOpen ? "" : "folded"}`}>
        <div className="aside__inner">
          <h1 className="aside__logo-meta">
            <Button
              className="aside__toggle_btn"
              onClick={toggleAside}
              tabIndex={1}
            >
              {isOpen ? <ToggleCloseIcon /> : <ToggleOpenIcon />}
            </Button>
            <div className="aside__logo-desc">
              <a href="#" tabIndex={1}>
                <span className="aside__logo-img">
                  <Logo></Logo>
                </span>
                <span className="aside__logo-version">1.4</span>
              </a>
              <span className="aside__logo-text">한국도로공사 AI</span>
            </div>
          </h1>
          {/* 프로필 이미지, 현재 버전 정보 */}
          <div className="user-info">
            <div className="user-info__profile">
              <img
                src={
                  theme == "light" ? userDefaultIconLight : userDefaultIconDark
                }
                alt="사용자 기본 프로필"
              />
            </div>
            <div className="user-info__meta">
              <div className="user-info__name">ex-GPT</div>
              <div className="user-info__version">한국도로공사 AI 1.4</div>
            </div>
          </div>
          {/* 새 대화, 대화 지우기, 국정감사 전용 AI */}
          <div className="aside__list">
            <a href="#" className="aside__link aside__link-new">
              <div className="aside__link__inner">
                <div className="icon">
                  <PlusIcon />
                </div>
                <span className="aside__link-text">새 대화</span>
                <NewChatGliterIcon />
              </div>
            </a>
            <a href="#" className="aside__link aside__link-delete">
              <div className="aside__link__inner">
                <div className="icon">
                  <DeleteChatIcon />
                </div>
                <span className="aside__link-text">대화 지우기</span>
                <ChevronRightIcon className="aside__link-arrow" />
              </div>
            </a>
            <a href="#" className="aside__link aside__link-gov">
              <div className="aside__link__inner">
                <div className="icon">
                  <GovInspctionIcon />
                </div>
                <span className="aside__link-text">국정감사 전용 AI</span>
                <ChevronRightIcon className="aside__link-arrow" />
              </div>
            </a>
          </div>
          {/* 이전 대화 기록 - 추후 필요한 내용이라 들어서 추가 작업 해두었습니다. */}
          <div className="history-list">
            <div className="history-title">이전 대화</div>
            <a href="#" className="history-item active">
              이전 대화 기록 1
              말줄임테스트말줄임테스트말줄임테스트말줄임테스트말줄임테스트말줄임테스트
            </a>
            <a href="#" className="history-item">
              이전 대화 기록 2
            </a>
            <a href="#" className="history-item">
              이전 대화 기록 3
            </a>
            <a href="#" className="history-item">
              이전 대화 기록 4
            </a>
          </div>
        </div>
        {/* 부서 */}
        <div className="user__dept">
          <div className="user__dept-profile">
            <img src={userDeptProfile} alt="ex-GPT 로고" />
          </div>
          <div className="user__dept-details">
            <div className="user__dept-name">디지털계획처</div>
            <div className="user__dept-extension">(내선:800-4552)</div>
          </div>
        </div>
      </aside>
      {isOpen && <div className="overlay" onClick={toggleAside}></div>}
    </>
  );
};
