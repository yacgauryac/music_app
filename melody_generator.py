"""Génère une mélodie guide MIDI à partir des paroles via Claude."""

import json
import os
import anthropic
from midiutil import MIDIFile
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

NOTE_MAP = {
    "C3": 48, "D3": 50, "E3": 52, "F3": 53, "G3": 55, "A3": 57, "B3": 59,
    "C4": 60, "D4": 62, "E4": 64, "F4": 65, "G4": 67, "A4": 69, "B4": 71,
    "C5": 72, "D5": 74, "E5": 76, "F5": 77, "G5": 79, "A5": 81, "B5": 83,
    "Db4": 61, "Eb4": 63, "Gb4": 66, "Ab4": 68, "Bb4": 70,
    "Db5": 73, "Eb5": 75, "Gb5": 78, "Ab5": 80, "Bb5": 82,
}


def generer_melodie(paroles: str, style: str, bpm: int = 90) -> str:
    """Génère un fichier MIDI de la mélodie vocale guide."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY non configurée dans .env")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    notes = _demander_notes_a_claude(paroles, style, bpm)
    midi_path = _creer_midi(notes, bpm)
    return midi_path


def _demander_notes_a_claude(paroles: str, style: str, bpm: int) -> list[dict]:
    """Claude génère une séquence de notes MIDI pour la mélodie vocale."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Extrait les 2 premiers couplets/refrains pour rester concis
    lignes = [l.strip() for l in paroles.strip().split("\n") if l.strip()][:20]
    extrait = "\n".join(lignes)

    prompt = f"""Tu es un compositeur. Génère une mélodie vocale pour ces paroles de {style} à {bpm} BPM.

Paroles :
{extrait}

Génère une séquence JSON de notes pour la mélodie vocale. Chaque note correspond à une syllabe ou un mot clé.

Réponds UNIQUEMENT avec un tableau JSON valide, sans markdown, sans explication :
[
  {{"note": "G4", "duration": 0.5, "text": "mot"}},
  ...
]

Règles :
- Notes disponibles : C3 D3 E3 F3 G3 A3 B3 C4 D4 E4 F4 G4 A4 B4 C5 D5 E5 F5 G5 A5 Db4 Eb4 Gb4 Ab4 Bb4
- Duration en beats (0.25=croche, 0.5=noire, 1.0=blanche)
- Style {style} : adapte le registre (rap=notes plates C4-E4, pop=mélodie variée C4-G4)
- 30 à 50 notes maximum
- Mélodie cohérente avec une progression musicale naturelle"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Nettoyer le JSON si Claude a ajouté des backticks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    notes = json.loads(raw)
    return notes


def _creer_midi(notes: list[dict], bpm: int) -> str:
    """Crée un fichier MIDI à partir de la séquence de notes."""
    midi = MIDIFile(1)
    track, channel = 0, 0
    time = 0.0

    midi.addTempo(track, 0, bpm)
    midi.addProgramChange(track, channel, 0, 0)  # Piano acoustique

    for note in notes:
        note_name = note.get("note", "C4")
        duration = float(note.get("duration", 0.5))
        pitch = NOTE_MAP.get(note_name, 60)

        midi.addNote(track, channel, pitch, time, duration, velocity=80)
        time += duration

    import time as time_mod
    output_path = os.path.join(OUTPUT_DIR, f"melodie_{int(time_mod.time())}.mid")
    with open(output_path, "wb") as f:
        midi.writeFile(f)

    return output_path
