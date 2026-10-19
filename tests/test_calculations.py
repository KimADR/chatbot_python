import pytest

from orinasa.calculations import calculate_trs, convert_unit, estimate_downtime_cost, safe_arithmetic


DOWNTIME_CASES = [
    (i * 15, 1000 + i * 250, round((i * 15 / 60) * (1000 + i * 250), 2))
    for i in range(40)
]


@pytest.mark.parametrize("minutes,rate,expected", DOWNTIME_CASES)
def test_downtime_estimates(minutes, rate, expected):
    assert estimate_downtime_cost(minutes, rate) == expected


ARITH_CASES = [(f"{i}+{i*2}", float(i + i * 2)) for i in range(45)]


@pytest.mark.parametrize("expr,expected", ARITH_CASES)
def test_arithmetic(expr, expected):
    assert safe_arithmetic(expr) == expected


PAIRS = [
    ("mm", "cm", 0.1),
    ("cm", "mm", 10),
    ("cm", "m", 0.01),
    ("m", "cm", 100),
    ("m", "km", 0.001),
    ("km", "m", 1000),
    ("g", "kg", 0.001),
    ("kg", "g", 1000),
    ("ml", "l", 0.001),
    ("l", "ml", 1000),
]
UNIT_CASES = [(value, src, dst, round(value * factor, 6)) for src, dst, factor in PAIRS for value in (1, 2.5, 10, 100)]


@pytest.mark.parametrize("value,src,dst,expected", UNIT_CASES)
def test_unit_conversions(value, src, dst, expected):
    assert convert_unit(value, src, dst) == expected


TRS_CASES = []
for i in range(30):
    a = 70 + (i % 30)
    p = 80 + (i % 20)
    q = 90 + (i % 10)
    TRS_CASES.append((a, p, q, round((a / 100) * (p / 100) * (q / 100) * 100, 2)))


@pytest.mark.parametrize("availability,performance,quality,expected", TRS_CASES)
def test_trs(availability, performance, quality, expected):
    assert calculate_trs(availability, performance, quality) == expected
