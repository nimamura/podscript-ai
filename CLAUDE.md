# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Podscript-AI is an AI-powered podcast content generation tool that:
- Processes audio files (podcast episodes) using OpenAI's Whisper API for transcription
- Generates titles, descriptions, and blog posts using GPT API
- Provides a user-friendly Gradio web interface
- Follows strict Test-Driven Development (TDD) methodology
- **Status**: ✅ Fully implemented and tested (Phase 1-8 completed)
- **Quality**: 86% test coverage, 133 tests (131 passing, 98.5% success rate)

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

# Run integration tests specifically
pytest tests/test_integration.py -v

# Run linting
flake8 src/ tests/
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

**Implemented Testing:**
- **Total Tests**: 133 (131 passing, 98.5% success rate)
- **Test Coverage**: 86% overall
- **Test Categories**:
  - Unit tests (120 tests) for individual modules
  - Integration tests (13 tests) for end-to-end workflows
  - Error handling tests for API failures
  - Performance tests for large content processing
  - UI integration tests for Gradio interface

Key testing practices:
- Use `pytest-mock` for mocking external API calls
- Each module has corresponding test file in `tests/` directory
- Comprehensive integration tests in `test_integration.py`
- Mock-based testing to avoid actual API calls during testing

### API Configuration

Environment variables (store in `.env` file):
```
OPENAI_API_KEY=your_api_key_here
```

### Development Phases ✅ COMPLETED

The project followed an 8-week development plan:
1. **Phase 1**: ✅ Foundation (API client, data management) - 24 tests
2. **Phase 2**: ✅ Audio processing (validation, Whisper integration) - 17 tests
3. **Phase 3**: ✅ Text processing (manuscript handling) - 21 tests
4. **Phase 4**: ✅ Title generation - 18 tests
5. **Phase 5**: ✅ Description generation - 11 tests
6. **Phase 6**: ✅ Blog post generation - 12 tests
7. **Phase 7**: ✅ Gradio UI implementation - 17 tests
8. **Phase 8**: ✅ Integration testing and refactoring - 13 tests

**Development Completed**: All 8 phases successfully implemented with comprehensive testing

### Implementation Status

**✅ Completed Features:**
- Audio file processing (MP3, WAV, M4A) with validation
- Text file processing (TXT) with UTF-8 encoding
- OpenAI Whisper API integration for transcription
- GPT API integration for content generation
- Title generation (3 variations per episode)
- Description generation (200-400 characters)
- Blog post generation (1000-2000 characters, Markdown)
- Gradio web interface with file upload and real-time editing
- Comprehensive error handling and retry logic
- Data persistence with JSON-based history management
- Style learning from previous episodes

**🧪 Quality Assurance:**
- 133 comprehensive tests (98.5% success rate)
- 86% test coverage across all modules
- End-to-end integration testing
- Performance testing for large content
- Error handling validation
- UI integration testing

**📋 Development Guidelines:**
- Always write tests before implementation code
- Mock all external API calls in tests
- Ensure proper error handling for API failures
- Validate all user inputs (file size, format, duration)
- Maintain consistent code style across modules
- Use type hints for better code clarity
- Document complex logic with inline comments

### Running the Application

```bash
# Start the Gradio web interface
python src/app.py

# Access at: http://localhost:7860
```

### Future Development

The core application is complete. Potential enhancements:
- CI/CD pipeline setup (GitHub Actions)
- Production deployment configuration
- Additional output formats
- Multi-language support expansion
- Advanced style customization options