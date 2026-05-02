"""Test d'intégration : pipeline complet mocké (paroles → musique → post-prod → export)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock


SAMPLE_RATE = 44100


@pytest.fixture
def vocal_synthetique(tmp_path):
    """Génère un fichier vocal de test."""
    path = str(tmp_path / "vocal.wav")
    t = np.linspace(0, 2.0, SAMPLE_RATE * 2, dtype="float32")
    audio = (np.sin(2 * np.pi * 250 * t) * 0.5).reshape(-1, 1)
    sf.write(path, audio, SAMPLE_RATE)
    return path


@pytest.fixture
def instrumental_synthetique(tmp_path):
    """Génère un instrumental de test."""
    path = str(tmp_path / "instru.wav")
    t = np.linspace(0, 2.0, SAMPLE_RATE * 2, dtype="float32")
    audio = (np.sin(2 * np.pi * 120 * t) * 0.3).reshape(-1, 1)
    sf.write(path, audio, SAMPLE_RATE)
    return path


class TestPipelineComplet:

    @patch("lyrics_generator.anthropic.Anthropic")
    def test_etape1_paroles(self, mock_anthropic):
        """Étape 1 : génération de paroles mocké."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [
            MagicMock(text="[Couplet 1]\nDans les rues de la ville\nLa nuit tombe tranquille")
        ]
        mock_anthropic.return_value = mock_client

        from lyrics_generator import generer_paroles

        with patch("lyrics_generator.ANTHROPIC_API_KEY", "sk-test"):
            paroles = generer_paroles("rap", "nuit, ville", "fr")

        assert len(paroles) > 0

    def test_etape2_fallback_musique(self, tmp_path):
        """Étape 2 : génération instrumentale via fallback."""
        with patch("music_generator.SUNO_API_KEY", ""):
            with patch("music_generator.FALLBACK_BEAT", str(tmp_path / "beat.wav")):
                from music_generator import generer_musique
                instru = generer_musique("hip-hop", "dark")

        assert instru is not None
        assert os.path.exists(instru)

    def test_etape3_post_prod(self, tmp_path, vocal_synthetique):
        """Étape 4 : post-production sur le vocal."""
        from post_prod import post_production_vocale

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            vocal_prod = post_production_vocale(vocal_synthetique, reverb_size="small")

        assert os.path.exists(vocal_prod)

    def test_etape4_mix(self, tmp_path, vocal_synthetique, instrumental_synthetique):
        """Étape 4 : mix final voix + instrumental."""
        from post_prod import post_production_vocale, mixer_final

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            vocal_prod = post_production_vocale(vocal_synthetique, reverb_size="small")
            mix = mixer_final(vocal_prod, instrumental_synthetique)

        assert os.path.exists(mix)
        data, sr = sf.read(mix)
        assert sr == SAMPLE_RATE

    def test_etape5_export_mp3(self, tmp_path, vocal_synthetique):
        """Étape 5 : export en MP3."""
        from pydub import AudioSegment

        audio = AudioSegment.from_file(vocal_synthetique)
        mp3_path = str(tmp_path / "export.mp3")
        audio.export(mp3_path, format="mp3", bitrate="128k")

        assert os.path.exists(mp3_path)
        assert os.path.getsize(mp3_path) > 1000

    @patch("lyrics_generator.anthropic.Anthropic")
    def test_pipeline_complet_enchaine(self, mock_anthropic, tmp_path):
        """Pipeline complet de bout en bout (tout mocké)."""
        # Mock Claude
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [
            MagicMock(text="Refrain test\nLigne de test")
        ]
        mock_anthropic.return_value = mock_client

        # 1. Paroles
        from lyrics_generator import generer_paroles
        with patch("lyrics_generator.ANTHROPIC_API_KEY", "sk-test"):
            paroles = generer_paroles("pop", "été")

        assert len(paroles) > 0

        # 2. Musique (fallback)
        with patch("music_generator.SUNO_API_KEY", ""):
            with patch("music_generator.FALLBACK_BEAT", str(tmp_path / "beat.wav")):
                from music_generator import generer_musique
                instru = generer_musique("pop", "été")

        assert os.path.exists(instru)

        # 3. Simuler un enregistrement vocal
        vocal = str(tmp_path / "vocal.wav")
        t = np.linspace(0, 2.0, SAMPLE_RATE * 2, dtype="float32")
        sf.write(vocal, (np.sin(2 * np.pi * 220 * t) * 0.4).reshape(-1, 1), SAMPLE_RATE)

        # 4. Post-prod + mix
        from post_prod import post_production_vocale, mixer_final
        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            vocal_prod = post_production_vocale(vocal, reverb_size="small")
            mix = mixer_final(vocal_prod, instru)

        assert os.path.exists(mix)
        print(f"\n✅ Pipeline complet OK → {mix}")
