import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class UserProfile:
    """מחלקה המייצגת פרופיל משתמש"""
    user_id: str
    name: str
    email: str
    created_at: datetime
    last_login: datetime
    preferences: Dict
    total_practice_time: int = 0
    completed_piyyutim: int = 0
    level: str = "מתחיל"

@dataclass
class LearningProgress:
    """מחלקה המייצגת התקדמות בלימוד"""
    piyyut_id: str
    practice_time: int
    completion_percentage: float
    last_practiced: datetime
    notes: List[str]
    mastery_level: str

class UserProfileManager:
    def __init__(self, db_path: str = "data/users.db"):
        """אתחול מנהל פרופילי משתמשים"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """יצירת טבלאות בבסיס הנתונים"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # טבלת משתמשים
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        preferences TEXT,
                        total_practice_time INTEGER DEFAULT 0,
                        completed_piyyutim INTEGER DEFAULT 0,
                        level TEXT DEFAULT 'מתחיל'
                    )
                ''')

                # טבלת התקדמות
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS learning_progress (
                        user_id TEXT,
                        piyyut_id TEXT,
                        practice_time INTEGER DEFAULT 0,
                        completion_percentage REAL DEFAULT 0,
                        last_practiced TIMESTAMP,
                        mastery_level TEXT DEFAULT 'מתחיל',
                        PRIMARY KEY (user_id, piyyut_id),
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')

                # טבלת הערות לימוד
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS learning_notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        piyyut_id TEXT,
                        note TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')

                # טבלת מועדפים
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS favorites (
                        user_id TEXT,
                        piyyut_id TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, piyyut_id),
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                ''')

                conn.commit()
                logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise

    def create_profile(self, user_data: Dict) -> Optional[str]:
        """יצירת פרופיל משתמש חדש"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (
                        user_id, name, email, password_hash, 
                        preferences
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data['name'],
                    user_data['email'],
                    user_data['password_hash'],
                    json.dumps(user_data.get('preferences', {}))
                ))
                conn.commit()
                logging.info(f"Created new profile for user {user_data['name']}")
                return user_data['user_id']
        except sqlite3.IntegrityError:
            logging.error(f"User with email {user_data['email']} already exists")
            return None
        except Exception as e:
            logging.error(f"Error creating profile: {e}")
            return None

    def update_profile(self, user_id: str, data: Dict) -> bool:
        """עדכון פרטי פרופיל"""
        try:
            updates = []
            params = []
            for key, value in data.items():
                if key in ['name', 'email', 'preferences', 'level']:
                    updates.append(f"{key} = ?")
                    params.append(value if key != 'preferences' else json.dumps(value))

            if not updates:
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                params.append(user_id)
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            return False

    def get_learning_progress(self, user_id: str) -> List[LearningProgress]:
        """קבלת התקדמות בלימוד"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.*, 
                           GROUP_CONCAT(n.note) as notes
                    FROM learning_progress p
                    LEFT JOIN learning_notes n 
                        ON p.user_id = n.user_id 
                        AND p.piyyut_id = n.piyyut_id
                    WHERE p.user_id = ?
                    GROUP BY p.piyyut_id
                ''', (user_id,))
                
                return [
                    LearningProgress(
                        piyyut_id=row[1],
                        practice_time=row[2],
                        completion_percentage=row[3],
                        last_practiced=datetime.fromisoformat(row[4]),
                        notes=row[6].split(',') if row[6] else [],
                        mastery_level=row[5]
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting learning progress: {e}")
            return []

    def get_favorite_piyyutim(self, user_id: str) -> List[str]:
        """קבלת פיוטים מועדפים"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT piyyut_id 
                    FROM favorites 
                    WHERE user_id = ?
                    ORDER BY added_at DESC
                ''', (user_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting favorites: {e}")
            return []

    def add_learning_note(self, user_id: str, piyyut_id: str, note: str) -> bool:
        """הוספת הערת לימוד"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_notes (user_id, piyyut_id, note)
                    VALUES (?, ?, ?)
                ''', (user_id, piyyut_id, note))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding learning note: {e}")
            return False

    def track_practice_time(self, user_id: str, piyyut_id: str, duration: int) -> bool:
        """מעקב אחר זמני תרגול"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # עדכון זמן תרגול לפיוט ספציפי
                cursor.execute('''
                    INSERT INTO learning_progress 
                        (user_id, piyyut_id, practice_time, last_practiced)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, piyyut_id) DO UPDATE SET
                        practice_time = practice_time + ?,
                        last_practiced = CURRENT_TIMESTAMP
                ''', (user_id, piyyut_id, duration, duration))
                
                # עדכון זמן תרגול כולל למשתמש
                cursor.execute('''
                    UPDATE users 
                    SET total_practice_time = total_practice_time + ?
                    WHERE user_id = ?
                ''', (duration, user_id))
                
                # עדכון רמת המשתמש בהתאם לזמן התרגול הכולל
                cursor.execute('''
                    UPDATE users SET level = 
                    CASE 
                        WHEN total_practice_time > 100000 THEN 'מומחה'
                        WHEN total_practice_time > 50000 THEN 'מתקדם'
                        WHEN total_practice_time > 10000 THEN 'בינוני'
                        ELSE 'מתחיל'
                    END
                    WHERE user_id = ?
                ''', (user_id,))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error tracking practice time: {e}")
            return False

    def get_user_stats(self, user_id: str) -> Dict:
        """קבלת סטטיסטיקות משתמש"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        total_practice_time,
                        completed_piyyutim,
                        level,
                        (SELECT COUNT(*) FROM favorites WHERE user_id = u.user_id) as favorites_count,
                        (SELECT COUNT(*) FROM learning_notes WHERE user_id = u.user_id) as notes_count
                    FROM users u
                    WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'total_practice_time': row[0],
                        'completed_piyyutim': row[1],
                        'level': row[2],
                        'favorites_count': row[3],
                        'notes_count': row[4]
                    }
                return {}
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return {}

# יצירת singleton
user_manager = UserProfileManager()