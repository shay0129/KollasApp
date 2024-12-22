from urllib.parse import urlparse, parse_qs, urlencode
from typing import Dict, Optional, Union
import re
import logging
import json
from pathlib import Path
import time

class URLTransformer:
    """מחלקה לטיפול בקישורים של Google Drive"""
    
    @staticmethod
    def transform_drive_url(url: str) -> str:
        """
        המרת URL של Google Drive לקישור הורדה ישיר
        
        Args:
            url: קישור המקור של Google Drive
            
        Returns:
            קישור מותאם להורדה ישירה
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # הסרת פרמטרים לא רצויים
            params_to_remove = ['view', 'open', 'usp']
            for param in params_to_remove:
                query_params.pop(param, None)
            
            # הוספת פרמטרים נדרשים
            query_params.update({
                'export': ['download'],
                'confirm': ['t']
            })
            
            # בניית ה-URL החדש
            new_query = urlencode(query_params, doseq=True)
            return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
            
        except Exception as e:
            logging.error(f"Error transforming URL: {e}")
            return url

class FileManager:
    """מחלקה לניהול קבצים"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """קבלת סיומת הקובץ"""
        return Path(filename).suffix.lower()

    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """בדיקה האם הקובץ הוא קובץ שמע"""
        audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        return FileManager.get_file_extension(filename) in audio_extensions

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ניקוי שם קובץ מתווים לא חוקיים"""
        invalid_chars = r'[<>:"/\\|?*]'
        return re.sub(invalid_chars, '_', filename)

class DataManager:
    """מחלקה לניהול נתונים"""
    
    @staticmethod
    def load_json(file_path: str) -> Optional[Dict]:
        """טעינת קובץ JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading JSON file: {e}")
            return None

    @staticmethod
    def save_json(data: Dict, file_path: str) -> bool:
        """שמירת נתונים לקובץ JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving JSON file: {e}")
            return False

class TimeManager:
    """מחלקה לניהול זמנים"""
    
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """המרת משך זמן בשניות לפורמט מתאים"""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def get_timestamp() -> str:
        """קבלת חותמת זמן נוכחית"""
        return time.strftime("%Y-%m-%d %H:%M:%S")

# יצירת אובייקטים גלובליים לשימוש
url_transformer = URLTransformer()
file_manager = FileManager()
data_manager = DataManager()
time_manager = TimeManager()

# פונקציות מעטפת לתאימות לאחור
def transform_google_drive_url(url: str) -> str:
    """פונקציית מעטפת לתאימות עם הקוד הישן"""
    return url_transformer.transform_drive_url(url)