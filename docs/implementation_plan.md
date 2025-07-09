# Podscript-AI TDD開発計画書

## 開発アプローチ
- **開発手法**: テスト駆動開発（TDD）
- **サイクル**: Red（失敗するテスト作成）→ Green（最小限の実装）→ Refactor（リファクタリング）
- **テストフレームワーク**: pytest
- **モックライブラリ**: pytest-mock（API呼び出しのモック）

## 進捗状況
- ✅ Phase 1: 基盤構築（完了）
- ✅ Phase 2: 音声処理機能（完了）
- ✅ Phase 3: テキスト処理機能（完了）
- ✅ Phase 4: コンテンツ生成機能 - タイトル（完了）
- ⏳ Phase 5: コンテンツ生成機能 - 概要欄（次の実装）
- ⏳ Phase 6: コンテンツ生成機能 - ブログ記事
- ⏳ Phase 7: Gradio UI実装
- ⏳ Phase 8: 統合テストとリファクタリング

## プロジェクト構成
```
podscript-ai/
├── src/
│   ├── __init__.py                ✅
│   ├── audio_processor.py         ✅ # 音声処理モジュール（実装済み）
│   ├── text_processor.py          ✅ # テキスト処理モジュール（実装済み）
│   ├── content_generator.py       ✅ # コンテンツ生成モジュール（実装済み - タイトル生成）
│   ├── data_manager.py            ✅ # データ管理モジュール（実装済み）
│   ├── api_client.py              ✅ # API通信モジュール（実装済み）
│   └── app.py                     # Gradioアプリケーション
├── tests/
│   ├── __init__.py                ✅
│   ├── test_audio_processor.py    ✅ # 音声処理テスト（17テスト全合格）
│   ├── test_text_processor.py     ✅ # テキスト処理テスト（21テスト全合格）
│   ├── test_content_generator.py  ✅ # コンテンツ生成テスト（18テスト全合格）
│   ├── test_data_manager.py       ✅ # データ管理テスト（11テスト全合格）
│   ├── test_api_client.py         ✅ # APIクライアントテスト（10テスト全合格）
│   ├── test_project_setup.py      ✅ # プロジェクト構造テスト（3テスト全合格）
│   └── test_integration.py        # 統合テスト
├── docs/
│   └── implementation_plan.md     ✅ # 実装計画書
├── requirements.txt               ✅
├── .env.example                   ✅
├── .flake8                        ✅ # Linter設定
├── .gitignore                     ✅
├── CLAUDE.md                      ✅ # Claude Code用ガイド
├── README.md                      ✅
└── pytest.ini                     ✅
```

## Phase 1: 基盤構築（1週目）✅ 完了

### 1.1 プロジェクトセットアップ ✅
**完了内容:**
- ~~GitHubリポジトリ作成~~
- ~~基本的なディレクトリ構造~~
- ~~仮想環境とrequirements.txt~~
- ~~pytest設定~~
- ~~.gitignore, README.md, CLAUDE.md作成~~
- ~~flake8によるLinter設定~~

**テスト結果:**
```python
# test_project_setup.py
✅ test_project_structure: プロジェクト構造が正しいことを確認
✅ test_python_packages: Pythonパッケージとして認識されることを確認
✅ test_imports: srcパッケージがインポート可能であることを確認
# 3/3 テスト合格
```

### 1.2 API Client基礎実装 ✅
**完了内容:**
- ~~OpenAI APIクライアントのラッパークラス~~
- ~~環境変数からのAPIキー読み込み~~
- ~~エラーハンドリング基礎~~
- ~~シングルトンパターン実装~~
- ~~リトライ機構（指数バックオフ）~~
- ~~タイムアウト処理~~

**テスト結果:**
```python
# test_api_client.py
✅ test_api_key_loading_from_env: APIキーが環境変数から正しく読み込まれる
✅ test_api_key_missing_raises_error: APIキーがない場合のエラーハンドリング
✅ test_api_key_validation: 無効なAPIキーの検証
✅ test_client_initialization: OpenAIクライアントの初期化
✅ test_connection_error_handling: 接続エラーのハンドリング
✅ test_retry_mechanism: リトライ機構（3回まで）
✅ test_retry_exhaustion: リトライ回数超過時のエラー
✅ test_timeout_handling: タイムアウト処理（30秒）
✅ test_rate_limit_handling: レート制限エラーの処理
✅ test_singleton_pattern: シングルトンパターンの動作確認
# 10/10 テスト合格
```

### 1.3 データ管理基礎実装 ✅
**完了内容:**
- ~~JSONファイルの読み書き機能~~
- ~~データディレクトリの作成~~
- ~~基本的なデータ構造~~
- ~~履歴の自動削除（最新10件保持）~~
- ~~履歴エクスポート機能~~
- ~~スタイル学習用のタイトル取得~~

**テスト結果:**
```python
# test_data_manager.py
✅ test_create_data_directory: データディレクトリが作成される
✅ test_data_directory_already_exists: 既存ディレクトリでも正常動作
✅ test_permission_error_handling: 権限エラーのハンドリング
✅ test_save_history: 履歴データの保存
✅ test_load_history: 履歴データの読み込み
✅ test_handle_missing_file: ファイルが存在しない場合の処理
✅ test_handle_corrupted_json: 破損したJSONファイルの処理
✅ test_get_all_histories: 全履歴の取得
✅ test_history_limit: 履歴の最大保持数（最新10件）
✅ test_get_recent_titles: 最近のタイトル取得（スタイル学習用）
✅ test_export_history: 履歴のエクスポート機能
# 11/11 テスト合格
```

### Phase 1 成果サマリー
- **総テスト数**: 24個（全合格）
- **テストカバレッジ**: 基盤部分100%
- **実装モジュール**: api_client.py, data_manager.py
- **開発環境**: pytest, flake8, python-dotenv設定完了
- **コミット**: dca4de0 feat: Complete Phase 1 foundation implementation

## Phase 2: 音声処理機能（2週目）✅ 完了

### 2.1 音声ファイル検証 ✅
**完了内容:**
- ~~ファイル形式チェック（MP3, WAV, M4A）~~
- ~~ファイルサイズチェック（1GB以下）~~
- ~~音声長さチェック（120分以下）~~
- ~~カスタム例外クラスの実装~~
- ~~環境変数による制限値の設定~~

**テスト結果:**
```python
# test_audio_processor.py - TestAudioValidation
✅ test_valid_file_formats: 対応形式のファイルが受け入れられることを確認
✅ test_invalid_file_format: 非対応形式が拒否されることを確認
✅ test_file_size_under_limit: 1GB以下のファイルが受け入れられることを確認
✅ test_file_size_over_limit: 1GB超のファイルが拒否されることを確認
✅ test_file_not_found: 存在しないファイルのエラー処理
✅ test_corrupted_file: 破損ファイルのエラー処理
# 6/6 テスト合格
```

### 2.2 音声長さ検証 ✅
**完了内容:**
- ~~mutagenによる音声メタデータ取得~~
- ~~120分制限の検証~~
- ~~エラーハンドリング~~

**テスト結果:**
```python
# test_audio_processor.py - TestAudioDuration
✅ test_duration_under_limit: 120分以下の音声が受け入れられることを確認
✅ test_duration_over_limit: 120分超の音声が拒否されることを確認
✅ test_duration_extraction_error: 長さ取得エラーの処理
# 3/3 テスト合格
```

### 2.3 Whisper API統合 ✅
**完了内容:**
- ~~Whisper API呼び出し実装~~
- ~~言語指定機能（ja/en対応）~~
- ~~リトライ機構（指数バックオフ）~~
- ~~タイムアウト処理~~
- ~~エラーハンドリング~~

**テスト結果:**
```python
# test_audio_processor.py - TestWhisperIntegration
✅ test_transcribe_audio_success: 音声が正しく文字起こしされることを確認
✅ test_transcribe_with_language: 言語指定が正しく動作することを確認
✅ test_transcribe_api_error: APIエラーが適切に処理されることを確認
✅ test_transcribe_timeout: タイムアウト処理
✅ test_transcribe_empty_audio: 無音/空の音声ファイル処理
✅ test_transcribe_retry_mechanism: リトライ機構の動作確認
✅ test_transcribe_file_validation_fails: ファイル検証失敗時の処理
✅ test_transcribe_duration_validation_fails: 音声長さ検証失敗時の処理
# 8/8 テスト合格
```

### Phase 2 成果サマリー
- **総テスト数**: 17個（全合格）
- **テストカバレッジ**: 99%（audio_processor.py）
- **実装機能**: 
  - ファイル検証（形式、サイズ、存在確認）
  - 音声長さ検証（mutagen統合）
  - Whisper API統合（リトライ機構付き）
  - カスタム例外クラス（4種類）
- **コミット**: af98cc7 feat: Implement Phase 2 audio processing functionality

## Phase 3: テキスト処理機能（3週目）✅ 完了

### 3.1 原稿ファイル処理 ✅
**完了内容:**
- ~~TXTファイル読み込み~~
- ~~UTF-8エンコーディング処理（BOM対応）~~
- ~~原稿優先ロジック~~
- ~~ファイル形式検証~~
- ~~カスタム例外クラス（3種類）~~

**テスト結果:**
```python
# test_text_processor.py - TestManuscriptProcessing
✅ test_read_txt_file: TXTファイルが正しく読み込まれることを確認
✅ test_encoding_handling: UTF-8エンコーディングが正しく処理されることを確認
✅ test_manuscript_priority: 原稿がある場合、音声処理をスキップすることを確認
✅ test_invalid_file_format: 非対応形式のファイルが拒否されることを確認
✅ test_file_not_found: 存在しないファイルのエラー処理
✅ test_empty_file: 空のファイルの処理
✅ test_large_file_handling: 大きなファイルの処理
✅ test_read_permission_error: 読み取り権限がない場合のエラー処理
# 8/8 テスト合格
```

### 3.2 テキスト前処理 ✅
**完了内容:**
- ~~テキストクリーニング（空白・改行の正規化）~~
- ~~文字数カウント~~
- ~~言語検出（日本語/英語/混合）~~
- ~~URL除去機能~~
- ~~テキスト検証~~
- ~~メタデータ抽出~~

**テスト結果:**
```python
# test_text_processor.py - TestTextPreprocessing
✅ test_text_cleaning: テキストが適切にクリーニングされることを確認
✅ test_character_count: 文字数が正しくカウントされることを確認
✅ test_text_preprocessing_pipeline: 前処理パイプライン全体の動作確認
✅ test_remove_urls: URLの除去が正しく動作することを確認
✅ test_normalize_whitespace: 空白の正規化が正しく動作することを確認
✅ test_text_validation: テキストの検証機能
✅ test_extract_metadata: テキストからメタデータを抽出
# 7/7 テスト合格

# test_text_processor.py - TestLanguageDetection
✅ test_detect_japanese: 日本語の検出
✅ test_detect_english: 英語の検出
✅ test_detect_mixed_language: 混合言語の検出（日本語優先）
✅ test_detect_unknown_language: 未知の言語や判定不能な場合
# 4/4 テスト合格

# test_text_processor.py - TestTextProcessorIntegration
✅ test_process_manuscript_file: 原稿ファイルの完全な処理フロー
✅ test_process_with_encoding_options: 異なるエンコーディングオプションでの処理
# 2/2 テスト合格
```

### Phase 3 成果サマリー
- **総テスト数**: 21個（全合格）
- **テストカバレッジ**: 93%（text_processor.py）
- **実装機能**: 
  - 原稿ファイル読み込み（TXT形式、UTF-8対応）
  - テキスト前処理（クリーニング、正規化）
  - URL除去機能
  - 言語検出（日本語/英語判定）
  - メタデータ抽出（文字数、行数、段落数、読了時間）
  - カスタム例外クラス（3種類）
- **コミット**: eb2ba1b feat: Implement Phase 3 text processing functionality

## Phase 4: コンテンツ生成機能 - タイトル（4週目）✅ 完了

### 4.1 タイトル生成基礎 ✅
**完了内容:**
- ~~GPT API呼び出し実装~~
- ~~プロンプトテンプレート~~
- ~~3案生成ロジック~~
- ~~カスタム例外クラス（3種類）~~
- ~~エラーハンドリングとリトライ機構~~
- ~~言語自動検出~~

**テスト結果:**
```python
# test_content_generator.py - TestTitleGeneration
✅ test_generate_titles: タイトルが3つ生成されることを確認
✅ test_prompt_construction: プロンプトが正しく構築されることを確認
✅ test_language_handling: 出力言語が正しく反映されることを確認
✅ test_api_error_handling: APIエラーが適切に処理されることを確認
✅ test_empty_transcript_handling: 空の文字起こしテキストの処理
✅ test_malformed_response_handling: 不正なAPIレスポンスの処理
✅ test_timeout_handling: タイムアウト処理の確認
✅ test_prompt_too_long: プロンプトが長すぎる場合の処理
✅ test_title_extraction_edge_cases: タイトル抽出のエッジケース
# 9/9 テスト合格
```

### 4.2 過去データ参照 ✅
**完了内容:**
- ~~過去タイトルの読み込み~~
- ~~プロンプトへの組み込み~~
- ~~文体学習ロジック~~
- ~~履歴エラーのグレースフルハンドリング~~

**テスト結果:**
```python
# test_content_generator.py - TestTitleWithHistory
✅ test_load_past_titles: 過去のタイトルが読み込まれることを確認
✅ test_style_learning_prompt: 文体学習がプロンプトに含まれることを確認
✅ test_no_history_handling: 履歴がない場合の処理
✅ test_history_limit: 履歴の取得数制限が機能することを確認
✅ test_history_error_handling: 履歴取得エラーの処理
# 5/5 テスト合格

# test_content_generator.py - TestContentGeneratorIntegration
✅ test_complete_title_generation_flow: 完全なタイトル生成フローのテスト
✅ test_language_auto_detection: 言語自動検出との統合
✅ test_retry_mechanism_integration: リトライ機構の統合テスト
✅ test_model_and_parameters: モデルとパラメータが正しく設定されることを確認
# 4/4 テスト合格
```

### Phase 4 成果サマリー
- **総テスト数**: 18個（全合格）
- **テストカバレッジ**: 82%（content_generator.py）
- **実装機能**: 
  - タイトル3案生成（GPT API統合）
  - 過去タイトルによる文体学習
  - 言語自動検出（日本語/英語）
  - プロンプト長制限（8000文字）
  - リトライ機構（最大2回）
  - 複数のタイトル抽出パターン対応
  - カスタム例外クラス（3種類）
- **コミット**: 5d0bef7 feat: Implement Phase 4 content generation - title generation

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

1. **各機能の開発前に必ずテストを書く** ✅ 実践中
2. **モックを活用してAPI呼び出しをテスト** ✅ 実践中
3. **小さな単位でコミット** ✅ 実践中
4. **CIパイプラインの早期構築（GitHub Actions）**
5. **定期的なコードレビュー（セルフレビューも含む）**

## 現在までの進捗サマリー

### 累計成果（Phase 1-4）
- **総テスト数**: 80個（全合格）
  - Phase 1: 24個（API Client: 10, Data Manager: 11, Project Setup: 3）
  - Phase 2: 17個（Audio Validation: 6, Duration: 3, Whisper Integration: 8）
  - Phase 3: 21個（Manuscript: 8, Preprocessing: 7, Language: 4, Integration: 2）
  - Phase 4: 18個（Title Generation: 9, History: 5, Integration: 4）
- **テストカバレッジ**: 89%（全体）
  - api_client.py: 88%
  - data_manager.py: 85%
  - audio_processor.py: 99%
  - text_processor.py: 93%
  - content_generator.py: 82%
- **実装モジュール**: 5個
  - api_client.py（シングルトン、リトライ機構）
  - data_manager.py（JSON永続化、履歴管理）
  - audio_processor.py（ファイル検証、Whisper統合）
  - text_processor.py（原稿処理、前処理、言語検出）
  - content_generator.py（タイトル生成、文体学習）
- **開発期間**: 4週間相当の作業を完了

## 使用技術スタック

### 確定済み
- **言語**: Python 3.13.5
- **テストフレームワーク**: pytest 8.4.1
- **モック**: pytest-mock 3.14.1
- **カバレッジ**: pytest-cov 6.2.1
- **APIクライアント**: openai 1.93.2
- **Linter**: flake8 7.3.0
- **環境変数管理**: python-dotenv 1.1.1
- **音声メタデータ**: mutagen 1.47.0
- **音声処理**: pydub 0.25.1

### 予定
- **Web UI**: gradio
- **CI/CD**: GitHub Actions