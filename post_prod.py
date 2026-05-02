"""Module de post-production vocale automatique."""

import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pedalboard import (
    Pedalboard,
    Compressor,
    Reverb,
    HighpassFilter,
    LowShelfFilter,
    HighShelfFilter,
    Delay,
    Gain,
)
from pedalboard.io import AudioFile
import os
import time
from config import SAMPLE_RATE, DEFAULT_REVERB

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

REVERB_PRESETS = {
    "small": {"room_size": 0.2, "wet_level": 0.15},
    "medium": {"room_size": 0.5, "wet_level": 0.25},
    "large": {"room_size": 0.8, "wet_level": 0.35},
}


def post_production_vocale(
    vocal_path: str,
    reverb_size: str = None,
    avec_delay: bool = False,
    pitch_correction: bool = True,
) -> str:
    """Applique la chaîne de post-production complète sur la voix."""
    if reverb_size is None:
        reverb_size = DEFAULT_REVERB

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Charger l'audio
    audio, sr = sf.read(vocal_path, dtype="float32")
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    # Réduction de bruit (gate simple basé sur le niveau RMS)
    audio = _noise_gate(audio, threshold_db=-40)

    # Chaîne d'effets avec Pedalboard
    reverb_params = REVERB_PRESETS.get(reverb_size, REVERB_PRESETS["medium"])

    effets = [
        HighpassFilter(cutoff_frequency_hz=80),       # Coupe sous 80Hz
        LowShelfFilter(cutoff_frequency_hz=200, gain_db=-3),  # Nettoyage bas-médiums
        HighShelfFilter(cutoff_frequency_hz=3000, gain_db=4),  # Boost présence 3-5kHz
        Compressor(
            threshold_db=-20,
            ratio=3.0,
            attack_ms=10,
            release_ms=100,
        ),
        Reverb(
            room_size=reverb_params["room_size"],
            wet_level=reverb_params["wet_level"],
            dry_level=0.8,
        ),
    ]

    if avec_delay:
        effets.append(Delay(delay_seconds=0.3, feedback=0.2, mix=0.15))

    # Gain de sortie
    effets.append(Gain(gain_db=2))

    board = Pedalboard(effets)
    audio_traite = board(audio, sr)

    # Correction de pitch légère (centrage sur la note la plus proche)
    if pitch_correction:
        audio_traite = _pitch_correction_legere(audio_traite, sr)

    # Normalisation
    audio_traite = _normaliser(audio_traite)

    output_path = os.path.join(OUTPUT_DIR, f"vocal_prod_{int(time.time())}.wav")
    sf.write(output_path, audio_traite, sr)

    return output_path


def mixer_final(vocal_prod_path: str, instrumental_path: str) -> str:
    """Mixe la voix post-produite avec l'instrumental."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    vocal = AudioSegment.from_file(vocal_prod_path)
    instru = AudioSegment.from_file(instrumental_path)

    # Ajuster la longueur de l'instru à la voix
    if len(instru) < len(vocal):
        instru = instru + AudioSegment.silent(duration=len(vocal) - len(instru))
    else:
        instru = instru[:len(vocal)]

    # Balance : instru -3dB par rapport à la voix
    instru = instru - 3

    # Mixage
    mix = vocal.overlay(instru)

    # Master léger : limiter + normalisation
    mix = mix.normalize()

    output_path = os.path.join(OUTPUT_DIR, f"mix_final_{int(time.time())}.wav")
    mix.export(output_path, format="wav")

    return output_path


def _noise_gate(audio: np.ndarray, threshold_db: float = -40) -> np.ndarray:
    """Gate de bruit simple : silence les passages sous le seuil."""
    threshold_linear = 10 ** (threshold_db / 20)
    frame_size = 1024

    result = audio.copy()
    for i in range(0, len(audio), frame_size):
        frame = audio[i : i + frame_size]
        rms = np.sqrt(np.mean(frame**2))
        if rms < threshold_linear:
            result[i : i + frame_size] *= 0.01  # Atténuation douce

    return result


def _pitch_correction_legere(audio: np.ndarray, sr: int) -> np.ndarray:
    """Correction de pitch subtile — recentre vers la note la plus proche."""
    try:
        import librosa

        # Mono pour l'analyse
        mono = audio[:, 0] if audio.ndim > 1 else audio

        # Détecter le pitch
        pitches, magnitudes = librosa.piptrack(y=mono, sr=sr, fmin=80, fmax=800)

        # Correction subtile via pitch shift proportionnel
        pitch_median = np.median(pitches[pitches > 0]) if np.any(pitches > 0) else 0

        if pitch_median > 0:
            # Trouver la note MIDI la plus proche
            midi_note = librosa.hz_to_midi(pitch_median)
            nearest_midi = round(midi_note)
            correction_semitones = (nearest_midi - midi_note) * 0.3  # 30% de correction

            if abs(correction_semitones) > 0.05:
                corrected = librosa.effects.pitch_shift(
                    mono, sr=sr, n_steps=correction_semitones
                )
                if audio.ndim > 1:
                    return corrected.reshape(-1, 1)
                return corrected

    except ImportError:
        pass
    except Exception as e:
        print(f"[post_prod] Pitch correction ignorée : {e}")

    return audio


def _normaliser(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """Normalise le signal au niveau cible."""
    peak = np.max(np.abs(audio))
    if peak > 0:
        target_linear = 10 ** (target_db / 20)
        audio = audio * (target_linear / peak)
    return audio
