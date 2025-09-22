import AttachedFileItem from "./AttachedFileItem";
import Button from "../../common/Button/Button";

const AttachedFiles = () => {
  return (
    <div className="attached-files">
      <div className="attached-file-header">
        <span className="attached-file-header-title">첨부파일</span>
        <Button className="attached-file-header-remove-all">모두 삭제</Button>
      </div>
      <div className="attached-file-list">
        <AttachedFileItem />
      </div>
    </div>
  );
};

export default AttachedFiles;
