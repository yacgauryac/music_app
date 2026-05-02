"""Module de génération musicale via GoAPI (Suno) avec fallback local."""

import os
import time
import requests
from config import SUNO_API_KEY

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated")
FALLBACK_BEAT = os.path.join(os.path.dirname(__file__), "assets", "placeholder_beat.wav")

# GoAPI endpoint Suno
GOAPI_BASE = "https://api.goapi.ai"


def generer_musique(style: str, theme: str, duree_sec: int = 120) -> str:
    """Génère un instrumental via GoAPI/Suno. Retourne le chemin du fichier audio."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not SUNO_API_KEY:
        print("[music_generator] Pas de clé API — fallback local")
        return _fallback_local()

    try:
        return _appel_goapi(style, theme)
    except Exception as e:
        print(f"[music_generator] Erreur GoAPI : {e}")
        return _fallback_local()


def _appel_goapi(style: str, theme: str) -> str:
    """Génère un beat via GoAPI (wrapper Suno)."""
    prompt = f"{style} instrumental beat, {theme}, no vocals, professional quality"

    # 1. Lancer la génération
    resp = requests.post(
        f"{GOAPI_BASE}/api/suno/v1/music",
        headers={
            "X-API-Key": SUNO_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": "chirp-v3-5",
            "task_type": "generate_music",
            "input": {
                "gpt_description_prompt": prompt,
                "make_instrumental": True,
                "mv": "chirp-v3-5",
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    task_id = data.get("data", {}).get("task_id") or data.get("task_id")
    if not task_id:
        raise RuntimeError(f"GoAPI : pas de task_id dans la réponse — {data}")

    print(f"[music_generator] Task ID : {task_id} — en attente...")

    # 2. Polling jusqu'à ce que ce soit prêt
    audio_url = _attendre_goapi(task_id)

    # 3. Télécharger le fichier
    output_path = os.path.join(OUTPUT_DIR, f"beat_{int(time.time())}.mp3")
    print(f"[music_generator] Téléchargement : {audio_url}")
    audio_resp = requests.get(audio_url, timeout=120)
    audio_resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(audio_resp.content)

    print(f"[music_generator] Beat sauvegardé : {output_path}")
    return output_path


def _attendre_goapi(task_id: str, max_attempts: int = 60) -> str:
    """Polling du statut GoAPI jusqu'à ce que l'audio soit prêt (~1-3 min)."""
    for attempt in range(max_attempts):
        time.sleep(5)

        resp = requests.get(
            f"{GOAPI_BASE}/api/suno/v1/music/{task_id}",
            headers={"X-API-Key": SUNO_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # Naviguer dans la réponse GoAPI
        output = data.get("data", {}).get("output", {})
        status = data.get("data", {}).get("status") or data.get("status", "")

        print(f"[music_generator] Statut ({attempt+1}/{max_attempts}) : {status}")

        if status == "completed":
            # L'audio peut être dans clips[0].audio_url ou directement audio_url
            clips = output.get("clips", [])
            if clips:
                return clips[0].get("audio_url") or clips[0].get("audio_proxy_url")
            audio_url = output.get("audio_url")
            if audio_url:
                return audio_url

        if status in ("failed", "error"):
            raise RuntimeError(f"GoAPI génération échouée : {data}")

    raise TimeoutError("Génération trop longue (>5 min) — réessaie")


def _fallback_local() -> str:
    """Génère un beat placeholder minimal si l'API n'est pas disponible."""
    if os.path.exists(FALLBACK_BEAT):
        return FALLBACK_BEAT

    from pydub import AudioSegment
    from pydub.generators import Sine

    os.makedirs(os.path.dirname(FALLBACK_BEAT), exist_ok=True)

    beat = AudioSegment.silent(duration=30000)
    kick = Sine(60).to_audio_segment(duration=100).apply_gain(-10)

    for i in range(0, 30000, 500):
        beat = beat.overlay(kick, position=i)

    beat.export(FALLBACK_BEAT, format="wav")
    print("[music_generator] Beat placeholder généré (30s, 120 BPM)")
    return FALLBACK_BEAT
