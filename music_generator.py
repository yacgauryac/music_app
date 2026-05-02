"""Module de génération musicale via Suno API (avec fallback local)."""

import os
import time
import requests
from config import SUNO_API_KEY

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated")
FALLBACK_BEAT = os.path.join(os.path.dirname(__file__), "assets", "placeholder_beat.wav")


def generer_musique(style: str, theme: str, duree_sec: int = 120) -> str:
    """Génère un instrumental via Suno API. Retourne le chemin du fichier audio."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not SUNO_API_KEY:
        return _fallback_local()

    try:
        return _appel_suno(style, theme, duree_sec)
    except Exception as e:
        print(f"[music_generator] Erreur Suno API : {e}")
        return _fallback_local()


def _appel_suno(style: str, theme: str, duree_sec: int) -> str:
    """Appel réel à l'API Suno pour générer un beat."""
    # Suno API v3 (non-officielle, basée sur https://github.com/gcui-art/suno-api)
    base_url = os.getenv("SUNO_API_URL", "http://localhost:3000")

    prompt = f"{style} instrumental beat, {theme}, no vocals, {duree_sec} seconds"

    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "prompt": prompt,
            "make_instrumental": True,
            "wait_audio": False,
        },
        headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Polling jusqu'à ce que l'audio soit prêt
    song_id = data[0]["id"] if isinstance(data, list) else data["id"]
    audio_url = _attendre_generation(base_url, song_id)

    # Télécharger le fichier
    output_path = os.path.join(OUTPUT_DIR, f"beat_{int(time.time())}.mp3")
    audio_response = requests.get(audio_url, timeout=60)
    with open(output_path, "wb") as f:
        f.write(audio_response.content)

    return output_path


def _attendre_generation(base_url: str, song_id: str, max_attempts: int = 60) -> str:
    """Polling de l'état de génération Suno."""
    for _ in range(max_attempts):
        resp = requests.get(
            f"{base_url}/api/get",
            params={"ids": song_id},
            headers={"Authorization": f"Bearer {SUNO_API_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        info = resp.json()
        song = info[0] if isinstance(info, list) else info

        if song.get("audio_url"):
            return song["audio_url"]
        if song.get("status") == "error":
            raise RuntimeError(f"Suno erreur : {song.get('error_message', 'inconnu')}")

        time.sleep(5)

    raise TimeoutError("Génération Suno trop longue (>5 min)")


def _fallback_local() -> str:
    """Retourne un beat placeholder si Suno n'est pas disponible."""
    if os.path.exists(FALLBACK_BEAT):
        return FALLBACK_BEAT

    # Génère un silence de 30s comme placeholder minimal
    from pydub import AudioSegment
    from pydub.generators import Sine

    os.makedirs(os.path.dirname(FALLBACK_BEAT), exist_ok=True)

    # Beat minimaliste : kick pattern simple
    beat = AudioSegment.silent(duration=30000)
    kick = Sine(60).to_audio_segment(duration=100).apply_gain(-10)

    # Pattern kick toutes les 500ms (120 BPM)
    for i in range(0, 30000, 500):
        beat = beat.overlay(kick, position=i)

    beat.export(FALLBACK_BEAT, format="wav")
    print("[music_generator] Fallback : beat placeholder généré (Suno non disponible)")
    return FALLBACK_BEAT
