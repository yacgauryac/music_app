"""Tests du module de génération musicale (fallback local + mock Suno)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock


class TestFallbackLocal:

    def test_fallback_genere_fichier(self, tmp_path):
        """Sans Suno API, le fallback doit générer un fichier audio."""
        with patch("music_generator.SUNO_API_KEY", ""):
            with patch("music_generator.FALLBACK_BEAT", str(tmp_path / "beat.wav")):
                from music_generator import generer_musique

                result = generer_musique("rap", "nuit urbaine")

        assert result is not None
        assert os.path.exists(result)

    def test_fallback_fichier_est_wav(self, tmp_path):
        """Le fichier fallback doit être un WAV valide."""
        import soundfile as sf

        with patch("music_generator.SUNO_API_KEY", ""):
            with patch("music_generator.FALLBACK_BEAT", str(tmp_path / "beat.wav")):
                from music_generator import generer_musique

                result = generer_musique("electro", "danse")

        if result and result.endswith(".wav"):
            data, sr = sf.read(result)
            assert sr > 0
            assert len(data) > 0

    def test_fallback_si_suno_erreur(self, tmp_path):
        """En cas d'erreur Suno, le fallback doit s'activer."""
        import requests

        with patch("music_generator.SUNO_API_KEY", "fausse-cle"):
            with patch("music_generator.FALLBACK_BEAT", str(tmp_path / "beat.wav")):
                with patch("music_generator.requests.post") as mock_post:
                    mock_post.side_effect = requests.RequestException("connexion refusée")

                    from music_generator import generer_musique
                    result = generer_musique("pop", "soleil")

        assert result is not None


class TestSunoAPIMock:

    @patch("music_generator.requests.get")
    @patch("music_generator.requests.post")
    def test_appel_suno_succes(self, mock_post, mock_get, tmp_path):
        """Mock d'un appel Suno réussi."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": "song-123"}],
        )
        mock_post.return_value.raise_for_status = MagicMock()

        # Premier appel get : en cours, deuxième : terminé
        mock_get.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: [{"status": "processing", "audio_url": None}],
                raise_for_status=MagicMock(),
            ),
            MagicMock(
                status_code=200,
                json=lambda: [{"status": "complete", "audio_url": "http://fake/audio.mp3"}],
                raise_for_status=MagicMock(),
            ),
            # Téléchargement
            MagicMock(
                status_code=200,
                content=b"FAKE_MP3_CONTENT",
                raise_for_status=MagicMock(),
            ),
        ]

        with patch("music_generator.SUNO_API_KEY", "test-key"):
            with patch("music_generator.OUTPUT_DIR", str(tmp_path)):
                from music_generator import _appel_suno

                result = _appel_suno("rap", "nuit", 30)

        assert result is not None
        assert os.path.exists(result)


# --- Test réel Suno (nécessite SUNO_API_KEY) ---

@pytest.mark.skipif(
    not os.getenv("SUNO_API_KEY"),
    reason="SUNO_API_KEY non configurée — test réel ignoré"
)
class TestSunoReel:

    def test_generer_beat_rap(self):
        """Test réel : génère un beat rap via Suno."""
        from music_generator import generer_musique

        result = generer_musique("hip-hop beat", "dark, cinematic", duree_sec=30)
        assert result is not None
        assert os.path.exists(result)
        print(f"\n--- Beat généré : {result} ---")
