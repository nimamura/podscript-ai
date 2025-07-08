# Podscript-AI

AI-powered podcast content generation tool that automatically generates titles, descriptions, and blog posts from podcast audio files or transcripts.

## Features

- Audio transcription using OpenAI's Whisper API
- Automatic generation of:
  - Episode titles (3 variations)
  - Episode descriptions (200-400 characters)
  - Blog posts (1000-2000 characters in Markdown format)
- Support for multiple audio formats (MP3, WAV, M4A)
- Text file input support (TXT format)
- Style learning from previous episodes
- User-friendly Gradio web interface

## Requirements

- Python 3.8+
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/podscript-ai.git
cd podscript-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

Run the Gradio application:
```bash
python src/app.py
```

Then open your browser and navigate to the URL shown in the terminal (typically http://localhost:7860).

## Development

This project follows Test-Driven Development (TDD) methodology.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api_client.py
```

### Project Structure

```
podscript-ai/
├── src/                    # Source code
│   ├── api_client.py      # OpenAI API client
│   ├── audio_processor.py # Audio file processing
│   ├── text_processor.py  # Text file processing
│   ├── content_generator.py # Content generation
│   ├── data_manager.py    # Data persistence
│   └── app.py            # Gradio application
├── tests/                 # Test files
├── data/                  # Data storage
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## License

This project is licensed under the MIT License.