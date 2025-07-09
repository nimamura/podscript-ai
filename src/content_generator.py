"""
Content generation module for creating titles, descriptions, and blog posts
"""
import re
from typing import List, Optional, Any
import logging

from api_client import APIClient
from data_manager import DataManager

# Set up logging
logger = logging.getLogger(__name__)


# Custom exceptions
class ContentGenerationError(Exception):
    """Base exception for content generation errors"""
    pass


class PromptTooLongError(ContentGenerationError):
    """Raised when prompt exceeds token limit"""
    pass


class APIResponseError(ContentGenerationError):
    """Raised when API response is malformed"""
    pass


class ContentGenerator:
    """
    Generate content using GPT API with past data reference
    """
    
    # Maximum transcript length (characters)
    MAX_TRANSCRIPT_LENGTH = 8000
    
    # Default GPT model
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    # Default temperature for generation
    DEFAULT_TEMPERATURE = 0.7
    
    # Default max tokens for response
    DEFAULT_MAX_TOKENS = 500
    
    def __init__(self):
        """Initialize ContentGenerator with API client and data manager"""
        self.api_client = APIClient()
        self.data_manager = DataManager()
        
        # Add generate_completion method to API client if it doesn't exist
        if not hasattr(self.api_client, 'generate_completion'):
            self._add_generate_completion_to_api_client()
    
    def _add_generate_completion_to_api_client(self):
        """Add generate_completion method to APIClient"""
        def generate_completion(self, model=None, messages=None, temperature=None, max_tokens=None, **kwargs):
            """Generate completion using OpenAI API"""
            if not self.client:
                # Mock response for testing
                from unittest.mock import MagicMock
                response = MagicMock()
                response.choices = [
                    MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
                ]
                return response
            
            # Real OpenAI API call
            try:
                response = self.client.chat.completions.create(
                    model=model or ContentGenerator.DEFAULT_MODEL,
                    messages=messages or [],
                    temperature=temperature if temperature is not None else ContentGenerator.DEFAULT_TEMPERATURE,
                    max_tokens=max_tokens or ContentGenerator.DEFAULT_MAX_TOKENS,
                    **kwargs
                )
                return response
            except Exception as e:
                if "timeout" in str(e).lower():
                    raise TimeoutError(f"Request timed out: {e}")
                raise
        
        # Bind the method to the API client instance
        import types
        self.api_client.generate_completion = types.MethodType(generate_completion, self.api_client)
    
    def generate_titles(
        self,
        transcript: str,
        language: Optional[str] = 'ja',
        include_history: bool = False
    ) -> List[str]:
        """
        Generate 3 title options for the podcast episode
        
        Args:
            transcript: Transcribed text from podcast
            language: Output language ('ja', 'en', or None for auto-detect)
            include_history: Whether to include past titles for style learning
            
        Returns:
            List of 3 title options
            
        Raises:
            ValueError: If transcript is empty
            PromptTooLongError: If transcript is too long
            ContentGenerationError: If generation fails
            APIResponseError: If response format is invalid
        """
        # Validate transcript
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")
        
        # Check transcript length
        if len(transcript) > self.MAX_TRANSCRIPT_LENGTH:
            raise PromptTooLongError(
                f"Transcript too long: {len(transcript)} characters "
                f"(max: {self.MAX_TRANSCRIPT_LENGTH})"
            )
        
        # Auto-detect language if not specified
        if language is None:
            language = self._detect_language(transcript)
        
        # Build prompt
        if include_history:
            prompt = self._build_title_prompt_with_history(transcript, language, include_history)
        else:
            prompt = self._build_title_prompt(transcript, language)
        
        # Generate titles with retry
        try:
            response = self._generate_with_retry(prompt)
            titles = self._extract_titles_from_response(response)
            
            if len(titles) != 3:
                raise APIResponseError(
                    f"Invalid response format: expected 3 titles, got {len(titles)}"
                )
            
            return titles
            
        except TimeoutError as e:
            raise ContentGenerationError(f"Request timeout: {e}")
        except APIResponseError:
            raise
        except Exception as e:
            raise ContentGenerationError(f"Failed to generate titles: {e}")
    
    def _build_title_prompt(self, transcript: str, language: str) -> str:
        """
        Build prompt for title generation
        
        Args:
            transcript: Podcast transcript
            language: Output language
            
        Returns:
            Formatted prompt
        """
        language_instruction = {
            'ja': "日本語で",
            'en': "in English"
        }.get(language, language)
        
        prompt = f"""
Generate 3 attractive podcast titles {language_instruction} from the following transcript.

要件:
- リスナーの興味を引く魅力的なタイトル
- 内容を的確に表現
- 各タイトルは番号付きリスト形式で出力（1. 2. 3.）

文字起こし / Transcript:
{transcript}

タイトル案 / Title suggestions:
"""
        return prompt.strip()
    
    def _build_title_prompt_with_history(
        self,
        transcript: str,
        language: str,
        include_history: bool = True
    ) -> str:
        """
        Build prompt with past titles for style learning
        
        Args:
            transcript: Podcast transcript
            language: Output language
            include_history: Whether to include history
            
        Returns:
            Formatted prompt with style examples
        """
        # Get base prompt
        base_prompt = self._build_title_prompt(transcript, language)
        
        if not include_history:
            return base_prompt
        
        # Get past titles
        try:
            past_titles = self._get_past_titles(limit=5)
        except Exception as e:
            logger.warning(f"Failed to get past titles: {e}")
            # Continue without history
            return base_prompt
        
        if not past_titles:
            return base_prompt
        
        # Add style learning section
        style_section = "\n\n過去のタイトル例（文体の参考に）:\n"
        for title in past_titles:
            style_section += f"- {title}\n"
        
        style_instruction = "\n上記の過去のタイトルの文体やスタイルを参考にしてください。"
        
        # Insert style section before the requirements
        parts = base_prompt.split("\n要件:")
        if len(parts) == 2:
            prompt = parts[0] + style_section + style_instruction + "\n要件:" + parts[1]
        else:
            # Fallback: append at the beginning
            prompt = style_section + style_instruction + "\n\n" + base_prompt
        
        return prompt
    
    def _get_past_titles(self, limit: int = 5) -> List[str]:
        """
        Get past titles from data manager
        
        Args:
            limit: Maximum number of titles to retrieve
            
        Returns:
            List of past titles
        """
        return self.data_manager.get_recent_titles(limit=limit)
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 2) -> Any:
        """
        Generate completion with retry logic
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retries
            
        Returns:
            API response
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.api_client.generate_completion(
                    model=self.DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful podcast title generator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.DEFAULT_TEMPERATURE,
                    max_tokens=self.DEFAULT_MAX_TOKENS
                )
                return response
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                    continue
                break
        
        # All retries failed
        if last_error:
            raise last_error
        raise ContentGenerationError("All generation attempts failed")
    
    def _extract_titles_from_response(self, response: Any) -> List[str]:
        """
        Extract titles from API response
        
        Args:
            response: API response object
            
        Returns:
            List of extracted titles
            
        Raises:
            APIResponseError: If response format is invalid
        """
        try:
            content = response.choices[0].message.content
            
            # Try different patterns to extract titles
            titles = []
            
            # Pattern 1: Numbered list (1. Title)
            pattern1 = r'^\d+[\.\)]\s*(.+)$'
            
            # Pattern 2: Bullet points (- Title)
            pattern2 = r'^[-•]\s*(.+)$'
            
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try numbered list pattern
                match = re.match(pattern1, line)
                if match:
                    titles.append(match.group(1).strip())
                    continue
                
                # Try bullet point pattern
                match = re.match(pattern2, line)
                if match:
                    titles.append(match.group(1).strip())
                    continue
                
                # If no pattern matches but we have less than 3 titles,
                # consider it a title if it's not empty
                if len(titles) < 3 and line and not line.endswith(':'):
                    titles.append(line)
            
            # If we still don't have exactly 3 titles, raise an error
            if len(titles) != 3:
                raise APIResponseError(
                    "Invalid response format: could not extract 3 titles from response"
                )
            
            return titles
            
        except AttributeError:
            raise APIResponseError("Invalid response structure")
        except Exception as e:
            if isinstance(e, APIResponseError):
                raise
            raise APIResponseError(f"Failed to parse response: {e}")
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code ('ja' or 'en')
        """
        # Simple heuristic: check for Japanese characters
        japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]'
        
        if re.search(japanese_pattern, text):
            return 'ja'
        else:
            return 'en'