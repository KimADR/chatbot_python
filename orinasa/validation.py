from __future__ import annotations

VALID_PRIORITIES = {"faible", "normale", "haute", "critique"}
VALID_STATUSES = {"ouvert", "en_cours", "resolu", "annule"}
VALID_CATEGORIES = {"Electricite", "Mecanique", "Qualite", "Securite", "Maintenance", "Production", "Organisation", "Autre"}


def validate_priority(value: str) -> str:
    v = value.strip().lower()
    if v not in VALID_PRIORITIES:
        raise ValueError("Priorite invalide")
    return v


def validate_status(value: str) -> str:
    v = value.strip().lower()
    if v not in VALID_STATUSES:
        raise ValueError("Statut invalide")
    return v


def validate_nonnegative(value: float, field: str = "valeur") -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{field} doit etre positif ou nul")
    return value


def safe_text(value: str, max_length: int = 180) -> str:
    v = " ".join(value.strip().split())
    if not v:
        raise ValueError("Texte requis")
    if len(v) > max_length:
        raise ValueError("Texte trop long")
    return v
