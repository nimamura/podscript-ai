"""
Test audio processing functionality
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from audio_processor import (  # noqa: E402
    AudioProcessor,
    AudioProcessingError,
    InvalidFileFormatError,
    FileSizeError,
    DurationError
)


class TestAudioValidation:
    """Test audio file validation"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance with mocked API client"""
        mock_client = Mock()
        return AudioProcessor(api_client=mock_client)
    
    def test_valid_file_formats(self, audio_processor):
        """対応形式のファイルが受け入れられることを確認"""
        valid_formats = ['test.mp3', 'test.MP3', 'test.wav', 'test.WAV',
                         'test.m4a', 'test.M4A']
        
        for file_path in valid_formats:
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1000000):  # 1MB
                    result = audio_processor.validate_file(file_path)
                    assert result['valid'] is True
                    assert result['error'] is None
                    assert 'file_info' in result
    
    def test_invalid_file_format(self, audio_processor):
        """非対応形式が拒否されることを確認"""
        invalid_formats = ['test.txt', 'test.pdf', 'test.doc', 'test.jpg']
        
        for file_path in invalid_formats:
            with patch('os.path.exists', return_value=True):
                with pytest.raises(InvalidFileFormatError) as exc_info:
                    audio_processor.validate_file(file_path)
                assert "Unsupported file format" in str(exc_info.value)
    
    def test_file_size_under_limit(self, audio_processor):
        """1GB以下のファイルが受け入れられることを確認"""
        file_sizes = [
            1000,  # 1KB
            1000000,  # 1MB
            500000000,  # 500MB
            1073741824,  # Exactly 1GB
        ]
        
        for size in file_sizes:
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=size):
                    result = audio_processor.validate_file('test.mp3')
                    assert result['valid'] is True
                    assert result['file_info']['size'] == size
    
    def test_file_size_over_limit(self, audio_processor):
        """1GB超のファイルが拒否されることを確認"""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1073741825):  # 1GB + 1 byte
                with pytest.raises(FileSizeError) as exc_info:
                    audio_processor.validate_file('test.mp3')
                assert "File size exceeds limit" in str(exc_info.value)
    
    def test_file_not_found(self, audio_processor):
        """存在しないファイルのエラー処理"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                audio_processor.validate_file('non_existent.mp3')
            assert "File not found" in str(exc_info.value)
    
    def test_corrupted_file(self, audio_processor):
        """破損ファイルのエラー処理"""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', side_effect=OSError("File is corrupted")):
                with pytest.raises(AudioProcessingError) as exc_info:
                    audio_processor.validate_file('corrupted.mp3')
                assert "Error reading file" in str(exc_info.value)


class TestAudioDuration:
    """Test audio duration validation"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance"""
        mock_client = Mock()
        return AudioProcessor(api_client=mock_client)
    
    def test_duration_under_limit(self, audio_processor):
        """120分以下の音声が受け入れられることを確認"""
        durations = [60, 1800, 3600, 7200]  # 1min, 30min, 60min, 120min
        
        for duration in durations:
            mock_audio = Mock()
            mock_audio.info = Mock(length=duration)
            with patch('mutagen.File', return_value=mock_audio):
                actual_duration = audio_processor.get_audio_duration('test.mp3')
                assert actual_duration == duration
                assert audio_processor.validate_duration(actual_duration) is True
    
    def test_duration_over_limit(self, audio_processor):
        """120分超の音声が拒否されることを確認"""
        mock_audio = Mock()
        mock_audio.info = Mock(length=7201)  # 120min + 1sec
        with patch('mutagen.File', return_value=mock_audio):
            duration = audio_processor.get_audio_duration('test.mp3')
            assert audio_processor.validate_duration(duration) is False
    
    def test_duration_extraction_error(self, audio_processor):
        """長さ取得エラーの処理"""
        # Mutagen returns None for some files
        with patch('mutagen.File', return_value=None):
            with pytest.raises(AudioProcessingError) as exc_info:
                audio_processor.get_audio_duration('test.mp3')
            assert "Could not extract audio duration" in str(exc_info.value)
        
        # Mutagen raises exception
        with patch('mutagen.File', side_effect=Exception("Mutagen error")):
            with pytest.raises(AudioProcessingError) as exc_info:
                audio_processor.get_audio_duration('test.mp3')
            assert "Error extracting audio duration" in str(exc_info.value)


class TestWhisperIntegration:
    """Test Whisper API integration"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance with mocked API client"""
        mock_client = Mock()
        return AudioProcessor(api_client=mock_client)
    
    @pytest.fixture
    def mock_file_validation(self):
        """Mock file validation to pass"""
        with patch.object(AudioProcessor, 'validate_file') as mock:
            mock.return_value = {
                'valid': True,
                'error': None,
                'file_info': {'size': 1000000, 'format': 'mp3'}
            }
            yield mock
    
    @pytest.fixture
    def mock_duration_validation(self):
        """Mock duration validation to pass"""
        with patch.object(AudioProcessor, 'get_audio_duration', return_value=3600):  # 60 min
            with patch.object(AudioProcessor, 'validate_duration', return_value=True):
                yield
    
    def test_transcribe_audio_success(self, audio_processor, mock_file_validation,
                                      mock_duration_validation):
        """音声が正しく文字起こしされることを確認"""
        mock_response = Mock()
        mock_response.text = "これはテスト音声の内容です。"
        
        # Mock the API client's transcribe method
        audio_processor.api_client.client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            result = audio_processor.transcribe_audio('test.mp3')
            
        assert result == "これはテスト音声の内容です。"
        audio_processor.api_client.client.audio.transcriptions.create.assert_called_once()
    
    def test_transcribe_with_language(self, audio_processor, mock_file_validation,
                                      mock_duration_validation):
        """言語指定が正しく動作することを確認"""
        mock_response = Mock()
        mock_response.text = "This is test audio content."
        
        audio_processor.api_client.client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            result = audio_processor.transcribe_audio('test.mp3', language='en')
            
        # Check that language parameter was passed
        call_args = audio_processor.api_client.client.audio.transcriptions.create.call_args
        assert call_args[1]['language'] == 'en'
        assert result == "This is test audio content."
    
    def test_transcribe_api_error(self, audio_processor, mock_file_validation,
                                  mock_duration_validation):
        """APIエラーが適切に処理されることを確認"""
        # Mock API error
        audio_processor.api_client.client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            with pytest.raises(AudioProcessingError) as exc_info:
                audio_processor.transcribe_audio('test.mp3')
            assert "Transcription failed" in str(exc_info.value)
    
    def test_transcribe_timeout(self, audio_processor, mock_file_validation,
                                mock_duration_validation):
        """タイムアウト処理"""
        # Mock timeout error
        audio_processor.api_client.client.audio.transcriptions.create.side_effect = TimeoutError("Request timed out")
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            with pytest.raises(AudioProcessingError) as exc_info:
                audio_processor.transcribe_audio('test.mp3')
            assert "Request timed out" in str(exc_info.value)
    
    def test_transcribe_empty_audio(self, audio_processor, mock_file_validation,
                                    mock_duration_validation):
        """無音/空の音声ファイル処理"""
        mock_response = Mock()
        mock_response.text = ""  # Empty transcription
        
        audio_processor.api_client.client.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            result = audio_processor.transcribe_audio('test.mp3')
            
        assert result == ""
    
    def test_transcribe_retry_mechanism(self, audio_processor, mock_file_validation,
                                        mock_duration_validation):
        """リトライ機構の動作確認"""
        mock_response = Mock()
        mock_response.text = "Success after retry"
        
        # First call fails, second succeeds
        audio_processor.api_client.client.audio.transcriptions.create.side_effect = [
            Exception("Temporary error"),
            mock_response
        ]
        
        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = audio_processor.transcribe_audio('test.mp3')
                
        assert result == "Success after retry"
        assert audio_processor.api_client.client.audio.transcriptions.create.call_count == 2
    
    def test_transcribe_file_validation_fails(self, audio_processor):
        """ファイル検証失敗時の処理"""
        # Mock file validation to fail
        with patch.object(AudioProcessor, 'validate_file') as mock_validate:
            mock_validate.side_effect = InvalidFileFormatError("Invalid format")
            
            with pytest.raises(InvalidFileFormatError):
                audio_processor.transcribe_audio('test.txt')
    
    def test_transcribe_duration_validation_fails(self, audio_processor, mock_file_validation):
        """音声長さ検証失敗時の処理"""
        # Mock duration to exceed limit
        with patch.object(AudioProcessor, 'get_audio_duration', return_value=7500):  # 125 min
            with patch.object(AudioProcessor, 'validate_duration', return_value=False):
                with pytest.raises(DurationError) as exc_info:
                    audio_processor.transcribe_audio('test.mp3')
                assert "Audio duration exceeds limit" in str(exc_info.value)