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


class TestBlogGeneration:
    """Test blog post generation functionality"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_generate_blog_post(self, content_generator, mocker):
        """ブログ記事が生成されることを確認"""
        # Mock API response with Markdown blog post
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""# AIの未来を探る：最新トレンドと実用例

## はじめに

今回のエピソードでは、人工知能（AI）の最新動向と、私たちの生活にもたらす変革について深く掘り下げました。機械学習からディープラーニングまで、AIの進化は目覚ましく、様々な産業で実用化が進んでいます。本記事では、エピソードで語られた内容を整理し、AIがもたらす未来についての洞察をお伝えします。

## 主なトピック

### 1. 機械学習の基礎

従来のプログラミングとは異なり、機械学習はデータから学習し、パターンを見つけ出すことができます。この技術により、画像認識、音声認識、自然言語処理など、様々な分野で革新的なアプリケーションが生まれています。特に注目すべきは、人間の判断を模倣するだけでなく、時には人間を超える精度を実現している点です。

### 2. ディープラーニングの革新

ニューラルネットワークを多層化したディープラーニングは、人間の脳の仕組みを模倣した技術です。特に画像認識や音声認識の精度は人間を超える水準に達しており、医療診断や自動運転などの分野で活用されています。この技術の進歩により、従来不可能だった複雑な問題解決が可能になりつつあります。

### 3. 実用化事例

- **医療分野**: がんの早期発見、創薬支援、個別化医療の実現
- **金融分野**: 不正検知、投資戦略の最適化、リスク管理の高度化
- **製造業**: 品質管理、予知保全、生産プロセスの最適化
- **小売業**: 需要予測、パーソナライゼーション、在庫管理の効率化

これらの事例は、AIが単なる研究段階を超えて、実際のビジネスや社会に価値をもたらしていることを示しています。

## 今後の展望

AIの発展は今後も加速すると予想されます。量子コンピューティングとの融合により、さらに高度な計算が可能になり、現在では解決困難な問題にも取り組めるようになるでしょう。また、エッジコンピューティングの発展により、よりリアルタイムで効率的なAI処理が可能になると期待されています。

## まとめ

AIは単なる技術革新ではなく、私たちの生活や社会構造そのものを変える可能性を秘めています。この変化の波に乗り遅れないよう、常に最新の情報をキャッチアップし、自分の分野でどのように活用できるかを考えることが重要です。重要なのは、AIを恐れるのではなく、人間とAIが協調して新たな価値を生み出すことです。

次回のエピソードでは、具体的なAIツールの使い方について詳しく解説します。お楽しみに！"""))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate blog post
        transcript = "今日はAIについて話します。機械学習とディープラーニングの違いや、実際の応用例について解説していきます。"
        blog_post = content_generator.generate_blog_post(transcript, language='ja')
        
        # Assertions
        assert isinstance(blog_post, str)
        assert blog_post.strip()  # Not empty
        assert len(blog_post) > 0
    
    def test_markdown_format(self, content_generator, mocker):
        """Markdown形式で出力されることを確認"""
        # Mock API response with Markdown elements
        markdown_content = """# メインタイトル：技術ブログの書き方

## セクション1：導入部分

これは段落です。**太字**や*斜体*も使えます。Markdownは、シンプルなテキストフォーマットでありながら、豊富な表現力を持つマークアップ言語です。ブログ記事を書く際には、読みやすさと構造化された内容が重要になります。本記事では、効果的な技術ブログの書き方について詳しく解説していきます。

### サブセクション：Markdownの基本要素

Markdownには様々な要素があります。以下に主要な要素をリストアップします：

- リスト項目1：見出しの使い方（#, ##, ###）
- リスト項目2：段落とテキストの装飾（太字、斜体、取り消し線）
- リスト項目3：リストの作成（箇条書き、番号付きリスト）
- リスト項目4：リンクと画像の挿入方法
- リスト項目5：コードブロックとインラインコードの使い分け

## セクション2：実践的な活用方法

技術ブログを書く際に重要なポイントを番号付きリストで整理します：

1. 読者のターゲットを明確にする：初心者向けなのか、経験者向けなのかを決める
2. 構造化された内容にする：見出しを適切に使い、論理的な流れを作る
3. 具体例を豊富に含める：理論だけでなく、実際のコード例や実装例を示す
4. 視覚的な要素を活用する：図表、スクリーンショット、フローチャートなどを使う
5. 結論と次のステップを明確にする：読者が次に何をすべきかを示す

> 引用文も使えます。「良いドキュメントは、読者の時間を節約し、理解を促進するものである」

### コードの表現方法

`インラインコード`は短いコードや変数名を示す際に使用し、より長いコードは以下のようにコードブロックを使用します：

```python
# コードブロックも使えます
def hello(name):
    print(f"Hello, {name}!")
    return f"Welcome to the blog"
```

## セクション3：まとめ

[公式ドキュメント](https://example.com)や[参考リンク](https://example.com)も含められます。技術ブログは、知識の共有と技術コミュニティへの貢献の重要な手段です。Markdownを効果的に使用することで、読みやすく、構造化された記事を作成できます。"""
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=markdown_content))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        blog_post = content_generator.generate_blog_post("Test transcript")
        
        # Check for Markdown elements
        assert "#" in blog_post  # Headers
        assert "##" in blog_post  # Subheaders
        assert "-" in blog_post or "*" in blog_post  # Lists
        assert blog_post.count('\n') > 5  # Multiple paragraphs
    
    def test_heading_structure(self, content_generator, mocker):
        """適切な見出し構造があることを確認"""
        # Mock API response with structured headings
        structured_content = """# ポッドキャストタイトル：テクノロジーの未来を語る

## はじめに

今回のポッドキャストでは、テクノロジーの最新トレンドと未来について深く掘り下げました。急速に進化するデジタル技術が、私たちの生活やビジネスにどのような影響を与えているのか、専門家の視点から分析します。特に、人工知能、IoT、ブロックチェーンなどの革新的な技術に焦点を当て、これらが相互に作用しながら新しい価値を生み出している現状を解説します。現代は第4次産業革命の真っ只中にあり、デジタル変革が全ての業界に波及している状況です。

## 主要トピック

### トピック1：人工知能の現在と未来

人工知能（AI）は、もはや研究室の中だけの技術ではありません。日常生活のあらゆる場面で活用されており、医療診断から金融取引、エンターテインメントまで幅広い分野で革新をもたらしています。機械学習とディープラーニングの進化により、AIは人間の能力を補完し、時には超える性能を発揮しています。今後は、より倫理的で説明可能なAIの開発が重要な課題となるでしょう。特に、生成AIの登場により、クリエイティブな分野でも人間とAIの協働が現実のものとなっています。

### トピック2：IoTとスマートシティの実現

Internet of Things（IoT）技術は、あらゆるデバイスをインターネットに接続し、データの収集と分析を可能にします。スマートホーム、スマートファクトリー、そしてスマートシティの実現に向けて、IoTは重要な役割を果たしています。センサー技術の進化と5G通信の普及により、リアルタイムでの大量データ処理が可能になり、より効率的で持続可能な社会の構築が期待されています。これにより、エネルギー効率の向上や交通渋滞の解消など、具体的な社会課題の解決が進んでいます。

### トピック3：ブロックチェーンが変える信頼の仕組み

ブロックチェーン技術は、分散型台帳技術として、金融から物流、医療まで様々な分野で応用されています。中央集権的な管理を必要とせず、透明性と改ざん防止性を確保できるこの技術は、デジタル社会における新しい信頼の仕組みを提供します。暗号通貨だけでなく、サプライチェーン管理、デジタルアイデンティティ、スマートコントラクトなど、多様な用途で活用が進んでいます。

## まとめ

テクノロジーの進化は加速度的に進んでおり、私たちの生活やビジネスに大きな変革をもたらしています。重要なのは、これらの技術を恐れるのではなく、適切に理解し活用することです。技術の恩恵を最大限に享受しながら、同時に人間らしさや創造性を大切にするバランスが求められます。次回のエピソードでは、これらの技術を実際にビジネスに活用する方法について、具体例を交えて解説します。お楽しみに！"""
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=structured_content))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        blog_post = content_generator.generate_blog_post("Test transcript")
        
        # Check heading structure
        lines = blog_post.split('\n')
        h1_count = sum(1 for line in lines if line.startswith('# '))
        h2_count = sum(1 for line in lines if line.startswith('## '))
        h3_count = sum(1 for line in lines if line.startswith('### '))
        
        assert h1_count >= 1  # At least one main title
        assert h2_count >= 2  # At least introduction and conclusion
        assert h3_count >= 0  # Optional subheadings
    
    def test_word_count_range(self, content_generator, mocker):
        """1000-2000文字の範囲内であることを確認"""
        # Create content with specific length
        test_content = "# タイトル\n\n" + "これはテストコンテンツです。" * 100
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=test_content))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        blog_post = content_generator.generate_blog_post("Test transcript")
        
        # Check character count (1000-2000 characters)
        char_count = len(blog_post)
        assert 1000 <= char_count <= 2000
    
    def test_prompt_construction_for_blog(self, content_generator):
        """ブログ記事用プロンプトが正しく構築されることを確認"""
        transcript = "This is a test transcript about podcasting."
        language = 'en'
        
        prompt = content_generator._build_blog_prompt(transcript, language)
        
        # Check prompt contains necessary elements
        assert isinstance(prompt, str)
        assert transcript in prompt
        assert "blog" in prompt.lower() or "article" in prompt.lower()
        assert "markdown" in prompt.lower()
        assert "1000-2000" in prompt or "1000" in prompt
    
    def test_language_handling_for_blog(self, content_generator, mocker):
        """ブログ記事の出力言語が正しく反映されることを確認"""
        # Test Japanese
        mock_response_ja = MagicMock()
        mock_response_ja.choices = [
            MagicMock(message=MagicMock(content="""# 日本語のブログ記事タイトル：最新テクノロジートレンドの全貌

## はじめに

これは日本語で書かれたブログ記事です。今回のポッドキャストでは、最新のテクノロジートレンドについて詳しく解説しました。2024年現在、私たちは技術革新の真っ只中にいます。人工知能、量子コンピューティング、拡張現実（AR）、仮想現実（VR）など、様々な技術が融合し、新しい価値を生み出しています。本記事では、これらの技術がどのように私たちの未来を形作っていくのか、具体的な事例を交えながら探っていきます。

## 主なポイント

### 1. AIの進化と社会実装

人工知能は急速に発展しており、私たちの生活に大きな影響を与えています。機械学習やディープラーニングの技術により、様々な分野で革新的なソリューションが生まれています。特に、大規模言語モデル（LLM）の登場により、自然言語処理の能力は飛躍的に向上しました。これにより、人間とコンピュータのインタラクションがより自然で直感的なものになっています。

### 2. 実用例と産業への影響

技術の進歩は、様々な産業に革命的な変化をもたらしています：

- **医療診断の精度向上**：AIを活用した画像診断により、がんの早期発見率が大幅に向上しています
- **自動運転技術の発展**：レベル4の自動運転が一部地域で実用化され、交通事故の削減に貢献しています
- **言語翻訳の高度化**：リアルタイム音声翻訳により、言語の壁がなくなりつつあります
- **製造業の効率化**：AIとロボティクスの融合により、生産性が飛躍的に向上しています
- **教育のパーソナライゼーション**：個々の学習者に最適化された教育コンテンツの提供が可能になっています

### 3. 未来への展望

今後5年から10年の間に、これらの技術はさらに進化し、私たちの生活に深く浸透していくでしょう。重要なのは、技術の恩恵を最大限に活用しながら、倫理的な課題にも適切に対処することです。

## まとめ

テクノロジーの進化は止まることがありません。常に最新の情報をキャッチアップし、自分のビジネスや生活にどう活かせるかを考えることが重要です。次回のエピソードでは、これらの技術を実際に活用するための具体的なステップについて解説します。皆様のイノベーションの旅に、少しでもお役に立てれば幸いです。

次回もお楽しみに！"""))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response_ja
        )
        
        blog_post_ja = content_generator.generate_blog_post("テスト", language='ja')
        assert "日本語" in blog_post_ja
        assert "はじめに" in blog_post_ja
    
    def test_empty_transcript_handling_for_blog(self, content_generator):
        """空の文字起こしテキストの処理（ブログ記事）"""
        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_blog_post("")
        
        assert "Transcript cannot be empty" in str(exc_info.value)
    
    def test_api_error_handling_for_blog(self, content_generator, mocker):
        """ブログ記事生成時のAPIエラー処理"""
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_blog_post("Test transcript")
        
        assert "Failed to generate blog post" in str(exc_info.value)
    
    def test_length_validation_for_blog(self, content_generator, mocker):
        """生成されたブログ記事の長さ検証"""
        # Test too short response
        short_content = "# Too short\n\nThis is too short."
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=short_content))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        with pytest.raises(ContentGenerationError) as exc_info:
            content_generator.generate_blog_post("Test transcript")
        
        assert "too short" in str(exc_info.value).lower()
    
    def test_past_blogs_reference(self, content_generator, mocker):
        """過去のブログ記事を参照した文体学習"""
        # Mock past blog posts
        mock_past_blogs = [
            "# 過去のブログ記事1\n\n## はじめに\n\nこれは過去のブログ記事のサンプルです...",
            "# 過去のブログ記事2\n\n## 今回のテーマ\n\n特別ゲストを迎えて..."
        ]
        
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_blog_posts',
            return_value=mock_past_blogs
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""# AIの未来について：技術革新がもたらす新たな可能性

## はじめに

今回のエピソードでは、人工知能の未来について深く探求しました。専門家の視点から、最新のトレンドと今後の展望を詳しく解説します。AIは単なる技術的な進歩ではなく、人類の歴史における重要な転換点となる可能性を秘めています。本記事では、現在のAI技術の到達点から、今後10年、20年先の未来まで、包括的に考察していきます。

## 主要なトピック

### 1. 現在のAI技術の到達点

現在のAI技術は、機械学習とディープラーニングを中心に発展しています。特に自然言語処理と画像認識の分野では、人間を超える精度を達成しています。GPT-4に代表される大規模言語モデルは、文章生成、翻訳、要約、プログラミング支援など、幅広いタスクで驚異的な性能を発揮しています。また、画像生成AIは、クリエイティブ産業に革命をもたらし、新しい表現の可能性を開いています。

### 2. 今後の技術的展開

量子コンピューティングとの融合により、AIの計算能力は飛躍的に向上すると予想されます。これにより、現在では不可能な複雑な問題の解決が可能になるでしょう。また、ニューロモーフィックコンピューティングの発展により、より人間の脳に近い情報処理が実現される可能性があります。さらに、エッジAIの進化により、デバイス単体でも高度な処理が可能になり、プライバシーとパフォーマンスの両立が実現されるでしょう。

### 3. 社会への影響と変革

AIは単なる技術革新ではなく、社会構造そのものを変える可能性があります。雇用、教育、医療など、あらゆる分野で大きな変化が起こるでしょう。特に、AIと人間の協働により、新しい職業が生まれ、既存の仕事の性質も大きく変わっていきます。教育分野では、個別最適化された学習体験が提供され、医療分野では、予防医療と個別化医療が主流となるでしょう。

## 実践的なアドバイス

AI時代を生き抜くために、以下の点が重要です：

- **継続的な学習が重要**：技術の進化に合わせて、常に新しいスキルを習得する姿勢が必要です
- **AIツールを積極的に活用**：AIを脅威ではなく、強力な協力者として捉え、積極的に活用しましょう
- **倫理的な側面も考慮**：AIの発展に伴う倫理的課題にも目を向け、責任ある使用を心がけましょう
- **創造性と批判的思考を磨く**：AIが得意とする領域とは異なる、人間ならではの能力を伸ばすことが重要です

## まとめ

AIの進化は止まることがありません。この変化の波に乗り遅れないよう、常に最新の情報をキャッチアップし、自分の分野でどのように活用できるかを考えることが重要です。同時に、人間としての価値や創造性を大切にし、AIと共存する未来を築いていく必要があります。

次回のエピソードでは、具体的なAIツールの使い方について詳しく解説します。お楽しみに！"""))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Generate with history
        blog_post = content_generator.generate_blog_post(
            "Test transcript",
            language='ja',
            include_history=True
        )
        
        # Verify API was called with history in prompt
        api_call_args = content_generator.api_client.generate_completion.call_args
        prompt = api_call_args[1]['messages'][1]['content']
        assert "過去のブログ記事" in prompt or "past blog" in prompt.lower()


class TestBlogIntegration:
    """Integration tests for blog post generation"""
    
    @pytest.fixture
    def content_generator(self):
        """Create ContentGenerator instance"""
        with patch('content_generator.APIClient'):
            with patch('content_generator.DataManager'):
                return ContentGenerator()
    
    def test_complete_blog_generation_flow(self, content_generator, mocker):
        """完全なブログ記事生成フローのテスト"""
        # Mock past blog posts
        mock_past_blogs = ["# 過去のブログ記事サンプル\n\n内容..."]
        mocker.patch.object(
            content_generator.data_manager,
            'get_recent_blog_posts',
            return_value=mock_past_blogs
        )
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""# ポッドキャストエピソード：AIの最新動向と未来への展望

## はじめに

本エピソードでは、人工知能（AI）の最新動向について深く掘り下げました。OpenAIのGPT-4から始まり、画像生成AI、そして今後のAI発展の方向性まで幅広く解説しています。2024年現在、私たちはAI革命の真っ只中にいます。この記事では、エピソードで議論された内容を整理し、AIがもたらす変革について詳しく解説します。

## 主な内容

### 1. 大規模言語モデルの進化

GPT-4に代表される大規模言語モデルは、自然言語処理の分野で革命的な進歩をもたらしました。これらのモデルは、文章生成、翻訳、要約など、様々なタスクで人間に匹敵する性能を発揮しています。特に注目すべきは、コンテキスト理解能力の向上により、より自然で人間らしい対話が可能になったことです。また、マルチモーダル機能により、テキストだけでなく画像も理解できるようになりました。

### 2. 画像生成AIの可能性

DALL-E 3やMidjourneyなどの画像生成AIは、クリエイティブ業界に大きな影響を与えています。デザイナーやアーティストは、これらのツールを活用して、より効率的に高品質な作品を生み出すことができるようになりました。重要なのは、これらのツールが人間のクリエイティビティを置き換えるのではなく、拡張するものであるという点です。AIとの協働により、これまで不可能だった表現が可能になっています。

### 3. プロンプトエンジニアリングの重要性

AIを効果的に活用するためには、適切なプロンプトを設計することが重要です。プロンプトエンジニアリングは、新しいスキルとして注目されており、多くの企業がこの分野の専門家を求めています。良いプロンプトは、AIの能力を最大限に引き出し、望む結果を得るための鍵となります。

## 実用的な応用例

現在、AIは様々な分野で実用化されています：

- **コンテンツ制作**: ブログ記事、マーケティングコピー、スクリプトの作成
- **プログラミング支援**: コード生成、デバッグ、ドキュメント作成
- **教育分野**: パーソナライズされた学習コンテンツの生成
- **カスタマーサポート**: チャットボット、FAQ自動生成
- **研究開発**: 文献調査、仮説生成、データ分析

## 今後の展望

AI技術は急速に進化しており、今後も新しいブレークスルーが期待されます。特に、マルチモーダルAI（テキスト、画像、音声を統合的に扱うAI）の発展により、より人間に近い形でのインタラクションが可能になるでしょう。また、エージェント型AIの進化により、複雑なタスクを自律的に実行できるようになることも期待されています。

## まとめ

AIは私たちの仕事や生活を大きく変える可能性を秘めています。重要なのは、この技術を恐れるのではなく、どのように活用できるかを考え、実践することです。継続的な学習と実験を通じて、AIと共に成長していきましょう。次回のエピソードでは、具体的なAIツールの使い方とベストプラクティスについて詳しく解説します。ぜひお聞きください！"""))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            return_value=mock_response
        )
        
        # Full flow
        transcript = "これはテストのトランスクリプトです。AIについて詳しく話しています。"
        blog_post = content_generator.generate_blog_post(
            transcript,
            language='ja',
            include_history=True
        )
        
        # Verify
        assert isinstance(blog_post, str)
        assert 1000 <= len(blog_post) <= 2000
        assert blog_post.strip()
        assert "#" in blog_post  # Has headers
        assert "##" in blog_post  # Has subheaders
    
    def test_retry_mechanism_for_blog(self, content_generator, mocker):
        """ブログ記事生成のリトライ機構テスト"""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="""# テクノロジーの最前線：AI革命がもたらす未来

## はじめに

このポッドキャストでは、最新のテクノロジートレンドについて深く掘り下げます。今回は特に人工知能の進化と、それが私たちの日常生活にもたらす変化について詳しく解説しました。技術革新のスピードは加速度的に増しており、私たちは歴史的な転換点に立っています。本記事では、エピソードで語られた内容を整理し、テクノロジーがもたらす未来について考察します。

## 主要トピック

### 1. AIの現状と到達点

現在のAI技術は、深層学習の発展により飛躍的に進歩しています。画像認識、音声認識、自然言語処理など、様々な分野で人間を超える性能を発揮しています。特に2023年から2024年にかけて、生成AIの能力は劇的に向上し、クリエイティブな作業においても人間と協働できるレベルに達しました。この進化は、単なる技術的進歩ではなく、私たちの働き方や生活様式そのものを変革する可能性を秘めています。

### 2. 実用化の事例と成功事例

現在、AIは様々な産業で実用化され、具体的な成果を上げています：

- **医療分野**: 画像診断での早期がん発見、創薬支援による新薬開発の加速、個別化医療の実現
- **金融分野**: リアルタイムリスク管理、高度な不正検知システム、投資戦略の最適化
- **製造業**: 予知保全による稼働率向上、品質管理の自動化、サプライチェーンの最適化
- **小売業**: 需要予測の精度向上、在庫最適化、パーソナライズされた顧客体験の提供
- **教育分野**: 個別最適化された学習プログラム、インタラクティブな教材開発

これらの事例は、AIが単なる実験段階を超えて、実際のビジネス価値を生み出していることを示しています。

### 3. 今後の課題と対応策

AIの発展には、倫理的な課題も伴います。プライバシー保護、バイアスの除去、説明可能性の向上など、解決すべき問題は多くあります。しかし、これらの課題に対しても、業界全体で取り組みが進んでいます。規制の整備、倫理ガイドラインの策定、技術的なソリューションの開発など、多面的なアプローチが採用されています。

## 実践的なアドバイス

AI時代を生き抜くための具体的なステップ：

1. **小さく始める**: まずは簡単なAIツールから試してみて、徐々に高度な活用へ
2. **継続的な学習**: オンラインコースや書籍で知識を更新し、最新トレンドをキャッチアップ
3. **コミュニティ参加**: 勉強会やカンファレンスで情報交換し、ネットワークを構築
4. **実践と振り返り**: 実際にAIツールを使い、その効果を測定して改善
5. **倫理的配慮**: AIの使用において、常に倫理的な側面を考慮

## まとめ

AIは単なるツールではなく、私たちの働き方や生き方を変える可能性を持っています。この変化を恐れずに、積極的に学び、活用していくことが重要です。技術の進歩と共に、私たち自身も成長していきましょう。重要なのは、人間とAIが協働する未来を築くことです。

次回は、具体的なAIツールの活用方法について詳しく解説します。お楽しみに！"""))
        ]
        
        mocker.patch.object(
            content_generator.api_client,
            'generate_completion',
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        # Should succeed on retry
        blog_post = content_generator.generate_blog_post("Test transcript")
        
        assert isinstance(blog_post, str)
        assert content_generator.api_client.generate_completion.call_count == 2