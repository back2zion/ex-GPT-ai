// 0905 파일 추가
import Modal from "../../common/Modal/Modal";
import "./noticeModal.scss";

const notices = [
  {
    title: "시스템 업데이트 안내",
    date: "2025-08-18",
    detail:
      "ex-GPT 1.4 버전이 출시되었습니다. 새로운 기능으로 음성 입력, 국정감사 전용 AI 설정 등이 추가되었습니다. 더 나은 서비스를 위해 지속적으로 개선하고 있습니다.",
  },
  {
    title: "정기 점검 예정",
    date: "2025- 01-15",
  },
  {
    title: "신규 기능 추가",
    date: "2025-01-15",
  },
];

const NoticeModal = ({ isOpen, onCancel, onConfirm }) => {
  return (
    <Modal
      className="notice-modal"
      isOpen={isOpen}
      title="공지사항"
      onCancel={onCancel}
      footerButtons={[
        { className: "secondary", label: "취소", onClick: onCancel },
        { className: "primary", label: "확인", onClick: onConfirm },
      ]}
    >
      <div className="notice-modal-area">
        {notices.map((notice, index) => (
          <div className="notice-modal-item" key={index}>
            <div className="notice-modal-title">
              <span className="notice-modal-title-bullet">•</span>
              <div className="notice-modal-title-content" tabIndex={0}>
                <div className="notice-modal-title-text">{notice.title}</div>
                <div className="notice-modal-title-date">{notice.date}</div>
              </div>
            </div>
            {notice.detail && (
              <div className="notice-modal-detail">{notice.detail}</div>
            )}
          </div>
        ))}
      </div>
    </Modal>
  );
};

export default NoticeModal;
