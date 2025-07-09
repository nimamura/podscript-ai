"""
Text processing module for manuscript handling
"""
import os
import re
from pathlib import Path
from typing import Dict, Any


# Custom exceptions
class TextProcessingError(Exception):
    """Base exception for text processing errors"""
    pass


class EncodingError(TextProcessingError):
    """Raised when encoding issues occur"""
    pass


class FileFormatError(TextProcessingError):
    """Raised when file format is not supported"""
    pass


class TextProcessor:
    """Handle text file processing and preprocessing"""
    
    # Supported text formats
    SUPPORTED_FORMATS = {'.txt'}
    
    # Language detection patterns
    JAPANESE_PATTERN = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+')
    ENGLISH_PATTERN = re.compile(r'[a-zA-Z]+')
    
    # Average reading speed (characters per second)
    READING_SPEED_JA = 5  # Japanese characters per second
    READING_SPEED_EN = 3  # English words per second (approximate)
    
    def read_manuscript(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read manuscript from text file
        
        Args:
            file_path: Path to text file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            FileFormatError: If file format is not supported
            EncodingError: If encoding issues occur
            TextProcessingError: For other reading errors
        """
        path = Path(file_path)
        
        # Check file format
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise FileFormatError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Read file with specified encoding
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # Remove BOM if present
            if content.startswith('\ufeff'):
                content = content[1:]
                
            return content
            
        except FileNotFoundError:
            raise
        except UnicodeDecodeError as e:
            raise EncodingError(f"Encoding error: {e}")
        except PermissionError as e:
            raise TextProcessingError(f"Permission denied: {e}")
        except Exception as e:
            if isinstance(e, (FileFormatError, EncodingError, TextProcessingError)):
                raise
            raise TextProcessingError(f"Error reading file: {e}")
    
    def check_manuscript_exists(self, file_path: str) -> bool:
        """
        Check if manuscript file exists
        
        Args:
            file_path: Path to check
            
        Returns:
            True if manuscript exists, False otherwise
        """
        return os.path.exists(file_path)
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by normalizing whitespace and line endings
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return text
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Convert tabs to spaces
        text = text.replace('\t', ' ')
        
        # Normalize multiple newlines to double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Normalize full-width spaces to regular spaces
        text = text.replace('\u3000', ' ')
        
        # Normalize multiple spaces to single space
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
    def count_characters(self, text: str) -> int:
        """
        Count characters in text
        
        Args:
            text: Input text
            
        Returns:
            Character count
        """
        return len(text)
    
    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """
        Run complete preprocessing pipeline
        
        Args:
            text: Raw input text
            
        Returns:
            Dictionary with cleaned text and metadata
        """
        original_count = self.count_characters(text)
        cleaned_text = self.clean_text(text)
        cleaned_count = self.count_characters(cleaned_text)
        
        return {
            'cleaned_text': cleaned_text,
            'character_count': cleaned_count,
            'original_character_count': original_count
        }
    
    def remove_urls(self, text: str) -> str:
        """
        Remove URLs from text and replace with placeholder
        
        Args:
            text: Input text
            
        Returns:
            Text with URLs replaced
        """
        # Pattern to match URLs - exclude common Japanese characters
        url_pattern = re.compile(
            r'https?://[^\s<>"\{\}\|\\\^\[\]`\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'
        )
        
        return url_pattern.sub('[URL]', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize various types of whitespace
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace full-width spaces
        text = text.replace('\u3000', ' ')
        
        # Replace multiple spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Clean up spaces between newlines
        text = re.sub(r'\n[ \t]+\n', '\n\n', text)
        
        return text
    
    def validate_text(self, text: str) -> bool:
        """
        Validate if text has meaningful content
        
        Args:
            text: Input text
            
        Returns:
            True if valid, False otherwise
        """
        if not text:
            return False
        
        # Remove all whitespace to check if there's actual content
        stripped = text.strip()
        if not stripped:
            return False
        
        # Check if it's only whitespace characters
        if re.match(r'^[\s\n\r\t]+$', text):
            return False
        
        return True
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with metadata
        """
        character_count = self.count_characters(text)
        lines = text.split('\n')
        line_count = len(lines)
        
        # Count paragraphs (separated by empty lines)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Estimate reading time
        # Simple estimation based on character count
        estimated_reading_time = character_count / self.READING_SPEED_JA
        
        return {
            'character_count': character_count,
            'line_count': line_count,
            'paragraph_count': paragraph_count,
            'estimated_reading_time_seconds': int(estimated_reading_time)
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect primary language of text
        
        Args:
            text: Input text
            
        Returns:
            Language code ('ja', 'en', 'unknown')
        """
        if not text:
            return 'unknown'
        
        # Find all Japanese and English matches
        japanese_matches = self.JAPANESE_PATTERN.findall(text)
        english_matches = self.ENGLISH_PATTERN.findall(text)
        
        # Count total characters (not matches)
        japanese_chars = sum(len(match) for match in japanese_matches)
        english_chars = sum(len(match) for match in english_matches)
        
        # Determine primary language
        if japanese_chars == 0 and english_chars == 0:
            return 'unknown'
        
        # Give more weight to Japanese characters since they are more distinctive
        # and English words might appear in Japanese text
        if japanese_chars > 0:
            # If there's any significant Japanese content, consider it Japanese
            return 'ja'
        elif english_chars > 0:
            return 'en'
        else:
            return 'unknown'
    
    def process_manuscript_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete manuscript processing pipeline
        
        Args:
            file_path: Path to manuscript file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Read manuscript
            raw_content = self.read_manuscript(file_path)
            
            # Preprocess text
            preprocessed = self.preprocess_text(raw_content)
            cleaned_content = preprocessed['cleaned_text']
            
            # Remove URLs
            cleaned_content = self.remove_urls(cleaned_content)
            
            # Extract metadata
            metadata = self.extract_metadata(cleaned_content)
            
            # Detect language
            language = self.detect_language(cleaned_content)
            metadata['language'] = language
            
            return {
                'status': 'success',
                'content': cleaned_content,
                'metadata': metadata,
                'original_content': raw_content
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }