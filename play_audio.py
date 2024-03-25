# play_audio.py
# Contains functions to play audio files and control playback
from request import download_google_drive_audio
from pygame import mixer
import logging
import time
import os

# Global variable to store the currently playing audio filename
current_audio_filename = None

def play_audio_from_url(url, progress_bar=None):
    global current_audio_filename
    
    # Stop the previous audio playback, if any
    stop_audio()
    
    mixer.init()
    audio_filename = download_google_drive_audio(url)
    if audio_filename:
        try:
            # Delete the previous temporary file, if it exists
            if current_audio_filename and os.path.exists(current_audio_filename):
                mixer.music.stop()  # Stop the audio playback
                mixer.music.unload()  # Unload the current audio
                os.remove(current_audio_filename)  # Delete the file
            
            mixer.music.load(audio_filename)
            mixer.music.play()

            # Update progress bar while playing
            if progress_bar:
                length = mixer.Sound(audio_filename).get_length()
                for i in range(int(length)):
                    progress_bar['value'] = (i / length) * 100
                    progress_bar.update()
                    time.sleep(1)
            
            # Store the current audio filename
            current_audio_filename = audio_filename
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    else:
        logging.error("Failed to download audio file")

def stop_audio():
    global current_audio_filename
    
    if current_audio_filename:
        mixer.music.stop()
        mixer.music.unload()  # Unload the current audio
        current_audio_filename = None
