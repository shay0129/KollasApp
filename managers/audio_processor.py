import numpy as np
from scipy.io import wavfile
from scipy import signal
import librosa
import soundfile as sf
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class AudioMetadata:
    """מטה-דאטה של קובץ שמע"""
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    format: str
    size_bytes: int

@dataclass
class TimingData:
    """נתוני תזמון לסנכרון מילים"""
    start_time: float
    end_time: float
    confidence: float

class AudioProcessor:
    def __init__(self, cache_dir: str = "data/audio_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # הגדרות ברירת מחדל
        self.target_sample_rate = 44100
        self.target_channels = 1
        self.min_silence_length = 0.3
        self.silence_threshold = -40

    def analyze_audio(self, file_path: str) -> Dict:
        """ניתוח קובץ שמע והחזרת נתונים"""
        try:
            # טעינת הקובץ
            y, sr = librosa.load(file_path)
            
            # חישוב מאפיינים
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            rms = librosa.feature.rms(y=y)
            
            return {
                'duration': librosa.get_duration(y=y, sr=sr),
                'tempo': float(tempo),
                'beats_locations': beats.tolist(),
                'average_volume': float(np.mean(rms)),
                'pitch_profile': np.mean(chroma, axis=1).tolist()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing audio: {e}")
            return {}

    def extract_timing_data(
        self,
        audio_path: str,
        text: str
    ) -> List[TimingData]:
        """חילוץ נתוני תזמון לסנכרון מילים"""
        try:
            y, sr = librosa.load(audio_path)
            
            # זיהוי מקטעי שקט
            intervals = librosa.effects.split(
                y,
                top_db=self.silence_threshold,
                frame_length=int(sr * self.min_silence_length)
            )
            
            # יצירת נתוני תזמון
            words = text.split()
            timing_data = []
            
            for i, (start, end) in enumerate(intervals):
                if i >= len(words):
                    break
                    
                timing_data.append(TimingData(
                    start_time=float(start) / sr,
                    end_time=float(end) / sr,
                    confidence=self._calculate_confidence(y[start:end])
                ))
                
            return timing_data
            
        except Exception as e:
            logging.error(f"Error extracting timing data: {e}")
            return []

    def normalize_volume(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        target_db: float = -20.0
    ) -> Optional[str]:
        """נרמול עוצמת השמע"""
        try:
            # טעינת הקובץ
            y, sr = librosa.load(input_path)
            
            # חישוב העוצמה הנוכחית
            current_db = librosa.amplitude_to_db(
                np.abs(y), ref=np.max
            ).mean()
            
            # חישוב פקטור ההגברה
            db_change = target_db - current_db
            scaling_factor = 10 ** (db_change / 20.0)
            
            # נרמול
            y_normalized = y * scaling_factor
            
            # שמירה
            output_path = output_path or str(
                self.cache_dir / f"normalized_{Path(input_path).name}"
            )
            sf.write(output_path, y_normalized, sr)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error normalizing volume: {e}")
            return None

    def improve_quality(
        self,
        input_path: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """שיפור איכות השמע"""
        try:
            # טעינת הקובץ
            y, sr = librosa.load(input_path)
            
            # הפחתת רעש
            y_denoised = self._reduce_noise(y)
            
            # איזון תדרים
            y_eq = self._apply_eq(y_denoised)
            
            # הגברת הבהירות
            y_enhanced = self._enhance_clarity(y_eq)
            
            # שמירה
            output_path = output_path or str(
                self.cache_dir / f"enhanced_{Path(input_path).name}"
            )
            sf.write(output_path, y_enhanced, sr)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error improving audio quality: {e}")
            return None

    def convert_format(
        self,
        input_path: str,
        target_format: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """המרת פורמט הקובץ"""
        try:
            # טעינת הקובץ
            y, sr = librosa.load(input_path)
            
            # הגדרת נתיב פלט
            output_path = output_path or str(
                self.cache_dir / f"converted_{Path(input_path).stem}.{target_format}"
            )
            
            # המרה ושמירה
            if target_format.lower() == 'wav':
                sf.write(output_path, y, sr, subtype='PCM_16')
            elif target_format.lower() in ['mp3', 'ogg', 'flac']:
                sf.write(output_path, y, sr, format=target_format)
            else:
                raise ValueError(f"Unsupported format: {target_format}")
                
            return output_path
            
        except Exception as e:
            logging.error(f"Error converting format: {e}")
            return None

    def _reduce_noise(self, y: np.ndarray) -> np.ndarray:
        """הפחתת רעש"""
        # חישוב פרופיל רעש
        noise_profile = np.mean(
            librosa.decompose.nn_filter(y),
            axis=1, keepdims=True
        )
        # הפחתת הרעש
        return y - noise_profile

    def _apply_eq(self, y: np.ndarray) -> np.ndarray:
        """איזון תדרים"""
        # הגברת תדרים אמצעיים (חשוב לקול)
        return signal.filtfilt(
            [1, -0.97],
            [1, -0.95],
            y
        )

    def _enhance_clarity(self, y: np.ndarray) -> np.ndarray:
        """שיפור בהירות"""
        # הגברת הרמוניות
        D = librosa.stft(y)
        D_harmonic = librosa.decompose.hpss(D)[0]
        return librosa.istft(D_harmonic)

    def _calculate_confidence(self, y: np.ndarray) -> float:
        """חישוב רמת הביטחון בזיהוי"""
        # חישוב לפי עוצמת האות ויציבות
        energy = np.mean(y ** 2)
        stability = 1 - np.std(y) / np.mean(np.abs(y))
        return float(min(energy * stability, 1.0))

# יצירת singleton
audio_processor = AudioProcessor()