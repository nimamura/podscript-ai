"""
Integration tests for the complete Podscript-AI workflow
"""
import sys
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from app import PodscriptApp  # noqa: E402
from audio_processor import AudioProcessor  # noqa: E402
from text_processor import TextProcessor  # noqa: E402
from content_generator import ContentGenerator  # noqa: E402
from data_manager import DataManager  # noqa: E402


class TestEndToEnd:
    """End-to-end tests for complete workflow"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance for testing"""
        return PodscriptApp()
    
    @pytest.fixture
    def mock_audio_file(self):
        """Create a temporary mock audio file"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'mock audio data for testing')
            tmp_file_path = tmp_file.name
        
        yield tmp_file_path
        
        # Cleanup
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
    
    @pytest.fixture
    def mock_text_file(self):
        """Create a temporary mock text file"""
        content = """
        これはポッドキャスト番組の原稿です。
        今回は人工知能について話したいと思います。
        AIは私たちの生活を大きく変えており、
        特に自然言語処理の分野では目覚ましい進歩があります。
        今後もこの技術の発展が期待されます。
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                       encoding='utf-8', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        yield tmp_file_path
        
        # Cleanup
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
    
    def test_full_workflow_with_audio(self, app, mock_audio_file):
        """音声ファイルから全出力を生成する完全なワークフロー"""
        # Mock all external dependencies
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_audio.transcribe_audio.return_value = "これはテスト用の音声文字起こし結果です。AIについて話しています。"
            
            # Mock title generation
            mock_content.generate_titles.return_value = [
                "AIの未来について語る",
                "人工知能が変える世界",
                "テクノロジーの新時代"
            ]
            
            # Mock description generation
            mock_content.generate_description.return_value = (
                "今回のエピソードでは人工知能の未来について詳しく解説しています。" * 8
            )
            
            # Mock blog post generation
            mock_content.generate_blog_post.return_value = (
                "# AIの未来について\n\n## はじめに\n\n" +
                "人工知能技術の進歩について詳しく解説します。" * 50
            )
            
            # Mock language detection
            mock_content._detect_language.return_value = "ja"
            
            # Mock data saving
            mock_data.save_history.return_value = "test-history-id-12345"
            
            # Execute the complete workflow
            result = app.process_file(
                file_path=mock_audio_file,
                language='auto',
                output_types=['titles', 'description', 'blog_post']
            )
            
            # Verify the workflow completed successfully
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'titles' in result
            assert 'description' in result
            assert 'blog_post' in result
            assert result['history_id'] == "test-history-id-12345"
            
            # Verify the content quality
            assert len(result['titles']) == 3
            assert len(result['description']) >= 200
            assert len(result['blog_post']) >= 1000
            assert 'AI' in result['transcript']
            
            # Verify all components were called
            mock_audio.transcribe_audio.assert_called_once_with(
                mock_audio_file, language=None
            )
            mock_content.generate_titles.assert_called_once()
            mock_content.generate_description.assert_called_once()
            mock_content.generate_blog_post.assert_called_once()
            mock_data.save_history.assert_called_once()
    
    def test_full_workflow_with_manuscript(self, app, mock_text_file):
        """原稿から全出力を生成する完全なワークフロー"""
        # Mock all external dependencies
        with patch.object(app, 'text_processor') as mock_text, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_text.process_manuscript_file.return_value = {
                'status': 'success',
                'content': 'これはテスト用の原稿内容です。人工知能について詳しく説明しています。',
                'metadata': {
                    'language': 'ja',
                    'character_count': 150,
                    'reading_time': 2
                }
            }
            
            # Mock content generation
            mock_content.generate_titles.return_value = [
                "原稿から生成されたタイトル1",
                "原稿から生成されたタイトル2", 
                "原稿から生成されたタイトル3"
            ]
            
            mock_content.generate_description.return_value = (
                "この原稿では人工知能の技術について詳しく解説されています。" * 10
            )
            
            mock_content.generate_blog_post.return_value = (
                "# 原稿から生成されたブログ記事\n\n## 概要\n\n" +
                "人工知能技術の最新動向について解説します。" * 55
            )
            
            # Mock language detection
            mock_content._detect_language.return_value = "ja"
            
            # Mock data saving
            mock_data.save_history.return_value = "manuscript-history-id-67890"
            
            # Execute the complete workflow
            result = app.process_file(
                file_path=mock_text_file,
                language='ja',
                output_types=['titles', 'description', 'blog_post']
            )
            
            # Verify the workflow completed successfully
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'titles' in result
            assert 'description' in result
            assert 'blog_post' in result
            assert result['history_id'] == "manuscript-history-id-67890"
            
            # Verify the content quality
            assert len(result['titles']) == 3
            assert len(result['description']) >= 200
            assert len(result['blog_post']) >= 1000
            assert '人工知能' in result['transcript']
            
            # Verify text processor was called (not audio processor)
            mock_text.process_manuscript_file.assert_called_once_with(mock_text_file)
            mock_content.generate_titles.assert_called_once()
            mock_content.generate_description.assert_called_once()
            mock_content.generate_blog_post.assert_called_once()
            mock_data.save_history.assert_called_once()
    
    def test_selective_output_generation(self, app, mock_audio_file):
        """選択的な出力生成が正しく動作することを確認"""
        # Mock dependencies
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_audio.transcribe_audio.return_value = "選択的出力テスト用の音声です。"
            mock_content.generate_titles.return_value = ["テストタイトル1", "テストタイトル2", "テストタイトル3"]
            mock_content._detect_language.return_value = "ja"
            mock_data.save_history.return_value = "selective-test-id"
            
            # Test 1: Only titles
            result = app.process_file(
                file_path=mock_audio_file,
                language='ja',
                output_types=['titles']
            )
            
            assert result['status'] == 'success'
            assert 'titles' in result
            assert 'description' not in result
            assert 'blog_post' not in result
            
            # Verify only title generation was called
            mock_content.generate_titles.assert_called()
            mock_content.generate_description.assert_not_called()
            mock_content.generate_blog_post.assert_not_called()
            
            # Reset mocks for next test
            mock_content.reset_mock()
            
            # Test 2: Only description
            mock_content.generate_description.return_value = "テスト概要欄" * 20
            
            result = app.process_file(
                file_path=mock_audio_file,
                language='ja',
                output_types=['description']
            )
            
            assert result['status'] == 'success'
            assert 'description' in result
            assert 'titles' not in result
            assert 'blog_post' not in result
            
            # Verify only description generation was called
            mock_content.generate_titles.assert_not_called()
            mock_content.generate_description.assert_called()
            mock_content.generate_blog_post.assert_not_called()


class TestWorkflowErrorHandling:
    """Test error handling in complete workflows"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance for testing"""
        return PodscriptApp()
    
    def test_audio_processing_failure(self, app):
        """音声処理失敗時のエラーハンドリング"""
        with patch.object(app, 'audio_processor') as mock_audio:
            # Mock transcription failure
            mock_audio.transcribe_audio.side_effect = Exception("Whisper API failed")
            
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
                assert 'Whisper API failed' in result['message']
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    def test_content_generation_failure(self, app):
        """コンテンツ生成失敗時のエラーハンドリング"""
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content:
            
            # Mock successful transcription
            mock_audio.transcribe_audio.return_value = "テスト音声"
            
            # Mock content generation failure
            mock_content.generate_titles.side_effect = Exception("GPT API rate limit exceeded")
            mock_content._detect_language.return_value = "ja"
            
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
                assert 'GPT API rate limit exceeded' in result['message']
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    def test_data_saving_failure(self, app):
        """データ保存失敗時のエラーハンドリング"""
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Mock successful processing
            mock_audio.transcribe_audio.return_value = "テスト音声"
            mock_content.generate_titles.return_value = ["タイトル1", "タイトル2", "タイトル3"]
            mock_content._detect_language.return_value = "ja"
            
            # Mock data saving failure
            mock_data.save_history.side_effect = Exception("Disk space full")
            
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
                assert 'Disk space full' in result['message']
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    def test_invalid_file_handling(self, app):
        """無効なファイルの処理"""
        # Test non-existent file
        result = app.process_file(
            file_path="non_existent_file.mp3",
            language='ja',
            output_types=['titles']
        )
        
        assert result['status'] == 'error'
        assert 'File not found' in result['message']
        
        # Test unsupported file format
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'mock pdf content')
            tmp_file_path = tmp_file.name
        
        try:
            result = app.process_file(
                file_path=tmp_file_path,
                language='ja',
                output_types=['titles']
            )
            
            assert result['status'] == 'error'
            assert 'Unsupported file type' in result['message']
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)


class TestPerformanceAndLimits:
    """Test performance characteristics and limits"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance for testing"""
        return PodscriptApp()
    
    def test_large_transcript_handling(self, app):
        """大きな文字起こしデータの処理性能"""
        # Create a large mock transcript (simulating 2-hour audio)
        large_transcript = "これは長い音声の文字起こし結果です。" * 1000  # ~50KB text
        
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_audio.transcribe_audio.return_value = large_transcript
            mock_content.generate_titles.return_value = ["大容量タイトル1", "大容量タイトル2", "大容量タイトル3"]
            mock_content._detect_language.return_value = "ja"
            mock_data.save_history.return_value = "large-test-id"
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(b'mock large audio file')
                tmp_file_path = tmp_file.name
            
            try:
                # Measure processing time
                start_time = time.time()
                
                result = app.process_file(
                    file_path=tmp_file_path,
                    language='ja',
                    output_types=['titles']
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Verify success and reasonable performance
                assert result['status'] == 'success'
                assert processing_time < 5.0  # Should complete within 5 seconds for mocked operations
                assert len(result['transcript']) > 10000  # Large transcript was processed
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
    
    def test_concurrent_processing_simulation(self, app):
        """並行処理のシミュレーション（複数ファイルの連続処理）"""
        with patch.object(app, 'audio_processor') as mock_audio, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_audio.transcribe_audio.return_value = "並行処理テスト用の音声です。"
            mock_content.generate_titles.return_value = ["並行タイトル1", "並行タイトル2", "並行タイトル3"]
            mock_content._detect_language.return_value = "ja"
            mock_data.save_history.return_value = "concurrent-test-id"
            
            # Create multiple temporary files
            temp_files = []
            for i in range(3):
                tmp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                tmp_file.write(f'mock audio file {i}'.encode())
                tmp_file.close()
                temp_files.append(tmp_file.name)
            
            try:
                start_time = time.time()
                results = []
                
                # Process multiple files sequentially (simulating concurrent loads)
                for file_path in temp_files:
                    result = app.process_file(
                        file_path=file_path,
                        language='ja',
                        output_types=['titles']
                    )
                    results.append(result)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # Verify all processed successfully
                assert len(results) == 3
                assert all(r['status'] == 'success' for r in results)
                assert total_time < 10.0  # Should complete all within 10 seconds
                
                # Verify each processing was called
                assert mock_audio.transcribe_audio.call_count == 3
                assert mock_content.generate_titles.call_count == 3
                
            finally:
                for file_path in temp_files:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
    
    def test_memory_usage_with_large_content(self, app):
        """大容量コンテンツでのメモリ使用量テスト"""
        # This test simulates processing very large content to ensure memory efficiency
        very_large_content = "これは非常に大きなコンテンツです。" * 8000  # ~240KB
        
        with patch.object(app, 'text_processor') as mock_text, \
             patch.object(app, 'content_generator') as mock_content, \
             patch.object(app, 'data_manager') as mock_data:
            
            # Setup mocks
            mock_text.process_manuscript_file.return_value = {
                'status': 'success',
                'content': very_large_content,
                'metadata': {'language': 'ja', 'character_count': len(very_large_content)}
            }
            
            mock_content.generate_titles.return_value = ["大容量メモリテスト1", "大容量メモリテスト2", "大容量メモリテスト3"]
            mock_content._detect_language.return_value = "ja"
            mock_data.save_history.return_value = "memory-test-id"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as tmp_file:
                tmp_file.write(very_large_content)
                tmp_file_path = tmp_file.name
            
            try:
                result = app.process_file(
                    file_path=tmp_file_path,
                    language='ja',
                    output_types=['titles']
                )
                
                # Verify successful processing of large content
                assert result['status'] == 'success'
                assert len(result['transcript']) > 100000  # Large content was processed
                
                # Memory efficiency: ensure content can be processed without issues
                # (In a real test, you might measure actual memory usage here)
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)


class TestUIIntegration:
    """Test UI-specific integration scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create PodscriptApp instance for testing"""
        return PodscriptApp()
    
    def test_gradio_interface_integration(self, app):
        """Gradio インターフェースとの統合テスト"""
        # Test that the interface can be built without errors
        interface = app.build_interface()
        
        assert interface is not None
        assert hasattr(app, 'file_input')
        assert hasattr(app, 'language_dropdown')
        assert hasattr(app, 'output_checkboxes')
        assert hasattr(app, 'process_button')
        assert hasattr(app, 'result_display')
    
    def test_session_state_persistence(self, app):
        """セッション状態の永続化テスト"""
        # Initialize session
        session = app.initialize_session()
        
        # Simulate file upload
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b'test audio')
            tmp_file_path = tmp_file.name
        
        try:
            # Update session state
            upload_result = app.handle_file_upload(tmp_file_path)
            assert upload_result['status'] == 'success'
            
            # Verify session state was updated
            assert app.session_state['current_file'] == tmp_file_path
            assert app.session_state['file_type'] == 'audio'
            
            # Test session state update
            app.update_session_state(app.session_state, 'processing_status', 'processing')
            assert app.session_state['processing_status'] == 'processing'
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_result_formatting_integration(self, app):
        """結果フォーマット処理の統合テスト"""
        # Mock processing results
        raw_results = {
            'status': 'success',
            'transcript': 'テスト用の文字起こし結果です。',
            'titles': ['統合テストタイトル1', '統合テストタイトル2', '統合テストタイトル3'],
            'description': 'これは統合テスト用の概要欄です。' * 10,
            'blog_post': '# 統合テストブログ\n\n統合テストの内容です。' * 30
        }
        
        # Format results for display
        formatted = app.format_results_for_display(raw_results)
        
        # Verify formatting
        assert formatted['status'] == 'success'
        assert 'transcript' in formatted
        assert 'titles' in formatted
        assert 'description' in formatted
        assert 'blog_post' in formatted
        
        # Verify title formatting (numbered list)
        assert '1. 統合テストタイトル1' in formatted['titles']
        assert '2. 統合テストタイトル2' in formatted['titles']
        assert '3. 統合テストタイトル3' in formatted['titles']