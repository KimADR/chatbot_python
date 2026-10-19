from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from .knowledge import CARDS


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def search_cards(query: str, limit: int = 3) -> list[dict]:
    q = _normalize(query)
    if not q:
        return []
    terms = set(q.split())
    scored: list[tuple[int, dict]] = []
    for card in CARDS:
        hay = _normalize(" ".join([card["title"], card["category"], *card["keywords"], card["content"]]))
        hterms = set(hay.split())
        overlap = len(terms & hterms)
        phrase_bonus = 3 if q in hay else 0
        keyword_bonus = sum(2 for k in card["keywords"] if _normalize(k) in q)
        score = overlap + phrase_bonus + keyword_bonus
        if score > 0:
            scored.append((score, card))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [card for _, card in scored[: max(1, min(limit, 5))]]


def answer_question(query: str) -> dict:
    normalized = _normalize(query)
    greetings = {"salama", "manao ahoana", "bonjour", "salut", "hello"}
    if normalized in greetings:
        return {
            "answer": "Bonjour. Salama. Je peux vous aider a retrouver une fiche d'atelier ou a structurer un incident.",
            "references": [],
            "confidence": "greeting",
        }
    results = search_cards(query)
    if not results:
        return {
            "answer": "Je ne trouve pas de fiche suffisamment proche. Decrivez le symptome, l'equipement et le contexte. Pour toute situation dangereuse, appliquez d'abord les procedures de securite du site et faites intervenir une personne competente.",
            "references": [],
            "confidence": "none",
        }
    top = results[0]
    return {
        "answer": f"{top['content']} {top['safety']}",
        "references": [{"id": c["id"], "title": c["title"]} for c in results],
        "confidence": "local-knowledge",
    }
