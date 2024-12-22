# Import missing libraries
import hashlib
import shutil
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# ... [Previous code remains the same until AudioPlayer class end]

class AudioController(QWidget):
    """Audio controller widget for the UI"""
    
    # Custom signals
    playbackStarted = pyqtSignal()
    playbackPaused = pyqtSignal()
    playbackStopped = pyqtSignal()
    positionChanged = pyqtSignal(float)
    durationChanged = pyqtSignal(float)
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = audio_player
        self._setup_ui()
        self._connect_signals()
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)  # 100ms update interval
        self.update_timer.timeout.connect(self._update_position)
        
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Time labels layout
        time_layout = QHBoxLayout()
        self.position_label = QLabel("00:00")
        self.duration_label = QLabel("00:00")
        time_layout.addWidget(self.position_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        layout.addLayout(time_layout)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)  # Using 1000 steps for smooth sliding
        layout.addWidget(self.progress_slider)
        
        # Control buttons layout
        controls_layout = QHBoxLayout()
        
        # Create control buttons
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)
        
    def _connect_signals(self):
        """Connect all signals"""
        # Button clicks
        self.play_button.clicked.connect(self.play)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)
        
        # Sliders
        self.progress_slider.sliderMoved.connect(self.seek)
        self.volume_slider.valueChanged.connect(self._set_volume)
        
        # Player callbacks
        self.player.add_callback('on_progress', self._on_progress)
        self.player.add_callback('on_state_change', self._on_state_change)
        self.player.add_callback('on_error', self._on_error)
        self.player.add_callback('on_metadata_change', self._on_metadata_change)
        
    async def load_file(self, url: str, title: str = ""):
        """Load an audio file"""
        success = await self.player.play_from_url(url, title)
        if success:
            self.playbackStarted.emit()
            self.update_timer.start()
            self._update_controls(True)
        
    def play(self):
        """Play or resume playback"""
        if self.player.state == PlayerState.PAUSED:
            self.player.resume()
            self.playbackStarted.emit()
            self.update_timer.start()
        elif self.player.metadata:
            self.player.play_from_url(self.player.metadata.url)
            
        self._update_controls(True)
        
    def pause(self):
        """Pause playback"""
        self.player.pause()
        self.playbackPaused.emit()
        self.update_timer.stop()
        self._update_controls(False)
        
    def stop(self):
        """Stop playback"""
        self.player.stop()
        self.playbackStopped.emit()
        self.update_timer.stop()
        self.progress_slider.setValue(0)
        self._update_controls(False)
        
    def seek(self, position: int):
        """Seek to position"""
        if self.player.metadata:
            # Convert slider position (0-1000) to seconds
            duration = self.player.metadata.duration
            seconds = (position / 1000.0) * duration
            self.player.seek(seconds)
            
    def _set_volume(self, value: int):
        """Set volume level"""
        volume = value / 100.0
        self.player.set_volume(volume)
        
    def _update_controls(self, playing: bool):
        """Update control buttons state"""
        self.play_button.setEnabled(not playing)
        self.pause_button.setEnabled(playing)
        self.stop_button.setEnabled(playing)
        
    def _update_position(self):
        """Update position slider and labels"""
        if self.player.metadata:
            position = self.player.current_position
            duration = self.player.metadata.duration
            
            # Update slider
            if not self.progress_slider.isSliderDown():
                self.progress_slider.setValue(int((position / duration) * 1000))
            
            # Update labels
            self.position_label.setText(self._format_time(position))
            self.duration_label.setText(self._format_time(duration))
            
    def _on_progress(self, position: float):
        """Handle progress updates"""
        self.positionChanged.emit(position)
        
    def _on_state_change(self, state: PlayerState):
        """Handle state changes"""
        if state == PlayerState.STOPPED:
            self._update_controls(False)
            self.update_timer.stop()
            
    def _on_error(self, error: str):
        """Handle errors"""
        self.errorOccurred.emit(error)
        self._update_controls(False)
        self.update_timer.stop()
        
    def _on_metadata_change(self, metadata: AudioMetadata):
        """Handle metadata changes"""
        self.durationChanged.emit(metadata.duration)
        
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

# Create singleton instance
audio_controller = AudioController()