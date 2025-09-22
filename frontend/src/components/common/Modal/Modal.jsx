import { useEffect, useRef, useCallback } from "react";
import Button from "../Button/Button";
import { ModalCloseIcon } from "../../../assets/components/modal/ModalCloseIcon";

import "./modal.scss";

const Modal = ({
  className,
  isOpen,
  title,
  children,
  onCancel,
  footerButtons = [],
}) => {
  // 0905 modal 포커스 트랩 기능 구현
  const modalRef = useRef(null);
  const lastFocusedElement = useRef(null);

  // 포커스 가능한 요소 가져오기
  const getFocusableElements = (element) => {
    if (!element) return [];
    return element.querySelectorAll(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
  };

  // ESC 및 Tab 키 처리
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape") {
        onCancel?.();
      }

      if (e.key === "Tab") {
        const focusableEls = getFocusableElements(modalRef.current);
        if (focusableEls.length === 0) return;

        const firstEl = focusableEls[0];
        const lastEl = focusableEls[focusableEls.length - 1];

        if (e.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
          }
        }
      }
    },
    [onCancel]
  );

  useEffect(() => {
    if (isOpen) {
      // 모달 열기 전 포커스 저장
      lastFocusedElement.current = document.activeElement;

      // ESC, Tab 이벤트 리스너 등록
      document.addEventListener("keydown", handleKeyDown);

      // 첫 번째 focusable 요소에 포커스
      const focusableEls = getFocusableElements(modalRef.current);
      focusableEls[0]?.focus();
    } else {
      // 모달 닫힐 때 이벤트 제거
      document.removeEventListener("keydown", handleKeyDown);

      // 렌더링 후 포커스 복원
      setTimeout(() => {
        lastFocusedElement.current?.focus();
      }, 0);
    }

    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleKeyDown]);

  // overlay 클릭 시 닫기
  const handleOverlayClick = (e) => {
    if (e.target.classList.contains("modal")) {
      onCancel?.();
    }
  };

  return (
    <div
      className={`modal ${isOpen ? "on" : ""} ${className}`}
      onMouseDown={handleOverlayClick}
      ref={modalRef}
    >
      <div className="modal-box">
        <button className="modal-close" onClick={onCancel}>
          <ModalCloseIcon />
        </button>

        {/* 모달 헤더 */}
        {title && (
          <div className="modal-header">
            <p className="modal-header-title">{title}</p>
          </div>
        )}

        {/* 모달 바디 */}
        <div className="modal-content">
          <div className="modal-content-inn">{children}</div>
        </div>

        {/* 모달 푸터 */}
        {footerButtons.length > 0 && (
          <div className="modal-footer">
            <div className="flex-end">
              {footerButtons.map((btn, idx) => (
                <Button
                  key={idx}
                  className={btn.className || ""}
                  onClick={btn.onClick}
                >
                  {btn.label}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Modal;
