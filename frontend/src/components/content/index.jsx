import Intro from "./Intro/Intro";
import Suggests from "./Suggests/Suggests";
// import Messages from "./Messages/Messages";
import Form from "./Form/Form";

import "./styles/index.scss";

const Content = () => {
  return (
    <div className="content content--layout">
      <div className="top--scrollable">
        <Intro />
        <Suggests />
        <Messages />
      </div>
      <Form />
    </div>
  );
};

export default Content;
