"""
Audio processing module for podcast transcription
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import mutagen
from dotenv import load_dotenv

from api_client import APIClient

# Load environment variables
load_dotenv()


# Custom exceptions
class AudioProcessingError(Exception):
    """Base exception for audio processing errors"""
    pass


class InvalidFileFormatError(AudioProcessingError):
    """Raised when file format is not supported"""
    pass


class FileSizeError(AudioProcessingError):
    """Raised when file size exceeds limit"""
    pass


class DurationError(AudioProcessingError):
    """Raised when audio duration exceeds limit"""
    pass


class AudioProcessor:
    """Handle audio file validation and transcription"""
    
    # Supported audio formats
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a'}
    
    # Default limits (can be overridden by environment variables)
    DEFAULT_MAX_FILE_SIZE = 1073741824  # 1GB in bytes
    DEFAULT_MAX_DURATION = 7200  # 120 minutes in seconds
    
    def __init__(self, api_client: Optional[APIClient] = None):
        """
        Initialize AudioProcessor
        
        Args:
            api_client: Optional APIClient instance for testing
        """
        self.api_client = api_client or APIClient()
        
        # Load configuration from environment
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', self.DEFAULT_MAX_FILE_SIZE))
        # MAX_AUDIO_DURATION is in minutes, convert to seconds
        max_duration_minutes = int(os.getenv('MAX_AUDIO_DURATION',
                                             self.DEFAULT_MAX_DURATION // 60))
        self.max_duration = max_duration_minutes * 60
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with validation results
            
        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidFileFormatError: If file format is not supported
            FileSizeError: If file size exceeds limit
            AudioProcessingError: For other validation errors
        """
        path = Path(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file format
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise InvalidFileFormatError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Check file size
        try:
            file_size = os.path.getsize(file_path)
        except OSError as e:
            raise AudioProcessingError(f"Error reading file: {e}")
        
        if file_size > self.max_file_size:
            raise FileSizeError(
                f"File size exceeds limit. "
                f"Size: {file_size / 1024 / 1024:.1f}MB, "
                f"Limit: {self.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        return {
            'valid': True,
            'error': None,
            'file_info': {
                'size': file_size,
                'format': path.suffix.lower()[1:]  # Remove leading dot
            }
        }
    
    def get_audio_duration(self, file_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Duration in seconds
            
        Raises:
            AudioProcessingError: If duration cannot be extracted
        """
        try:
            audio = mutagen.File(file_path)
            
            if audio is None:
                raise AudioProcessingError(
                    f"Could not extract audio duration from {file_path}"
                )
            
            if hasattr(audio.info, 'length'):
                return float(audio.info.length)
            else:
                raise AudioProcessingError(
                    f"Could not extract audio duration from {file_path}"
                )
                
        except Exception as e:
            raise AudioProcessingError(f"Error extracting audio duration: {e}")
    
    def validate_duration(self, duration: float) -> bool:
        """
        Check if audio duration is within limit
        
        Args:
            duration: Duration in seconds
            
        Returns:
            True if duration is within limit, False otherwise
        """
        return duration <= self.max_duration
    
    def transcribe(self, file_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file using Whisper API
        
        Args:
            file_path: Path to audio file
            language: Optional language code (e.g., 'ja', 'en')
            
        Returns:
            Transcribed text
            
        Raises:
            Various exceptions for validation and API errors
        """
        # Validate file
        self.validate_file(file_path)
        
        # Check duration
        duration = self.get_audio_duration(file_path)
        if not self.validate_duration(duration):
            raise DurationError(
                f"Audio duration exceeds limit. "
                f"Duration: {duration / 60:.1f} minutes, "
                f"Limit: {self.max_duration / 60} minutes"
            )
        
        # Transcribe with retry mechanism
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                with open(file_path, 'rb') as audio_file:
                    # Prepare API parameters
                    params = {
                        'model': 'whisper-1',
                        'file': audio_file,
                        'response_format': 'json'
                    }
                    
                    # Add language if specified
                    if language:
                        params['language'] = language
                    
                    # Call Whisper API
                    response = self.api_client.audio.transcriptions.create(**params)
                    
                    return response.text
                    
            except TimeoutError as e:
                raise AudioProcessingError(f"Request timed out: {e}")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Retry with exponential backoff
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    # Final attempt failed
                    raise AudioProcessingError(f"Transcription failed: {e}")