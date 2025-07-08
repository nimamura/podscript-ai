"""
Test data management functionality
"""
import json
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_manager import DataManager, DataError  # noqa: E402


class TestDataManager:
    """Test Data Manager functionality"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """一時的なデータディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir)
    
    def test_create_data_directory(self, temp_data_dir):
        """データディレクトリが作成されることを確認"""
        data_path = Path(temp_data_dir) / "test_data"
        DataManager(data_dir=str(data_path))
        
        assert data_path.exists(), "Data directory was not created"
        assert data_path.is_dir(), "Data path is not a directory"
    
    def test_data_directory_already_exists(self, temp_data_dir):
        """既存のデータディレクトリでも正常に動作することを確認"""
        data_path = Path(temp_data_dir) / "test_data"
        data_path.mkdir(parents=True)
        
        # Should not raise error
        DataManager(data_dir=str(data_path))
        assert data_path.exists()
    
    def test_permission_error_handling(self):
        """権限エラーのハンドリング"""
        # Try to create directory in a location without permission
        with pytest.raises(DataError) as exc_info:
            DataManager(data_dir="/root/no_permission_dir")
        # Check for either permission denied or read-only file system
        error_msg = str(exc_info.value)
        assert "Permission denied" in error_msg or "Read-only file system" in error_msg
    
    def test_save_history(self, temp_data_dir):
        """履歴データが正しく保存されることを確認"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Test data
        history_data = {
            "timestamp": datetime.now().isoformat(),
            "episode_title": "Test Episode",
            "titles": ["Title 1", "Title 2", "Title 3"],
            "description": "Test description",
            "blog_post": "Test blog content"
        }
        
        # Save history
        history_id = manager.save_history(history_data)
        
        # Check file was created
        history_file = Path(temp_data_dir) / f"history_{history_id}.json"
        assert history_file.exists(), "History file was not created"
        
        # Check content
        with open(history_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["episode_title"] == "Test Episode"
        assert len(saved_data["titles"]) == 3
        assert saved_data["id"] == history_id
    
    def test_load_history(self, temp_data_dir):
        """履歴データが正しく読み込まれることを確認"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Save test data
        history_data = {
            "episode_title": "Test Episode",
            "titles": ["Title 1", "Title 2", "Title 3"]
        }
        history_id = manager.save_history(history_data)
        
        # Load history
        loaded_data = manager.load_history(history_id)
        
        assert loaded_data is not None
        assert loaded_data["episode_title"] == "Test Episode"
        assert loaded_data["id"] == history_id
    
    def test_handle_missing_file(self, temp_data_dir):
        """ファイルが存在しない場合の処理"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Try to load non-existent history
        result = manager.load_history("non_existent_id")
        assert result is None
    
    def test_handle_corrupted_json(self, temp_data_dir):
        """破損したJSONファイルの処理"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Create corrupted JSON file
        corrupted_file = Path(temp_data_dir) / "history_corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should handle gracefully
        result = manager.load_history("corrupted")
        assert result is None
    
    def test_get_all_histories(self, temp_data_dir):
        """全履歴の取得"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Save multiple histories
        for i in range(5):
            manager.save_history({
                "episode_title": f"Episode {i}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Get all histories
        histories = manager.get_all_histories()
        
        assert len(histories) == 5
        # Should be sorted by timestamp (newest first)
        assert histories[0]["episode_title"] == "Episode 4"
    
    def test_history_limit(self, temp_data_dir):
        """履歴の最大保持数（最新10件）"""
        manager = DataManager(data_dir=temp_data_dir, max_histories=10)
        
        # Save more than limit
        for i in range(15):
            manager.save_history({
                "episode_title": f"Episode {i}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check only 10 most recent are kept
        histories = manager.get_all_histories()
        assert len(histories) == 10
        
        # Oldest should be Episode 5
        assert histories[-1]["episode_title"] == "Episode 5"
    
    def test_get_recent_titles(self, temp_data_dir):
        """最近のタイトル取得（スタイル学習用）"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Save histories with titles
        for i in range(3):
            manager.save_history({
                "episode_title": f"Episode {i}",
                "titles": [f"Title {i}-1", f"Title {i}-2", f"Title {i}-3"],
                "timestamp": datetime.now().isoformat()
            })
        
        # Get recent titles
        recent_titles = manager.get_recent_titles(limit=5)
        
        assert len(recent_titles) == 5  # Latest 5 titles
        assert recent_titles[0] == "Title 2-1"  # Most recent
    
    def test_export_history(self, temp_data_dir):
        """履歴のエクスポート機能"""
        manager = DataManager(data_dir=temp_data_dir)
        
        # Save some histories
        for i in range(3):
            manager.save_history({
                "episode_title": f"Episode {i}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Export all histories
        export_path = Path(temp_data_dir) / "export.json"
        manager.export_histories(str(export_path))
        
        assert export_path.exists()
        
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert len(exported_data["histories"]) == 3
        assert "export_date" in exported_data