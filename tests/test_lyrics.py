"""Tests du module de génération de paroles (nécessite ANTHROPIC_API_KEY)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock


# --- Tests sans API (mock) ---

class TestLyricsGeneratorMock:

    @patch("lyrics_generator.anthropic.Anthropic")
    def test_generer_paroles_retourne_texte(self, mock_anthropic_class):
        """Vérifie que la fonction retourne bien un texte."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [
            MagicMock(text="Couplet 1\nLigne 1\n\nRefrain\nAccroche")
        ]
        mock_anthropic_class.return_value = mock_client

        from lyrics_generator import generer_paroles

        with patch("lyrics_generator.ANTHROPIC_API_KEY", "sk-test"):
            result = generer_paroles("rap", "nuit urbaine", "fr")

        assert isinstance(result, str)
        assert len(result) > 0
        mock_client.messages.create.assert_called_once()

    @patch("lyrics_generator.anthropic.Anthropic")
    def test_langue_en(self, mock_anthropic_class):
        """Vérifie que la langue EN est bien passée dans le prompt."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [
            MagicMock(text="Verse 1\nLine 1\n\nChorus\nHook")
        ]
        mock_anthropic_class.return_value = mock_client

        from lyrics_generator import generer_paroles

        with patch("lyrics_generator.ANTHROPIC_API_KEY", "sk-test"):
            generer_paroles("pop", "love story", "en")

        call_args = mock_client.messages.create.call_args
        prompt_contenu = call_args.kwargs["messages"][0]["content"]
        assert "English" in prompt_contenu

    def test_sans_cle_api_leve_exception(self):
        """Sans clé API, doit lever ValueError."""
        from lyrics_generator import generer_paroles
        import importlib
        import lyrics_generator

        with patch.object(lyrics_generator, "ANTHROPIC_API_KEY", ""):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                generer_paroles("rap", "test")

    @patch("lyrics_generator.anthropic.Anthropic")
    def test_prompt_contient_style_et_theme(self, mock_anthropic_class):
        """Le prompt envoyé à Claude doit contenir le style et le thème."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="paroles")]
        mock_anthropic_class.return_value = mock_client

        from lyrics_generator import generer_paroles

        with patch("lyrics_generator.ANTHROPIC_API_KEY", "sk-test"):
            generer_paroles("electro", "mélancolie nocturne")

        call_args = mock_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        assert "electro" in prompt
        assert "mélancolie nocturne" in prompt


# --- Test réel (nécessite ANTHROPIC_API_KEY dans .env) ---

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY non configurée — test réel ignoré"
)
class TestLyricsGeneratorReel:

    def test_generer_paroles_rap_fr(self):
        """Test réel : génère un couplet rap en français."""
        from lyrics_generator import generer_paroles

        result = generer_paroles("rap", "rue, ambition, nuit")
        print(f"\n--- Paroles générées ---\n{result[:300]}...\n")

        assert len(result) > 100
        assert isinstance(result, str)

    def test_generer_paroles_pop_en(self):
        """Test réel : génère une chanson pop en anglais."""
        from lyrics_generator import generer_paroles

        result = generer_paroles("pop", "summer, freedom, love", "en")
        assert len(result) > 100
