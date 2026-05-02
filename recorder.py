"""Module d'enregistrement vocal avec lecture simultanée de l'instrumental."""

import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time
import os
from config import SAMPLE_RATE, CHANNELS

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")


class Enregistreur:
    """Gère l'enregistrement vocal avec playback instrumental simultané."""

    def __init__(self):
        self.recording = False
        self.frames = []
        self._stream = None
        self._playback_thread = None

    def demarrer(self, instrumental_path: str = None) -> None:
        """Démarre l'enregistrement. Joue l'instrumental en fond si fourni."""
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        self.frames = []
        self.recording = True

        # Lancer le playback instrumental en parallèle
        if instrumental_path and os.path.exists(instrumental_path):
            self._playback_thread = threading.Thread(
                target=self._jouer_instrumental,
                args=(instrumental_path,),
                daemon=True,
            )
            self._playback_thread.start()

        # Démarrer la capture micro
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def arreter(self) -> str:
        """Arrête l'enregistrement et sauvegarde le fichier WAV."""
        self.recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        sd.stop()

        if not self.frames:
            return ""

        audio_data = np.concatenate(self.frames, axis=0)
        output_path = os.path.join(RECORDINGS_DIR, f"vocal_{int(time.time())}.wav")
        sf.write(output_path, audio_data, SAMPLE_RATE)

        return output_path

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback appelé par sounddevice pour chaque bloc audio capturé."""
        if self.recording:
            self.frames.append(indata.copy())

    def _jouer_instrumental(self, path: str) -> None:
        """Joue l'instrumental en arrière-plan pendant l'enregistrement."""
        try:
            data, sr = sf.read(path, dtype="float32")
            sd.play(data, sr)
        except Exception as e:
            print(f"[recorder] Erreur playback : {e}")


def enregistrer_simple(duree_sec: int = 30) -> str:
    """Enregistrement simple sans instrumental (utile pour les tests)."""
    os.makedirs(RECORDINGS_DIR, exist_ok=True)

    print(f"[recorder] Enregistrement {duree_sec}s...")
    audio = sd.rec(
        int(duree_sec * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
    )
    sd.wait()

    output_path = os.path.join(RECORDINGS_DIR, f"vocal_{int(time.time())}.wav")
    sf.write(output_path, audio, SAMPLE_RATE)
    return output_path
