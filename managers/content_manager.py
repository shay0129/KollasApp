# content_manager.py
import sqlite3
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PiyyutMetadata:
    """מחלקה המייצגת מידע על פיוט"""
    id: str
    name: str
    hebrew_text: str
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    occasions: List[str] = None
    audio_file: Optional[str] = None
    description: Optional[str] = None
    sheet_music: Optional[str] = None
    difficulty_level: Optional[str] = None
    duration: Optional[int] = None
    tags: List[str] = None

class ContentManager:
    def __init__(self, db_path: str = "kollas_content.db"):
        """אתחול מנהל התוכן"""
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """יצירת מסד הנתונים וטבלאות"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS piyyutim (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    hebrew_text TEXT NOT NULL,
                    transliteration TEXT,
                    translation TEXT,
                    occasions TEXT,
                    audio_file TEXT,
                    description TEXT,
                    sheet_music TEXT,
                    difficulty_level TEXT,
                    duration INTEGER,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id TEXT,
                    piyyut_id TEXT,
                    last_played TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    completion_percentage INTEGER DEFAULT 0,
                    is_favorite BOOLEAN DEFAULT 0,
                    notes TEXT,
                    PRIMARY KEY (user_id, piyyut_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    piyyutim_list TEXT,
                    difficulty TEXT,
                    estimated_duration INTEGER
                )
            """)

    def add_piyyut(self, piyyut: PiyyutMetadata) -> bool:
        """הוספת פיוט חדש למסד הנתונים"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO piyyutim (
                        id, name, hebrew_text, transliteration, translation,
                        occasions, audio_file, description, sheet_music,
                        difficulty_level, duration, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    piyyut.id, piyyut.name, piyyut.hebrew_text,
                    piyyut.transliteration, piyyut.translation,
                    json.dumps(piyyut.occasions), piyyut.audio_file,
                    piyyut.description, piyyut.sheet_music,
                    piyyut.difficulty_level, piyyut.duration,
                    json.dumps(piyyut.tags)
                ))
                return True
        except Exception as e:
            logging.error(f"Error adding piyyut: {e}")
            return False

    def get_piyyut(self, piyyut_id: str) -> Optional[PiyyutMetadata]:
        """קבלת מידע על פיוט ספציפי"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM piyyutim WHERE id = ?", (piyyut_id,))
                row = cursor.fetchone()
                if row:
                    return PiyyutMetadata(
                        id=row[0],
                        name=row[1],
                        hebrew_text=row[2],
                        transliteration=row[3],
                        translation=row[4],
                        occasions=json.loads(row[5]) if row[5] else [],
                        audio_file=row[6],
                        description=row[7],
                        sheet_music=row[8],
                        difficulty_level=row[9],
                        duration=row[10],
                        tags=json.loads(row[11]) if row[11] else []
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting piyyut: {e}")
            return None

    def search_piyyutim(self, query: str) -> List[PiyyutMetadata]:
        """חיפוש פיוטים לפי טקסט חופשי"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM piyyutim 
                    WHERE name LIKE ? OR hebrew_text LIKE ? 
                    OR transliteration LIKE ? OR tags LIKE ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
                return [PiyyutMetadata(*row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error searching piyyutim: {e}")
            return []

    def update_user_progress(
        self, 
        user_id: str, 
        piyyut_id: str, 
        completion: int = None,
        is_favorite: bool = None,
        notes: str = None
    ):
        """עדכון התקדמות המשתמש"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # עדכון או יצירת רשומה חדשה
                conn.execute("""
                    INSERT INTO user_progress (user_id, piyyut_id, last_played, play_count)
                    VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                    ON CONFLICT(user_id, piyyut_id) DO UPDATE SET
                        last_played = CURRENT_TIMESTAMP,
                        play_count = play_count + 1
                """, (user_id, piyyut_id))
                
                # עדכון שדות נוספים אם סופקו
                if any(x is not None for x in [completion, is_favorite, notes]):
                    updates = []
                    params = []
                    if completion is not None:
                        updates.append("completion_percentage = ?")
                        params.append(completion)
                    if is_favorite is not None:
                        updates.append("is_favorite = ?")
                        params.append(is_favorite)
                    if notes is not None:
                        updates.append("notes = ?")
                        params.append(notes)
                    
                    if updates:
                        query = f"""
                            UPDATE user_progress 
                            SET {', '.join(updates)}
                            WHERE user_id = ? AND piyyut_id = ?
                        """
                        params.extend([user_id, piyyut_id])
                        conn.execute(query, params)
                
                return True
        except Exception as e:
            logging.error(f"Error updating user progress: {e}")
            return False

    def get_recommended_piyyutim(self, user_id: str) -> List[PiyyutMetadata]:
        """קבלת המלצות מותאמות אישית"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # מציאת פיוטים דומים לאלו שהמשתמש אהב
                cursor = conn.execute("""
                    SELECT p.* FROM piyyutim p
                    JOIN user_progress up1 ON p.id = up1.piyyut_id
                    WHERE up1.user_id = ? AND up1.is_favorite = 1
                    AND p.id NOT IN (
                        SELECT piyyut_id FROM user_progress
                        WHERE user_id = ?
                    )
                    ORDER BY up1.play_count DESC
                    LIMIT 5
                """, (user_id, user_id))
                return [PiyyutMetadata(*row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting recommendations: {e}")
            return []

    def get_learning_paths(self) -> List[Dict[str, Any]]:
        """קבלת מסלולי למידה"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM learning_paths")
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'piyyutim_list': json.loads(row[3]),
                        'difficulty': row[4],
                        'estimated_duration': row[5]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting learning paths: {e}")
            return []

# יצירת singleton
content_manager = ContentManager()