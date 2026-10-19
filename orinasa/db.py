from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .validation import safe_text, validate_nonnegative, validate_priority, validate_status


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Repository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL DEFAULT '',
                    hourly_rate REAL NOT NULL DEFAULT 0 CHECK(hourly_rate >= 0),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    equipment_id INTEGER,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    downtime_minutes REAL NOT NULL DEFAULT 0 CHECK(downtime_minutes >= 0),
                    hourly_rate REAL NOT NULL DEFAULT 0 CHECK(hourly_rate >= 0),
                    description TEXT NOT NULL DEFAULT '',
                    resolution TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS incident_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(incident_id) REFERENCES incidents(id) ON DELETE CASCADE
                );
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
            if count:
                return
            equipment = [
                ("EQ-001", "Ensacheuse", "Ligne 1", 80000),
                ("EQ-002", "Compresseur", "Utilites", 60000),
                ("EQ-003", "Convoyeur", "Ligne 1", 45000),
                ("EQ-004", "Melangeur", "Preparation", 70000),
                ("EQ-005", "Etiqueteuse", "Conditionnement", 50000),
            ]
            now = _utcnow()
            conn.executemany(
                "INSERT INTO equipment(code,name,location,hourly_rate,created_at) VALUES(?,?,?,?,?)",
                [(c, n, l, r, now) for c, n, l, r in equipment],
            )
            incidents = [
                ("ORI-0001", "Coupure electrique sur la ligne", 1, "Electricite", "critique", "ouvert", 90, 80000, "Arret soudain de la ligne", ""),
                ("ORI-0002", "Bruit inhabituel sur le compresseur", 2, "Mecanique", "haute", "en_cours", 45, 60000, "Bruit intermittent", ""),
                ("ORI-0003", "Defaut d'etiquetage sur un lot", 5, "Qualite", "normale", "ouvert", 30, 50000, "Etiquettes decalees", ""),
                ("ORI-0004", "Coupure d'alimentation du melangeur", 4, "Electricite", "haute", "resolu", 60, 70000, "Protection declenchee", "Controle realise"),
                ("ORI-0005", "Protection endommagee a signaler", 3, "Securite", "haute", "ouvert", 75, 45000, "Carter abime", ""),
            ]
            for item in incidents:
                conn.execute(
                    """INSERT INTO incidents(code,title,equipment_id,category,priority,status,downtime_minutes,hourly_rate,description,resolution,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (*item, now, now),
                )
            for incident_id in range(1, 6):
                conn.execute(
                    "INSERT INTO incident_history(incident_id,event_type,details,created_at) VALUES(?,?,?,?)",
                    (incident_id, "creation", "Incident de demonstration cree", now),
                )

    def add_equipment(self, name: str, location: str = "", hourly_rate: float = 0) -> dict:
        name = safe_text(name, 120)
        location = " ".join(location.strip().split())[:120]
        hourly_rate = validate_nonnegative(hourly_rate, "taux horaire")
        with self.connect() as conn:
            next_id = conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM equipment").fetchone()[0]
            code = f"EQ-{next_id:03d}"
            now = _utcnow()
            cur = conn.execute(
                "INSERT INTO equipment(code,name,location,hourly_rate,created_at) VALUES(?,?,?,?,?)",
                (code, name, location, hourly_rate, now),
            )
            return dict(conn.execute("SELECT * FROM equipment WHERE id=?", (cur.lastrowid,)).fetchone())

    def list_equipment(self) -> list[dict]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM equipment ORDER BY name")]

    def add_incident(
        self,
        title: str,
        category: str,
        priority: str = "normale",
        status: str = "ouvert",
        equipment_id: int | None = None,
        downtime_minutes: float = 0,
        hourly_rate: float | None = None,
        description: str = "",
    ) -> dict:
        title = safe_text(title, 180)
        category = safe_text(category, 80)
        priority = validate_priority(priority)
        status = validate_status(status)
        downtime_minutes = validate_nonnegative(downtime_minutes, "duree")
        description = " ".join(description.strip().split())[:1000]
        with self.connect() as conn:
            if equipment_id is not None:
                eq = conn.execute("SELECT * FROM equipment WHERE id=?", (equipment_id,)).fetchone()
                if not eq:
                    raise ValueError("Equipement introuvable")
                rate = eq["hourly_rate"] if hourly_rate is None else validate_nonnegative(hourly_rate, "taux horaire")
            else:
                rate = 0 if hourly_rate is None else validate_nonnegative(hourly_rate, "taux horaire")
            next_id = conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM incidents").fetchone()[0]
            code = f"ORI-{next_id:04d}"
            now = _utcnow()
            cur = conn.execute(
                """INSERT INTO incidents(code,title,equipment_id,category,priority,status,downtime_minutes,hourly_rate,description,resolution,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, title, equipment_id, category, priority, status, downtime_minutes, rate, description, "", now, now),
            )
            incident_id = cur.lastrowid
            conn.execute(
                "INSERT INTO incident_history(incident_id,event_type,details,created_at) VALUES(?,?,?,?)",
                (incident_id, "creation", f"Incident cree avec priorite {priority}", now),
            )
            return self._incident_by_id(conn, incident_id)

    def _incident_by_id(self, conn: sqlite3.Connection, incident_id: int) -> dict:
        row = conn.execute(
            """SELECT i.*, e.name AS equipment_name, e.code AS equipment_code
               FROM incidents i LEFT JOIN equipment e ON e.id=i.equipment_id WHERE i.id=?""",
            (incident_id,),
        ).fetchone()
        if not row:
            raise KeyError("Incident introuvable")
        data = dict(row)
        data["estimated_cost"] = round(data["downtime_minutes"] / 60 * data["hourly_rate"], 2)
        return data

    def get_incident(self, incident_id: int) -> dict:
        with self.connect() as conn:
            data = self._incident_by_id(conn, incident_id)
            data["history"] = [
                dict(r)
                for r in conn.execute(
                    "SELECT event_type,details,created_at FROM incident_history WHERE incident_id=? ORDER BY id DESC",
                    (incident_id,),
                )
            ]
            return data

    def list_incidents(self, status: str | None = None, category: str | None = None, limit: int = 100) -> list[dict]:
        query = """SELECT i.*, e.name AS equipment_name, e.code AS equipment_code
                   FROM incidents i LEFT JOIN equipment e ON e.id=i.equipment_id WHERE 1=1"""
        args: list[object] = []
        if status:
            query += " AND i.status=?"
            args.append(validate_status(status))
        if category:
            query += " AND i.category=?"
            args.append(category)
        query += " ORDER BY i.id DESC LIMIT ?"
        args.append(max(1, min(int(limit), 500)))
        with self.connect() as conn:
            items = [dict(r) for r in conn.execute(query, args)]
            for item in items:
                item["estimated_cost"] = round(item["downtime_minutes"] / 60 * item["hourly_rate"], 2)
            return items

    def list_handover_incidents(self) -> list[dict]:
        with self.connect() as conn:
            items = [
                dict(row)
                for row in conn.execute(
                    """SELECT i.*, e.name AS equipment_name, e.code AS equipment_code,
                              (SELECT h.details FROM incident_history h
                               WHERE h.incident_id=i.id AND h.event_type='mise_a_jour'
                               ORDER BY h.id DESC LIMIT 1) AS latest_update,
                              (SELECT h.created_at FROM incident_history h
                               WHERE h.incident_id=i.id AND h.event_type='mise_a_jour'
                               ORDER BY h.id DESC LIMIT 1) AS latest_update_at
                       FROM incidents i LEFT JOIN equipment e ON e.id=i.equipment_id
                       WHERE i.status IN ('ouvert','en_cours')
                       ORDER BY CASE i.priority
                           WHEN 'critique' THEN 0 WHEN 'haute' THEN 1
                           WHEN 'normale' THEN 2 ELSE 3 END, i.updated_at DESC"""
                )
            ]
            for item in items:
                item["estimated_cost"] = round(item["downtime_minutes"] / 60 * item["hourly_rate"], 2)
            return items

    def update_incident(self, incident_id: int, *, status: str | None = None, resolution: str | None = None) -> dict:
        with self.connect() as conn:
            current = self._incident_by_id(conn, incident_id)
            updates: list[str] = []
            args: list[object] = []
            details: list[str] = []
            if status is not None:
                status = validate_status(status)
                updates.append("status=?")
                args.append(status)
                details.append(f"statut: {current['status']} -> {status}")
            if resolution is not None:
                resolution = " ".join(resolution.strip().split())[:1000]
                updates.append("resolution=?")
                args.append(resolution)
                details.append("resolution mise a jour")
            if not updates:
                return current
            now = _utcnow()
            updates.append("updated_at=?")
            args.append(now)
            args.append(incident_id)
            conn.execute(f"UPDATE incidents SET {', '.join(updates)} WHERE id=?", args)
            conn.execute(
                "INSERT INTO incident_history(incident_id,event_type,details,created_at) VALUES(?,?,?,?)",
                (incident_id, "mise_a_jour", "; ".join(details), now),
            )
            return self._incident_by_id(conn, incident_id)

    def summary(self) -> dict:
        with self.connect() as conn:
            open_count = conn.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('ouvert','en_cours')").fetchone()[0]
            critical = conn.execute("SELECT COUNT(*) FROM incidents WHERE priority='critique' AND status!='resolu'").fetchone()[0]
            minutes = conn.execute("SELECT COALESCE(SUM(downtime_minutes),0) FROM incidents").fetchone()[0]
            cost = conn.execute("SELECT COALESCE(SUM((downtime_minutes/60.0)*hourly_rate),0) FROM incidents").fetchone()[0]
            equipment = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
            categories = [dict(r) for r in conn.execute("SELECT category, COUNT(*) AS count FROM incidents GROUP BY category ORDER BY count DESC, category")]
        return {
            "open_incidents": int(open_count),
            "critical_open": int(critical),
            "downtime_minutes": round(float(minutes), 2),
            "estimated_cost": round(float(cost), 2),
            "equipment_count": int(equipment),
            "categories": categories,
        }

    def export_csv(self, status: str | None = None) -> str:
        items = self.list_incidents(status=status, limit=500)
        output = io.StringIO()
        fields = ["code", "title", "equipment_name", "category", "priority", "status", "downtime_minutes", "hourly_rate", "estimated_cost", "created_at"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)
        return output.getvalue()
