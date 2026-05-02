"""Tests du module d'enregistrement audio."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import numpy as np
import soundfile as sf
from unittest.mock import patch, MagicMock
import tempfile


class TestEnregistreur:

    def test_instantiation(self):
        """L'enregistreur se crée sans erreur."""
        from recorder import Enregistreur
        rec = Enregistreur()
        assert not rec.recording
        assert rec.frames == []

    def test_sauvegarder_audio(self, tmp_path):
        """Sauvegarde un array numpy en WAV valide."""
        from recorder import Enregistreur
        from config import SAMPLE_RATE

        rec = Enregistreur()

        # Génère une sinusoïde 440Hz de 1 seconde
        t = np.linspace(0, 1.0, SAMPLE_RATE, dtype="float32")
        audio = (np.sin(2 * np.pi * 440 * t) * 0.3).reshape(-1, 1)

        output_path = str(tmp_path / "test_vocal.wav")
        rec.sauvegarder(audio, output_path)

        assert os.path.exists(output_path)
        data, sr = sf.read(output_path)
        assert sr == SAMPLE_RATE
        assert len(data) == SAMPLE_RATE  # 1 seconde

    @patch("recorder.sd.InputStream")
    @patch("recorder.sd.play")
    def test_demarrer_sans_instrumental(self, mock_play, mock_stream_class):
        """Démarrer sans instrumental ne doit pas appeler sd.play."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        from recorder import Enregistreur
        rec = Enregistreur()
        rec.demarrer(instrumental_path=None)

        assert rec.recording
        mock_stream.start.assert_called_once()
        mock_play.assert_not_called()

        rec.recording = False
        if rec._stream:
            rec._stream = None

    @patch("recorder.sd.InputStream")
    def test_arreter_sans_frames(self, mock_stream_class):
        """Arrêter sans avoir enregistré doit retourner une chaîne vide."""
        mock_stream = MagicMock()
        mock_stream_class.return_value = mock_stream

        from recorder import Enregistreur
        rec = Enregistreur()
        rec.recording = False

        result = rec.arreter()
        assert result == ""

    @patch("recorder.sd.InputStream")
    def test_audio_callback_ajoute_frames(self, mock_stream_class):
        """Le callback doit accumuler les frames audio."""
        from recorder import Enregistreur
        rec = Enregistreur()
        rec.recording = True

        frame = np.zeros((1024, 1), dtype="float32")
        rec._audio_callback(frame, 1024, None, None)
        rec._audio_callback(frame, 1024, None, None)

        assert len(rec.frames) == 2

    @patch("recorder.sd.InputStream")
    def test_callback_ignore_si_pas_recording(self, mock_stream_class):
        """Le callback ne doit pas stocker si recording=False."""
        from recorder import Enregistreur
        rec = Enregistreur()
        rec.recording = False

        frame = np.zeros((1024, 1), dtype="float32")
        rec._audio_callback(frame, 1024, None, None)

        assert len(rec.frames) == 0


class TestEnregistrementSimple:

    @patch("recorder.sd.rec")
    @patch("recorder.sd.wait")
    def test_enregistrer_simple(self, mock_wait, mock_rec, tmp_path):
        """Vérifie que enregistrer_simple sauvegarde un fichier."""
        from config import SAMPLE_RATE

        # Simule 1 seconde de silence
        mock_rec.return_value = np.zeros((SAMPLE_RATE, 1), dtype="float32")

        with patch("recorder.RECORDINGS_DIR", str(tmp_path)):
            from recorder import enregistrer_simple
            result = enregistrer_simple(duree_sec=1)

        assert result.endswith(".wav")
        assert os.path.exists(result)
