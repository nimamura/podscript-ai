"""
Test content generation functionality
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from content_generator import (  # noqa: E402
    ContentGenerator,
    ContentGenerationError,
    PromptTooLongError,
    APIResponseError
)


class TestTitleGeneration:
    """Test title generation functionality"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            return ContentGenerator()
    
    def test_generate_titles(self, content_generator, mocker):
        """タイトルが3つ生成されることを確認"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. AIの未来について考える\n2. テクノロジーが変える私たちの生活\n3. 人工知能との共存への道"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate titles
        transcript = "今日はAIについて話したいと思います。AIは私たちの生活を大きく変えています。"
        titles = content_generator.generate_titles(transcript, language='ja')
        
        # Assertions
        assert isinstance(titles, list)
        assert len(titles) == 3
        assert all(isinstance(title, str) for title in titles)
        assert all(title.strip() for title in titles)  # No empty titles
    
    def test_prompt_construction(self, content_generator):
        """プロンプトが正しく構築されることを確認"""
        transcript = "This is a test transcript about podcasting."
        language = 'en'
        
        prompt = content_generator._build_title_prompt(transcript, language)
        
        # Check prompt contains necessary elements
        assert isinstance(prompt, str)
        assert transcript in prompt
        assert "3" in prompt  # Should generate 3 titles
        assert "title" in prompt.lower()
        assert language in prompt or "English" in prompt
    
    def test_language_handling(self, content_generator, mocker):
        """出力言語が正しく反映されることを確認"""
        # Test Japanese
        mock_response_ja = MagicMock()
        mock_response_ja.choices = [
            MagicMock(message=MagicMock(content="1. 日本語タイトル1\n2. 日本語タイトル2\n3. 日本語タイトル3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_ja
        )
        
        titles_ja = content_generator.generate_titles("テスト", language='ja')
        assert all("日本語" in title for title in titles_ja)
        
        # Test English
        mock_response_en = MagicMock()
        mock_response_en.choices = [
            MagicMock(message=MagicMock(content="1. English Title 1\n2. English Title 2\n3. English Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_en
        )
        
        titles_en = content_generator.generate_titles("Test", language='en')
        assert all("English" in title for title in titles_en)
    
    def test_api_error_handling(self, content_generator, mocker):
        """APIエラーが適切に処理されることを確認"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "Failed to generate titles" in str(exc_info.value)
    
    def test_empty_transcript_handling(self, content_generator):
        """空の文字起こしテキストの処理"""
        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_titles("")
        
        assert "Transcript cannot be empty" in str(exc_info.value)
    
    def test_malformed_response_handling(self, content_generator, mocker):
        """不正なAPIレスポンスの処理"""
        # Response with no numbered list
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Just a single title without numbers"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        with pytest.raises(APIResponseError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "Invalid response format" in str(exc_info.value)
    
    def test_timeout_handling(self, content_generator, mocker):
        """タイムアウト処理の確認"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=TimeoutError("Request timed out")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "timeout" in str(exc_info.value).lower()
    
    def test_prompt_too_long(self, content_generator):
        """プロンプトが長すぎる場合の処理"""
        # Create a very long transcript (over 8000 characters)
        long_transcript = "これは非常に長いトランスクリプトです。" * 500
        
        with pytest.raises(PromptTooLongError) as exc_info:
            content_generator.generate_titles(long_transcript)
        
        assert "Transcript too long" in str(exc_info.value)
    
    def test_title_extraction_edge_cases(self, content_generator, mocker):
        """タイトル抽出のエッジケース"""
        # Test various formats
        test_cases = [
            # (response_content, expected_count)
            ("1. Title One\n2. Title Two\n3. Title Three", 3),
            ("1) Title One\n2) Title Two\n3) Title Three", 3),
            ("- Title One\n- Title Two\n- Title Three", 3),
            ("Title One\nTitle Two\nTitle Three", 3),  # No numbers
        ]
        
        for response_content, expected_count in test_cases:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content=response_content))
            ]
            
            mocker.patch.object(
                content_generator.api_client,
                'generate_completion',
                return_value=mock_response
            )
            
            titles = content_generator.generate_titles("Test")
            assert len(titles) == expected_count


class TestTitleWithHistory:
    """Test title generation with past data reference"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_load_past_titles(self, content_generator, mocker):
        """過去のタイトルが読み込まれることを確認"""
        # Mock past titles from DataManager
        mock_past_titles = [
            "AIの未来を語る - エピソード1",
            "機械学習入門 - エピソード2",
            "ディープラーニングの基礎 - エピソード3"
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        past_titles = content_generator._get_past_titles(limit=3)
        
        assert past_titles == mock_past_titles
        assert len(past_titles) == 3
    
    def test_style_learning_prompt(self, content_generator, mocker):
        """文体学習がプロンプトに含まれることを確認"""
        # Mock past titles
        mock_past_titles = [
            "【徹底解説】AIの基礎知識",
            "【初心者向け】プログラミング入門"
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        # Build prompt with style learning
        transcript = "今日はAIについて話します。"
        prompt = content_generator._build_title_prompt_with_history(
            transcript, language='ja', include_history=True
        )
        
        # Check that past titles are included in prompt
        assert "【徹底解説】" in prompt
        assert "【初心者向け】" in prompt
        assert "style" in prompt.lower() or "文体" in prompt
    
    def test_no_history_handling(self, content_generator, mocker):
        """履歴がない場合の処理"""
        # Mock empty history
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=[]
        )
        
        # Should work without history
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        titles = content_generator.generate_titles(
            "Test transcript", include_history=True
        )
        
        assert len(titles) == 3
    
    def test_history_limit(self, content_generator, mocker):
        """履歴の取得数制限が機能することを確認"""
        # Mock many past titles
        mock_past_titles = [f"Title {i}" for i in range(20)]
        
        # Mock get_recent_titles to respect the limit parameter
        def mock_get_recent_titles(limit=5):
            return mock_past_titles[:limit]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            side_effect=mock_get_recent_titles
        )
        
        # Get limited history
        past_titles = content_generator._get_past_titles(limit=5)
        
        assert len(past_titles) == 5
        assert past_titles == mock_past_titles[:5]
    
    def test_history_error_handling(self, content_generator, mocker):
        """履歴取得エラーの処理"""
        # Mock error in getting history
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            side_effect=Exception("Database error")
        )
        
        # Should continue without history
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Should not raise error, just proceed without history
        titles = content_generator.generate_titles(
            "Test transcript", include_history=True
        )
        
        assert len(titles) == 3


class TestContentGeneratorIntegration:
    """Integration tests for ContentGenerator"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_complete_title_generation_flow(self, content_generator, mocker):
        """完全なタイトル生成フローのテスト"""
        # Mock past titles
        mock_past_titles = ["過去のタイトル1", "過去のタイトル2"]
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. 新しいタイトル1\n2. 新しいタイトル2\n3. 新しいタイトル3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Full flow
        transcript = "これはテストのトランスクリプトです。"
        titles = content_generator.generate_titles(
            transcript,
            language='ja',
            include_history=True
        )
        
        # Verify
        assert len(titles) == 3
        assert all(isinstance(title, str) for title in titles)
        
        # Check API was called with proper prompt
        api_call_args = content_generator.api_client.generate_completion.call_args
        prompt = api_call_args[1]['messages'][1]['content']  # User message is at index 1
        assert transcript in prompt
        assert any(past_title in prompt for past_title in mock_past_titles)
    
    def test_language_auto_detection(self, content_generator, mocker):
        """言語自動検出との統合"""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Test with Japanese transcript (language not specified)
        titles = content_generator.generate_titles(
            "日本語のトランスクリプト",
            language=None  # Should auto-detect
        )
        
        assert len(titles) == 3
    
    def test_retry_mechanism_integration(self, content_generator, mocker):
        """リトライ機構の統合テスト"""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        # Should succeed on retry
        titles = content_generator.generate_titles("Test transcript")
        
        assert len(titles) == 3
        assert content_generator.api_client.generate_completion.call_count == 2
    
    def test_model_and_parameters(self, content_generator, mocker):
        """モデルとパラメータが正しく設定されることを確認"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        content_generator.generate_titles("Test transcript")
        
        # Check API call parameters
        api_call_args = content_generator.api_client.generate_completion.call_args
        assert api_call_args[1]['model'] in ['gpt-3.5-turbo', 'gpt-4']
        assert 'temperature' in api_call_args[1]
        assert 0 <= api_call_args[1]['temperature'] <= 1
        assert 'max_tokens' in api_call_args[1]