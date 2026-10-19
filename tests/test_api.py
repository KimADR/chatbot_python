from fastapi.testclient import TestClient

from orinasa.app import create_app


def client(tmp_path):
    return TestClient(create_app(tmp_path / "api.sqlite", seed_demo=False))


def add_equipment(c):
    return c.post("/api/equipment", json={"name":"Pompe","location":"Zone A","hourly_rate":80000}).json()


def add_incident(c):
    eq = add_equipment(c)
    return c.post("/api/incidents", json={"title":"Arret pompe","category":"Mecanique","priority":"haute","equipment_id":eq["id"],"downtime_minutes":45}).json()


def test_api_health(tmp_path):
    r=client(tmp_path).get("/health"); assert r.status_code==200 and r.json()["status"]=="ok"

def test_api_summary(tmp_path):
    r=client(tmp_path).get("/api/summary"); assert r.status_code==200 and r.json()["knowledge_count"]==14

def test_api_equipment_list(tmp_path):
    r=client(tmp_path).get("/api/equipment"); assert r.status_code==200 and r.json()==[]

def test_api_equipment_create(tmp_path):
    c=client(tmp_path); r=c.post("/api/equipment",json={"name":"Convoyeur","hourly_rate":45000}); assert r.status_code==201 and r.json()["code"]=="EQ-001"

def test_api_incidents_list(tmp_path):
    r=client(tmp_path).get("/api/incidents"); assert r.status_code==200 and r.json()==[]

def test_api_shift_handover_lists_open_incidents_and_flags_missing_details(tmp_path):
    c=client(tmp_path)
    equipment=add_equipment(c)
    incident=c.post("/api/incidents",json={"title":"Pompe à vérifier","equipment_id":equipment["id"],"priority":"critique"}).json()
    c.patch(f"/api/incidents/{incident['id']}",json={"status":"en_cours"})
    c.post("/api/incidents",json={"title":"Incident clos","status":"resolu"})

    response=c.get("/api/shift-handover")

    assert response.status_code==200
    report=response.json()
    assert report["open_count"]==1
    assert report["critical_count"]==1
    assert report["incidents"][0]["code"]==incident["code"]
    assert report["incidents"][0]["status"]=="en_cours"
    assert report["incidents"][0]["missing_information"]==["Faits observés à préciser"]
    assert "ouvert -> en_cours" in report["incidents"][0]["latest_update"]
    assert report["generated_at"]

def test_api_shift_handover_empty_when_no_incidents_need_followup(tmp_path):
    c=client(tmp_path)
    incident=add_incident(c)
    c.patch(f"/api/incidents/{incident['id']}",json={"status":"resolu"})

    response=c.get("/api/shift-handover")

    assert response.status_code==200
    assert response.json()["open_count"]==0
    assert response.json()["critical_count"]==0
    assert response.json()["incidents"]==[]

def test_api_incident_create(tmp_path):
    c=client(tmp_path); data=add_incident(c); assert data["code"]=="ORI-0001" and data["estimated_cost"]==60000

def test_api_incident_detail(tmp_path):
    c=client(tmp_path); data=add_incident(c); r=c.get(f"/api/incidents/{data['id']}"); assert r.status_code==200 and "history" in r.json()

def test_api_incident_patch(tmp_path):
    c=client(tmp_path); data=add_incident(c); r=c.patch(f"/api/incidents/{data['id']}",json={"status":"resolu"}); assert r.status_code==200 and r.json()["status"]=="resolu"

def test_api_knowledge(tmp_path):
    r=client(tmp_path).get("/api/knowledge"); assert r.status_code==200 and len(r.json())==14

def test_api_assistant(tmp_path):
    r=client(tmp_path).get("/api/assistant",params={"q":"coupure electricite"}); assert r.status_code==200 and r.json()["references"]

def test_api_calc_downtime(tmp_path):
    r=client(tmp_path).post("/api/calculate/downtime",json={"minutes":45,"hourly_rate":80000}); assert r.status_code==200 and r.json()["result"]==60000

def test_api_calc_trs(tmp_path):
    r=client(tmp_path).post("/api/calculate/trs",json={"availability":90,"performance":95,"quality":98}); assert r.status_code==200 and r.json()["result"]==83.79

def test_api_calc_unit(tmp_path):
    r=client(tmp_path).post("/api/calculate/unit",json={"value":1,"from_unit":"m","to_unit":"cm"}); assert r.status_code==200 and r.json()["result"]==100

def test_api_calc_arithmetic(tmp_path):
    r=client(tmp_path).post("/api/calculate/arithmetic",json={"expression":"45/60*80000"}); assert r.status_code==200 and r.json()["result"]==60000

def test_api_export_csv(tmp_path):
    c=client(tmp_path); add_incident(c); r=c.get("/api/incidents/export.csv"); assert r.status_code==200 and "ORI-0001" in r.text and "text/csv" in r.headers["content-type"]
