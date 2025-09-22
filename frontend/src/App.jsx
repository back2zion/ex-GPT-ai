import React, { useState, useEffect, useRef, useCallback } from "react";
import Button from "./components/common/Button/Button";
import EnhancedImageSearchResults from "./components/content/ImageSearch/EnhancedImageSearchResults";
import SearchHistory from "./components/content/SearchHistory/SearchHistory";
import { simulateApiCall } from "./utils/mockImageData";
import ExGPTAPI, { ImageSearchAPI, ChatAPI, HealthAPI, API_CONFIG } from "./utils/exgptAPI";

// header
import ThemeIcon from "./assets/components/header/ThemeIcon";
import TextIcon from "./assets/components/header/TextIcon";
import BookIcon from "./assets/components/header/BookIcon";
import NoticeIcon from "./assets/components/header/NoticeIcon";
import StarIcon from "./assets/components/header/StarIcon";
import Logo from "./assets/components/header/Logo";

// 0905 Header 컴포넌트에 modal 추가
import FontSizeModal from "./components/modals/FontSizeModal/FontSizeModal"; // 글자크기 모달
import NoticeModal from "./components/modals/NoticeModal/NoticeModal"; // 공지사항 모달
import SurveyModal from "./components/modals/SurveyModal/SurveyModal"; // 만족도 조사 모달

// aside
import userDefaultIconLight from "./assets/icons/aside/userDefaultIcon_light.svg";
import userDefaultIconDark from "./assets/icons/aside/userDefaultIcon_dark.svg";
import userDeptProfile from "./assets/icons/aside/userDeptProfile.svg";
import { ToggleCloseIcon } from "./assets/components/aside/ToggleCloseIcon";
import { ToggleOpenIcon } from "./assets/components/aside/ToggleOpenIcon";
import { PlusIcon } from "./assets/components/aside/PlusIcon";
import { NewChatGliterIcon } from "./assets/components/aside/NewChatGliterIcon";
import { DeleteChatIcon } from "./assets/components/aside/DeleteChatIcon";
import { GovInspctionIcon } from "./assets/components/aside/GovInspctionIcon";
import { ChevronRightIcon } from "./assets/components/aside/ChevronRightIcon";

// modal
import { ModalCloseIcon } from "./assets/components/modal/ModalCloseIcon";

// form - 첨부파일 관련 아이콘
import { ClipIcon } from "./assets/components/file/ClipIcon";
import { DocumentIcon } from "./assets/components/file/DocumentIcon";
import { FileDeleteIcon } from "./assets/components/file/FileDeleteIcon";
import SubmitIcon from "./assets/icons/form/submitIcon.svg?react";

// form - 검색 강조 아이콘
import fileHighLightIcon from "./assets/icons/form/fileHighLightIcon.svg";

// message - 길퉁이 캐릭터 아이콘
import { GptIcon } from "./assets/components/messages/gptIcon";
import { ErrorSubmitIcon } from "./assets/components/messages/errorSubmitIcon";
// 0905 - 상세보기 화살표 아이콘
import { DetailArrowIcon } from "./assets/components/button/detailArrowIcon";

// 0905 Suggests 컴포넌트로 분리 및 상단 ex-GPT 로고 텍스트 -> 이미지로 변경
import Suggests from "./components/content/Suggests/Suggest";
import { ContentLogo } from "./assets/components/Intro/ContentLogo";

function App() {
  // aside 열/닫
  const [isOpen, setIsOpen] = useState(true); // 기본은 큰 화면 열림
  // 0905 850 -> 1430 변경
  const [isLargeScreen, setIsLargeScreen] = useState(window.innerWidth > 1430);
  const [manualClosed, setManualClosed] = useState(false); // 큰 화면에서 닫았는지 기억

  // 버튼 토글
  const toggleAside = () => {
    if (isLargeScreen) {
      setIsOpen(!isOpen);
      setManualClosed(!isOpen === false); // 열린 상태에서 누르면 -> 닫은 걸 기록
    } else {
      setIsOpen(!isOpen);
    }
  };

  // 리사이즈 핸들러
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth > 1430; // 0905 850 -> 1430 변경
      setIsLargeScreen(large);

      if (large) {
        // 큰 화면으로 돌아왔을 때
        setIsOpen(!manualClosed); // 닫은 적 있으면 닫힘 유지, 아니면 열림
      } else {
        // 작은 화면은 항상 닫힘 기본
        setIsOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // 최초 실행

    return () => window.removeEventListener("resize", handleResize);
  }, [manualClosed]);

  // 상단 헤더 버튼
  const getTitleLabel = (isLargeScreen, label) => {
    return isLargeScreen ? "" : label;
  };

  // 0905 - 글자크기 버튼 폰트 사이즈 설정
  // fontSizeModal 열/닫 및 글자 크기 구현
  const [isFontModalOpen, setIsFontModalOpen] = useState(false);
  const [selectedSize, setSelectedSize] = useState(2); // 기본 선택값 (예: 0번)

  // 글자 크기 옵션 (16, 18, 20, 22, 24)
  const fontSizes = [16, 18, 20, 22, 24];

  useEffect(() => {
    // 기본값 20px 설정
    document.documentElement.style.setProperty("--ds-font-size-base", "20px");
  }, []);

  // 확인 버튼 눌렀을 때
  const handleFontsizeConfirm = () => {
    const size = fontSizes[selectedSize];

    // CSS 변수 업데이트
    document.documentElement.style.setProperty(
      "--ds-font-size-base",
      `${size}px`
    );

    setIsFontModalOpen(false);
  };

  // 0905 - 공지사항, 만족도조사 모달 열/닫 구현
  const [isNoticeModalOpen, setIsNoticeModalOpen] = useState(false);
  const [isSurveyModalOpen, setIsSurveyModalOpen] = useState(false);

  // 테마
  const [theme, setTheme] = useState("light");

  // theme 상태가 바뀔 때 HTML 속성 변경
  useEffect(() => {
    document.documentElement.setAttribute("theme", theme);
  }, [theme]);

  // 0905 form - 입력창 높이, 텍스트 여부
  // texarea - paddingLeft "1.65em"  -> "2.2em" 변경
  const textareaRef = useRef(null);
  const [hasText, setHasText] = useState(false);
  const [inputValue, setInputValue] = useState("");

  // 이미지 검색 상태 (searchImages 함수보다 먼저 선언)
  const [imageSearchResults, setImageSearchResults] = useState([]);
  const [imageSearchLoading, setImageSearchLoading] = useState(false);
  const [imageSearchError, setImageSearchError] = useState(null);
  const [hasMoreImages, setHasMoreImages] = useState(false);
  const [totalImageCount, setTotalImageCount] = useState(0);
  const [currentImagePage, setCurrentImagePage] = useState(1);
  const [hasSearched, setHasSearched] = useState(false); // 검색 실행 여부 추적

  // 0905 추가 message 추론 상세 보기/숨기기
  const [isThinkingContentOpen, setThinkingContentOpen] = useState(false);
  // source-toggle-button 첨부파일
  const [isSourceContentOpen, setSourceContentOpen] = useState(false);

  const handleInput = (e) => {
    const value = e.target.value;
    setInputValue(value);
    const trimmedValue = value.trim();
    const textarea = textareaRef.current;

    // 자동 높이 조절
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }

    // 텍스트 여부 상태 업데이트
    setHasText(trimmedValue.length > 0);

    // 패딩 조절
    if (textarea) {
      textarea.style.paddingLeft = trimmedValue ? "0.4em" : "2.2em";
    }
  };

  // 엔터키 처리 (Shift+Enter는 줄바꿈)
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // 추천 질문 클릭 처리
  const handleSuggestClick = (text) => {
    setInputValue(text);
    setHasText(true);
    if (textareaRef.current) {
      textareaRef.current.style.paddingLeft = "0.4em";
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      textareaRef.current.focus();
    }
  };
  
  // ExGPT API 인스턴스
  const [exgptAPI] = useState(() => new ExGPTAPI());
  
  // 채팅 상태
  const [chatMessages, setChatMessages] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isResponding, setIsResponding] = useState(false);
  
  // 백엔드 상태
  const [backendStatus, setBackendStatus] = useState({
    multimodal: 'checking',
    mcp: 'checking'
  });
  
  // 컴포넌트 마운트 시 백엔드 상태 확인
  useEffect(() => {
    checkBackendStatus();
  }, []);
  
  const checkBackendStatus = async () => {
    try {
      const status = await HealthAPI.checkAllServices();
      setBackendStatus({
        multimodal: status.multimodal.status,
        mcp: status.mcp.status
      });
      console.log('백엔드 상태:', status);
    } catch (error) {
      console.error('백엔드 상태 확인 오류:', error);
      setBackendStatus({
        multimodal: 'error',
        mcp: 'error'
      });
    }
  };
  
  // 이미지 검색 함수 (새로운 API 사용)
  const searchImages = async (query, page = 1, append = false) => {
    if (!query.trim()) return;

    setImageSearchLoading(true);
    setHasSearched(true); // 검색이 실행됨을 표시
    if (!append) {
      setImageSearchError(null);
      setCurrentImagePage(1);
    }
    
    try {
      console.log(`이미지 검색 API 호출: "${query}", 페이지: ${page}`);
      
      const data = await ImageSearchAPI.searchImages(query, page, 20);
      
      if (data.success) {
        const newResults = data.images || [];
        setImageSearchResults(prev => append ? [...prev, ...newResults] : newResults);
        setTotalImageCount(data.total_count || newResults.length);
        setHasMoreImages(data.has_more || false);
        if (append) {
          setCurrentImagePage(page);
        }

        console.log(`검색 완료: ${newResults.length}개 결과, 전체: ${data.total_count}개`);

        // 이미지 검색 결과를 채팅 메시지로 추가
        if (!append) {
          const assistantMessage = {
            role: 'assistant',
            content: newResults.length > 0
              ? `${newResults.length}개의 이미지를 찾았습니다.`
              : '🔍 검색된 이미지가 없습니다. 다른 검색어를 시도해보세요.',
            imageSearchResults: newResults,
            totalImageCount: data.total_count || 0,
            query: query
          };
          setChatMessages(prev => [...prev, assistantMessage]);
        }
      } else {
        throw new Error('이미지 검색에 실패했습니다.');
      }
    } catch (error) {
      console.error('이미지 검색 오류:', error);
      setImageSearchError(error.message);
      if (!append) {
        setImageSearchResults([]);
        setTotalImageCount(0);
        setHasMoreImages(false);

        // 오류 메시지를 채팅에 추가
        const errorMessage = {
          role: 'assistant',
          content: '🔍 검색된 이미지가 없습니다. 다른 검색어를 시도해보세요.',
          imageSearchResults: [],
          totalImageCount: 0,
          query: query,
          error: true
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }

      // 백엔드 오류 시 목 데이터 사용 (개발용)
      if (import.meta.env.DEV) {
        console.log('백엔드 오류로 인해 목 데이터 사용');
        try {
          const mockResult = await simulateApiCall(query, page, 20);
          const mockResults = mockResult.results || [];
          setImageSearchResults(prev => append ? [...prev, ...mockResults] : mockResults);
          setTotalImageCount(mockResult.total || 0);
          setHasMoreImages(mockResult.hasMore || false);
          setImageSearchError(null);

          // 목 데이터 결과도 채팅에 추가
          if (!append) {
            const assistantMessage = {
              role: 'assistant',
              content: mockResults.length > 0
                ? `${mockResults.length}개의 이미지를 찾았습니다. (개발용 목 데이터)`
                : '🔍 검색된 이미지가 없습니다. 다른 검색어를 시도해보세요.',
              imageSearchResults: mockResults,
              totalImageCount: mockResult.total || 0,
              query: query
            };
            setChatMessages(prev => [...prev, assistantMessage]);
          }
        } catch (mockError) {
          console.error('목 데이터 로딩 오류:', mockError);
        }
      }
    } finally {
      setImageSearchLoading(false);
    }
  };
  
  // 텍스트 채팅 함수
  const sendChatMessage = async (query) => {
    if (!query.trim()) return;
    
    setIsResponding(true);
    setCurrentResponse('');
    
    try {
      // 사용자 메시지 추가
      const userMessage = { role: 'user', content: query };
      const newMessages = [...chatMessages, userMessage];
      setChatMessages(newMessages);
      
      console.log('텍스트 채팅 API 호출:', query);
      
      // 타이핑 효과를 위한 빈 assistant 메시지 추가
      const assistantMessage = {
        role: 'assistant',
        content: '',
        sources: [],
        suggested_questions: [],
        metadata: {},
        typing: true
      };

      setChatMessages(prev => [...prev, assistantMessage]);

      // 일반 채팅 API 호출
      console.log('API 호출 시작');
      const response = await ChatAPI.sendMessage(newMessages, {
        session_id: exgptAPI.sessionId,
        user_id: exgptAPI.userId,
        department_id: exgptAPI.departmentId
      });
      console.log('API 호출 완료, 응답:', response);

      // 타이핑 효과로 응답 표시
      const fullContent = response.response;
      const words = fullContent.split('');
      let displayedContent = '';

      for (let i = 0; i < words.length; i++) {
        displayedContent += words[i];

        setChatMessages(prev =>
          prev.map((msg, idx) =>
            idx === prev.length - 1
              ? { ...msg, content: displayedContent }
              : msg
          )
        );
        setCurrentResponse(displayedContent);

        // 타이핑 속도 조절 (한글자당 20ms)
        await new Promise(resolve => setTimeout(resolve, 20));
      }

      // 타이핑 완료 후 최종 데이터 설정
      setChatMessages(prev =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? {
                ...msg,
                content: fullContent,
                sources: response.sources,
                suggested_questions: response.suggested_questions,
                metadata: response.metadata,
                typing: false
              }
            : msg
        )
      );

      console.log('타이핑 효과 채팅 응답 완료:', response);
      
    } catch (error) {
      console.error('채팅 오류:', error);
      
      // 오류 메시지 추가
      const errorMessage = {
        role: 'assistant',
        content: `죄송합니다. 현재 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요.\n\n오류 내용: ${error.message}`,
        error: true
      };
      
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsResponding(false);
    }
  };
  
  // 검색 히스토리 처리 (임시 비활성화)
  /*
  const handleHistorySearchSelect = useCallback((query) => {
    setInputValue(query);
    // 자동으로 검색 실행
    const fakeEvent = { preventDefault: () => {} };
    handleSubmit(fakeEvent, query);
  }, []);
  */
  
  // 더 많은 이미지 로드
  const loadMoreImages = useCallback(async () => {
    if (!imageSearchLoading && hasMoreImages && inputValue.trim()) {
      await searchImages(inputValue.trim(), currentImagePage + 1, true);
    }
  }, [imageSearchLoading, hasMoreImages, inputValue, currentImagePage]);
  
  // 폼 제출 핸들러 (통합 검색)
  const handleSubmit = async (e, directQuery = null) => {
    e.preventDefault();
    const query = directQuery || inputValue.trim();
    
    if (!query) return;
    
    // 이미지 검색 키워드 감지
    const imageKeywords = [
      '사진', '이미지', '그림', '해무', '안개', 'cctv', '카메라', 
      '날씨', '시야', '가시거리', '강우', '강설', '야간', '맑음',
      '경부고속도로', '중부고속도로', '서해안고속도로'
    ];
    const hasImageKeyword = imageKeywords.some(keyword => 
      query.toLowerCase().includes(keyword.toLowerCase())
    );
    
    if (hasImageKeyword) {
      // 이미지 검색 실행
      console.log('이미지 검색 모드 감지:', query);

      // 사용자 메시지를 채팅 히스토리에 추가 (이미지 검색도 대화로 표시)
      const userMessage = { role: 'user', content: query };
      setChatMessages(prev => [...prev, userMessage]);

      await searchImages(query);
    } else {
      // 텍스트 채팅 실행
      console.log('텍스트 채팅 모드 감지:', query);
      await sendChatMessage(query);
    }
    
    // 입력 필드 초기화
    setInputValue('');
    setHasText(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.paddingLeft = '2.2em';
    }
  };

  return (
    <>
      {/* Header.jsx */}
      <header className="header">
        <div className="header__inner">
          <div className="header__util-menu">
            <Button
              iconComponent={<ThemeIcon />}
              className="header__util-button"
              label="테마선택"
              titleLabel={getTitleLabel(isLargeScreen, "테마선택")}
              onClick={() =>
                setTheme((prev) => (prev === "light" ? "dark" : "light"))
              }
            />
            <Button
              iconComponent={<TextIcon />}
              className="header__util-button text-size"
              label="글자크기"
              titleLabel={getTitleLabel(isLargeScreen, "글자크기")}
              // 0905 - 글자크기 모달 열기
              onClick={() => setIsFontModalOpen(true)}
            />
            <Button
              iconComponent={<BookIcon />}
              className="header__util-button"
              label="사용법안내"
              titleLabel={getTitleLabel(isLargeScreen, "사용법안내")}
            />
            <Button
              iconComponent={<NoticeIcon />}
              className="header__util-button"
              label="공지사항"
              titleLabel={getTitleLabel(isLargeScreen, "공지사항")}
              // 0905 - 공지사항 모달 열기
              onClick={() => setIsNoticeModalOpen(true)}
            />
            <Button
              iconComponent={<StarIcon />}
              className="header__util-button"
              label="만족도조사"
              titleLabel={getTitleLabel(isLargeScreen, "만족도 조사")}
              // 0905 - 만족도조사 모달 열기
              onClick={() => setIsSurveyModalOpen(true)}
            />
          </div>
        </div>
      </header>
      {/* 글자크기 모달 */}
      <FontSizeModal
        className="font-size-modal"
        isOpen={isFontModalOpen}
        onCancel={() => setIsFontModalOpen(false)}
        onConfirm={handleFontsizeConfirm}
        selectedSize={selectedSize}
        onSelect={(idx) => setSelectedSize(idx)}
      />
      {/* 공지사항 팝업 */}
      <NoticeModal
        className="notice-modal"
        isOpen={isNoticeModalOpen}
        onCancel={() => setIsNoticeModalOpen(false)}
        onConfirm={() => setIsNoticeModalOpen(false)}
      />
      {/* 만족도 조사 팝업 */}
      <SurveyModal
        className="survey-modal"
        isOpen={isSurveyModalOpen}
        onCancel={() => setIsSurveyModalOpen(false)}
        // 확인 로직 변경 작업 필요
        onConfirm={() => setIsSurveyModalOpen(false)}
      />
      <div className="app-container">
        {/* Aside.jsx */}
        <aside className={`aside ${isOpen ? "" : "folded"}`}>
          <div className="aside__inner">
            <h1 className="aside__logo-meta">
              <Button
                className="aside__toggle_btn"
                onClick={toggleAside}
                tabIndex={1}
              >
                {isOpen ? <ToggleCloseIcon /> : <ToggleOpenIcon />}
              </Button>
              <div className="aside__logo-desc">
                <a href="#" tabIndex={1}>
                  <Logo></Logo>
                  <span className="aside__logo-version">1.4</span>
                </a>
                <span className="aside__logo-text">한국도로공사 AI</span>
              </div>
            </h1>
            {/* 프로필 이미지, 현재 버전 정보 */}
            <div className="user-info">
              
            </div>
            {/* 새 대화, 대화 지우기, 국정감사 전용 AI */}
            <div className="aside__list">
              <a href="#" className="aside__link aside__link-new">
                <div className="aside__link__inner">
                  <div className="icon">
                    <PlusIcon />
                  </div>
                  <span className="aside__link-text">새 대화</span>
                  <NewChatGliterIcon />
                </div>
              </a>
              <a href="#" className="aside__link aside__link-gov">
                <div className="aside__link__inner">
                  <div className="icon">
                    <GovInspctionIcon />
                  </div>
                  <span className="aside__link-text">국정감사 전용 AI</span>
                  <ChevronRightIcon className="aside__link-arrow" />
                </div>
              </a>
            </div>
            {/* 이전 대화 기록 */}
            <div className="history-list">
              <div className="history-title">이전 대화</div>
              <a href="#" className="history-item active">
                이전 대화 기록 1
                말줄임테스트말줄임테스트말줄임테스트말줄임테스트말줄임테스트말줄임테스트
              </a>
              <a href="#" className="history-item">
                이전 대화 기록 2
              </a>
              <a href="#" className="history-item">
                이전 대화 기록 3
              </a>
              <a href="#" className="history-item">
                이전 대화 기록 4
              </a>
            </div>
          </div>
          {/* 부서 */}
          <div className="user__dept">
            <div className="user__dept-profile">
              <img src={userDeptProfile} alt="ex-GPT 로고" />
            </div>
            <div className="user__dept-details">
              <div className="user__dept-name">디지털계획처</div>
              <div className="user__dept-extension">(내선:800-4552)</div>
            </div>
          </div>
        </aside>
        {isOpen && <div className="overlay" onClick={toggleAside}></div>}
        {/* content > index.jsx */}
        <div className="content content--layout">
          <div className="top--scrollable">
            {/* Intro */}
            <div className="content__intro_wrapper">
              <div className="content__inner">
                <div className="content__intro">
                  <h2 className="content__intro-title">
                    {/* 0905 ex-GPT 에서 로고 이미지로 변경 */}
                    <ContentLogo />
                  </h2>
                </div>
              </div>
            </div>
            {/* Suggests */}
            {/* 0905 - Suggests.jsx 로 변경 */}
            <Suggests onSuggestClick={handleSuggestClick} />

            {/* Messages */}
            <div className="content__messages_wrapper">
              <div className="content__inner">
                {/* 백엔드 상태 표시 (개발용) - 비활성화 */}
                {false && import.meta.env.DEV && (
                  <div className="backend-status" style={{
                    padding: '10px',
                    margin: '10px 0',
                    backgroundColor: 'rgba(0,0,0,0.1)',
                    borderRadius: '5px',
                    fontSize: '12px'
                  }}>
                    <strong>백엔드 상태:</strong>
                    <span style={{color: backendStatus.multimodal === 'healthy' ? 'green' : 'red'}}>
                      멀티모달({backendStatus.multimodal})
                    </span>
                    {' | '}
                    <span style={{color: backendStatus.mcp === 'healthy' ? 'green' : 'red'}}>
                      MCP({backendStatus.mcp})
                    </span>
                    <button onClick={checkBackendStatus} style={{marginLeft: '10px', fontSize: '10px'}}>
                      상태 새로고침
                    </button>
                  </div>
                )}

                {chatMessages.length === 0 ? (
                  <div className="message-title">
                    <p className="message-title-text">새로운 채팅</p>
                    <span className="message-title-date">{new Date().toLocaleDateString('ko-KR')}</span>
                  </div>
                ) : (
                  <div className="message-title">
                    <p className="message-title-text">대화 진행 중</p>
                    <span className="message-title-date">{new Date().toLocaleDateString('ko-KR')}</span>
                  </div>
                )}

                {/* 이미지 검색 결과 - 이제 채팅 메시지 안에서 표시됨 */}
                {/* <EnhancedImageSearchResults
                  results={imageSearchResults}
                  isLoading={imageSearchLoading}
                  error={imageSearchError}
                  onLoadMore={loadMoreImages}
                  hasMore={hasMoreImages}
                  totalCount={totalImageCount}
                  hasSearched={hasSearched}
                /> */}
                {/* 채팅 메시지 렌더링 */}
                {chatMessages.map((message, index) => (
                  <div key={index} className={`message message--${message.role}`}>
                    {message.role === 'assistant' && (
                      <div className="message__avatar">
                        <GptIcon />
                      </div>
                    )}
                    <div className="message__content">
                      {message.role === 'assistant' && !message.error && (
                        <>
                          {/* 추론 과정 (로딩 중일 때만 표시) */}
                          {isResponding && index === chatMessages.length - 1 && (
                            <div className="message__content_box thinking-container">
                              <div>
                                <div className="message__content_header">
                                  <span className="message__content_header_title">
                                    <span className="icon">
                                      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M16 13.941V10.9354C16 10.7559 16 10.6662 15.9727 10.587C15.9485 10.5169 15.9091 10.4531 15.8572 10.4001C15.7986 10.3403 15.7183 10.3001 15.5578 10.2199L11 7.94098M3 8.94098V15.7476C3 16.1195 3 16.3055 3.05802 16.4683C3.10931 16.6122 3.1929 16.7425 3.30238 16.8491C3.42622 16.9697 3.59527 17.0471 3.93335 17.2021L10.3334 20.1354C10.5786 20.2478 10.7012 20.304 10.8289 20.3262C10.9421 20.3459 11.0579 20.3459 11.1711 20.3262C11.2988 20.304 11.4214 20.2478 11.6666 20.1354L18.0666 17.2021C18.4047 17.0471 18.5738 16.9697 18.6976 16.8491C18.8071 16.7425 18.8907 16.6122 18.942 16.4683C19 16.3055 19 16.1195 19 15.7476V8.94098M1 7.94098L10.6422 3.11987C10.7734 3.05428 10.839 3.02148 10.9078 3.00857C10.9687 2.99714 11.0313 2.99714 11.0922 3.00857C11.161 3.02148 11.2266 3.05428 11.3578 3.11987L21 7.94098L11.3578 12.7621C11.2266 12.8277 11.161 12.8605 11.0922 12.8734C11.0313 12.8848 10.9687 12.8848 10.9078 12.8734C10.839 12.8605 10.7734 12.8277 10.6422 12.7621L1 7.94098Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                      </svg>
                                    </span>
                                    <span style={{color: "#067EE1"}}>추론 중...</span>
                                  </span>
                                </div>
                                <div className="message__content_body thinking-content">
                                  <p>질문을 분석하고 최적의 답변을 준비하고 있습니다...</p>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* 답변 내용 */}
                          <div className="message__content_box response-content">
                            <div className="message__content_header">
                              <div className="message__content_header_title">
                                <span className="icon">
                                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M7.42478 8.84327H11.2941M7.42478 12.2289H14.1961M11.7777 19.0002C16.3188 19.0002 20 15.319 20 10.7779C20 6.2369 16.3188 2.55566 11.7777 2.55566C7.23671 2.55566 3.55548 6.2369 3.55548 10.7779C3.55548 11.6969 3.70624 12.5806 3.98436 13.4058C4.08903 13.7163 4.14136 13.8715 4.1508 13.9908C4.16012 14.1086 4.15307 14.1912 4.12393 14.3057C4.09442 14.4217 4.02927 14.5423 3.89897 14.7834L2.31676 17.712C2.09107 18.1298 1.97823 18.3387 2.00348 18.4999C2.02548 18.6403 2.10812 18.7639 2.22945 18.8379C2.36874 18.9229 2.60489 18.8985 3.07718 18.8496L8.03087 18.3376C8.18088 18.3221 8.25589 18.3143 8.32426 18.3169C8.3915 18.3195 8.43897 18.3258 8.50454 18.3409C8.57121 18.3563 8.65504 18.3886 8.82271 18.4532C9.73979 18.8065 10.7361 19.0002 11.7777 19.0002Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                </span>
                                <span>답변</span>
                              </div>
                            </div>
                            <div className="message__content_body">
                              <div style={{
                                whiteSpace: 'pre-wrap',
                                color: message.error ? '#d32f2f' : 'inherit'
                              }}>
                                {message.content}
                              </div>
                            </div>
                          </div>

                          {/* 이미지 검색 결과 (있는 경우) */}
                          {message.imageSearchResults && (
                            <div className="message__content_box image-search-results">
                              <div className="message__content_header">
                                <div className="message__content_header_title">
                                  <span className="icon">
                                    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M14.6667 1.83333H7.33333C4.11167 1.83333 1.5 4.445 1.5 7.66667V14.3333C1.5 17.555 4.11167 20.1667 7.33333 20.1667H14.6667C17.8883 20.1667 20.5 17.555 20.5 14.3333V7.66667C20.5 4.445 17.8883 1.83333 14.6667 1.83333Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                      <path d="M14.6667 7.33333C15.4031 7.33333 16 6.73638 16 6C16 5.26362 15.4031 4.66667 14.6667 4.66667C13.9303 4.66667 13.3333 5.26362 13.3333 6C13.3333 6.73638 13.9303 7.33333 14.6667 7.33333Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                      <path d="M20.5 15.5833L17.1667 12.25C16.625 11.7083 15.7083 11.7083 15.1667 12.25L7.83333 19.5833M1.5 15.5833L4.83333 12.25C5.375 11.7083 6.29167 11.7083 6.83333 12.25L10.1667 15.5833" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                  </span>
                                  <span>검색 결과 ({message.imageSearchResults.length}개)</span>
                                </div>
                              </div>
                              <div className="message__content_body">
                                {message.imageSearchResults.length > 0 ? (
                                  <div
                                    className="image-results-grid"
                                    style={{
                                      display: 'grid',
                                      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                      gap: '16px',
                                      marginTop: '12px'
                                    }}
                                  >
                                    {message.imageSearchResults.map((image, imageIndex) => (
                                      <div
                                        key={imageIndex}
                                        className="image-result-item"
                                        style={{
                                          border: '1px solid #e0e0e0',
                                          borderRadius: '8px',
                                          padding: '12px',
                                          backgroundColor: '#f9f9f9'
                                        }}
                                      >
                                        <div
                                          className="image-result-preview"
                                          style={{ marginBottom: '8px' }}
                                        >
                                          <img
                                            src={image.image_url || `${API_CONFIG.MULTIMODAL_BASE_URL}${image.image_url}`}
                                            alt={image.description || image.filename}
                                            className="image-result-thumbnail"
                                            style={{
                                              width: '100%',
                                              height: '200px',
                                              objectFit: 'cover',
                                              borderRadius: '4px'
                                            }}
                                            onError={(e) => {
                                              e.target.style.display = 'none';
                                            }}
                                          />
                                        </div>
                                        <div className="image-result-info">
                                          <h4 style={{
                                            fontSize: '14px',
                                            fontWeight: 'bold',
                                            margin: '0 0 8px 0',
                                            color: '#333'
                                          }}>
                                            {image.filename}
                                          </h4>
                                          <p
                                            className="image-description"
                                            style={{
                                              fontSize: '12px',
                                              color: '#666',
                                              margin: '0 0 8px 0',
                                              lineHeight: '1.4'
                                            }}
                                          >
                                            {image.description}
                                          </p>
                                          <div
                                            className="image-metadata"
                                            style={{
                                              display: 'flex',
                                              flexWrap: 'wrap',
                                              gap: '6px'
                                            }}
                                          >
                                            {image.location && (
                                              <span
                                                className="metadata-tag"
                                                style={{
                                                  fontSize: '11px',
                                                  padding: '2px 6px',
                                                  backgroundColor: '#e3f2fd',
                                                  borderRadius: '12px',
                                                  color: '#1976d2'
                                                }}
                                              >
                                                📍 {image.location}
                                              </span>
                                            )}
                                            {image.weather_condition && (
                                              <span
                                                className="metadata-tag"
                                                style={{
                                                  fontSize: '11px',
                                                  padding: '2px 6px',
                                                  backgroundColor: '#fff3e0',
                                                  borderRadius: '12px',
                                                  color: '#f57c00'
                                                }}
                                              >
                                                🌤️ {image.weather_condition}
                                              </span>
                                            )}
                                            {image.relevance_score && (
                                              <span
                                                className="metadata-tag relevance"
                                                style={{
                                                  fontSize: '11px',
                                                  padding: '2px 6px',
                                                  backgroundColor: '#e8f5e8',
                                                  borderRadius: '12px',
                                                  color: '#2e7d32'
                                                }}
                                              >
                                                🎯 {(image.relevance_score * 100).toFixed(0)}% 일치
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <p>검색된 이미지가 없습니다. 다른 검색어를 시도해보세요.</p>
                                )}
                              </div>
                            </div>
                          )}

                          {/* 근거 자료 (있는 경우) */}
                          {message.sources && message.sources.length > 0 && (
                            <div className="message__content_box source-documents">
                              <div className="message__content_header">
                                <div className="message__content_header_title">
                                  <span className="icon">
                                    <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M13.507 2.25624V6.18317C13.507 6.71561 13.507 6.98183 13.6107 7.1852C13.7018 7.36409 13.8472 7.50952 14.0261 7.60067C14.2295 7.70429 14.4957 7.70429 15.0282 7.70429H18.9551M15.4085 11.4437H7.80282M15.4085 15.2465H7.80282M9.70423 7.64084H7.80282M13.507 2H8.56338C6.96605 2 6.16738 2 5.55728 2.31086C5.02062 2.5843 4.5843 3.02062 4.31086 3.55728C4 4.16738 4 4.96605 4 6.56338V15.4366C4 17.034 4 17.8326 4.31086 18.4427C4.5843 18.9794 5.02062 19.4157 5.55728 19.6891C6.16738 20 6.96605 20 8.56338 20H14.6479C16.2452 20 17.0439 20 17.654 19.6891C18.1906 19.4157 18.627 18.9794 18.9004 18.4427C19.2113 17.8326 19.2113 17.034 19.2113 15.4366V7.70423L13.507 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                                    </svg>
                                  </span>
                                  <span>근거</span>
                                </div>
                              </div>
                              <div className="message__content_body">
                                <ul>
                                  {message.sources.map((source, sourceIndex) => (
                                    <li key={sourceIndex}>
                                      <strong>{source.title}</strong>
                                      <span className="relevance-score"> ({(source.relevance_score * 100).toFixed(0)}% 일치)</span>
                                      {source.url && (
                                        <a href={source.url} className="message__content_button" target="_blank" rel="noopener noreferrer">
                                          다운로드
                                        </a>
                                      )}
                                      <div className="source-documents-preview">
                                        <p>{source.content_preview}</p>
                                      </div>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                      
                      {message.role === 'user' && (
                        <div className="message__content_body" style={{whiteSpace: 'pre-wrap'}}>
                          {message.content}
                        </div>
                      )}
                    </div>
                    
                    {message.role === 'assistant' && !message.error && (
                      <div className="message__error__button">
                        <Button
                          iconComponent={<ErrorSubmitIcon />}
                          className="message__error__icon"
                        />
                        <span className="message__error__tooltip">
                          오류 신고하세요!
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* 기존 샘플 메시지 (개발용) - 비활성화 */}
                {false && chatMessages.length === 0 && (
                  <>
                    <div className="message message--assistant">
                      <div className="message__avatar">
                        <GptIcon />
                      </div>
                      <div className="message__content">
                        <div className="message__content_box thinking-container">
                        <div>
                          <div className="message__content_header">
                            <span className="message__content_header_title">
                              <span className="icon">
                                <svg
                                  width="22"
                                  height="22"
                                  viewBox="0 0 22 22"
                                  fill="none"
                                  xmlns="http://www.w3.org/2000/svg"
                                >
                                  <path
                                    d="M16 13.941V10.9354C16 10.7559 16 10.6662 15.9727 10.587C15.9485 10.5169 15.9091 10.4531 15.8572 10.4001C15.7986 10.3403 15.7183 10.3001 15.5578 10.2199L11 7.94098M3 8.94098V15.7476C3 16.1195 3 16.3055 3.05802 16.4683C3.10931 16.6122 3.1929 16.7425 3.30238 16.8491C3.42622 16.9697 3.59527 17.0471 3.93335 17.2021L10.3334 20.1354C10.5786 20.2478 10.7012 20.304 10.8289 20.3262C10.9421 20.3459 11.0579 20.3459 11.1711 20.3262C11.2988 20.304 11.4214 20.2478 11.6666 20.1354L18.0666 17.2021C18.4047 17.0471 18.5738 16.9697 18.6976 16.8491C18.8071 16.7425 18.8907 16.6122 18.942 16.4683C19 16.3055 19 16.1195 19 15.7476V8.94098M1 7.94098L10.6422 3.11987C10.7734 3.05428 10.839 3.02148 10.9078 3.00857C10.9687 2.99714 11.0313 2.99714 11.0922 3.00857C11.161 3.02148 11.2266 3.05428 11.3578 3.11987L21 7.94098L11.3578 12.7621C11.2266 12.8277 11.161 12.8605 11.0922 12.8734C11.0313 12.8848 10.9687 12.8848 10.9078 12.8734C10.839 12.8605 10.7734 12.8277 10.6422 12.7621L1 7.94098Z"
                                    stroke="currentColor"
                                    strokeWidth="1.6"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  />
                                </svg>
                              </span>
                              {/* 추론 중일 때 */}
                              <span style={{ color: "#067EE1" }}>추론 중...</span>
                              <span>추론 과정 보기</span>
                            </span>
                            <Button
                              type="button"
                              label={
                                isThinkingContentOpen ? "숨기기" : "상세보기"
                              }
                              className={`thinking-toggle-btn ${
                                isThinkingContentOpen ? "rotate" : ""
                              }`}
                              iconComponent={<DetailArrowIcon />}
                              iconPosition="right"
                              onClick={() =>
                                setThinkingContentOpen((prev) => !prev)
                              }
                            ></Button>
                          </div>
                          <div
                            className={`message__content_body thinking-content ${
                              isThinkingContentOpen ? "active" : ""
                            }`}
                          >
                            <p>
                              Okay, let's tackle this question about how toll fees
                              are calculated in Korea. The user is asking for the
                              method used to determine the toll, so I need to
                              refer to the provided documents.
                            </p>
                            <p>
                              First, I'll look through the retrieved data. There
                              are multiple sources, some from '영업규정' and
                              others from '통행요금제도 및 조정절차'. The first
                              source mentions a two-part toll system consisting of
                              a base fee and a running fee. The base fee depends
                              on the payment method and number of lanes, while the
                              running fee is based on the shortest distance and
                              vehicle type.{" "}
                            </p>
                            <p>
                              Looking at Source 4, there's a formula: Toll = Base
                              Fee + (Running Distance × Running Fee per km). The
                              base fee is listed as 900 won for closed systems and
                              720 won for open systems, with discounts for
                              two-lane roads. The running fee per km varies by
                              vehicle type, with different rates for small,
                              medium, large, and special vehicles. There's also
                              information on discounts and surcharges based on the
                              number of lanes.
                            </p>
                            <p>
                              Source 5 also outlines the base fees and running
                              fees, aligning with Source 4. It mentions that the
                              base fee is 900 won for closed systems (with 50%
                              discount for two-lane) and 720 won for open systems.
                              The running fee is calculated by multiplying the
                              distance by the vehicle-specific rate.
                            </p>
                            <p>
                              Additionally, Source 3 explains that the toll
                              structure is a two-part system to ensure fairness
                              and regional balance. The base fee covers fixed
                              costs like construction, while the running fee
                              covers variable operational costs based on distance
                              and vehicle type.
                            </p>
                            <p>
                              Putting this together, the answer should explain the
                              two-part system, the components of each part, and
                              how they are calculated, including any discounts or
                              surcharges. It's important to mention the different
                              vehicle categories and how lane numbers affect the
                              fees. Also, note that distances are rounded to the
                              nearest decimal as per the regulations.
                            </p>
                          </div>
                        </div>
                      </div>
                      {/* 답변 */}
                      <div className="message__content_box response-content">
                        <div className="message__content_header">
                          <div className="message__content_header_title">
                            <span className="icon">
                              <svg
                                width="22"
                                height="22"
                                viewBox="0 0 22 22"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                              >
                                <path
                                  d="M7.42478 8.84327H11.2941M7.42478 12.2289H14.1961M11.7777 19.0002C16.3188 19.0002 20 15.319 20 10.7779C20 6.2369 16.3188 2.55566 11.7777 2.55566C7.23671 2.55566 3.55548 6.2369 3.55548 10.7779C3.55548 11.6969 3.70624 12.5806 3.98436 13.4058C4.08903 13.7163 4.14136 13.8715 4.1508 13.9908C4.16012 14.1086 4.15307 14.1912 4.12393 14.3057C4.09442 14.4217 4.02927 14.5423 3.89897 14.7834L2.31676 17.712C2.09107 18.1298 1.97823 18.3387 2.00348 18.4999C2.02548 18.6403 2.10812 18.7639 2.22945 18.8379C2.36874 18.9229 2.60489 18.8985 3.07718 18.8496L8.03087 18.3376C8.18088 18.3221 8.25589 18.3143 8.32426 18.3169C8.3915 18.3195 8.43897 18.3258 8.50454 18.3409C8.57121 18.3563 8.65504 18.3886 8.82271 18.4532C9.73979 18.8065 10.7361 19.0002 11.7777 19.0002Z"
                                  stroke="currentColor"
                                  strokeWidth="1.6"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </span>
                            <span>답변</span>
                          </div>
                        </div>
                        <div className="message__content_body">
                          <p>
                            <strong>
                              둘째 자녀 출산 시 출산 지원비는 2,000천원(200만
                              원)입니다.
                            </strong>
                          </p>
                          <h3>근거: </h3>
                          <ul>
                            <li>
                              <p>
                                <strong>출산 지원 기준</strong>
                              </p>
                              <table>
                                <thead>
                                  <tr>
                                    <th>
                                      <strong>순서</strong>
                                    </th>
                                    <th>
                                      <strong>지급 금액</strong>
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr>
                                    <td>첫째 자녀</td>
                                    <td>1,000천원 (100만 원)</td>
                                  </tr>
                                  <tr>
                                    <td>둘째 자녀</td>
                                    <td>
                                      <strong>2,000천원 (200만 원)</strong>
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>셋째 자녀 이상</td>
                                    <td>3,000천원 (300만 원)</td>
                                  </tr>
                                  <tr>
                                    <td>다태아(쌍둥이 등)</td>
                                    <td>추가 500천원 (50만 원)</td>
                                  </tr>
                                </tbody>
                              </table>
                            </li>
                            <li>
                              <p>
                                <strong>출처</strong>:
                              </p>
                              <ul>
                                <li>
                                  <strong>Source 1</strong>의 "지원내용" 표 및{" "}
                                  <strong>Source 2</strong>의 "출산장려금"
                                  항목에서 확인 가능합니다.{" "}
                                </li>
                                <li>
                                  둘째 자녀 출산 시 <strong>200만 원</strong>이
                                  지급되며, 다태아일 경우{" "}
                                  <strong>추가 50만 원</strong>이 지급됩니다.
                                </li>
                              </ul>
                            </li>
                          </ul>
                          <h3>참고:</h3>
                          <ul>
                            <li>
                              <p>
                                <strong>신청 시 필요한 서류</strong>:
                              </p>
                              <ul>
                                <li>주민등록등본 또는 가족관계증명서 </li>
                                <li>임신 진단서(산전/산후 휴가 신청 시)</li>
                              </ul>
                            </li>
                            <li>
                              <p>
                                <strong>기타 혜택</strong>:
                              </p>
                              <ul>
                                <li>
                                  <strong>출산 전후 보호휴가</strong> (90일, 유급
                                  60일 + 고용보험 30일)
                                </li>
                                <li>
                                  <strong>난임시술 지원</strong> (최대 720만 원
                                  한도)
                                </li>
                              </ul>
                            </li>
                          </ul>
                          <p>
                            자세한 신청 절차는 <strong>인력처 노무부</strong> 또는{" "}
                            <strong>하이포탈</strong>을 통해 확인하시기 바랍니다.
                          </p>
                        </div>
                      </div>
                      {/* 근거 */}
                      <div className="message__content_box source-documents">
                        <div className="message__content_header">
                          <div className="message__content_header_title">
                            <span className="icon">
                              <svg
                                width="22"
                                height="22"
                                viewBox="0 0 22 22"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                              >
                                <path
                                  d="M13.507 2.25624V6.18317C13.507 6.71561 13.507 6.98183 13.6107 7.1852C13.7018 7.36409 13.8472 7.50952 14.0261 7.60067C14.2295 7.70429 14.4957 7.70429 15.0282 7.70429H18.9551M15.4085 11.4437H7.80282M15.4085 15.2465H7.80282M9.70423 7.64084H7.80282M13.507 2H8.56338C6.96605 2 6.16738 2 5.55728 2.31086C5.02062 2.5843 4.5843 3.02062 4.31086 3.55728C4 4.16738 4 4.96605 4 6.56338V15.4366C4 17.034 4 17.8326 4.31086 18.4427C4.5843 18.9794 5.02062 19.4157 5.55728 19.6891C6.16738 20 6.96605 20 8.56338 20H14.6479C16.2452 20 17.0439 20 17.654 19.6891C18.1906 19.4157 18.627 18.9794 18.9004 18.4427C19.2113 17.8326 19.2113 17.034 19.2113 15.4366V7.70423L13.507 2Z"
                                  stroke="currentColor"
                                  strokeWidth="1.6"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </span>
                            <span>근거</span>
                          </div>
                        </div>
                        <div className="message__content_body">
                          <ul>
                            <li>
                              <strong>2025년 복리후생 매뉴얼(복지제도편)</strong>
                              <span className="relevance-score"> (97% 일치)</span>
                              <a
                                href="./v1/file/public/fc508e91c2ecdd60/download"
                                className="message__content_button"
                                target="_blank"
                              >
                                {" "}
                                다운로드
                              </a>
                              <Button
                                type="button"
                                label={
                                  isSourceContentOpen ? "숨기기" : "상세보기"
                                }
                                className={`message__content_button source-toggle-button ${
                                  isSourceContentOpen ? "rotate" : ""
                                }`}
                                iconComponent={<DetailArrowIcon />}
                                iconPosition="right"
                                onClick={() =>
                                  setSourceContentOpen((prev) => !prev)
                                }
                              ></Button>
                              <div
                                className={`source-documents-preview ${
                                  isSourceContentOpen ? "active" : ""
                                }`}
                              >
                                {/* ❍ 서식을 • 로 변경 */}
                                <h1>출산장려금</h1>
                                <p>신청</p>
                                <p>
                                  • (첨부서류) 자녀가 표기된 주민등록등본 또는
                                  가족관계증명서
                                </p>
                                <p>
                                  <strong>지원내용</strong>
                                </p>
                                <p>
                                  {" "}
                                  | <strong>구 분</strong> |{" "}
                                  <strong>지급기준</strong> | | 출산 지원 | - 첫째
                                  자녀 출산시 1,000천원 - 둘째 자녀 출산시
                                  2,000천원 - 셋째 자녀 이상 출산시 3,000천원 -
                                  다태아(多胎兒) 출산시 500천원 추가 |{" "}
                                </p>
                                <p>
                                  {" "}
                                  | | 66 | | <strong>출산전후 휴가</strong> |{" "}
                                </p>
                                <p>인력처 노무부(800-2132)</p>
                                <p>
                                  <strong>제도개요</strong>
                                </p>
                                <p>
                                  • 임신 중인 여성직원에게 출산 전후에 보호휴가를
                                  부여
                                </p>
                                <p>
                                  <strong>관련근거</strong>
                                </p>
                                <p>• 취업규정 제25조 (특별휴가)</p>
                                <p>
                                  <strong>지원대상</strong>
                                </p>
                                <p>• 임신 중인 여성 직원 (기간제근로자 포함)</p>
                                <p>
                                  <strong>신청절차</strong>
                                </p>
                                <p>
                                  • (하이포탈) 인력정보 → 노무 → 근태관리 →
                                  휴가신청(특별휴가-여직원휴가-산전/산후)
                                </p>
                                <p>
                                  • (첨부서류) 임신기간 및 출산예정일이 기재된
                                  진단서
                                </p>
                                <p>
                                  <strong>지원내용</strong>
                                </p>
                                <p>
                                  • 출산의 전후를 통하여 90일(미숙아 100일, 쌍생아
                                  120일)의 보호휴가 부여
                                </p>
                                <p>
                                  • 최초 60일에 대해서는 유급휴가, 60일 초과기간은
                                  고용보험 지급
                                </p>
                                <p>
                                  <strong>기타</strong>
                                  <strong>
                                    (
                                    <strong>
                                      <strong>유의사항 등</strong>
                                    </strong>
                                    )
                                  </strong>
                                </p>
                                <p>
                                  • 출산 다음날로부터 휴가종료일까지의 기간이
                                  45일(쌍생아 60일) 이상이어야 함
                                </p>
                              </div>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                    <div className="message__error__button">
                      <Button
                        iconComponent={<ErrorSubmitIcon />}
                        className="message__error__icon"
                      ></Button>
                      <span className="message__error__tooltip">
                        오류 신고하세요!
                      </span>
                    </div>
                  </div>
                  <div className="message message--user">
                    {/* <div className="message__avatar"></div> */}
                    <div className="message__content">
                      메시지메시지메시지메시지
                    </div>
                  </div>
                  </>
                )}
              </div>
            </div>
          </div>
          {/* Form */}
          <div className="content__form_wrapper">
            <div className="content__inner">
              <div
                className={`content__form_section ${hasText ? "active" : ""}`}
              >
                {/* 첨부파일 목록 - 샘플 비활성화 */}
                {false && (
                  <div className="attached-files">
                    <div className="attached-file-header">
                      <span className="attached-file-header-title">첨부파일</span>
                      {/* 0905 모두 삭제 띄어쓰기 -> 모두삭제 */}
                      <Button className="attached-file-header-remove-all">
                        모두삭제
                      </Button>
                    </div>
                    <div className="attached-file-list">
                      <div className="attached-file-item">
                        <div className="attached-file-info">
                          <span className="attached-file-icon">
                            <ClipIcon />
                          </span>
                          <span className="attached-file-name">
                            의사결정지원시스템_오픈API(6종)_안내페이지(안).hwp
                          </span>
                          <span className="attached-file-size">15.5 KB</span>
                        </div>
                        <Button
                          className="attached-file-remove"
                          iconComponent={<FileDeleteIcon />}
                        ></Button>
                      </div>
                    </div>
                  </div>
                )}
                {/* 검색 */}
                <form className="content__form" onSubmit={handleSubmit}>
                  {/* <div className="form-header">
                    <SearchHistory
                      onSearchSelect={handleHistorySearchSelect}
                      currentQuery={inputValue}
                      className="search-history-widget"
                    />
                  </div> */}
                  <label htmlFor="message" className="sr-only">
                    메시지 입력
                  </label>
                  {!hasText && (
                    <img
                      src={fileHighLightIcon}
                      alt="강조 아이콘"
                      className="content__form-gliter-icon"
                    />
                  )}
                  {/* 0905 rows="1" 추가 */}
                  <textarea
                    id="message"
                    className="content__form-textarea"
                    name="message"
                    rows="1"
                    ref={textareaRef}
                    value={inputValue}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    placeholder="ex-GPT에 무엇이든 물어보세요"
                  ></textarea>
                  {/* 버튼들 */}
                  <div className="content__form_btn">
                    {/* 파일첨부 */}
                    <label
                      htmlFor="file-upload"
                      className="content__form-file-label"
                    >
                      <input type="file" id="file-upload" className="sr-only" />
                      {/* div로도 테스트 */}
                      <span className="tooltip">
                        파일첨부 (최대 5개, 각 파일 100MB 까지)
                      </span>
                    </label>
                    {/* 전송 */}
                    <Button
                      type="submit"
                      label="전송"
                      className={`content__form-submit ${
                        hasText ? "active" : ""
                      }`}
                      iconComponent={SubmitIcon}
                    ></Button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* modal.jsx */}
      {/* 사용법 안내 팝업 */}
      {/* GuideModal.jsx */}
      <div className="modal guide-modal">
        <div className="modal-box">
          <button className="modal-close">
            <ModalCloseIcon></ModalCloseIcon>
          </button>
          <div className="modal-header">
            <p className="modal-header-title">사용법 안내</p>
          </div>
          <div className="modal-content">
            <div className="modal-content-inn">
              <div className="guide-modal-set">
                <div className="guide-modal-title">기본 사용법</div>
                <ul className="guide-modal-list">
                  <li>질문을 입력하고 Enter 또는 전송 버튼을 클릭하세요</li>
                  <li>AI가 실시간으로 답변을 제공합니다</li>
                  <li>추천 질문을 클릭하여 빠르게 질문할 수 있습니다</li>
                </ul>
              </div>
              <div className="guide-modal-set">
                <div className="guide-modal-title">주요 기능</div>
                <ul className="guide-modal-list">
                  <li>
                    <span className="icon-inn">
                      <TextIcon />
                    </span>
                    글자 크기 조절: 읽기 편한 크기로 조정
                  </li>
                  <li>
                    <span className="icon-inn">
                      <NoticeIcon />
                    </span>
                    공지사항: 시스템 업데이트 및 공지 확인
                  </li>
                  <li>
                    <span className="icon-inn">
                      <StarIcon />
                    </span>
                    만족도 조사: 서비스 개선을 위한 의견 제출
                  </li>
                  <li>
                    <span className="icon-inn">
                      <GovInspctionIcon />
                    </span>
                    국정감사 전용 AI: 국정감사 업무에 특화된 AI 모드 선택
                  </li>
                </ul>
              </div>
              <div className="guide-modal-set">
                <div className="guide-modal-title">단축키</div>
                <ul className="guide-modal-list">
                  <li>
                    <em>Enter:</em> 메시지 전송
                  </li>
                  <li>
                    <em>Shift + Enter:</em> 줄바꿈
                  </li>
                  {/* <li>
                    <em>Ctrl + T:</em>Think 모드 토글
                  </li> */}
                </ul>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <div className="flex-end">
              <Button className="primary" label="확인"></Button>
            </div>
          </div>
        </div>
      </div>
      {/* 오류사항신고 팝업 */}
      {/* ErrorSubmitModal */}
      <div className="modal error-submit-modal">
        <div className="modal-box">
          <button className="modal-close">
            <ModalCloseIcon></ModalCloseIcon>
          </button>
          <div className="modal-header">
            <p className="modal-header-title">오류사항신고</p>
          </div>
          <div className="modal-content">
            <div className="modal-content-inn">
              <div className="error-submit-modal-title">
                <p>
                  이 답변을 오류신고 하시겠습니까?
                  <br />
                  답변내용과 해당 1개 질문이 디지털계획처로 전송됩니다.
                </p>
              </div>
              <div className="error-submit-modal-select">
                <div className="error-submit-modal-select__option">
                  더 자세히 알려주세요
                </div>
                <div className="error-submit-modal-select__option">
                  메모리를 사용해선 안 됐습니다
                </div>
                <div className="error-submit-modal-select__option">
                  성격이 별로예요
                </div>
                <div className="error-submit-modal-select__option">
                  스타일이 마음에 들지 않습니다
                </div>
                <div className="error-submit-modal-select__option">
                  올바른 사실이 아닌 말을 했습니다
                </div>
                <div className="error-submit-modal-select__option">
                  지시한 내용을 다 따르지 않았습니다
                </div>
              </div>
              <textarea
                name=""
                id=""
                rows="6"
                placeholder="추가의견"
                className="error-submit-modal-textarea"
              ></textarea>
            </div>
          </div>
          <div className="modal-footer">
            <div className="flex-end">
              <Button className="secondary" label="취소"></Button>
              <Button className="primary" label="제출"></Button>
            </div>
          </div>
        </div>
      </div>
      {/* 파일업로드 팝업 */}
      {/* FileUploadModal */}
      <div className="modal file-upload-modal">
        <div className="modal-box">
          <button className="modal-close">
            <ModalCloseIcon></ModalCloseIcon>
          </button>
          <div className="modal-header">
            <p className="modal-header-title">파일업로드</p>
          </div>
          <div className="modal-content">
            <div className="modal-content-inn">
              <div className="file-upload-modal-area">
                <div className="file-upload-modal-set">
                  <div className="file-upload-modal__icon">
                    <ClipIcon />
                  </div>
                  <div className="file-upload-modal-file">
                    <div className="file-upload-modal-file__name">
                      ex-GPT_화면기능 정의서 _v.0.txt
                    </div>
                    <div className="file-upload-modal-file__size">2.83MB</div>
                  </div>
                  <Button
                    iconComponent={<FileDeleteIcon />}
                    className="file-upload-modal__delete"
                  ></Button>
                </div>
                <div className="file-upload-modal-set">
                  <div className="file-upload-modal__icon">
                    <DocumentIcon />
                  </div>
                  <div className="file-upload-modal-file">
                    <div className="file-upload-modal-file__name">
                      ex-GPT_화면기능 정의서 _v.0.ppt
                    </div>
                    <div className="file-upload-modal-file__size">2.83MB</div>
                  </div>
                  <Button
                    iconComponent={<FileDeleteIcon />}
                    className="file-upload-modal__delete"
                  ></Button>
                </div>
              </div>
              <div className="file-upload-modal-info">
                선택한 파일들을 AI가 학습하여
                <br />
                문서 내용에 대한 질문에 답변 할 수 있습니다.
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <div className="flex-end">
              <Button className="secondary" label="취소"></Button>
              <Button className="primary" label="학습하기"></Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default App;

// 전체 구조 참고
{
  /* <Header></Header>
<div className="app-container">
  <Aside></Aside>
  <Content></Content>
</div> */
}

// 구조 변경 시 scss 에 적은 이미지 파일 경로 변경 필요

// // 마크다운 변환 라이브러리 예: marked.js 사용
// const input = document.getElementById('markdown-input');
// const preview = document.getElementById('markdown-preview');
// const downloadBtn = document.getElementById('download-btn');

// // 입력값이 바뀔 때마다 미리보기 업데이트
// input.addEventListener('input', () => {
//   preview.innerHTML = marked(input.value);
// });

// // 다운로드 기능
// downloadBtn.addEventListener('click', () => {
//   const blob = new Blob([input.value], { type: 'text/markdown' });
//   const url = URL.createObjectURL(blob);

//   const a = document.createElement('a');
//   a.href = url;
//   a.download = 'content.md';
//   a.click();
//   URL.revokeObjectURL(url);
// });
