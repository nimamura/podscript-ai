"""
Test text processing functionality
"""
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from text_processor import (  # noqa: E402
    TextProcessor,
    TextProcessingError,
    EncodingError,
    FileFormatError
)


class TestManuscriptProcessing:
    """Test manuscript file processing"""
    
    @pytest.fixture
    def text_processor(self):
        """Create TextProcessor instance"""
        return TextProcessor()
    
    def test_read_txt_file(self, text_processor):
        """TXTファイルが正しく読み込まれることを確認"""
        mock_content = "これはテストの原稿です。\nポッドキャストの内容について話しています。"
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_content)):
                result = text_processor.read_manuscript('test.txt')
            
        assert result == mock_content
        assert isinstance(result, str)
    
    def test_encoding_handling(self, text_processor):
        """UTF-8エンコーディングが正しく処理されることを確認"""
        # UTF-8 with BOM - test with string (mock_open handles it as string)
        mock_content_with_bom = "\ufeffテスト原稿"
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_content_with_bom)):
                result = text_processor.read_manuscript('test.txt')
                assert result == "テスト原稿"
        
        # Test invalid encoding - mock a UnicodeDecodeError
        with patch('os.path.exists', return_value=True):
            mock_file = mock_open()
            mock_file.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            with patch('builtins.open', mock_file):
                with pytest.raises(EncodingError) as exc_info:
                    text_processor.read_manuscript('test.txt')
                assert "Encoding error" in str(exc_info.value)
    
    def test_manuscript_priority(self, text_processor):
        """原稿がある場合、音声処理をスキップすることを確認"""
        # This method returns True if manuscript should be used instead of audio
        mock_content = "原稿内容"
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('os.path.exists', return_value=True):
                has_manuscript = text_processor.check_manuscript_exists('test.txt')
                assert has_manuscript is True
        
        # No manuscript file
        with patch('os.path.exists', return_value=False):
            has_manuscript = text_processor.check_manuscript_exists('test.txt')
            assert has_manuscript is False
    
    def test_invalid_file_format(self, text_processor):
        """非対応形式のファイルが拒否されることを確認"""
        invalid_files = ['test.pdf', 'test.doc', 'test.docx', 'test.rtf']
        
        for file_path in invalid_files:
            with pytest.raises(FileFormatError) as exc_info:
                text_processor.read_manuscript(file_path)
            assert "Unsupported file format" in str(exc_info.value)
    
    def test_file_not_found(self, text_processor):
        """存在しないファイルのエラー処理"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                text_processor.read_manuscript('non_existent.txt')
            assert "File not found" in str(exc_info.value)
    
    def test_empty_file(self, text_processor):
        """空のファイルの処理"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="")):
                result = text_processor.read_manuscript('empty.txt')
                assert result == ""
    
    def test_large_file_handling(self, text_processor):
        """大きなファイルの処理"""
        # 10MB of text (should be handled)
        large_content = "あ" * (10 * 1024 * 1024)
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=large_content)):
                result = text_processor.read_manuscript('large.txt')
                assert len(result) == len(large_content)
    
    def test_read_permission_error(self, text_processor):
        """読み取り権限がない場合のエラー処理"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(TextProcessingError) as exc_info:
                    text_processor.read_manuscript('protected.txt')
                assert "Permission denied" in str(exc_info.value)


class TestTextPreprocessing:
    """Test text preprocessing functionality"""
    
    @pytest.fixture
    def text_processor(self):
        """Create TextProcessor instance"""
        return TextProcessor()
    
    def test_text_cleaning(self, text_processor):
        """テキストが適切にクリーニングされることを確認"""
        # Test cases for cleaning
        test_cases = [
            # (input, expected)
            ("  テスト  ", "テスト"),  # Leading/trailing spaces
            ("テスト\n\n\n文章", "テスト\n\n文章"),  # Multiple newlines to double
            ("テスト\r\n文章", "テスト\n文章"),  # Windows line endings
            ("テスト\t文章", "テスト 文章"),  # Tab to space
            ("テスト　　文章", "テスト 文章"),  # Full-width spaces
            ("", ""),  # Empty string
        ]
        
        for input_text, expected in test_cases:
            result = text_processor.clean_text(input_text)
            assert result == expected
    
    def test_character_count(self, text_processor):
        """文字数が正しくカウントされることを確認"""
        test_cases = [
            ("Hello", 5),
            ("こんにちは", 5),
            ("Hello World", 11),
            ("こんにちは、世界", 8),
            ("", 0),
            ("  ", 2),  # Spaces count
            ("😀😃", 2),  # Emoji count
            ("テスト\n改行", 6),  # Newline counts as 1
        ]
        
        for text, expected_count in test_cases:
            count = text_processor.count_characters(text)
            assert count == expected_count
    
    def test_text_preprocessing_pipeline(self, text_processor):
        """前処理パイプライン全体の動作確認"""
        raw_text = "  これは\n\n\nテストの\r\n原稿です。　　たくさんの　空白があります。  "
        
        result = text_processor.preprocess_text(raw_text)
        
        assert result['cleaned_text'] == "これは\n\nテストの\n原稿です。 たくさんの 空白があります。"
        assert result['character_count'] == 30  # Actual count after cleaning
        assert 'original_character_count' in result
        assert result['original_character_count'] == len(raw_text)
    
    def test_remove_urls(self, text_processor):
        """URLの除去が正しく動作することを確認"""
        test_cases = [
            ("詳細はhttps://example.comをご覧ください", "詳細は[URL]をご覧ください"),
            ("http://test.comとhttps://test.jp", "[URL]と[URL]"),
            ("URLなしのテキスト", "URLなしのテキスト"),
        ]
        
        for input_text, expected in test_cases:
            result = text_processor.remove_urls(input_text)
            assert result == expected
    
    def test_normalize_whitespace(self, text_processor):
        """空白の正規化が正しく動作することを確認"""
        test_cases = [
            ("テスト   文章", "テスト 文章"),  # Multiple spaces
            ("テスト\u3000\u3000文章", "テスト 文章"),  # Full-width spaces
            ("テスト\t\t文章", "テスト 文章"),  # Multiple tabs
            ("テスト\n \n文章", "テスト\n\n文章"),  # Space between newlines
        ]
        
        for input_text, expected in test_cases:
            result = text_processor.normalize_whitespace(input_text)
            assert result == expected
    
    def test_text_validation(self, text_processor):
        """テキストの検証機能"""
        # Valid text
        valid_text = "これは有効なテキストです。"
        assert text_processor.validate_text(valid_text) is True
        
        # Invalid cases
        assert text_processor.validate_text("") is False  # Empty
        assert text_processor.validate_text("   ") is False  # Only spaces
        assert text_processor.validate_text("\n\n\n") is False  # Only newlines
    
    def test_extract_metadata(self, text_processor):
        """テキストからメタデータを抽出"""
        text = "これはテストです。\n段落が複数あります。\n\n別の段落です。"
        
        metadata = text_processor.extract_metadata(text)
        
        assert metadata['character_count'] == 29  # Corrected count
        assert metadata['line_count'] == 4  # Including empty line
        assert metadata['paragraph_count'] == 2  # Two paragraphs separated by empty line
        assert 'estimated_reading_time_seconds' in metadata
        assert metadata['estimated_reading_time_seconds'] > 0


class TestLanguageDetection:
    """Test optional language detection functionality"""
    
    @pytest.fixture
    def text_processor(self):
        """Create TextProcessor instance"""
        return TextProcessor()
    
    def test_detect_japanese(self, text_processor):
        """日本語の検出"""
        japanese_texts = [
            "これは日本語のテキストです。",
            "ひらがなとカタカナが混ざっています。",
            "漢字も含まれています。",
        ]
        
        for text in japanese_texts:
            language = text_processor.detect_language(text)
            assert language == 'ja'
    
    def test_detect_english(self, text_processor):
        """英語の検出"""
        english_texts = [
            "This is English text.",
            "Hello World!",
            "Testing language detection.",
        ]
        
        for text in english_texts:
            language = text_processor.detect_language(text)
            assert language == 'en'
    
    def test_detect_mixed_language(self, text_processor):
        """混合言語の検出（日本語優先）"""
        # Mixed with Japanese - should return 'ja'
        text1 = "これは日本語です。This is English. でも主に日本語。"
        assert text_processor.detect_language(text1) == 'ja'
        
        # Even small Japanese content returns 'ja'
        text2 = "This is mostly English text. ちょっと日本語。 But mainly English."
        assert text_processor.detect_language(text2) == 'ja'
        
        # Pure English returns 'en'
        text3 = "This is purely English text with no Japanese characters."
        assert text_processor.detect_language(text3) == 'en'
    
    def test_detect_unknown_language(self, text_processor):
        """未知の言語や判定不能な場合"""
        # Numbers and symbols only
        assert text_processor.detect_language("123456789") == 'unknown'
        assert text_processor.detect_language("!!!???") == 'unknown'
        assert text_processor.detect_language("") == 'unknown'


class TestTextProcessorIntegration:
    """Integration tests for TextProcessor"""
    
    @pytest.fixture
    def text_processor(self):
        """Create TextProcessor instance"""
        return TextProcessor()
    
    def test_process_manuscript_file(self, text_processor):
        """原稿ファイルの完全な処理フロー"""
        mock_content = """
        これはポッドキャストの原稿です。
        
        今日のテーマは「AIの活用」についてです。
        詳細はhttps://example.comをご覧ください。
        
        それでは、始めましょう。
        """
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('os.path.exists', return_value=True):
                result = text_processor.process_manuscript_file('episode1.txt')
                
                assert result['status'] == 'success'
                assert 'content' in result
                assert 'metadata' in result
                assert result['metadata']['language'] == 'ja'
                assert result['metadata']['character_count'] > 0
                assert '[URL]' in result['content']  # URL should be replaced
    
    def test_process_with_encoding_options(self, text_processor):
        """異なるエンコーディングオプションでの処理"""
        # Test with UTF-8
        mock_content = "テストコンテンツ"
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_content)):
                result = text_processor.read_manuscript('test.txt', encoding='utf-8')
                assert result == mock_content
        
        # Test with UTF-8 BOM
        mock_content_bom = "\ufeffテストコンテンツ"
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_content_bom)):
                result = text_processor.read_manuscript('test.txt', encoding='utf-8-sig')
                assert result == "テストコンテンツ"  # BOM should be removed