"""
멀티모달 백엔드 파일 관리 테스트
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from io import BytesIO

from app.main import app


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def sample_image():
    """샘플 이미지 파일"""
    # 간단한 1x1 PNG 이미지 바이트
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    return BytesIO(png_data)


@pytest.fixture
def sample_text_file():
    """샘플 텍스트 파일"""
    content = "This is a test file content."
    return BytesIO(content.encode('utf-8'))


class TestFileUpload:
    """파일 업로드 테스트"""
    
    def test_health_check(self, client):
        """헬스체크 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_cache_status(self, client):
        """캐시 상태 테스트"""
        response = client.get("/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "type" in data
        assert data["type"] == "memory"
    
    @patch("app.api.v1.files.get_cache_manager")
    @patch("app.api.v1.files.aiofiles.open")
    def test_upload_image_success(self, mock_aiofiles, mock_get_cache, client, sample_image):
        """이미지 업로드 성공 테스트"""
        # 캐시 매니저 모킹
        mock_cache = AsyncMock()
        mock_cache.set.return_value = True
        mock_get_cache.return_value = mock_cache
        
        # aiofiles 모킹
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        
        # 설정 모킹
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            mock_settings.ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg']
            mock_settings.UPLOAD_PATH = tempfile.mkdtemp()
            
            files = {"file": ("test.png", sample_image, "image/png")}
            data = {"description": "Test image upload"}
            
            response = client.post("/api/v1/files/upload", files=files, data=data)
            assert response.status_code == 200
            response_data = response.json()
            assert "file_id" in response_data
            assert response_data["filename"] == "test.png"
            assert response_data["content_type"] == "image/png"
    
    def test_upload_invalid_extension(self, client):
        """잘못된 확장자 업로드 테스트"""
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = ['.png', '.jpg']
            
            fake_file = BytesIO(b"fake content")
            files = {"file": ("test.exe", fake_file, "application/octet-stream")}
            
            response = client.post("/api/v1/files/upload", files=files)
            assert response.status_code == 400
            assert "지원하지 않는 파일 형식" in response.json()["detail"]
    
    def test_upload_file_too_large(self, client):
        """파일 크기 초과 테스트"""
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.MAX_FILE_SIZE = 100  # 100 bytes
            mock_settings.ALLOWED_EXTENSIONS = ['.txt']
            
            large_content = b"x" * 200  # 200 bytes
            fake_file = BytesIO(large_content)
            files = {"file": ("large.txt", fake_file, "text/plain")}
            
            response = client.post("/api/v1/files/upload", files=files)
            assert response.status_code == 413
            assert "파일 크기가 너무 큽니다" in response.json()["detail"]
    
    def test_upload_no_filename(self, client):
        """파일명이 없는 업로드 테스트"""
        fake_file = BytesIO(b"content")
        files = {"file": ("", fake_file, "text/plain")}
        
        response = client.post("/api/v1/files/upload", files=files)
        assert response.status_code == 400
        assert "파일명이 없습니다" in response.json()["detail"]


class TestFileRetrieval:
    """파일 조회 테스트"""
    
    @patch("app.api.v1.files.get_cache_manager")
    def test_get_file_info_success(self, mock_get_cache, client):
        """파일 정보 조회 성공 테스트"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {
            "file_id": "test-file-id",
            "filename": "test.png",
            "file_path": "/app/uploads/test.png",
            "file_size": 1024,
            "content_type": "image/png",
            "upload_time": "2024-01-01T00:00:00",
            "metadata": {"description": "Test file"}
        }
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/api/v1/files/info/test-file-id")
        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test-file-id"
        assert data["filename"] == "test.png"
    
    @patch("app.api.v1.files.get_cache_manager")
    def test_get_file_info_not_found(self, mock_get_cache, client):
        """파일 정보 조회 실패 테스트"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/api/v1/files/info/nonexistent-file-id")
        assert response.status_code == 404
        assert "파일을 찾을 수 없습니다" in response.json()["detail"]
    
    @patch("app.api.v1.files.get_cache_manager")
    @patch("app.api.v1.files.os.path.exists")
    def test_download_file_success(self, mock_exists, mock_get_cache, client):
        """파일 다운로드 성공 테스트"""
        # 파일 정보 모킹
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {
            "file_id": "test-file-id",
            "filename": "test.txt",
            "file_path": "/app/uploads/test.txt",
            "file_size": 100,
            "content_type": "text/plain",
            "upload_time": "2024-01-01T00:00:00",
            "metadata": {}
        }
        mock_get_cache.return_value = mock_cache
        
        # 파일 존재 모킹
        mock_exists.return_value = True
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(b"Test file content")
            temp_file_path = temp_file.name
        
        try:
            # 파일 경로 모킹
            mock_cache.get.return_value["file_path"] = temp_file_path
            
            response = client.get("/api/v1/files/download/test-file-id")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
        finally:
            # 임시 파일 삭제
            os.unlink(temp_file_path)
    
    @patch("app.api.v1.files.get_cache_manager")
    def test_download_file_not_found(self, mock_get_cache, client):
        """존재하지 않는 파일 다운로드 테스트"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/api/v1/files/download/nonexistent-file-id")
        assert response.status_code == 404


class TestFileManagement:
    """파일 관리 테스트"""
    
    @patch("app.api.v1.files.get_cache_manager")
    @patch("app.api.v1.files.os.path.exists")
    @patch("app.api.v1.files.os.remove")
    def test_delete_file_success(self, mock_remove, mock_exists, mock_get_cache, client):
        """파일 삭제 성공 테스트"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {
            "file_id": "test-file-id",
            "filename": "test.txt",
            "file_path": "/app/uploads/test.txt",
            "file_size": 100,
            "content_type": "text/plain",
            "upload_time": "2024-01-01T00:00:00",
            "metadata": {}
        }
        mock_cache.delete.return_value = True
        mock_get_cache.return_value = mock_cache
        
        mock_exists.return_value = True
        mock_remove.return_value = None
        
        response = client.delete("/api/v1/files/delete/test-file-id")
        assert response.status_code == 200
        data = response.json()
        assert "성공적으로 삭제되었습니다" in data["message"]
        assert data["file_id"] == "test-file-id"
    
    @patch("app.api.v1.files.get_cache_manager")
    def test_delete_file_not_found(self, mock_get_cache, client):
        """존재하지 않는 파일 삭제 테스트"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_get_cache.return_value = mock_cache
        
        response = client.delete("/api/v1/files/delete/nonexistent-file-id")
        assert response.status_code == 404
    
    @patch("app.api.v1.files.get_cache_manager")
    def test_list_files(self, mock_get_cache, client):
        """파일 목록 조회 테스트"""
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        
        response = client.get("/api/v1/files/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch("app.api.v1.files.settings")
    @patch("app.api.v1.files.os.path.exists")
    @patch("app.api.v1.files.os.walk")
    @patch("app.api.v1.files.get_cache_manager")
    def test_get_upload_stats(self, mock_get_cache, mock_walk, mock_exists, mock_settings, client):
        """업로드 통계 조회 테스트"""
        # 설정 모킹
        mock_settings.UPLOAD_PATH = "/app/uploads"
        mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024
        mock_settings.ALLOWED_EXTENSIONS = ['.png', '.jpg', '.txt']
        
        # 디렉토리 존재 모킹
        mock_exists.return_value = True
        
        # 파일 시스템 모킹
        mock_walk.return_value = [
            ("/app/uploads", [], ["file1.txt", "file2.png"])
        ]
        
        # 캐시 통계 모킹
        mock_cache = AsyncMock()
        mock_cache.get_stats.return_value = {
            "hits": 100,
            "misses": 20,
            "hit_rate": 0.83
        }
        mock_get_cache.return_value = mock_cache
        
        # 파일 크기 모킹
        with patch("app.api.v1.files.os.path.getsize") as mock_getsize:
            mock_getsize.return_value = 1024  # 1KB per file
            
            response = client.get("/api/v1/files/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_files" in data
            assert "total_size_bytes" in data
            assert "cache_stats" in data
            assert data["total_files"] == 2
            assert data["total_size_bytes"] == 2048  # 2 files * 1KB


class TestFileValidation:
    """파일 검증 테스트"""
    
    def test_validate_file_extension_valid(self):
        """유효한 파일 확장자 검증 테스트"""
        from app.api.v1.files import validate_file_extension
        
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = ['.png', '.jpg', '.txt']
            
            assert validate_file_extension("test.png") is True
            assert validate_file_extension("test.JPG") is True  # 대소문자 무관
            assert validate_file_extension("test.txt") is True
    
    def test_validate_file_extension_invalid(self):
        """유효하지 않은 파일 확장자 검증 테스트"""
        from app.api.v1.files import validate_file_extension
        
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = ['.png', '.jpg', '.txt']
            
            assert validate_file_extension("test.exe") is False
            assert validate_file_extension("test.pdf") is False
            assert validate_file_extension("test") is False  # 확장자 없음
    
    def test_get_file_path(self):
        """파일 경로 생성 테스트"""
        from app.api.v1.files import get_file_path
        
        with patch("app.api.v1.files.settings") as mock_settings:
            mock_settings.UPLOAD_PATH = "/app/uploads"
            
            with patch("app.api.v1.files.os.makedirs") as mock_makedirs:
                file_path = get_file_path("test-id", "test.png")
                
                # 경로가 올바르게 생성되는지 확인
                assert "/app/uploads/" in file_path
                assert "test-id.png" in file_path
                
                # 디렉토리 생성이 호출되는지 확인
                mock_makedirs.assert_called_once()


@pytest.mark.asyncio
class TestAsyncFunctions:
    """비동기 함수 테스트"""
    
    async def test_cache_file_operations(self):
        """캐시 파일 작업 테스트"""
        from app.services.cache_service import get_cache_manager
        
        cache_manager = get_cache_manager()
        
        # 파일 정보 캐시 저장
        file_info = {
            "file_id": "test-file-id",
            "filename": "test.txt",
            "file_path": "/app/uploads/test.txt",
            "file_size": 100,
            "content_type": "text/plain"
        }
        
        result = await cache_manager.set("file_info:test-file-id", file_info)
        assert result is True
        
        # 파일 정보 조회
        cached_info = await cache_manager.get("file_info:test-file-id")
        assert cached_info == file_info
        
        # 파일 정보 삭제
        result = await cache_manager.delete("file_info:test-file-id")
        assert result is True
        
        # 삭제 확인
        cached_info = await cache_manager.get("file_info:test-file-id")
        assert cached_info is None
