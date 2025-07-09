"""
Data management module for persisting podcast processing history
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)


class DataError(Exception):
    """Raised when data operations fail"""
    pass


class DataManager:
    """
    Manages data persistence for podcast processing history
    """
    
    def __init__(self, data_dir: str = "./data", max_histories: int = 10):
        """
        Initialize DataManager
        
        Args:
            data_dir: Directory to store data files
            max_histories: Maximum number of histories to keep
        """
        self.data_dir = Path(data_dir)
        self.max_histories = max_histories
        
        # Create data directory
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise DataError(f"Permission denied: Cannot create data directory at {self.data_dir}")
        except Exception as e:
            raise DataError(f"Failed to create data directory: {e}")
    
    def save_history(self, data: Dict[str, Any]) -> str:
        """
        Save processing history
        
        Args:
            data: History data to save
            
        Returns:
            History ID
        """
        # Generate unique ID
        history_id = str(uuid.uuid4())
        
        # Add metadata
        data['id'] = history_id
        data['timestamp'] = data.get('timestamp', datetime.now().isoformat())
        
        # Save to file
        file_path = self.data_dir / f"history_{history_id}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise DataError(f"Failed to save history: {e}")
        
        # Clean up old histories
        self._cleanup_old_histories()
        
        return history_id
    
    def load_history(self, history_id: str) -> Optional[Dict[str, Any]]:
        """
        Load history by ID
        
        Args:
            history_id: History ID to load
            
        Returns:
            History data or None if not found
        """
        file_path = self.data_dir / f"history_{history_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Corrupted JSON file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return None
    
    def get_all_histories(self) -> List[Dict[str, Any]]:
        """
        Get all histories sorted by timestamp (newest first)
        
        Returns:
            List of history data
        """
        histories = []
        
        # Read all history files
        for file_path in self.data_dir.glob("history_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    histories.append(history)
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        histories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return histories
    
    def get_recent_titles(self, limit: int = 5) -> List[str]:
        """
        Get recent titles for style learning
        
        Args:
            limit: Number of titles to return
            
        Returns:
            List of recent titles
        """
        histories = self.get_all_histories()
        titles = []
        
        for history in histories:
            if 'titles' in history and isinstance(history['titles'], list):
                titles.extend(history['titles'])
                if len(titles) >= limit:
                    break
        
        return titles[:limit]
    
    def get_recent_descriptions(self, limit: int = 5) -> List[str]:
        """
        Get recent descriptions for style learning
        
        Args:
            limit: Number of descriptions to return
            
        Returns:
            List of recent descriptions
        """
        histories = self.get_all_histories()
        descriptions = []
        
        for history in histories:
            if 'description' in history and history['description']:
                descriptions.append(history['description'])
                if len(descriptions) >= limit:
                    break
        
        return descriptions[:limit]
    
    def export_histories(self, export_path: str) -> None:
        """
        Export all histories to a single file
        
        Args:
            export_path: Path to export file
        """
        histories = self.get_all_histories()
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'histories': histories
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise DataError(f"Failed to export histories: {e}")
    
    def _cleanup_old_histories(self) -> None:
        """
        Remove old histories to keep only the most recent ones
        """
        histories = self.get_all_histories()
        
        if len(histories) <= self.max_histories:
            return
        
        # Keep only the most recent histories
        histories_to_remove = histories[self.max_histories:]
        
        for history in histories_to_remove:
            history_id = history.get('id')
            if history_id:
                file_path = self.data_dir / f"history_{history_id}.json"
                try:
                    file_path.unlink()
                    logger.info(f"Removed old history: {history_id}")
                except Exception as e:
                    logger.error(f"Failed to remove history {history_id}: {e}")