"""
Test Gradio application functionality
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from app import (  # noqa: E402
    PodscriptApp,
    UIError,
    ProcessingError
)


class TestGradioUI:
    """Test Gradio UI components and functionality"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance"""
        return PodscriptApp()
    
    def test_ui_components_exist(self, app):
        """必要なUIコンポーネントが存在することを確認"""
        # Build the Gradio interface
        interface = app.build_interface()
        
        # Check that interface is created
        assert interface is not None
        
        # Check that the interface has the expected components
        # (These will be mocked in actual implementation)
        assert hasattr(app, 'file_input')
        assert hasattr(app, 'language_dropdown')
        assert hasattr(app, 'output_checkboxes')
        assert hasattr(app, 'process_button')
        assert hasattr(app, 'result_display')
    
    def test_file_upload_handling(self, app):
        """ファイルアップロードが正しく処理されることを確認"""
        # Mock audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'mock audio data')
            tmp_file_path = tmp_file.name
        
        try:
            # Test audio file upload
            result = app.handle_file_upload(tmp_file_path)
            assert result['status'] == 'success'
            assert result['file_type'] == 'audio'
            assert result['file_path'] == tmp_file_path
            
            # Test text file upload
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as txt_file:
                txt_file.write('テスト原稿内容'.encode('utf-8'))
                txt_file_path = txt_file.name
            
            result = app.handle_file_upload(txt_file_path)
            assert result['status'] == 'success'
            assert result['file_type'] == 'text'
            assert result['file_path'] == txt_file_path
            
            # Test invalid file type
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
                pdf_file.write(b'mock pdf data')
                pdf_file_path = pdf_file.name
            
            result = app.handle_file_upload(pdf_file_path)
            assert result['status'] == 'error'
            assert 'Unsupported file type' in result['message']
            
        finally:
            # Clean up temporary files
            for file_path in [tmp_file_path, txt_file_path, pdf_file_path]:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    def test_language_selection(self, app):
        """言語選択が正しく動作することを確認"""
        # Test Japanese selection
        result = app.handle_language_selection('ja')
        assert result == 'ja'
        
        # Test English selection  
        result = app.handle_language_selection('en')
        assert result == 'en'
        
        # Test auto-detection
        result = app.handle_language_selection('auto')
        assert result == 'auto'
    
    def test_output_type_selection(self, app):
        """出力タイプ選択が正しく動作することを確認"""
        # Test all outputs selected
        selected_outputs = ['titles', 'description', 'blog_post']
        result = app.handle_output_selection(selected_outputs)
        assert result == selected_outputs
        
        # Test partial selection
        selected_outputs = ['titles', 'description']
        result = app.handle_output_selection(selected_outputs)
        assert result == selected_outputs
        
        # Test no selection
        result = app.handle_output_selection([])
        assert result == []


class TestProcessingWorkflow:
    """Test the complete processing workflow"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance"""
        return PodscriptApp()
    
    @patch('app.AudioProcessor')
    @patch('app.TextProcessor')
    @patch('app.ContentGenerator')
    @patch('app.DataManager')
    def test_process_audio_file(self, mock_data_manager, mock_content_generator, 
                               mock_text_processor, mock_audio_processor, app):
        """音声ファイルの完全な処理ワークフロー"""
        # Mock dependencies
        mock_audio_processor_instance = MagicMock()
        mock_content_generator_instance = MagicMock()
        mock_data_manager_instance = MagicMock()
        
        mock_audio_processor.return_value = mock_audio_processor_instance
        mock_content_generator.return_value = mock_content_generator_instance
        mock_data_manager.return_value = mock_data_manager_instance
        
        # Mock transcription
        mock_audio_processor_instance.transcribe_audio.return_value = "テスト音声の文字起こし結果"
        
        # Mock content generation
        mock_content_generator_instance.generate_titles.return_value = [
            "タイトル1", "タイトル2", "タイトル3"
        ]
        mock_content_generator_instance.generate_description.return_value = (
            "これはテスト用の概要欄です。" * 10  # 200+ characters
        )
        mock_content_generator_instance.generate_blog_post.return_value = (
            "# テストブログ記事\n\n" + "テスト内容です。" * 50  # 1000+ characters
        )
        
        # Mock data saving
        mock_data_manager_instance.save_history.return_value = "test-history-id"
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'mock audio data')
            tmp_file_path = tmp_file.name
        
        try:
            # Process the file
            result = app.process_file(
                file_path=tmp_file_path,
                language='ja',
                output_types=['titles', 'description', 'blog_post']
            )
            
            # Verify results
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'titles' in result
            assert 'description' in result
            assert 'blog_post' in result
            assert len(result['titles']) == 3
            assert len(result['description']) >= 200
            assert len(result['blog_post']) >= 1000
            
            # Verify that processing methods were called
            mock_audio_processor_instance.transcribe_audio.assert_called_once()
            mock_content_generator_instance.generate_titles.assert_called_once()
            mock_content_generator_instance.generate_description.assert_called_once()
            mock_content_generator_instance.generate_blog_post.assert_called_once()
            mock_data_manager_instance.save_history.assert_called_once()
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    @patch('app.TextProcessor')
    @patch('app.ContentGenerator')
    @patch('app.DataManager')
    def test_process_text_file(self, mock_data_manager, mock_content_generator, 
                              mock_text_processor, app):
        """テキストファイルの完全な処理ワークフロー"""
        # Mock dependencies
        mock_text_processor_instance = MagicMock()
        mock_content_generator_instance = MagicMock()
        mock_data_manager_instance = MagicMock()
        
        mock_text_processor.return_value = mock_text_processor_instance
        mock_content_generator.return_value = mock_content_generator_instance
        mock_data_manager.return_value = mock_data_manager_instance
        
        # Mock text processing
        mock_text_processor_instance.process_manuscript_file.return_value = {
            'status': 'success',
            'content': 'テスト原稿の内容です。',
            'metadata': {
                'language': 'ja',
                'character_count': 100
            }
        }
        
        # Mock content generation
        mock_content_generator_instance.generate_titles.return_value = [
            "原稿タイトル1", "原稿タイトル2", "原稿タイトル3"
        ]
        mock_content_generator_instance.generate_description.return_value = (
            "これは原稿用の概要欄です。" * 10  # 200+ characters
        )
        
        # Mock data saving
        mock_data_manager_instance.save_history.return_value = "test-history-id"
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write('テスト原稿内容'.encode('utf-8'))
            tmp_file_path = tmp_file.name
        
        try:
            # Process the file
            result = app.process_file(
                file_path=tmp_file_path,
                language='ja',
                output_types=['titles', 'description']
            )
            
            # Verify results
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'titles' in result
            assert 'description' in result
            assert len(result['titles']) == 3
            assert len(result['description']) >= 200
            
            # Verify that processing methods were called
            mock_text_processor_instance.process_manuscript_file.assert_called_once()
            mock_content_generator_instance.generate_titles.assert_called_once()
            mock_content_generator_instance.generate_description.assert_called_once()
            mock_data_manager_instance.save_history.assert_called_once()
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_selective_output_generation(self, app):
        """選択的な出力生成が正しく動作することを確認"""
        # Test title only generation
        with patch.object(app, 'audio_processor') as mock_audio:
            with patch.object(app, 'content_generator') as mock_content:
                mock_audio.transcribe_audio.return_value = "テスト音声"
                mock_content.generate_titles.return_value = ["タイトル1", "タイトル2", "タイトル3"]
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(b'mock audio')
                    tmp_file_path = tmp_file.name
                
                try:
                    result = app.process_file(
                        file_path=tmp_file_path,
                        language='ja',
                        output_types=['titles']
                    )
                    
                    assert result['status'] == 'success'
                    assert 'titles' in result
                    assert 'description' not in result
                    assert 'blog_post' not in result
                    
                    # Only title generation should be called
                    mock_content.generate_titles.assert_called_once()
                    mock_content.generate_description.assert_not_called()
                    mock_content.generate_blog_post.assert_not_called()
                    
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)


class TestResultDisplay:
    """Test result display functionality"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance"""
        return PodscriptApp()
    
    def test_display_results(self, app):
        """結果が正しく表示されることを確認"""
        # Mock processing results
        results = {
            'status': 'success',
            'transcript': 'テスト文字起こし結果',
            'titles': ['タイトル1', 'タイトル2', 'タイトル3'],
            'description': 'テスト概要欄' * 20,
            'blog_post': '# テストブログ記事\n\n' + 'テスト内容' * 100
        }
        
        # Format results for display
        formatted_results = app.format_results_for_display(results)
        
        assert formatted_results['status'] == 'success'
        assert 'transcript' in formatted_results
        assert 'titles' in formatted_results
        assert 'description' in formatted_results
        assert 'blog_post' in formatted_results
        
        # Check that titles are properly formatted
        assert isinstance(formatted_results['titles'], str)
        assert 'タイトル1' in formatted_results['titles']
        assert 'タイトル2' in formatted_results['titles']
        assert 'タイトル3' in formatted_results['titles']
    
    def test_edit_functionality(self, app):
        """編集機能が動作することを確認"""
        # Test editing titles
        original_titles = "1. タイトル1\n2. タイトル2\n3. タイトル3"
        edited_titles = "1. 編集済みタイトル1\n2. 編集済みタイトル2\n3. 編集済みタイトル3"
        
        result = app.handle_edit_titles(edited_titles)
        assert result == edited_titles
        
        # Test editing description
        original_description = "元の概要欄内容"
        edited_description = "編集済み概要欄内容"
        
        result = app.handle_edit_description(edited_description)
        assert result == edited_description
        
        # Test editing blog post
        original_blog = "# 元のブログ記事\n\n内容"
        edited_blog = "# 編集済みブログ記事\n\n編集済み内容"
        
        result = app.handle_edit_blog_post(edited_blog)
        assert result == edited_blog
    
    def test_copy_buttons(self, app):
        """コピーボタンが動作することを確認"""
        # Test copy functionality (returns the content to be copied)
        test_content = "コピーするテスト内容"
        
        result = app.handle_copy_content(test_content)
        assert result == test_content
        
        # Test copy with different content types
        titles_content = "1. タイトル1\n2. タイトル2\n3. タイトル3"
        result = app.handle_copy_content(titles_content)
        assert result == titles_content
    
    def test_progress_display(self, app):
        """プログレス表示が正しく動作することを確認"""
        # Test progress updates
        progress_stages = [
            "ファイル検証中...",
            "音声を文字起こし中...",
            "タイトルを生成中...",
            "概要欄を生成中...",
            "ブログ記事を生成中...",
            "完了しました！"
        ]
        
        for stage in progress_stages:
            result = app.update_progress(stage)
            assert result == stage


class TestErrorHandling:
    """Test error handling in the UI"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance"""
        return PodscriptApp()
    
    def test_file_upload_errors(self, app):
        """ファイルアップロードエラーの処理"""
        # Test non-existent file
        result = app.handle_file_upload("non_existent_file.mp3")
        assert result['status'] == 'error'
        assert 'File not found' in result['message']
        
        # Test empty file path
        result = app.handle_file_upload("")
        assert result['status'] == 'error'
        assert 'No file provided' in result['message']
        
        # Test None file path
        result = app.handle_file_upload(None)
        assert result['status'] == 'error'
        assert 'No file provided' in result['message']
    
    def test_processing_errors(self, app):
        """処理エラーのハンドリング"""
        with patch.object(app, 'audio_processor') as mock_audio:
            # Mock transcription error
            mock_audio.transcribe_audio.side_effect = Exception("Transcription failed")
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(b'mock audio')
                tmp_file_path = tmp_file.name
            
            try:
                result = app.process_file(
                    file_path=tmp_file_path,
                    language='ja',
                    output_types=['titles']
                )
                
                assert result['status'] == 'error'
                assert 'Transcription failed' in result['message']
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    def test_api_error_handling(self, app):
        """API エラーのハンドリング"""
        with patch.object(app, 'content_generator') as mock_content:
            # Mock API error
            mock_content.generate_titles.side_effect = Exception("API limit exceeded")
            
            with patch.object(app, 'audio_processor') as mock_audio:
                mock_audio.transcribe_audio.return_value = "テスト音声"
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(b'mock audio')
                    tmp_file_path = tmp_file.name
                
                try:
                    result = app.process_file(
                        file_path=tmp_file_path,
                        language='ja',
                        output_types=['titles']
                    )
                    
                    assert result['status'] == 'error'
                    assert 'API limit exceeded' in result['message']
                    
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)


class TestUIIntegration:
    """Test UI integration and interface building"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance"""
        return PodscriptApp()
    
    def test_interface_building(self, app):
        """インターフェースの構築テスト"""
        # This will test the actual Gradio interface construction
        interface = app.build_interface()
        
        # Check that the interface was created successfully
        assert interface is not None
        
        # Check that the interface has the expected configuration
        assert hasattr(interface, 'title') or hasattr(interface, 'app')
    
    def test_component_interactions(self, app):
        """コンポーネント間の相互作用テスト"""
        # Test file upload triggering language detection
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write('これは日本語の原稿です。'.encode('utf-8'))
            tmp_file_path = tmp_file.name
        
        try:
            # Upload file and check language detection
            upload_result = app.handle_file_upload(tmp_file_path)
            assert upload_result['status'] == 'success'
            
            # Test that language is detected from file content
            detected_language = app.detect_language_from_file(tmp_file_path)
            assert detected_language == 'ja'
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_session_management(self, app):
        """セッション管理のテスト"""
        # Test session state initialization
        session_state = app.initialize_session()
        assert 'current_file' in session_state
        assert 'processing_status' in session_state
        assert 'results' in session_state
        
        # Test session state updates
        app.update_session_state(session_state, 'current_file', 'test.mp3')
        assert session_state['current_file'] == 'test.mp3'