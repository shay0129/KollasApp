import time
import logging
from typing import Dict, Optional, List
from pathlib import Path
import json
from services.google_services import drive_service

class DriveSync:
    def __init__(self, cache_dir: str = "data/sync_cache"):
        self.last_sync = None
        self.metadata_cache: Dict = {}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sync_interval = 300  # 5 minutes
        self._load_cache()

    def _load_cache(self):
        """טעינת מטמון מהדיסק"""
        cache_file = self.cache_dir / "metadata_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.metadata_cache = json.load(f)
                logging.info("Metadata cache loaded successfully")
            except Exception as e:
                logging.error(f"Error loading metadata cache: {e}")

    def _save_cache(self):
        """שמירת מטמון לדיסק"""
        try:
            cache_file = self.cache_dir / "metadata_cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving metadata cache: {e}")

    async def sync_metadata(self, folder_id: Optional[str] = None) -> bool:
        """סנכרון מטא-דאטה של קבצים"""
        try:
            current_time = time.time()
            
            # בדיקה האם צריך סנכרון
            if (self.last_sync and 
                current_time - self.last_sync < self.sync_interval):
                return True

            # קבלת מידע מעודכן מ-Drive
            files = await drive_service.get_folder_contents(folder_id)
            
            # עדכון המטמון
            for file in files:
                file_id = file['id']
                self.metadata_cache[file_id] = {
                    'metadata': file,
                    'last_sync': current_time
                }

            self.last_sync = current_time
            self._save_cache()
            logging.info("Metadata synced successfully")
            return True

        except Exception as e:
            logging.error(f"Error syncing metadata: {e}")
            return False

    async def check_updates(self) -> List[Dict]:
        """בדיקת עדכונים בדרייב"""
        try:
            updates = []
            current_time = time.time()

            # סנכרון אם צריך
            if not self.last_sync or (
                current_time - self.last_sync > self.sync_interval
            ):
                await self.sync_metadata()

            # בדיקת קבצים מעודכנים
            files = await drive_service.get_folder_contents(None)
            for file in files:
                file_id = file['id']
                cached = self.metadata_cache.get(file_id)

                if not cached or (
                    file.get('modifiedTime', '') > 
                    cached['metadata'].get('modifiedTime', '')
                ):
                    updates.append({
                        'type': 'modified' if cached else 'new',
                        'file': file
                    })

            return updates

        except Exception as e:
            logging.error(f"Error checking updates: {e}")
            return []

    async def download_if_needed(self, file_id: str) -> Optional[str]:
        """הורדת קובץ רק אם צריך"""
        try:
            # בדיקה במטמון
            cached_file = drive_service.cache_manager.get_cached_file(file_id)
            if cached_file:
                # בדיקת גיל הקובץ במטמון
                cache_age = time.time() - Path(cached_file).stat().st_mtime
                if cache_age < self.sync_interval:
                    return cached_file

            # בדיקת עדכונים בדרייב
            file_metadata = await drive_service.get_file_metadata(file_id)
            if not file_metadata:
                return None

            cached_metadata = self.metadata_cache.get(file_id)
            if cached_metadata and (
                cached_metadata['metadata'].get('modifiedTime') ==
                file_metadata.get('modifiedTime')
            ):
                return cached_file

            # הורדת הקובץ אם צריך
            return await drive_service.get_file(file_id)

        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            return None

    def get_sync_status(self) -> Dict:
        """קבלת סטטוס סנכרון"""
        return {
            'last_sync': self.last_sync,
            'cache_size': len(self.metadata_cache),
            'cache_age': time.time() - (self.last_sync or 0)
        }

# יצירת singleton
drive_sync = DriveSync()