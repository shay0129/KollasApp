# audio.py
import pyaudio

def play_audio(audio_data):
    try:
        audio_player = pyaudio.PyAudio()
        stream = audio_player.open(format=pyaudio.paInt16,
                                   channels=2,
                                   rate=44100,
                                   output=True)
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
        audio_player.terminate()
    except Exception as e:
        print("Error playing audio:", e)

def get_audio_data(file_id, service):
    try:
        request = service.files().get_media(fileId=file_id)
        audio_data = request.execute()

        return audio_data
    except Exception as e:
        print("Error getting audio data:", e)
        return None
