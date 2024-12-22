from pathlib import Path
import logging
import time
import os
import hashlib
import json
from typing import Optional, Dict, Union
import shutil

class CacheManager:
    def __init__(self, cache_dir: str = "data/cache"):
        """אתחול מנהל המטמון"""
        self.cache_dir = Path(cache_dir)
        self.max_cache_size = 1024 * 1024 * 1024  # 1GB
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """טעינת מטא-דאטה של המטמון"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading cache metadata: {e}")
        return {}
        
    def _save_metadata(self):
        """שמירת מטא-דאטה של המטמון"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving cache metadata: {e}")

    def cache_file(self, file_id: str, content: Union[bytes, str]) -> Optional[str]:
        """
        שמירת קובץ במטמון המקומי
        
        Args:
            file_id: מזהה הקובץ
            content: תוכן הקובץ (בינארי או טקסט)
            
        Returns:
            נתיב הקובץ במטמון או None אם נכשל
        """
        try:
            # בדיקת גודל המטמון לפני השמירה
            self._ensure_cache_size()
            
            # יצירת נתיב הקובץ במטמון
            cache_path = self.cache_dir / self._generate_cache_filename(file_id)
            
            # שמירת הקובץ
            write_mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(cache_path, write_mode) as f:
                f.write(content)
            
            # עדכון מטא-דאטה
            self.metadata[file_id] = {
                'path': str(cache_path),
                'size': os.path.getsize(cache_path),
                'cached_at': time.time(),
                'last_accessed': time.time()
            }
            self._save_metadata()
            
            return str(cache_path)
            
        except Exception as e:
            logging.error(f"Error caching file {file_id}: {e}")
            return None

    def get_cached_file(self, file_id: str) -> Optional[str]:
        """
        קבלת קובץ מהמטמון אם קיים
        
        Args:
            file_id: מזהה הקובץ
            
        Returns:
            נתיב הקובץ במטמון או None אם לא קיים
        """
        try:
            if file_id in self.metadata:
                cache_path = Path(self.metadata[file_id]['path'])
                if cache_path.exists():
                    # עדכון זמן גישה אחרון
                    self.metadata[file_id]['last_accessed'] = time.time()
                    self._save_metadata()
                    return str(cache_path)
                else:
                    # הסרת מטא-דאטה אם הקובץ לא קיים
                    del self.metadata[file_id]
                    self._save_metadata()
            return None
            
        except Exception as e:
            logging.error(f"Error getting cached file {file_id}: {e}")
            return None

    def clear_old_cache(self, max_age_hours: int = 24):
        """
        ניקוי קבצים ישנים מהמטמון
        
        Args:
            max_age_hours: גיל מקסימלי בשעות
        """
        try:
            current_time = time.time()
            files_to_remove = []
            
            for file_id, meta in self.metadata.items():
                # בדיקת גיל הקובץ
                file_age = current_time - meta['cached_at']
                if file_age > (max_age_hours * 3600):
                    # הסרת הקובץ
                    cache_path = Path(meta['path'])
                    if cache_path.exists():
                        cache_path.unlink()
                    files_to_remove.append(file_id)
            
            # עדכון מטא-דאטה
            for file_id in files_to_remove:
                del self.metadata[file_id]
            self._save_metadata()
            
            logging.info(f"Cleared {len(files_to_remove)} old cache files")
            
        except Exception as e:
            logging.error(f"Error clearing old cache: {e}")

    def _ensure_cache_size(self):
        """וידוא שגודל המטמון לא חורג מהמקסימום"""
        try:
            # חישוב גודל נוכחי
            current_size = sum(meta['size'] for meta in self.metadata.values())
            
            # הסרת קבצים ישנים אם צריך
            if current_size > self.max_cache_size:
                # מיון לפי זמן גישה אחרון
                sorted_files = sorted(
                    self.metadata.items(),
                    key=lambda x: x[1]['last_accessed']
                )
                
                # הסרת קבצים עד שנגיע לגודל הרצוי
                for file_id, meta in sorted_files:
                    if current_size <= self.max_cache_size:
                        break
                        
                    cache_path = Path(meta['path'])
                    if cache_path.exists():
                        current_size -= meta['size']
                        cache_path.unlink()
                        del self.metadata[file_id]
                
                self._save_metadata()
                
        except Exception as e:
            logging.error(f"Error managing cache size: {e}")

    def _generate_cache_filename(self, file_id: str) -> str:
        """יצירת שם קובץ במטמון"""
        # שימוש ב-hash כדי ליצור שם קובץ ייחודי
        return hashlib.md5(file_id.encode()).hexdigest() + '.cache'

    def get_cache_stats(self) -> Dict:
        """קבלת סטטיסטיקות על המטמון"""
        try:
            total_size = sum(meta['size'] for meta in self.metadata.values())
            return {
                'total_files': len(self.metadata),
                'total_size': total_size,
                'size_limit': self.max_cache_size,
                'usage_percent': (total_size / self.max_cache_size) * 100
            }
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return {}

    def clear_all_cache(self):
        """ניקוי כל המטמון"""
        try:
            # מחיקת כל הקבצים
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            # איפוס מטא-דאטה
            self.metadata = {}
            self._save_metadata()
            
            logging.info("Cache cleared successfully")
            
        except Exception as e:
            logging.error(f"Error clearing cache: {e}")

# יצירת singleton
cache_manager = CacheManager()