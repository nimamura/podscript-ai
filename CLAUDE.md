# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Podscript-AI is an AI-powered podcast content generation tool that:
- Processes audio files (podcast episodes) using OpenAI's Whisper API for transcription
- Generates titles, descriptions, and blog posts using GPT API
- Provides a user-friendly Gradio web interface
- Follows strict Test-Driven Development (TDD) methodology

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_audio_processor.py

# Run tests in watch mode
pytest-watch

# Run tests with verbose output
pytest -v
```

### Development Workflow
```bash
# Run the Gradio application
python src/app.py

# Run linting (when configured)
flake8 src/ tests/

# Format code (when configured)
black src/ tests/
```

## Architecture

### Module Structure
- **audio_processor.py**: Handles audio file validation and Whisper API integration
  - File format validation (MP3, WAV, M4A)
  - File size limit (1GB)
  - Duration limit (120 minutes)
  
- **text_processor.py**: Manages text file processing and preprocessing
  - TXT file reading with UTF-8 encoding
  - Text cleaning and character counting
  - Manuscript priority logic (skip audio if manuscript exists)

- **content_generator.py**: Generates content using GPT API
  - Title generation (3 variations)
  - Description generation (200-400 characters)
  - Blog post generation (1000-2000 characters, Markdown format)
  - Past content style learning

- **data_manager.py**: Handles data persistence
  - JSON file operations for history storage
  - Past content retrieval for style learning

- **api_client.py**: Manages OpenAI API communication
  - API key management from environment variables
  - Error handling and retry logic

- **app.py**: Gradio web interface
  - File upload (audio/text)
  - Language selection
  - Output type selection
  - Result display and editing

### Testing Strategy

This project strictly follows TDD principles:
1. Write failing tests first (Red phase)
2. Implement minimal code to pass tests (Green phase)
3. Refactor while keeping tests passing (Refactor phase)

Key testing practices:
- Use `pytest-mock` for mocking external API calls
- Maintain 90%+ test coverage
- Each module has corresponding test file in `tests/` directory
- Integration tests in `test_integration.py`

### API Configuration

Environment variables (store in `.env` file):
```
OPENAI_API_KEY=your_api_key_here
```

### Development Phases

The project follows a 9-week development plan with 8 phases:
1. **Phase 1**: Foundation (API client, data management)
2. **Phase 2**: Audio processing (validation, Whisper integration)
3. **Phase 3**: Text processing (manuscript handling)
4. **Phase 4**: Title generation
5. **Phase 5**: Description generation
6. **Phase 6**: Blog post generation
7. **Phase 7-8**: Gradio UI implementation
8. **Phase 9**: Integration testing and refactoring

### Important Notes

- Always write tests before implementation code
- Mock all external API calls in tests
- Ensure proper error handling for API failures
- Validate all user inputs (file size, format, duration)
- Maintain consistent code style across modules
- Use type hints for better code clarity
- Document complex logic with inline comments