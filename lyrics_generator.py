"""Module de génération de paroles via Claude API."""

import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


def generer_paroles(style: str, theme: str, langue: str = "fr") -> str:
    """Génère des paroles complètes (couplet + refrain + pont) via Claude."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY non configurée dans .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    lang_instruction = "en français" if langue == "fr" else "in English"

    prompt = f"""Tu es un parolier professionnel. Écris des paroles de chanson {lang_instruction}.

Style musical : {style}
Thème / ambiance : {theme}

Structure demandée :
- 1 couplet (8 lignes)
- 1 refrain (4 lignes, accrocheur et mémorable)
- 1 couplet (8 lignes)
- 1 refrain (répétition)
- 1 pont (4 lignes, changement de perspective)
- 1 refrain final

Règles :
- Rimes cohérentes avec le style
- Rythme adapté au genre musical
- Vocabulaire authentique au style
- Pas de marqueurs de section entre crochets, utilise des lignes vides pour séparer

Écris uniquement les paroles, sans commentaires."""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def affiner_paroles(paroles: str, instruction: str, langue: str = "fr") -> str:
    """Modifie des paroles existantes selon une instruction en langage naturel."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY non configurée dans .env")
    if not paroles.strip():
        raise ValueError("Aucune parole à affiner")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    lang_instruction = "en français" if langue == "fr" else "in English"

    prompt = f"""Tu es un parolier professionnel. Voici des paroles de chanson {lang_instruction} :

---
{paroles}
---

Instruction de modification : {instruction}

Règles :
- Garde la même structure (couplets, refrains, pont)
- Conserve le style et l'ambiance générale
- Applique uniquement ce qui est demandé dans l'instruction
- Renvoie uniquement les paroles modifiées, sans commentaires"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
