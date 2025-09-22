// 0905 파일 추가
import { useState } from "react";
import Modal from "../../common/Modal/Modal";
import Button from "../../common/Button/Button";

import { SurveyStarIcon } from "../../../assets/components/modal/SurveyModal/SurveyStarIcon";

import "./surveyModal.scss";

const SurveyModal = ({ isOpen, onCancel, onConfirm }) => {
  const [activeIndex, setActiveIndex] = useState(-1); // 클릭된 idx 저장

  const surveyButtons = Array.from({ length: 5 }, (_, idx) => ({
    defaultClass: "survey-modal-star-button",
    onClick: () => setActiveIndex(idx),
  }));

  return (
    <Modal
      className="survey-modal"
      isOpen={isOpen}
      title="만족도 조사"
      onCancel={onCancel}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "제출", onClick: onConfirm },
      ]}
    >
      <div className="survey-modal-area">
        <div className="survey-modal-title">서비스 만족도를 평가해주세요!</div>
        <div className="survey-modal-buttons">
          {surveyButtons.map((btn, idx) => (
            <Button
              key={idx}
              className={`${btn.defaultClass} ${
                idx <= activeIndex ? "active" : ""
              }`}
              onClick={btn.onClick}
            >
              <SurveyStarIcon
                fill={idx <= activeIndex ? "#FFD900" : "#DBDAD6"}
                stroke={idx <= activeIndex ? "#F4D000" : "#BFBFBF"}
              />
            </Button>
          ))}
        </div>
        <textarea
          className="survey-modal-textarea"
          placeholder="개선사항이나 의견을 입력해주세요."
          rows="5"
        ></textarea>
      </div>
    </Modal>
  );
};

export default SurveyModal;
