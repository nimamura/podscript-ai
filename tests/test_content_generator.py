"""
Test content generation functionality
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from content_generator import (  # noqa: E402
    ContentGenerator,
    ContentGenerationError,
    PromptTooLongError,
    APIResponseError
)


class TestTitleGeneration:
    """Test title generation functionality"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            return ContentGenerator()
    
    def test_generate_titles(self, content_generator, mocker):
        """タイトルが3つ生成されることを確認"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. AIの未来について考える\n2. テクノロジーが変える私たちの生活\n3. 人工知能との共存への道"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate titles
        transcript = "今日はAIについて話したいと思います。AIは私たちの生活を大きく変えています。"
        titles = content_generator.generate_titles(transcript, language='ja')
        
        # Assertions
        assert isinstance(titles, list)
        assert len(titles) == 3
        assert all(isinstance(title, str) for title in titles)
        assert all(title.strip() for title in titles)  # No empty titles
    
    def test_prompt_construction(self, content_generator):
        """プロンプトが正しく構築されることを確認"""
        transcript = "This is a test transcript about podcasting."
        language = 'en'
        
        prompt = content_generator._build_title_prompt(transcript, language)
        
        # Check prompt contains necessary elements
        assert isinstance(prompt, str)
        assert transcript in prompt
        assert "3" in prompt  # Should generate 3 titles
        assert "title" in prompt.lower()
        assert language in prompt or "English" in prompt
    
    def test_language_handling(self, content_generator, mocker):
        """出力言語が正しく反映されることを確認"""
        # Test Japanese
        mock_response_ja = MagicMock()
        mock_response_ja.choices = [
            MagicMock(message=MagicMock(content="1. 日本語タイトル1\n2. 日本語タイトル2\n3. 日本語タイトル3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_ja
        )
        
        titles_ja = content_generator.generate_titles("テスト", language='ja')
        assert all("日本語" in title for title in titles_ja)
        
        # Test English
        mock_response_en = MagicMock()
        mock_response_en.choices = [
            MagicMock(message=MagicMock(content="1. English Title 1\n2. English Title 2\n3. English Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_en
        )
        
        titles_en = content_generator.generate_titles("Test", language='en')
        assert all("English" in title for title in titles_en)
    
    def test_api_error_handling(self, content_generator, mocker):
        """APIエラーが適切に処理されることを確認"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "Failed to generate titles" in str(exc_info.value)
    
    def test_empty_transcript_handling(self, content_generator):
        """空の文字起こしテキストの処理"""
        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_titles("")
        
        assert "Transcript cannot be empty" in str(exc_info.value)
    
    def test_malformed_response_handling(self, content_generator, mocker):
        """不正なAPIレスポンスの処理"""
        # Response with no numbered list
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Just a single title without numbers"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        with pytest.raises(APIResponseError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "Invalid response format" in str(exc_info.value)
    
    def test_timeout_handling(self, content_generator, mocker):
        """タイムアウト処理の確認"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=TimeoutError("Request timed out")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_titles("Test transcript")
        
        assert "timeout" in str(exc_info.value).lower()
    
    def test_prompt_too_long(self, content_generator):
        """プロンプトが長すぎる場合の処理"""
        # Create a very long transcript (over 8000 characters)
        long_transcript = "これは非常に長いトランスクリプトです。" * 500
        
        with pytest.raises(PromptTooLongError) as exc_info:
            content_generator.generate_titles(long_transcript)
        
        assert "Transcript too long" in str(exc_info.value)
    
    def test_title_extraction_edge_cases(self, content_generator, mocker):
        """タイトル抽出のエッジケース"""
        # Test various formats
        test_cases = [
            # (response_content, expected_count)
            ("1. Title One\n2. Title Two\n3. Title Three", 3),
            ("1) Title One\n2) Title Two\n3) Title Three", 3),
            ("- Title One\n- Title Two\n- Title Three", 3),
            ("Title One\nTitle Two\nTitle Three", 3),  # No numbers
        ]
        
        for response_content, expected_count in test_cases:
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content=response_content))
            ]
            
            mocker.patch.object(
                content_generator.api_client,
                'generate_completion',
                return_value=mock_response
            )
            
            titles = content_generator.generate_titles("Test")
            assert len(titles) == expected_count


class TestTitleWithHistory:
    """Test title generation with past data reference"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_load_past_titles(self, content_generator, mocker):
        """過去のタイトルが読み込まれることを確認"""
        # Mock past titles from DataManager
        mock_past_titles = [
            "AIの未来を語る - エピソード1",
            "機械学習入門 - エピソード2",
            "ディープラーニングの基礎 - エピソード3"
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        past_titles = content_generator._get_past_titles(limit=3)
        
        assert past_titles == mock_past_titles
        assert len(past_titles) == 3
    
    def test_style_learning_prompt(self, content_generator, mocker):
        """文体学習がプロンプトに含まれることを確認"""
        # Mock past titles
        mock_past_titles = [
            "【徹底解説】AIの基礎知識",
            "【初心者向け】プログラミング入門"
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        # Build prompt with style learning
        transcript = "今日はAIについて話します。"
        prompt = content_generator._build_title_prompt_with_history(
            transcript, language='ja', include_history=True
        )
        
        # Check that past titles are included in prompt
        assert "【徹底解説】" in prompt
        assert "【初心者向け】" in prompt
        assert "style" in prompt.lower() or "文体" in prompt
    
    def test_no_history_handling(self, content_generator, mocker):
        """履歴がない場合の処理"""
        # Mock empty history
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=[]
        )
        
        # Should work without history
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        titles = content_generator.generate_titles(
            "Test transcript", include_history=True
        )
        
        assert len(titles) == 3
    
    def test_history_limit(self, content_generator, mocker):
        """履歴の取得数制限が機能することを確認"""
        # Mock many past titles
        mock_past_titles = [f"Title {i}" for i in range(20)]
        
        # Mock get_recent_titles to respect the limit parameter
        def mock_get_recent_titles(limit=5):
            return mock_past_titles[:limit]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            side_effect=mock_get_recent_titles
        )
        
        # Get limited history
        past_titles = content_generator._get_past_titles(limit=5)
        
        assert len(past_titles) == 5
        assert past_titles == mock_past_titles[:5]
    
    def test_history_error_handling(self, content_generator, mocker):
        """履歴取得エラーの処理"""
        # Mock error in getting history
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            side_effect=Exception("Database error")
        )
        
        # Should continue without history
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Should not raise error, just proceed without history
        titles = content_generator.generate_titles(
            "Test transcript", include_history=True
        )
        
        assert len(titles) == 3


class TestContentGeneratorIntegration:
    """Integration tests for ContentGenerator"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_complete_title_generation_flow(self, content_generator, mocker):
        """完全なタイトル生成フローのテスト"""
        # Mock past titles
        mock_past_titles = ["過去のタイトル1", "過去のタイトル2"]
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_titles',
            return_value=mock_past_titles
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. 新しいタイトル1\n2. 新しいタイトル2\n3. 新しいタイトル3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Full flow
        transcript = "これはテストのトランスクリプトです。"
        titles = content_generator.generate_titles(
            transcript,
            language='ja',
            include_history=True
        )
        
        # Verify
        assert len(titles) == 3
        assert all(isinstance(title, str) for title in titles)
        
        # Check API was called with proper prompt
        api_call_args = content_generator.api_client.generate_completion.call_args
        prompt = api_call_args[1]['messages'][1]['content']  # User message is at index 1
        assert transcript in prompt
        assert any(past_title in prompt for past_title in mock_past_titles)
    
    def test_language_auto_detection(self, content_generator, mocker):
        """言語自動検出との統合"""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Test with Japanese transcript (language not specified)
        titles = content_generator.generate_titles(
            "日本語のトランスクリプト",
            language=None  # Should auto-detect
        )
        
        assert len(titles) == 3
    
    def test_retry_mechanism_integration(self, content_generator, mocker):
        """リトライ機構の統合テスト"""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        # Should succeed on retry
        titles = content_generator.generate_titles("Test transcript")
        
        assert len(titles) == 3
        assert content_generator.api_client.generate_completion.call_count == 2
    
    def test_model_and_parameters(self, content_generator, mocker):
        """モデルとパラメータが正しく設定されることを確認"""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="1. Title 1\n2. Title 2\n3. Title 3"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        content_generator.generate_titles("Test transcript")
        
        # Check API call parameters
        api_call_args = content_generator.api_client.generate_completion.call_args
        assert api_call_args[1]['model'] in ['gpt-3.5-turbo', 'gpt-4']
        assert 'temperature' in api_call_args[1]
        assert 0 <= api_call_args[1]['temperature'] <= 1
        assert 'max_tokens' in api_call_args[1]


class TestDescriptionGeneration:
    """Test description generation functionality"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_generate_description(self, content_generator, mocker):
        """概要欄が生成されることを確認"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="このポッドキャストエピソードでは、AIの最新動向について詳しく解説します。機械学習の基礎から最新の応用事例まで、幅広くカバーしています。特に今回は、ディープラーニングとは何か、従来の機械学習との違い、そして実際のビジネスでどのように活用されているのかを具体例を交えながら説明します。初心者の方にも分かりやすく、実践的な内容となっています。AI技術に興味がある方、ビジネスに活用したい方にぜひ聞いていただきたい内容です。"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate description
        transcript = "今日はAIについて話します。機械学習とディープラーニングの違いや、実際の応用例について解説していきます。"
        description = content_generator.generate_description(transcript, language='ja')
        
        # Assertions
        assert isinstance(description, str)
        assert description.strip()  # Not empty
        assert len(description) > 0
    
    def test_character_limit(self, content_generator, mocker):
        """文字数が200-400文字の範囲内であることを確認"""
        # Mock API response with specific length
        test_description = "A" * 300  # 300 characters
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=test_description))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        description = content_generator.generate_description("Test transcript")
        
        # Check character count
        assert 200 <= len(description) <= 400
    
    def test_structure_compliance(self, content_generator, mocker):
        """指定された構成に従っていることを確認"""
        # Mock API response with structured content
        structured_description = """今回のエピソードでは、AIの基礎について解説します。
前半では機械学習の基本概念を初心者にも分かりやすく説明し、後半ではニューラルネットワークの仕組みと実際の応用例を紹介します。
特に画像認識、自然言語処理、音声認識などの身近な活用事例を取り上げます。
このエピソードを通じて、AIの基礎知識を身につけ、今後の技術動向を理解する土台を作ることができます。専門用語を極力避け、実例を交えた解説でお送りします。"""
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=structured_description))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        description = content_generator.generate_description("Test transcript")
        
        # Check structure (introduction, summary, conclusion)
        lines = description.strip().split('\n')
        assert len(lines) >= 3  # At least 3 parts
    
    def test_prompt_construction_for_description(self, content_generator):
        """概要欄用プロンプトが正しく構築されることを確認"""
        transcript = "This is a test transcript about podcasting."
        language = 'en'
        
        prompt = content_generator._build_description_prompt(transcript, language)
        
        # Check prompt contains necessary elements
        assert isinstance(prompt, str)
        assert transcript in prompt
        assert "description" in prompt.lower()
        assert "200-400" in prompt or "200" in prompt
    
    def test_language_handling_for_description(self, content_generator, mocker):
        """概要欄の出力言語が正しく反映されることを確認"""
        # Test Japanese
        mock_response_ja = MagicMock()
        mock_response_ja.choices = [
            MagicMock(message=MagicMock(content="これは日本語の概要欄です。今回のポッドキャストでは、最新のテクノロジートレンドについて深く掘り下げます。AIの進化、ブロックチェーン技術の応用、そしてメタバースの可能性など、幅広いトピックをカバーしています。専門的な内容も含まれますが、初心者の方にも理解しやすいよう、丁寧に解説していきます。テクノロジーが私たちの生活をどのように変えていくのか、一緒に考えていきましょう。最新情報満載でお届けします。"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_ja
        )
        
        description_ja = content_generator.generate_description("テスト", language='ja')
        assert "日本語" in description_ja
    
    def test_empty_transcript_handling_for_description(self, content_generator):
        """空の文字起こしテキストの処理（概要欄）"""
        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_description("")
        
        assert "Transcript cannot be empty" in str(exc_info.value)
    
    def test_api_error_handling_for_description(self, content_generator, mocker):
        """概要欄生成時のAPIエラー処理"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_description("Test transcript")
        
        assert "Failed to generate description" in str(exc_info.value)
    
    def test_length_validation(self, content_generator, mocker):
        """生成された概要欄の長さ検証"""
        # Test too short response
        short_description = "Too short"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=short_description))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_description("Test transcript")
        
        assert "too short" in str(exc_info.value).lower()
    
    def test_past_descriptions_reference(self, content_generator, mocker):
        """過去の概要欄を参照した文体学習"""
        # Mock past descriptions
        mock_past_descriptions = [
            "過去の概要欄1: このエピソードでは...",
            "過去の概要欄2: 今回は特別ゲストを迎えて..."
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_descriptions',
            return_value=mock_past_descriptions
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="今回のエピソードでは、AIの未来について探求します。専門家の視点から、最新のトレンドと今後の展望を詳しく解説します。人工知能がもたらす社会変革、産業への影響、そして私たちの日常生活がどのように変わっていくのかを、具体的な事例を交えながらお話しします。技術的な側面だけでなく、倫理的な課題や規制の動向についても触れています。リスナーの皆様に有益な情報をお届けし、AIと共に歩む未来について考えるきっかけになれば幸いです。"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate with history
        description = content_generator.generate_description(
            "Test transcript",
            language='ja',
            include_history=True
        )
        
        # Verify API was called with history in prompt
        api_call_args = content_generator.api_client.generate_completion.call_args
        prompt = api_call_args[1]['messages'][1]['content']
        assert "過去の概要欄" in prompt or "past description" in prompt.lower()


class TestDescriptionIntegration:
    """Integration tests for description generation"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_complete_description_generation_flow(self, content_generator, mocker):
        """完全な概要欄生成フローのテスト"""
        # Mock past descriptions
        mock_past_descriptions = ["過去の概要欄サンプル"]
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_descriptions',
            return_value=mock_past_descriptions
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="本エピソードでは、最新のAI技術について深く掘り下げます。OpenAIのGPT-4から始まり、画像生成AI、そして今後のAI発展の方向性まで幅広く解説します。大規模言語モデルの仕組み、プロンプトエンジニアリングの重要性、そして生成AIがクリエイティブ業界に与える影響について詳しく説明します。技術者から一般の方まで、どなたでも理解できる内容でお送りします。AIの可能性と課題を共に考えていきましょう。"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Full flow
        transcript = "これはテストのトランスクリプトです。AIについて詳しく話しています。"
        description = content_generator.generate_description(
            transcript,
            language='ja',
            include_history=True
        )
        
        # Verify
        assert isinstance(description, str)
        assert 200 <= len(description) <= 400
        assert description.strip()
    
    def test_retry_mechanism_for_description(self, content_generator, mocker):
        """概要欄生成のリトライ機構テスト"""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="このポッドキャストでは、テクノロジーの最前線をお届けします。今回は特に人工知能の進化と、それが私たちの日常生活にもたらす変化について詳しく解説します。スマートホーム、自動運転、医療診断など、AIが実際に活用されている分野を具体例とともに紹介。さらに、今後5年、10年でどのような技術革新が起こるのか、専門家の予測も交えてお話しします。未来を先取りする情報満載でお送りしますので、ぜひ最後までお聞きください。"))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        # Should succeed on retry
        description = content_generator.generate_description("Test transcript")
        
        assert isinstance(description, str)
        assert content_generator.api_client.generate_completion.call_count == 2