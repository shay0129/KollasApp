import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import librosa
import numpy as np
from pathlib import Path
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor

@dataclass
class LyricTiming:
    """מחלקה המייצגת תזמון של מילה בודדת"""
    word: str
    start_time: float
    end_time: float
    is_highlighted: bool = False

class KaraokeDisplay(QWidget):
    """תצוגת קריוקי מותאמת אישית"""
    
    # אותות מותאמים
    wordClicked = pyqtSignal(str)  # נשלח כשלוחצים על מילה
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.current_line = 0
        self.words: List[LyricTiming] = []
        
    def _setup_ui(self):
        """הגדרת ממשק המשתמש"""
        layout = QVBoxLayout(self)
        
        # אזור גלילה לטקסט
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # מיכל למילים
        self.text_container = QWidget()
        self.text_layout = QVBoxLayout(self.text_container)
        
        scroll.setWidget(self.text_container)
        layout.addWidget(scroll)
        
    def set_lyrics(self, lyrics: List[LyricTiming]):
        """הגדרת מילות השיר"""
        self.words = lyrics
        self._refresh_display()
        
    def highlight_word(self, time: float):
        """הדגשת מילה לפי זמן"""
        for word in self.words:
            if word.start_time <= time <= word.end_time:
                word.is_highlighted = True
            else:
                word.is_highlighted = False
        self._refresh_display()
        
    def _refresh_display(self):
        """רענון תצוגת המילים"""
        # ניקוי תצוגה קודמת
        for i in reversed(range(self.text_layout.count())): 
            self.text_layout.itemAt(i).widget().setParent(None)
            
        # הוספת תוויות חדשות
        for word in self.words:
            label = QLabel(word.word)
            if word.is_highlighted:
                palette = label.palette()
                palette.setColor(QPalette.WindowText, QColor("#FF0000"))
                label.setPalette(palette)
            label.mousePressEvent = lambda _, w=word.word: self.wordClicked.emit(w)
            self.text_layout.addWidget(label)

class KaraokeManager:
    def __init__(self):
        """אתחול מנהל הקריוקי"""
        self.timing_cache = {}  # מטמון לנתוני תזמון
        self.display = KaraokeDisplay()
        
    def initialize_lyrics_timing(
        self,
        audio_file: str,
        lyrics: str
    ) -> List[LyricTiming]:
        """יצירת מיפוי בין המילים לזמנים"""
        try:
            # טעינת הקובץ
            y, sr = librosa.load(audio_file)
            
            # זיהוי התחלות וסופי מילים
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            onset_frames = librosa.onset.onset_detect(
                onset_envelope=onset_env,
                sr=sr
            )
            
            # המרת מסגרות לזמנים
            onset_times = librosa.frames_to_time(onset_frames)
            
            # פיצול המילים
            words = lyrics.split()
            
            # יצירת תזמון למילים
            word_timings = []
            for i, word in enumerate(words):
                if i < len(onset_times) - 1:
                    timing = LyricTiming(
                        word=word,
                        start_time=float(onset_times[i]),
                        end_time=float(onset_times[i + 1])
                    )
                    word_timings.append(timing)
            
            # שמירה במטמון
            cache_key = f"{audio_file}_{hash(lyrics)}"
            self.timing_cache[cache_key] = word_timings
            
            return word_timings
            
        except Exception as e:
            logging.error(f"Error initializing lyrics timing: {e}")
            return []

    def sync_lyrics_with_audio(self, current_time: float) -> str:
        """החזרת המילים המתאימות לזמן הנוכחי"""
        try:
            self.display.highlight_word(current_time)
            
            # מציאת המילה הנוכחית
            current_word = None
            for word in self.display.words:
                if word.start_time <= current_time <= word.end_time:
                    current_word = word.word
                    break
                    
            return current_word or ""
            
        except Exception as e:
            logging.error(f"Error syncing lyrics: {e}")
            return ""

    def highlight_current_word(self, timestamp: float):
        """הדגשת המילה הנוכחית"""
        self.display.highlight_word(timestamp)

    def display_lyrics_view(self) -> QWidget:
        """הצגת ממשק הקריוקי"""
        return self.display

    def export_timing_data(self, file_path: str) -> bool:
        """שמירת נתוני התזמון"""
        try:
            timing_data = [
                {
                    'word': word.word,
                    'start_time': word.start_time,
                    'end_time': word.end_time
                }
                for word in self.display.words
            ]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(timing_data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            logging.error(f"Error exporting timing data: {e}")
            return False

    def import_timing_data(self, file_path: str) -> bool:
        """טעינת נתוני תזמון קיימים"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                timing_data = json.load(f)
                
            words = [
                LyricTiming(
                    word=item['word'],
                    start_time=item['start_time'],
                    end_time=item['end_time']
                )
                for item in timing_data
            ]
            
            self.display.set_lyrics(words)
            return True
            
        except Exception as e:
            logging.error(f"Error importing timing data: {e}")
            return False

    def adjust_timing(
        self,
        word_index: int,
        new_start: float,
        new_end: float
    ) -> bool:
        """התאמה ידנית של תזמון"""
        try:
            if 0 <= word_index < len(self.display.words):
                word = self.display.words[word_index]
                word.start_time = new_start
                word.end_time = new_end
                self.display.set_lyrics(self.display.words)
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error adjusting timing: {e}")
            return False

    def get_word_at_time(self, timestamp: float) -> Optional[str]:
        """קבלת המילה בזמן מסוים"""
        for word in self.display.words:
            if word.start_time <= timestamp <= word.end_time:
                return word.word
        return None

# יצירת singleton
karaoke_manager = KaraokeManager()