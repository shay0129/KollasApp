import sqlite3
import shutil
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "data/kollas.db"):
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.connection_pool: List[sqlite3.Connection] = []
        self.max_connections = 5
        self.initialized = False
        
        self._init_db()

    def initialize_tables(self):
        """יצירת טבלאות הנדרשות"""
        try:
            with self._get_connection() as conn:
                # טבלת גרסאות
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS db_versions (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                ''')
                
                # טבלת מטריקות ביצועים
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_type TEXT NOT NULL,
                        execution_time REAL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # טבלת מעקב חיבורים
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS connection_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        disconnected_at TIMESTAMP,
                        error TEXT
                    )
                ''')
                
                # הוספת אינדקסים
                self._create_indexes(conn)
                
                return True
        except Exception as e:
            logging.error(f"Error initializing tables: {e}")
            return False

    def backup_database(self) -> bool:
        """גיבוי בסיס הנתונים"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"kollas_backup_{timestamp}.db"
            
            # ניקוי גיבויים ישנים
            self._cleanup_old_backups()
            
            # יצירת גיבוי
            with self._get_connection() as conn:
                # ביצוע VACUUM לפני הגיבוי
                conn.execute('VACUUM')
            
            shutil.copy2(self.db_path, backup_path)
            
            # בדיקת תקינות הגיבוי
            with sqlite3.connect(backup_path) as conn:
                cursor = conn.cursor()
                cursor.execute('PRAGMA integrity_check')
                if cursor.fetchone()[0] != 'ok':
                    raise Exception("Backup integrity check failed")
                    
            logging.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return False

    def optimize_performance(self) -> bool:
        """אופטימיזציה של ביצועי בסיס הנתונים"""
        try:
            with self._get_connection() as conn:
                # ביצוע אנליזה
                conn.execute('ANALYZE')
                
                # עדכון סטטיסטיקות
                conn.execute('ANALYZE sqlite_master')
                
                # אופטימיזציה של אינדקסים
                self._optimize_indexes(conn)
                
                # ניקוי וארגון מחדש
                conn.execute('VACUUM')
                
                # בדיקת ומחיקת מידע זמני
                self._cleanup_temp_data(conn)
                
                return True
        except Exception as e:
            logging.error(f"Error optimizing database: {e}")
            return False

    def manage_connections(self) -> Dict:
        """ניהול חיבורים וסטטיסטיקות"""
        try:
            with self._get_connection() as conn:
                # קבלת סטטיסטיקות חיבורים
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_connections,
                        SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as error_count,
                        AVG(CASE 
                            WHEN disconnected_at IS NOT NULL 
                            THEN julianday(disconnected_at) - julianday(connected_at) 
                            ELSE NULL 
                        END) * 86400 as avg_connection_time
                    FROM connection_log 
                    WHERE connected_at >= datetime('now', '-1 day')
                ''')
                stats = dict(cursor.fetchone())
                
                # ניקוי רשומות ישנות
                conn.execute('''
                    DELETE FROM connection_log 
                    WHERE connected_at < datetime('now', '-7 days')
                ''')
                
                return stats
        except Exception as e:
            logging.error(f"Error managing connections: {e}")
            return {}

    def handle_migrations(self) -> bool:
        """טיפול בשדרוגי מבנה"""
        try:
            with self._get_connection() as conn:
                # בדיקת גרסה נוכחית
                cursor = conn.execute(
                    'SELECT MAX(version) FROM db_versions'
                )
                current_version = cursor.fetchone()[0] or 0
                
                # הרצת שדרוגים נדרשים
                migrations = self._get_migrations()
                for version, migration in migrations.items():
                    if version > current_version:
                        # יצירת טבלה זמנית לגיבוי
                        conn.execute(migration['backup'])
                        
                        try:
                            # הרצת השדרוג
                            conn.execute(migration['upgrade'])
                            
                            # עדכון גרסה
                            conn.execute('''
                                INSERT INTO db_versions (version, description) 
                                VALUES (?, ?)
                            ''', (version, migration['description']))
                            
                        except Exception as e:
                            # שחזור מגיבוי במקרה של שגיאה
                            conn.execute(migration['rollback'])
                            raise
                
                return True
                
        except Exception as e:
            logging.error(f"Error handling migrations: {e}")
            return False

    def _get_migrations(self) -> Dict:
        """הגדרת שדרוגי מבנה אפשריים"""
        return {
            1: {
                'description': 'Add user preferences column',
                'backup': 'CREATE TABLE users_backup AS SELECT * FROM users',
                'upgrade': 'ALTER TABLE users ADD COLUMN preferences TEXT',
                'rollback': '''
                    DROP TABLE users;
                    ALTER TABLE users_backup RENAME TO users;
                '''
            },
            2: {
                'description': 'Add indices for performance',
                'backup': '',  # אין צורך בגיבוי לאינדקסים
                'upgrade': '''
                    CREATE INDEX IF NOT EXISTS idx_piyyutim_search 
                    ON piyyutim(name, hebrew_text);
                ''',
                'rollback': 'DROP INDEX IF EXISTS idx_piyyutim_search'
            }
            # ניתן להוסיף עוד שדרוגים כאן
        }

    def _create_indexes(self, conn: sqlite3.Connection):
        """יצירת אינדקסים לשיפור ביצועים"""
        indexes = [
            ('idx_performance_recorded', 'performance_metrics(recorded_at)'),
            ('idx_connections_time', 'connection_log(connected_at, disconnected_at)'),
            # הוסף אינדקסים נוספים כאן
        ]
        
        for index_name, index_def in indexes:
            conn.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')

    def _optimize_indexes(self, conn: sqlite3.Connection):
        """אופטימיזציה של אינדקסים"""
        conn.execute('ANALYZE sqlite_master')
        # ניתן להוסיף אופטימיזציות נוספות

    def _cleanup_temp_data(self, conn: sqlite3.Connection):
        """ניקוי נתונים זמניים"""
        # מחיקת רשומות ישנות מטבלאות לוג
        week_ago = datetime.now() - timedelta(days=7)
        conn.execute(
            'DELETE FROM performance_metrics WHERE recorded_at < ?', 
            (week_ago,)
        )

    @contextmanager
    def _get_connection(self):
        """ניהול חיבורים עם context manager"""
        connection = None
        try:
            if self.connection_pool:
                connection = self.connection_pool.pop()
            else:
                connection = sqlite3.connect(self.db_path)
                connection.row_factory = sqlite3.Row
            
            yield connection
            
        finally:
            if connection:
                if len(self.connection_pool) < self.max_connections:
                    self.connection_pool.append(connection)
                else:
                    connection.close()

    def _cleanup_old_backups(self):
        """ניקוי גיבויים ישנים"""
        backups = sorted(
            self.backup_dir.glob("kollas_backup_*.db"),
            key=lambda x: x.stat().st_mtime
        )
        # שמירת 7 גיבויים אחרונים
        while len(backups) > 7:
            backups[0].unlink()
            backups.pop(0)

# יצירת singleton
db_manager = DatabaseManager()