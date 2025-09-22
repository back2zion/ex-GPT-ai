// 0905 ex-GPT 에서 로고 이미지로 변경, 로고 이미지 추가
import { ContentLogo } from "../../../assets/components/Intro/ContentLogo";

const Intro = () => {
  return (
    <div className="content__intro_wrapper">
      <div className="content__inner">
        <div className="content__intro">
          <h2 className="content__intro-title">
            <ContentLogo />
          </h2>
        </div>
      </div>
    </div>
  );
};

export default Intro;
