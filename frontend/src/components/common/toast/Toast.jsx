import { SuccessToastIcon } from "../../../assets/components/toast/SuccessToastIcon";
import { FailToastIcon } from "../../../assets/components/toast/FailToastIcon";
import { WarningToastIcon } from "../../../assets/components/toast/WarningToastIcon";

import "./toast.scss";

const Toast = ({ type = "success", message }) => {
  const renderIcon = () => {
    switch (type) {
      case "success":
        return <SuccessToastIcon />;
      case "fail":
        return <FailToastIcon />;
      case "warning":
        return <WarningToastIcon />;
      default:
        return null;
    }
  };

  return (
    <div className={`toast show ${type}`}>
      <div className="toast-content">
        <div className="toast-icon">{renderIcon()}</div>
        <div className="toast-message">{message}</div>
      </div>
    </div>
  );
};

export default Toast;
