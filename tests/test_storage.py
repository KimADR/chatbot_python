import pytest

from orinasa.db import Repository


@pytest.mark.parametrize("idx", range(5))
def test_equipment_crud(tmp_path, idx):
    repo = Repository(tmp_path / f"eq_{idx}.sqlite")
    item = repo.add_equipment(f"Machine {idx}", f"Zone {idx}", 10000 + idx)
    assert item["name"] == f"Machine {idx}"
    assert len(repo.list_equipment()) == 1


@pytest.mark.parametrize("idx", range(5))
def test_incident_crud(tmp_path, idx):
    repo = Repository(tmp_path / f"inc_{idx}.sqlite")
    eq = repo.add_equipment(f"Machine {idx}", hourly_rate=60000)
    incident = repo.add_incident(f"Incident {idx}", "Mecanique", equipment_id=eq["id"], downtime_minutes=30)
    assert incident["status"] == "ouvert"
    updated = repo.update_incident(incident["id"], status="resolu", resolution="Action terminee")
    assert updated["status"] == "resolu"


@pytest.mark.parametrize("idx", range(5))
def test_summary_after_incident(tmp_path, idx):
    repo = Repository(tmp_path / f"sum_{idx}.sqlite")
    eq = repo.add_equipment(f"Machine {idx}", hourly_rate=80000)
    repo.add_incident(f"Incident {idx}", "Electricite", priority="critique", equipment_id=eq["id"], downtime_minutes=45)
    summary = repo.summary()
    assert summary["open_incidents"] == 1
    assert summary["critical_open"] == 1
    assert summary["estimated_cost"] == 60000
