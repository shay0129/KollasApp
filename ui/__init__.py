"""
User interface module for KollasApp
Contains custom widgets, themes and display components
"""

from .custom_widgets import BookPage, AudioPlayer, LyricsViewer
from .themes import StyleManager
from .display import DisplayManager
from .play_audio import AudioController

__all__ = [
    'BookPage',
    'AudioPlayer',
    'LyricsViewer',
    'StyleManager',
    'DisplayManager',
    'AudioController'
]