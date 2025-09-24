"""
Admin UI for ex-GPT System
관리도구 웹 인터페이스
"""

from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
import json
from werkzeug.utils import secure_filename
import logging

# 로컬 모듈
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from admin_tools.upload_handler import AdminUploadHandler, UploadType
from image_processing import IntegratedImageAnalyzer, ProcessingMode

# Flask 앱 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ex-gpt-admin-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 핸들러
upload_handler = None
image_analyzer = None

# HTML 템플릿
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ex-GPT 관리도구</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 5px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: #f7f7ff;
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background: #e7e7ff;
        }
        
        .file-input {
            display: none;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #5568d3;
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
        }
        
        .btn-danger {
            background: #dc3545;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .file-list {
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .file-item {
            background: #f8f9fa;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .file-info {
            flex-grow: 1;
        }
        
        .file-name {
            font-weight: bold;
            color: #333;
        }
        
        .file-meta {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 10px;
            margin-top: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            background: #667eea;
            height: 100%;
            width: 0%;
            transition: width 0.3s;
        }
        
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        
        .tab-container {
            margin-top: 20px;
        }
        
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab-button {
            padding: 10px 20px;
            background: #f8f9fa;
            border: none;
            border-radius: 5px 5px 0 0;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .tab-button.active {
            background: white;
            border-bottom: 2px solid #667eea;
        }
        
        .tab-content {
            background: white;
            padding: 20px;
            border-radius: 0 5px 5px 5px;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ex-GPT 관리도구</h1>
            <p>한국도로공사 AI 어시스턴트 시스템 관리</p>
        </div>
        
        <div id="alerts"></div>
        
        <div class="main-content">
            <!-- 파일 업로드 카드 -->
            <div class="card">
                <h2>📤 파일 업로드</h2>
                
                <div class="upload-area" id="uploadArea">
                    <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                    <p style="margin-top: 10px; color: #666;">파일을 드래그하거나 클릭하여 업로드</p>
                    <p style="font-size: 12px; color: #999; margin-top: 5px;">지원: 이미지, PDF, 문서, 엑셀</p>
                </div>
                
                <input type="file" id="fileInput" class="file-input" multiple accept=".jpg,.jpeg,.png,.pdf,.doc,.docx,.xls,.xlsx,.hwp,.txt">
                
                <div style="margin-top: 15px;">
                    <label style="color: #666; font-size: 14px;">
                        업로드 유형:
                        <select id="uploadType" style="margin-left: 10px; padding: 5px;">
                            <option value="admin">관리자 (영구저장)</option>
                            <option value="user">사용자 (임시저장)</option>
                            <option value="batch">배치 업로드</option>
                            <option value="ga">국정감사 자료</option>
                        </select>
                    </label>
                </div>
                
                <div class="progress-bar" id="progressBar" style="display: none;">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                
                <div class="file-list" id="fileList"></div>
                
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <button class="btn" onclick="uploadFiles()">업로드 시작</button>
                    <button class="btn btn-secondary" onclick="clearFiles()">목록 비우기</button>
                </div>
            </div>
            
            <!-- 통계 카드 -->
            <div class="card">
                <h2>📊 시스템 통계</h2>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="totalFiles">0</div>
                        <div class="stat-label">총 파일 수</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="processedFiles">0</div>
                        <div class="stat-label">처리 완료</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="queuedFiles">0</div>
                        <div class="stat-label">대기 중</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="totalSize">0MB</div>
                        <div class="stat-label">총 용량</div>
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="btn" onclick="refreshStats()">새로고침</button>
                    <button class="btn btn-secondary" onclick="exportStats()">통계 내보내기</button>
                </div>
            </div>
        </div>
        
        <!-- 탭 컨테이너 -->
        <div class="card" style="margin-top: 20px;">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="switchTab('processing')">처리 현황</button>
                <button class="tab-button" onclick="switchTab('search')">이미지 검색</button>
                <button class="tab-button" onclick="switchTab('settings')">설정</button>
            </div>
            
            <div class="tab-content">
                <div class="tab-pane active" id="processingTab">
                    <h3>🔄 처리 현황</h3>
                    <div id="processingList" style="margin-top: 15px;">
                        <p style="color: #666;">처리 중인 파일이 없습니다.</p>
                    </div>
                </div>
                
                <div class="tab-pane" id="searchTab">
                    <h3>🔍 이미지 검색</h3>
                    <div style="margin-top: 15px;">
                        <input type="text" id="searchQuery" placeholder="검색어를 입력하세요..." 
                               style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        <button class="btn" onclick="searchImages()" style="margin-top: 10px;">검색</button>
                    </div>
                    <div id="searchResults" style="margin-top: 20px;"></div>
                </div>
                
                <div class="tab-pane" id="settingsTab">
                    <h3>⚙️ 설정</h3>
                    <div style="margin-top: 15px;">
                        <label style="display: block; margin-bottom: 10px;">
                            <input type="checkbox" id="enableOCR" checked> OCR 자동 실행
                        </label>
                        <label style="display: block; margin-bottom: 10px;">
                            <input type="checkbox" id="enableVLM" checked> Vision Language Model 사용
                        </label>
                        <label style="display: block; margin-bottom: 10px;">
                            <input type="checkbox" id="detectPersonalInfo" checked> 개인정보 자동 검출
                        </label>
                        <label style="display: block; margin-bottom: 10px;">
                            <input type="checkbox" id="checkDuplicate" checked> 중복 파일 검사
                        </label>
                        
                        <div style="margin-top: 20px;">
                            <button class="btn" onclick="saveSettings()">설정 저장</button>
                            <button class="btn btn-danger" onclick="cleanupOldFiles()" style="margin-left: 10px;">
                                오래된 파일 정리
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFiles = [];
        let uploadQueue = [];
        
        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            refreshStats();
            loadSettings();
        });
        
        function setupEventListeners() {
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            
            // 클릭 이벤트
            uploadArea.addEventListener('click', () => fileInput.click());
            
            // 드래그 앤 드롭
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFiles(e.dataTransfer.files);
            });
            
            // 파일 선택
            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });
        }
        
        function handleFiles(files) {
            for (let file of files) {
                if (!selectedFiles.find(f => f.name === file.name)) {
                    selectedFiles.push(file);
                }
            }
            updateFileList();
        }
        
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            
            if (selectedFiles.length === 0) {
                fileList.innerHTML = '<p style="color: #999; text-align: center;">선택된 파일이 없습니다.</p>';
                return;
            }
            
            fileList.innerHTML = selectedFiles.map((file, index) => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">
                            크기: ${formatFileSize(file.size)} | 유형: ${file.type || 'unknown'}
                        </div>
                    </div>
                    <button class="btn btn-danger" onclick="removeFile(${index})">삭제</button>
                </div>
            `).join('');
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileList();
        }
        
        function clearFiles() {
            selectedFiles = [];
            updateFileList();
        }
        
        async function uploadFiles() {
            if (selectedFiles.length === 0) {
                showAlert('선택된 파일이 없습니다.', 'warning');
                return;
            }
            
            const uploadType = document.getElementById('uploadType').value;
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            
            progressBar.style.display = 'block';
            
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const formData = new FormData();
                formData.append('file', file);
                formData.append('upload_type', uploadType);
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        showAlert(`${file.name} 업로드 성공`, 'success');
                    } else {
                        showAlert(`${file.name} 업로드 실패`, 'error');
                    }
                } catch (error) {
                    showAlert(`오류: ${error.message}`, 'error');
                }
                
                // 진행률 업데이트
                const progress = ((i + 1) / selectedFiles.length) * 100;
                progressFill.style.width = progress + '%';
            }
            
            // 완료 후 초기화
            setTimeout(() => {
                progressBar.style.display = 'none';
                progressFill.style.width = '0%';
                clearFiles();
                refreshStats();
            }, 1000);
        }
        
        async function refreshStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('totalFiles').textContent = stats.total_uploads || 0;
                document.getElementById('processedFiles').textContent = stats.processed || 0;
                document.getElementById('queuedFiles').textContent = stats.queued || 0;
                document.getElementById('totalSize').textContent = formatFileSize(stats.total_size || 0);
            } catch (error) {
                console.error('통계 로드 실패:', error);
            }
        }
        
        async function searchImages() {
            const query = document.getElementById('searchQuery').value;
            if (!query) {
                showAlert('검색어를 입력하세요.', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });
                
                const results = await response.json();
                displaySearchResults(results);
            } catch (error) {
                showAlert(`검색 실패: ${error.message}`, 'error');
            }
        }
        
        function displaySearchResults(results) {
            const resultsDiv = document.getElementById('searchResults');
            
            if (!results || results.length === 0) {
                resultsDiv.innerHTML = '<p style="color: #999;">검색 결과가 없습니다.</p>';
                return;
            }
            
            resultsDiv.innerHTML = results.map(result => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-name">${result.filename}</div>
                        <div class="file-meta">유사도: ${(result.score * 100).toFixed(1)}%</div>
                    </div>
                    <button class="btn" onclick="viewDetails('${result.id}')">상세보기</button>
                </div>
            `).join('');
        }
        
        function switchTab(tabName) {
            // 모든 탭 버튼 비활성화
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // 모든 탭 패널 숨기기
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // 선택된 탭 활성화
            event.target.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
        }
        
        function loadSettings() {
            // 로컬 스토리지에서 설정 로드
            const settings = localStorage.getItem('exGPTSettings');
            if (settings) {
                const parsed = JSON.parse(settings);
                document.getElementById('enableOCR').checked = parsed.enableOCR !== false;
                document.getElementById('enableVLM').checked = parsed.enableVLM !== false;
                document.getElementById('detectPersonalInfo').checked = parsed.detectPersonalInfo !== false;
                document.getElementById('checkDuplicate').checked = parsed.checkDuplicate !== false;
            }
        }
        
        function saveSettings() {
            const settings = {
                enableOCR: document.getElementById('enableOCR').checked,
                enableVLM: document.getElementById('enableVLM').checked,
                detectPersonalInfo: document.getElementById('detectPersonalInfo').checked,
                checkDuplicate: document.getElementById('checkDuplicate').checked
            };
            
            localStorage.setItem('exGPTSettings', JSON.stringify(settings));
            showAlert('설정이 저장되었습니다.', 'success');
        }
        
        async function cleanupOldFiles() {
            if (!confirm('7일 이상된 파일을 삭제하시겠습니까?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/cleanup', {method: 'POST'});
                const result = await response.json();
                showAlert(`${result.cleaned}개 파일이 정리되었습니다.`, 'success');
                refreshStats();
            } catch (error) {
                showAlert(`정리 실패: ${error.message}`, 'error');
            }
        }
        
        function showAlert(message, type) {
            const alertsDiv = document.getElementById('alerts');
            const alertClass = `alert-${type}`;
            
            const alert = document.createElement('div');
            alert.className = `alert ${alertClass}`;
            alert.textContent = message;
            
            alertsDiv.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // 자동 새로고침 (10초마다)
        setInterval(refreshStats, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(ADMIN_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
async def upload():
    """파일 업로드 API"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400
            
        file = request.files['file']
        upload_type = request.form.get('upload_type', 'admin')
        
        # 업로드 처리
        result = await upload_handler.upload_file(
            file,
            UploadType[upload_type.upper()],
            user_id='admin'
        )
        
        return jsonify({
            'success': True,
            'file_id': result.file_id,
            'status': result.processing_status
        })
        
    except Exception as e:
        logger.error(f"업로드 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
async def stats():
    """통계 조회 API"""
    try:
        stats = await upload_handler.get_upload_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"통계 조회 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
async def search():
    """이미지 검색 API"""
    try:
        query = request.json.get('query')
        
        # 검색 로직 구현
        results = []  # 실제 검색 구현 필요
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"검색 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
async def cleanup():
    """오래된 파일 정리 API"""
    try:
        await upload_handler.cleanup_old_files(days=7)
        return jsonify({'success': True, 'cleaned': 10})  # 실제 개수 반환 필요
    except Exception as e:
        logger.error(f"정리 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_async(coro):
    """비동기 함수 실행 헬퍼"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Flask 라우트를 동기로 래핑
app.route('/api/upload', methods=['POST'])(lambda: run_async(upload()))
app.route('/api/stats')(lambda: run_async(stats()))
app.route('/api/search', methods=['POST'])(lambda: run_async(search()))
app.route('/api/cleanup', methods=['POST'])(lambda: run_async(cleanup()))

if __name__ == '__main__':
    # 핸들러 초기화
    upload_handler = AdminUploadHandler()
    image_analyzer = IntegratedImageAnalyzer()
    
    # 비동기 초기화
    run_async(upload_handler.initialize_modules())
    
    print("="*50)
    print("ex-GPT 관리도구 서버 시작")
    print("URL: http://localhost:5000")
    print("="*50)
    
    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000, debug=True)
