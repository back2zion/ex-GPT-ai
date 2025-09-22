// 0905 ErrorSubmitModal.jsx 파일 추가, 이미 작업하셨으면 삭제하셔도 될 것 같습니다
import Modal from "../../common/Modal/Modal";
import Button from "../../common/Button/Button";

const ErrorSubmitModal = ({
  isOpen,
  onCancel,
  onConfirm,
  selectedSize,
  onSelect,
}) => {
  // --ds-font-size-base: 1em; // 16px -> 1px 씩 늘리기
  // const sizes = ["가", "가", "가", "가", "가"];

  return (
    <Modal
      className="error-submit-modal"
      isOpen={isOpen}
      title="오류사항신고"
      onCancel={onCancel}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "제출", onClick: onConfirm },
      ]}
    >
      <div className="font-size-options">
        {sizes.map((label, idx) => (
          <Button
            key={idx}
            defaultClass="font-size-button"
            className={selectedSize === idx ? "active" : ""}
            onClick={() => onSelect(idx)}
          >
            {label}
          </Button>
        ))}
      </div>
    </Modal>
  );
};

export default ErrorSubmitModal;
