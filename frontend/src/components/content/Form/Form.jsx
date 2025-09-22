import AttachedFiles from "./AttachedFiles";
import FormTextarea from "./FormTextarea";
import FormButtons from "./FormButtons";

import "./form.scss";

const Form = ({ hasText, textareaRef, handleInput }) => {
  return (
    <div className="content__form_wrapper">
      <div className="content__inner">
        <div className={`content__form_section ${hasText ? "active" : ""}`}>
          <AttachedFiles />
          <form className="content__form">
            <FormTextarea
              hasText={hasText}
              textareaRef={textareaRef}
              handleInput={handleInput}
            />
            <FormButtons hasText={hasText} />
          </form>
        </div>
      </div>
    </div>
  );
};

export default Form;
