"""
Test API client functionality
"""
import os
import sys
from pathlib import Path

import pytest
from unittest.mock import patch

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from api_client import APIClient, APIKeyError, APIConnectionError  # noqa: E402


class TestAPIClient:
    """Test API Client functionality"""
    
    def setup_method(self):
        """Reset singleton before each test"""
        APIClient._instance = None
    
    def test_api_key_loading_from_env(self):
        """APIキーが環境変数から正しく読み込まれることを確認"""
        # Set test API key
        test_key = "test-api-key-123"
        with patch.dict(os.environ, {'OPENAI_API_KEY': test_key}):
            client = APIClient()
            assert client.api_key == test_key
    
    def test_api_key_missing_raises_error(self):
        """APIキーがない場合のエラーハンドリング"""
        # Remove API key from environment
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIKeyError) as exc_info:
                client = APIClient()
            assert "OPENAI_API_KEY not found" in str(exc_info.value)
    
    def test_api_key_validation(self):
        """無効なAPIキーの検証"""
        # Test empty API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with pytest.raises(APIKeyError) as exc_info:
                client = APIClient()
            assert "API key is empty" in str(exc_info.value)
        
        # Test whitespace-only API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': '   '}):
            with pytest.raises(APIKeyError) as exc_info:
                client = APIClient()
            assert "API key is empty" in str(exc_info.value)
    
    @patch('openai.OpenAI')
    def test_client_initialization(self, mock_openai):
        """OpenAIクライアントが正しく初期化されることを確認"""
        test_key = "test-api-key-123"
        with patch.dict(os.environ, {'OPENAI_API_KEY': test_key}):
            client = APIClient()
            mock_openai.assert_called_once_with(api_key=test_key)
    
    def test_connection_error_handling(self):
        """接続エラーのハンドリング"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client = APIClient()
            
            # Mock a connection error
            with patch.object(client, '_make_request') as mock_request:
                mock_request.side_effect = APIConnectionError("Connection failed")
                
                with pytest.raises(APIConnectionError) as exc_info:
                    client.test_connection()
                assert "Connection failed" in str(exc_info.value)
    
    def test_retry_mechanism(self):
        """リトライ機構のテスト（3回まで）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client = APIClient()
            
            # Mock a request that fails twice then succeeds
            with patch.object(client, '_make_request') as mock_request:
                mock_request.side_effect = [
                    APIConnectionError("Attempt 1 failed"),
                    APIConnectionError("Attempt 2 failed"),
                    {"status": "success"}
                ]
                
                result = client.make_request_with_retry("test_endpoint")
                assert result == {"status": "success"}
                assert mock_request.call_count == 3
    
    def test_retry_exhaustion(self):
        """リトライ回数を超えた場合のエラー"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client = APIClient()
            
            # Mock a request that always fails
            with patch.object(client, '_make_request') as mock_request:
                mock_request.side_effect = APIConnectionError("Connection failed")
                
                with pytest.raises(APIConnectionError) as exc_info:
                    client.make_request_with_retry("test_endpoint", max_retries=3)
                
                assert mock_request.call_count == 3
                assert "Connection failed" in str(exc_info.value)
    
    def test_timeout_handling(self):
        """タイムアウト処理（30秒）"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client = APIClient()
            
            # Mock a timeout
            with patch.object(client, '_make_request') as mock_request:
                # Create a timeout exception
                mock_request.side_effect = Exception("Request timed out")
                
                with pytest.raises(APIConnectionError) as exc_info:
                    client.make_request_with_retry("test_endpoint", timeout=30)
                assert "Request timed out" in str(exc_info.value)
    
    def test_rate_limit_handling(self):
        """レート制限エラーの処理"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client = APIClient()
            
            # Mock a rate limit error
            with patch.object(client, '_make_request') as mock_request:
                mock_request.side_effect = [
                    {"error": {"type": "rate_limit_error", "message": "Rate limit exceeded"}},
                    {"status": "success"}
                ]
                
                # Should retry with exponential backoff
                with patch('time.sleep'):  # Mock sleep to speed up test
                    result = client.make_request_with_retry("test_endpoint")
                    assert result == {"status": "success"}
    
    def test_singleton_pattern(self):
        """シングルトンパターンの動作確認"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            client1 = APIClient()
            client2 = APIClient()
            assert client1 is client2  # Same instance