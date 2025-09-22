import React from "react";
import "./button.scss";

const Button = (props) => {
  let {
    onClick,
    disabled,
    children,
    style,
    className,
    tabIndex,
    label,
    defaultClass = "",
    iconPosition = "left",
    iconcolor,
    iconComponent,
    titleLabel,
    primary,
    secondary,
    type = "button",
  } = props;

  className = className || defaultClass;

  // custom Svg Icon
  const SvgIcon = iconComponent;

  const renderSvgIcon = () => {
    if (!SvgIcon) return null;

    const iconProps = {
      className: "button-icon-svg",
      iconcolor: iconcolor || "currentColor",
    };

    // 컴포넌트 (함수 or 클래스)
    if (typeof SvgIcon === "function") {
      return <SvgIcon {...iconProps} />;
    }

    // 리액트 엘리먼트
    if (React.isValidElement(SvgIcon)) {
      return React.cloneElement(SvgIcon, { ...iconProps, ...SvgIcon.props });
    }

    return null;
  };

  className = [defaultClass, className].filter(Boolean).join(" ");

  return (
    <button
      type={type}
      className={`ds-button ${className ? " " + className : ""} ${
        primary ? "primary" : secondary ? "secondary" : ""
      }`}
      tabIndex={tabIndex}
      title={titleLabel}
      style={style}
      disabled={disabled}
      onClick={onClick}
    >
      <p className={`button-inner`}>
        {/* SvgIcon 왼쪽일 때 */}
        {SvgIcon && iconPosition === "left" && renderSvgIcon()}
        {children
          ? children
          : label && <span className="button-label">{label}</span>}
        {/* SvgIcon 오른쪽일 때 */}
        {SvgIcon && iconPosition === "right" && renderSvgIcon()}
      </p>
    </button>
  );
};

export default Button;
