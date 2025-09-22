// 0905 <div className="font-size-options"> 태그만 삭제 부탁드립니다.
import Modal from "../../common/Modal/Modal";
import Button from "../../common/Button/Button";
import "./fontSizeModal.scss";

const FontSizeModal = ({
  isOpen,
  onCancel,
  onConfirm,
  selectedSize,
  onSelect,
}) => {
  // --ds-font-size-base: 1em; // 20px -> 2px 씩 늘리기
  const sizes = ["가", "가", "가", "가", "가"];

  return (
    <Modal
      className="font-size-modal"
      isOpen={isOpen}
      title="글자 크기 선택"
      onCancel={onCancel}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "확인", onClick: onConfirm },
      ]}
    >
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
      {/* <div className="font-size-options">
      </div> */}
    </Modal>
  );
};

export default FontSizeModal;
