import sounddevice as sd
import soundfile as sf
import numpy as np
import librosa
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import sqlite3
from datetime import datetime
import threading
from queue import Queue

@dataclass
class RecordingMetadata:
    """מטא-דאטה של הקלטה"""
    id: str
    user_id: str
    piyyut_id: str
    duration: float
    sample_rate: int
    created_at: datetime
    file_path: str
    scores: Optional[Dict] = None

@dataclass
class AnalysisResult:
    """תוצאות ניתוח הקלטה"""
    pitch_accuracy: float
    rhythm_accuracy: float
    timing_offset: float
    confidence: float
    detailed_scores: Dict

class RecordingManager:
    def __init__(self, recordings_dir: str = "data/recordings"):
        """אתחול מנהל ההקלטות"""
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # הגדרות הקלטה
        self.sample_rate = 44100
        self.channels = 1
        
        # מצב נוכחי
        self.is_recording = False
        self.current_recording: Optional[np.ndarray] = None
        self.recording_stream = None
        self.audio_queue = Queue()
        
        # מסד נתונים
        self._init_db()

    def _init_db(self):
        """יצירת מסד נתונים להקלטות"""
        db_path = self.recordings_dir / "recordings.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    piyyut_id TEXT NOT NULL,
                    duration REAL,
                    sample_rate INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    scores TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (piyyut_id) REFERENCES piyyutim(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    recording_id TEXT,
                    original_id TEXT,
                    pitch_accuracy REAL,
                    rhythm_accuracy REAL,
                    timing_offset REAL,
                    confidence REAL,
                    detailed_scores TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recording_id) REFERENCES recordings(id),
                    FOREIGN KEY (original_id) REFERENCES piyyutim(id)
                )
            """)

    def start_recording(self) -> bool:
        """התחלת הקלטה"""
        if self.is_recording:
            return False
            
        try:
            def callback(indata, frames, time, status):
                """Callback שנקרא עבור כל חלק של ההקלטה"""
                if status:
                    logging.warning(f"Recording status: {status}")
                self.audio_queue.put(indata.copy())

            # פתיחת stream להקלטה
            self.recording_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback
            )
            self.recording_stream.start()
            self.is_recording = True
            logging.info("Started recording")
            return True
            
        except Exception as e:
            logging.error(f"Error starting recording: {e}")
            return False

    def stop_recording(self) -> Optional[np.ndarray]:
        """סיום הקלטה"""
        if not self.is_recording:
            return None
            
        try:
            self.recording_stream.stop()
            self.recording_stream.close()
            self.is_recording = False
            
            # איסוף כל חלקי ההקלטה
            chunks = []
            while not self.audio_queue.empty():
                chunks.append(self.audio_queue.get())
            
            self.current_recording = np.concatenate(chunks)
            logging.info("Stopped recording")
            return self.current_recording
            
        except Exception as e:
            logging.error(f"Error stopping recording: {e}")
            return None

    def save_recording(
        self,
        user_id: str,
        piyyut_id: str,
        recording_id: Optional[str] = None
    ) -> Optional[str]:
        """שמירת הקלטה"""
        if self.current_recording is None:
            return None
            
        try:
            # יצירת מזהה להקלטה
            recording_id = recording_id or f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # שמירת הקובץ
            file_path = self.recordings_dir / f"{recording_id}.wav"
            sf.write(file_path, self.current_recording, self.sample_rate)
            
            # יצירת מטא-דאטה
            metadata = RecordingMetadata(
                id=recording_id,
                user_id=user_id,
                piyyut_id=piyyut_id,
                duration=len(self.current_recording) / self.sample_rate,
                sample_rate=self.sample_rate,
                created_at=datetime.now(),
                file_path=str(file_path)
            )
            
            # שמירה במסד הנתונים
            self._save_metadata(metadata)
            
            logging.info(f"Saved recording {recording_id}")
            return recording_id
            
        except Exception as e:
            logging.error(f"Error saving recording: {e}")
            return None

    def compare_with_original(
        self,
        recording_id: str,
        original_id: str
    ) -> Optional[AnalysisResult]:
        """השוואה למקור"""
        try:
            # טעינת ההקלטות
            recording = self._load_recording(recording_id)
            original = self._load_recording(original_id)
            
            if recording is None or original is None:
                return None
                
            # ניתוח הקלטות
            pitch_accuracy = self.analyze_pitch_accuracy(recording_id)
            rhythm_accuracy = self.analyze_rhythm_accuracy(recording_id)
            
            # חישוב הזזת זמן
            y_rec, _ = librosa.load(recording.file_path)
            y_orig, _ = librosa.load(original.file_path)
            offset = self._calculate_time_offset(y_rec, y_orig)
            
            # חישוב ציון ביטחון
            confidence = self._calculate_confidence(
                pitch_accuracy, rhythm_accuracy
            )
            
            # ניתוח מפורט
            detailed_scores = self._analyze_detailed_comparison(
                y_rec, y_orig
            )
            
            result = AnalysisResult(
                pitch_accuracy=pitch_accuracy,
                rhythm_accuracy=rhythm_accuracy,
                timing_offset=offset,
                confidence=confidence,
                detailed_scores=detailed_scores
            )
            
            # שמירת תוצאות
            self._save_analysis_results(
                recording_id, original_id, result
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Error comparing recordings: {e}")
            return None

    def analyze_pitch_accuracy(self, recording_id: str) -> float:
        """ניתוח דיוק הפיץ'"""
        try:
            recording = self._load_recording(recording_id)
            if not recording:
                return 0.0
                
            y, sr = librosa.load(recording.file_path)
            
            # חילוץ תדירויות בסיסיות
            f0, voiced_flag, _ = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7')
            )
            
            # חישוב יציבות הפיץ'
            pitch_stability = np.mean(
                np.abs(np.diff(f0[voiced_flag])) < 1
            )
            
            # חישוב דיוק כללי
            accuracy = (pitch_stability * 100)
            return float(min(max(accuracy, 0), 100))
            
        except Exception as e:
            logging.error(f"Error analyzing pitch: {e}")
            return 0.0

    def analyze_rhythm_accuracy(self, recording_id: str) -> float:
        """ניתוח דיוק הקצב"""
        try:
            recording = self._load_recording(recording_id)
            if not recording:
                return 0.0
                
            y, sr = librosa.load(recording.file_path)
            
            # זיהוי פעימות
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # חישוב יציבות הקצב
            beat_intervals = np.diff(beats)
            rhythm_stability = np.std(beat_intervals)
            
            # נרמול לציון באחוזים
            max_deviation = 10  # הגדרת סטייה מקסימלית
            accuracy = max(0, 100 - (rhythm_stability / max_deviation * 100))
            
            return float(accuracy)
            
        except Exception as e:
            logging.error(f"Error analyzing rhythm: {e}")
            return 0.0

    def get_user_recordings(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[RecordingMetadata]:
        """קבלת הקלטות המשתמש"""
        try:
            db_path = self.recordings_dir / "recordings.db"
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM recordings 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                recordings = []
                for row in cursor.fetchall():
                    recordings.append(RecordingMetadata(
                        id=row[0],
                        user_id=row[1],
                        piyyut_id=row[2],
                        duration=row[3],
                        sample_rate=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        file_path=row[6],
                        scores=json.loads(row[7]) if row[7] else None
                    ))
                    
                return recordings
                
        except Exception as e:
            logging.error(f"Error getting user recordings: {e}")
            return []

    def _load_recording(self, recording_id: str) -> Optional[RecordingMetadata]:
        """טעינת מטא-דאטה של הקלטה"""
        try:
            db_path = self.recordings_dir / "recordings.db"
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    'SELECT * FROM recordings WHERE id = ?',
                    (recording_id,)
                )
                row = cursor.fetchone()
                if row:
                    return RecordingMetadata(
                        id=row[0],
                        user_id=row[1],
                        piyyut_id=row[2],
                        duration=row[3],
                        sample_rate=row[4],
                        created_at=datetime.fromisoformat(row[5]),
                        file_path=row[6],
                        scores=json.loads(row[7]) if row[7] else None
                    )
                return None
                
        except Exception as e:
            logging.error(f"Error loading recording: {e}")
            return None

    def _save_metadata(self, metadata: RecordingMetadata):
        """שמירת מטא-דאטה במסד הנתונים"""
        try:
            db_path = self.recordings_dir / "recordings.db"
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO recordings (
                        id, user_id, piyyut_id, duration,
                        sample_rate, created_at, file_path, scores
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.id,
                    metadata.user_id,
                    metadata.piyyut_id,
                    metadata.duration,
                    metadata.sample_rate,
                    metadata.created_at.isoformat(),
                    metadata.file_path,
                    json.dumps(metadata.scores) if metadata.scores else None
                ))
                
        except Exception as e:
            logging.error(f"Error saving metadata: {e}")

    def _calculate_time_offset(
        self,
        recording: np.ndarray,
        original: np.ndarray
    ) -> float:
        """חישוב הזזת זמן בין הקלטות"""
        correlation = np.correlate(recording, original, mode='full')
        max_correlation_idx = np.argmax(correlation)
        offset = (max_correlation_idx - len(original)) / self.sample_rate
        return offset

    def _calculate_confidence(
        self,
        pitch_accuracy: float,
        rhythm_accuracy: float
    ) -> float:
        """חישוב רמת הביטחון בניתוח"""
        # ממוצע משוקלל של הדיוקים
        weighted_accuracy = (0.6 * pitch_accuracy + 0.4 * rhythm_accuracy)
        
        # נרמול ל-0-1
        return float(weighted_accuracy / 100)
    
    def _analyze_detailed_comparison(
        self,
        recording: np.ndarray,
        original: np.ndarray
    ) -> Dict:
        """ניתוח מפורט של ההשוואה"""
        try:
            # חישוב מאפיינים שונים
            chroma_rec = librosa.feature.chroma_cqt(y=recording)
            chroma_orig = librosa.feature.chroma_cqt(y=original)
            
            mfcc_rec = librosa.feature.mfcc(y=recording)
            mfcc_orig = librosa.feature.mfcc(y=original)
            
            onset_env_rec = librosa.onset.onset_strength(y=recording)
            onset_env_orig = librosa.onset.onset_strength(y=original)
            
            return {
                'tonal_similarity': float(
                    np.mean(
                        np.correlate(
                            chroma_rec.flatten(),
                            chroma_orig.flatten()
                        )
                    )
                ),
                'timbre_similarity': float(
                    np.mean(
                        np.correlate(
                            mfcc_rec.flatten(),
                            mfcc_orig.flatten()
                        )
                    )
                ),
                'rhythm_similarity': float(
                    np.mean(
                        np.correlate(
                            onset_env_rec,
                            onset_env_orig
                        )
                    )
                ),
                'spectral_contrast': {
                    'recording': float(
                        np.mean(
                            librosa.feature.spectral_contrast(y=recording)
                        )
                    ),
                    'original': float(
                        np.mean(
                            librosa.feature.spectral_contrast(y=original)
                        )
                    )
                },
                'tempo_difference': float(
                    abs(
                        librosa.beat.tempo(y=recording)[0] -
                        librosa.beat.tempo(y=original)[0]
                    )
                ),
                'dynamic_range': {
                    'recording': float(
                        np.percentile(np.abs(recording), 95) -
                        np.percentile(np.abs(recording), 5)
                    ),
                    'original': float(
                        np.percentile(np.abs(original), 95) -
                        np.percentile(np.abs(original), 5)
                    )
                }
            }
            
        except Exception as e:
            logging.error(f"Error in detailed comparison: {e}")
            return {
                'error': str(e),
                'tonal_similarity': 0.0,
                'timbre_similarity': 0.0,
                'rhythm_similarity': 0.0,
                'spectral_contrast': {'recording': 0.0, 'original': 0.0},
                'tempo_difference': 0.0,
                'dynamic_range': {'recording': 0.0, 'original': 0.0}
            }

    def _save_analysis_results(
        self,
        recording_id: str,
        original_id: str,
        results: AnalysisResult
    ):
        """שמירת תוצאות הניתוח"""
        try:
            db_path = self.recordings_dir / "recordings.db"
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO analysis_results (
                        recording_id, original_id,
                        pitch_accuracy, rhythm_accuracy,
                        timing_offset, confidence,
                        detailed_scores
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    recording_id,
                    original_id,
                    results.pitch_accuracy,
                    results.rhythm_accuracy,
                    results.timing_offset,
                    results.confidence,
                    json.dumps(results.detailed_scores)
                ))
                
        except Exception as e:
            logging.error(f"Error saving analysis results: {e}")

# יצירת singleton
recording_manager = RecordingManager()