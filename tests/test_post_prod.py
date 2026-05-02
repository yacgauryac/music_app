"""Tests du module de post-production vocale."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch


def _generer_vocal_test(path: str, duree_sec: float = 2.0) -> None:
    """Génère un fichier vocal synthétique pour les tests."""
    from config import SAMPLE_RATE

    t = np.linspace(0, duree_sec, int(SAMPLE_RATE * duree_sec), dtype="float32")
    # Simule une voix : fondamentale 200Hz + harmoniques + bruit léger
    audio = (
        np.sin(2 * np.pi * 200 * t) * 0.4
        + np.sin(2 * np.pi * 400 * t) * 0.2
        + np.sin(2 * np.pi * 800 * t) * 0.1
        + np.random.normal(0, 0.02, len(t)).astype("float32")
    ).reshape(-1, 1)
    sf.write(path, audio, SAMPLE_RATE)


class TestNoiseGate:

    def test_silence_attenue(self):
        """Les passages silencieux doivent être atténués."""
        from post_prod import _noise_gate

        audio = np.zeros((4096, 1), dtype="float32")
        result = _noise_gate(audio, threshold_db=-40)

        assert np.max(np.abs(result)) < 0.1

    def test_signal_fort_conserve(self):
        """Un signal fort doit passer le gate sans atténuation."""
        from config import SAMPLE_RATE
        from post_prod import _noise_gate

        t = np.linspace(0, 1.0, SAMPLE_RATE, dtype="float32")
        audio = (np.sin(2 * np.pi * 200 * t) * 0.8).reshape(-1, 1)
        result = _noise_gate(audio, threshold_db=-40)

        # Le max ne doit pas être réduit de plus de 50%
        assert np.max(np.abs(result)) > 0.3


class TestNormalisation:

    def test_normalise_au_bon_niveau(self):
        """La normalisation doit amener le pic à la cible."""
        from post_prod import _normaliser

        audio = np.random.randn(10000, 1).astype("float32") * 0.1
        result = _normaliser(audio, target_db=-1.0)

        peak_db = 20 * np.log10(np.max(np.abs(result)) + 1e-10)
        assert abs(peak_db - (-1.0)) < 0.5

    def test_silence_ne_crash_pas(self):
        """La normalisation d'un signal nul ne doit pas lever d'exception."""
        from post_prod import _normaliser

        audio = np.zeros((1024, 1), dtype="float32")
        result = _normaliser(audio)
        assert result is not None


class TestPostProductionVocale:

    def test_produit_fichier_wav(self, tmp_path):
        """La post-production doit produire un fichier WAV valide."""
        from post_prod import post_production_vocale
        from config import SAMPLE_RATE

        vocal_path = str(tmp_path / "vocal.wav")
        _generer_vocal_test(vocal_path)

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            result = post_production_vocale(vocal_path, reverb_size="small")

        assert os.path.exists(result)
        data, sr = sf.read(result)
        assert sr == SAMPLE_RATE
        assert len(data) > 0

    def test_reverb_presets_valides(self, tmp_path):
        """Les trois presets reverb doivent fonctionner sans erreur."""
        from post_prod import post_production_vocale

        vocal_path = str(tmp_path / "vocal.wav")
        _generer_vocal_test(vocal_path)

        for preset in ["small", "medium", "large"]:
            with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
                result = post_production_vocale(vocal_path, reverb_size=preset)
            assert os.path.exists(result), f"Preset '{preset}' a échoué"

    def test_avec_delay(self, tmp_path):
        """L'option delay doit fonctionner sans erreur."""
        from post_prod import post_production_vocale

        vocal_path = str(tmp_path / "vocal.wav")
        _generer_vocal_test(vocal_path)

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            result = post_production_vocale(vocal_path, avec_delay=True)

        assert os.path.exists(result)

    def test_sortie_normalisee(self, tmp_path):
        """Le fichier de sortie ne doit pas saturer (pic < 0 dBFS)."""
        from post_prod import post_production_vocale

        vocal_path = str(tmp_path / "vocal.wav")
        _generer_vocal_test(vocal_path)

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            result = post_production_vocale(vocal_path)

        data, _ = sf.read(result)
        assert np.max(np.abs(data)) <= 1.0


class TestMixFinal:

    def test_mix_produit_fichier(self, tmp_path):
        """Le mixage voix + instru doit produire un fichier WAV."""
        from post_prod import mixer_final
        from config import SAMPLE_RATE

        # Génère un vocal et un instrumental de test
        vocal_path = str(tmp_path / "vocal_prod.wav")
        instru_path = str(tmp_path / "instru.wav")

        _generer_vocal_test(vocal_path, duree_sec=3.0)

        # Instrumental = 120Hz sinusoïde 5 secondes
        t = np.linspace(0, 5.0, SAMPLE_RATE * 5, dtype="float32")
        instru = (np.sin(2 * np.pi * 120 * t) * 0.5).reshape(-1, 1)
        sf.write(instru_path, instru, SAMPLE_RATE)

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            result = mixer_final(vocal_path, instru_path)

        assert os.path.exists(result)
        data, sr = sf.read(result)
        assert sr > 0

    def test_mix_longueur_vocale(self, tmp_path):
        """Le mix doit avoir la longueur du vocal."""
        from post_prod import mixer_final
        from config import SAMPLE_RATE

        vocal_path = str(tmp_path / "vocal.wav")
        instru_path = str(tmp_path / "instru.wav")

        # Vocal : 3s, Instru : 10s
        _generer_vocal_test(vocal_path, duree_sec=3.0)
        t = np.linspace(0, 10.0, SAMPLE_RATE * 10, dtype="float32")
        sf.write(instru_path, (np.sin(2 * np.pi * 60 * t) * 0.3).reshape(-1, 1), SAMPLE_RATE)

        with patch("post_prod.OUTPUT_DIR", str(tmp_path)):
            result = mixer_final(vocal_path, instru_path)

        data, _ = sf.read(result)
        # Durée du mix ≈ durée du vocal (±200ms de tolérance)
        duree_mix = len(data) / SAMPLE_RATE
        assert abs(duree_mix - 3.0) < 0.2
