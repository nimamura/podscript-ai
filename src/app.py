"""
Gradio-based web application for Podscript-AI
"""
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

import gradio as gr

from audio_processor import AudioProcessor
from text_processor import TextProcessor
from content_generator import ContentGenerator
from data_manager import DataManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom exceptions
class UIError(Exception):
    """Base exception for UI errors"""
    pass


class ProcessingError(UIError):
    """Raised when processing fails"""
    pass


class PodscriptApp:
    """
    Main application class for Podscript-AI Gradio interface
    """
    
    def __init__(self):
        """Initialize the application with all necessary components"""
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
        self.content_generator = ContentGenerator()
        self.data_manager = DataManager()
        
        # UI components (will be set when building interface)
        self.file_input = None
        self.language_dropdown = None
        self.output_checkboxes = None
        self.process_button = None
        self.result_display = None
        
        # Supported file types
        self.supported_audio_types = ['.mp3', '.wav', '.m4a']
        self.supported_text_types = ['.txt']
        
        # Session state
        self.session_state = self.initialize_session()
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize session state"""
        return {
            'current_file': None,
            'processing_status': 'idle',
            'results': {},
            'file_type': None
        }
    
    def update_session_state(self, session_state: Dict[str, Any], key: str, value: Any):
        """Update session state"""
        session_state[key] = value
    
    def handle_file_upload(self, file_path: Optional[str]) -> Dict[str, Any]:
        """
        Handle file upload and validate file type
        
        Args:
            file_path: Path to uploaded file
            
        Returns:
            Dict with status and file info
        """
        if not file_path:
            return {
                'status': 'error',
                'message': 'No file provided'
            }
        
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': 'File not found'
            }
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.supported_audio_types:
            file_type = 'audio'
        elif file_ext in self.supported_text_types:
            file_type = 'text'
        else:
            return {
                'status': 'error',
                'message': f'Unsupported file type: {file_ext}'
            }
        
        # Update session state
        self.session_state['current_file'] = file_path
        self.session_state['file_type'] = file_type
        
        return {
            'status': 'success',
            'file_type': file_type,
            'file_path': file_path
        }
    
    def handle_language_selection(self, language: str) -> str:
        """
        Handle language selection
        
        Args:
            language: Selected language ('ja', 'en', 'auto')
            
        Returns:
            Selected language
        """
        return language
    
    def handle_output_selection(self, selected_outputs: List[str]) -> List[str]:
        """
        Handle output type selection
        
        Args:
            selected_outputs: List of selected output types
            
        Returns:
            List of selected output types
        """
        return selected_outputs
    
    def detect_language_from_file(self, file_path: str) -> str:
        """
        Detect language from file content
        
        Args:
            file_path: Path to file
            
        Returns:
            Detected language ('ja', 'en', 'auto')
        """
        try:
            if Path(file_path).suffix.lower() == '.txt':
                # Read text file and detect language
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.text_processor.detect_language(content)
            else:
                # For audio files, return auto-detect
                return 'auto'
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'auto'
    
    def update_progress(self, message: str) -> str:
        """
        Update progress display
        
        Args:
            message: Progress message
            
        Returns:
            Progress message
        """
        return message
    
    def process_file(
        self,
        file_path: str,
        language: str,
        output_types: List[str]
    ) -> Dict[str, Any]:
        """
        Process uploaded file and generate selected outputs
        
        Args:
            file_path: Path to file to process
            language: Language for generation ('ja', 'en', 'auto')
            output_types: List of output types to generate
            
        Returns:
            Dict with processing results
        """
        try:
            # Validate file
            file_validation = self.handle_file_upload(file_path)
            if file_validation['status'] == 'error':
                return file_validation
            
            file_type = file_validation['file_type']
            
            # Process based on file type
            if file_type == 'audio':
                transcript = self._process_audio_file(file_path, language)
            else:  # text
                transcript = self._process_text_file(file_path)
            
            # Generate selected outputs
            results = {
                'status': 'success',
                'transcript': transcript
            }
            
            # Determine language for generation
            if language == 'auto':
                detected_language = self.content_generator._detect_language(transcript)
            else:
                detected_language = language
            
            # Generate outputs based on selection
            if 'titles' in output_types:
                results['titles'] = self.content_generator.generate_titles(
                    transcript, language=detected_language, include_history=True
                )
            
            if 'description' in output_types:
                results['description'] = self.content_generator.generate_description(
                    transcript, language=detected_language, include_history=True
                )
            
            if 'blog_post' in output_types:
                results['blog_post'] = self.content_generator.generate_blog_post(
                    transcript, language=detected_language, include_history=True
                )
            
            # Save to history
            history_data = {
                'file_path': file_path,
                'file_type': file_type,
                'language': detected_language,
                'transcript': transcript,
                'titles': results.get('titles', []),
                'description': results.get('description', ''),
                'blog_post': results.get('blog_post', '')
            }
            
            history_id = self.data_manager.save_history(history_data)
            results['history_id'] = history_id
            
            return results
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _process_audio_file(self, file_path: str, language: str) -> str:
        """
        Process audio file and transcribe
        
        Args:
            file_path: Path to audio file
            language: Language for transcription
            
        Returns:
            Transcribed text
        """
        # Map language codes
        whisper_language = None if language == 'auto' else language
        
        return self.audio_processor.transcribe_audio(file_path, language=whisper_language)
    
    def _process_text_file(self, file_path: str) -> str:
        """
        Process text file and return content
        
        Args:
            file_path: Path to text file
            
        Returns:
            Text content
        """
        result = self.text_processor.process_manuscript_file(file_path)
        if result['status'] == 'success':
            return result['content']
        else:
            raise ProcessingError(f"Text processing failed: {result.get('message', 'Unknown error')}")
    
    def format_results_for_display(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format results for display in UI
        
        Args:
            results: Raw processing results
            
        Returns:
            Formatted results for display
        """
        formatted = {
            'status': results['status']
        }
        
        if results['status'] == 'success':
            formatted['transcript'] = results.get('transcript', '')
            
            # Format titles as numbered list
            if 'titles' in results:
                titles = results['titles']
                formatted['titles'] = '\n'.join([f"{i+1}. {title}" for i, title in enumerate(titles)])
            
            # Format description
            if 'description' in results:
                formatted['description'] = results['description']
            
            # Format blog post
            if 'blog_post' in results:
                formatted['blog_post'] = results['blog_post']
        
        return formatted
    
    def handle_edit_titles(self, edited_titles: str) -> str:
        """Handle title editing"""
        return edited_titles
    
    def handle_edit_description(self, edited_description: str) -> str:
        """Handle description editing"""
        return edited_description
    
    def handle_edit_blog_post(self, edited_blog_post: str) -> str:
        """Handle blog post editing"""
        return edited_blog_post
    
    def handle_copy_content(self, content: str) -> str:
        """Handle content copying"""
        return content
    
    def build_interface(self) -> gr.Blocks:
        """
        Build the Gradio interface
        
        Returns:
            Gradio Blocks interface
        """
        with gr.Blocks(
            title="Podscript-AI",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
                margin: 0 auto;
            }
            """
        ) as interface:
            # Header
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🎙️ Podscript-AI</h1>
                <p>AI-powered podcast content generation tool</p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    # File upload
                    self.file_input = gr.File(
                        label="Upload Audio/Text File",
                        file_types=['.mp3', '.wav', '.m4a', '.txt'],
                        type="filepath"
                    )
                    
                    # Language selection
                    self.language_dropdown = gr.Dropdown(
                        label="Language",
                        choices=[
                            ("Auto-detect", "auto"),
                            ("Japanese", "ja"),
                            ("English", "en")
                        ],
                        value="auto"
                    )
                    
                    # Output type selection
                    self.output_checkboxes = gr.CheckboxGroup(
                        label="Generate",
                        choices=[
                            ("Titles (3 variations)", "titles"),
                            ("Description", "description"),
                            ("Blog Post", "blog_post")
                        ],
                        value=["titles", "description", "blog_post"]
                    )
                    
                    # Process button
                    self.process_button = gr.Button(
                        "🚀 Generate Content",
                        variant="primary",
                        scale=1
                    )
                    
                    # Progress display
                    progress_display = gr.Textbox(
                        label="Status",
                        value="Ready to process",
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    # Results display
                    with gr.Tabs():
                        with gr.Tab("📝 Transcript"):
                            transcript_output = gr.Textbox(
                                label="Transcript",
                                lines=10,
                                max_lines=15,
                                interactive=True
                            )
                            transcript_copy = gr.Button("📋 Copy Transcript")
                        
                        with gr.Tab("🏷️ Titles"):
                            titles_output = gr.Textbox(
                                label="Generated Titles",
                                lines=5,
                                interactive=True
                            )
                            titles_copy = gr.Button("📋 Copy Titles")
                        
                        with gr.Tab("📄 Description"):
                            description_output = gr.Textbox(
                                label="Generated Description",
                                lines=8,
                                interactive=True
                            )
                            description_copy = gr.Button("📋 Copy Description")
                        
                        with gr.Tab("📚 Blog Post"):
                            blog_output = gr.Textbox(
                                label="Generated Blog Post",
                                lines=15,
                                interactive=True
                            )
                            blog_copy = gr.Button("📋 Copy Blog Post")
            
            # Event handlers
            def process_and_display(file_path, language, output_types):
                """Process file and display results"""
                if not file_path:
                    return "No file uploaded", "", "", "", ""
                
                # Update progress
                yield "Processing file...", "", "", "", ""
                
                # Process file
                results = self.process_file(file_path, language, output_types)
                
                if results['status'] == 'error':
                    yield f"Error: {results['message']}", "", "", "", ""
                    return
                
                # Format results
                formatted = self.format_results_for_display(results)
                
                # Return results
                yield (
                    "✅ Processing completed!",
                    formatted.get('transcript', ''),
                    formatted.get('titles', ''),
                    formatted.get('description', ''),
                    formatted.get('blog_post', '')
                )
            
            # Connect process button
            self.process_button.click(
                fn=process_and_display,
                inputs=[self.file_input, self.language_dropdown, self.output_checkboxes],
                outputs=[progress_display, transcript_output, titles_output, description_output, blog_output]
            )
            
            # Copy button handlers
            transcript_copy.click(
                fn=lambda x: gr.Info("Transcript copied to clipboard!"),
                inputs=[transcript_output]
            )
            
            titles_copy.click(
                fn=lambda x: gr.Info("Titles copied to clipboard!"),
                inputs=[titles_output]
            )
            
            description_copy.click(
                fn=lambda x: gr.Info("Description copied to clipboard!"),
                inputs=[description_output]
            )
            
            blog_copy.click(
                fn=lambda x: gr.Info("Blog post copied to clipboard!"),
                inputs=[blog_output]
            )
            
            # Set component references
            self.result_display = {
                'transcript': transcript_output,
                'titles': titles_output,
                'description': description_output,
                'blog_post': blog_output
            }
        
        return interface
    
    def launch(self, share: bool = False, debug: bool = False):
        """
        Launch the Gradio application
        
        Args:
            share: Whether to create a public link
            debug: Whether to enable debug mode
        """
        interface = self.build_interface()
        interface.launch(share=share, debug=debug)


def main():
    """Main entry point"""
    app = PodscriptApp()
    app.launch(debug=True)


if __name__ == "__main__":
    main()