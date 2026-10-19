import pytest

from orinasa.validation import safe_text, validate_nonnegative, validate_priority, validate_status


@pytest.mark.parametrize("value", ["faible", "normale", "haute", "critique"])
def test_valid_priorities(value):
    assert validate_priority(value) == value


@pytest.mark.parametrize("value", ["ouvert", "en_cours", "resolu", "annule"])
def test_valid_statuses(value):
    assert validate_status(value) == value


@pytest.mark.parametrize("value", [0, 1, 2.5, 10, 100, 99999])
def test_nonnegative_values(value):
    assert validate_nonnegative(value) == float(value)


@pytest.mark.parametrize("value,expected", [
    ("Machine A", "Machine A"),
    ("  Machine A  ", "Machine A"),
    ("Machine   A", "Machine A"),
    ("Incident critique", "Incident critique"),
    ("Pompe-01", "Pompe-01"),
    ("Ligne 2 / convoyeur", "Ligne 2 / convoyeur"),
])
def test_safe_text(value, expected):
    assert safe_text(value) == expected
