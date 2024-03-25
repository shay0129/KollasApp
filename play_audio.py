# play_audio.py
from request import download_google_drive_audio
from pygame import mixer
import logging
import time

def play_audio_from_url(url):
    audio_filename = download_google_drive_audio(url)
    if audio_filename:
        try:
            # Initialize Pygame mixer once
            if not mixer.get_init():
                mixer.init()

            mixer.music.load(audio_filename)
            mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    else:
        logging.error("Failed to download audio file")

def play_audio(url):
    audio_filename = download_google_drive_audio(url)
    if audio_filename:
        try:
            # Initialize Pygame mixer once
            if not mixer.get_init():
                mixer.init()

            mixer.music.load(audio_filename)
            mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    else:
        logging.error("Failed to download audio file")
