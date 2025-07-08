# Podscript-AI TDD開発計画書

## 開発アプローチ
- **開発手法**: テスト駆動開発（TDD）
- **サイクル**: Red（失敗するテスト作成）→ Green（最小限の実装）→ Refactor（リファクタリング）
- **テストフレームワーク**: pytest
- **モックライブラリ**: pytest-mock（API呼び出しのモック）

## プロジェクト構成
```
podscript-ai/
├── src/
│   ├── __init__.py
│   ├── audio_processor.py      # 音声処理モジュール
│   ├── text_processor.py       # テキスト処理モジュール
│   ├── content_generator.py    # コンテンツ生成モジュール
│   ├── data_manager.py         # データ管理モジュール
│   ├── api_client.py          # API通信モジュール
│   └── app.py                 # Gradioアプリケーション
├── tests/
│   ├── __init__.py
│   ├── test_audio_processor.py
│   ├── test_text_processor.py
│   ├── test_content_generator.py
│   ├── test_data_manager.py
│   ├── test_api_client.py
│   └── test_integration.py
├── requirements.txt
├── .env.example
├── README.md
└── pytest.ini
```

## Phase 1: 基盤構築（1週目）

### 1.1 プロジェクトセットアップ
**作成内容:**
- GitHubリポジトリ作成
- 基本的なディレクトリ構造
- 仮想環境とrequirements.txt
- pytest設定

**テスト内容:**
```python
# test_project_setup.py
def test_project_structure():
    """プロジェクト構造が正しいことを確認"""
    assert os.path.exists('src/')
    assert os.path.exists('tests/')
    assert os.path.exists('requirements.txt')
```

### 1.2 API Client基礎実装
**作成内容:**
- OpenAI APIクライアントのラッパークラス
- 環境変数からのAPIキー読み込み
- エラーハンドリング基礎

**テスト内容:**
```python
# test_api_client.py
class TestAPIClient:
    def test_api_key_loading(self):
        """APIキーが正しく読み込まれることを確認"""
        
    def test_api_key_missing(self):
        """APIキーがない場合のエラーハンドリング"""
        
    def test_connection_error_handling(self):
        """接続エラーのハンドリング"""
```

### 1.3 データ管理基礎実装
**作成内容:**
- JSONファイルの読み書き機能
- データディレクトリの作成
- 基本的なデータ構造

**テスト内容:**
```python
# test_data_manager.py
class TestDataManager:
    def test_create_data_directory(self):
        """データディレクトリが作成されることを確認"""
        
    def test_save_history(self):
        """履歴データが正しく保存されることを確認"""
        
    def test_load_history(self):
        """履歴データが正しく読み込まれることを確認"""
        
    def test_handle_missing_file(self):
        """ファイルが存在しない場合の処理"""
```

## Phase 2: 音声処理機能（2週目）

### 2.1 音声ファイル検証
**作成内容:**
- ファイル形式チェック（MP3, WAV, M4A）
- ファイルサイズチェック（1GB以下）
- 音声長さチェック（120分以下）

**テスト内容:**
```python
# test_audio_processor.py
class TestAudioValidation:
    def test_valid_file_formats(self):
        """対応形式のファイルが受け入れられることを確認"""
        
    def test_invalid_file_format(self):
        """非対応形式が拒否されることを確認"""
        
    def test_file_size_limit(self):
        """1GB超のファイルが拒否されることを確認"""
        
    def test_duration_limit(self):
        """120分超の音声が拒否されることを確認"""
```

### 2.2 Whisper API統合
**作成内容:**
- Whisper API呼び出し実装
- 言語指定機能
- レスポンス処理

**テスト内容:**
```python
class TestWhisperIntegration:
    def test_transcribe_audio(self, mocker):
        """音声が正しく文字起こしされることを確認"""
        mock_response = {"text": "テスト音声の内容"}
        mocker.patch('openai.Audio.transcribe', return_value=mock_response)
        
    def test_language_specification(self, mocker):
        """言語指定が正しく動作することを確認"""
        
    def test_api_error_handling(self, mocker):
        """API エラーが適切に処理されることを確認"""
```

## Phase 3: テキスト処理機能（3週目）

### 3.1 原稿ファイル処理
**作成内容:**
- TXTファイル読み込み
- UTF-8エンコーディング処理
- 原稿優先ロジック

**テスト内容:**
```python
# test_text_processor.py
class TestManuscriptProcessing:
    def test_read_txt_file(self):
        """TXTファイルが正しく読み込まれることを確認"""
        
    def test_encoding_handling(self):
        """UTF-8エンコーディングが正しく処理されることを確認"""
        
    def test_manuscript_priority(self):
        """原稿がある場合、音声処理をスキップすることを確認"""
```

### 3.2 テキスト前処理
**作成内容:**
- テキストクリーニング
- 文字数カウント
- 言語検出（オプション）

**テスト内容:**
```python
class TestTextPreprocessing:
    def test_text_cleaning(self):
        """テキストが適切にクリーニングされることを確認"""
        
    def test_character_count(self):
        """文字数が正しくカウントされることを確認"""
```

## Phase 4: コンテンツ生成機能 - タイトル（4週目）

### 4.1 タイトル生成基礎
**作成内容:**
- GPT API呼び出し実装
- プロンプトテンプレート
- 3案生成ロジック

**テスト内容:**
```python
# test_content_generator.py
class TestTitleGeneration:
    def test_generate_titles(self, mocker):
        """タイトルが3つ生成されることを確認"""
        
    def test_prompt_construction(self):
        """プロンプトが正しく構築されることを確認"""
        
    def test_language_handling(self):
        """出力言語が正しく反映されることを確認"""
```

### 4.2 過去データ参照
**作成内容:**
- 過去タイトルの読み込み
- プロンプトへの組み込み
- 文体学習ロジック

**テスト内容:**
```python
class TestTitleWithHistory:
    def test_load_past_title(self):
        """過去のタイトルが読み込まれることを確認"""
        
    def test_style_learning_prompt(self):
        """文体学習がプロンプトに含まれることを確認"""
```

## Phase 5: コンテンツ生成機能 - 概要欄（5週目）

### 5.1 概要欄生成基礎
**作成内容:**
- 概要欄生成ロジック
- 文字数制御（200-400文字）
- 構成テンプレート（導入・要約・締め）

**テスト内容:**
```python
class TestDescriptionGeneration:
    def test_generate_description(self, mocker):
        """概要欄が生成されることを確認"""
        
    def test_character_limit(self):
        """文字数が200-400の範囲内であることを確認"""
        
    def test_structure_compliance(self):
        """指定された構成に従っていることを確認"""
```

## Phase 6: コンテンツ生成機能 - ブログ記事（6週目）

### 6.1 ブログ記事生成
**作成内容:**
- ブログ記事生成ロジック
- Markdown形式出力
- 見出し構造の生成

**テスト内容:**
```python
class TestBlogGeneration:
    def test_generate_blog_post(self, mocker):
        """ブログ記事が生成されることを確認"""
        
    def test_markdown_format(self):
        """Markdown形式で出力されることを確認"""
        
    def test_heading_structure(self):
        """適切な見出し構造があることを確認"""
        
    def test_word_count_range(self):
        """1000-2000文字の範囲内であることを確認"""
```

## Phase 7: Gradio UI実装（7-8週目）

### 7.1 基本UI構築
**作成内容:**
- ファイルアップロードコンポーネント
- 言語選択ドロップダウン
- 出力選択チェックボックス

**テスト内容:**
```python
# test_integration.py
class TestGradioUI:
    def test_ui_components_exist(self):
        """必要なUIコンポーネントが存在することを確認"""
        
    def test_file_upload_handling(self):
        """ファイルアップロードが正しく処理されることを確認"""
```

### 7.2 結果表示と編集機能
**作成内容:**
- 結果表示エリア
- 編集可能フィールド
- コピーボタン実装
- プログレス表示

**テスト内容:**
```python
class TestResultDisplay:
    def test_display_results(self):
        """結果が正しく表示されることを確認"""
        
    def test_edit_functionality(self):
        """編集機能が動作することを確認"""
        
    def test_copy_buttons(self):
        """コピーボタンが動作することを確認"""
```

## Phase 8: 統合テストとリファクタリング（9週目）

### 8.1 エンドツーエンドテスト
**作成内容:**
- 全機能の統合テスト
- エラーケースの網羅的テスト
- パフォーマンステスト

**テスト内容:**
```python
class TestEndToEnd:
    def test_full_workflow_with_audio(self):
        """音声ファイルから全出力を生成する完全なワークフロー"""
        
    def test_full_workflow_with_manuscript(self):
        """原稿から全出力を生成する完全なワークフロー"""
        
    def test_selective_output_generation(self):
        """選択的な出力生成が正しく動作することを確認"""
```

### 8.2 最終調整
**作成内容:**
- コードのリファクタリング
- ドキュメント整備
- デプロイ準備

## 各フェーズの成果物

### 共通成果物（各フェーズ）
- テストコード（先に作成）
- 実装コード
- テストカバレッジレポート
- 簡単なドキュメント更新

### 最終成果物
- 完全に動作するGradioアプリケーション
- 90%以上のテストカバレッジ
- README.mdとユーザーガイド
- API設定ガイド

## 開発のベストプラクティス

1. **各機能の開発前に必ずテストを書く**
2. **モックを活用してAPI呼び出しをテスト**
3. **小さな単位でコミット**
4. **CIパイプラインの早期構築（GitHub Actions）**
5. **定期的なコードレビュー（セルフレビューも含む）**