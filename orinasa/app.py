from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from .assistant import answer_question
from .ai import AIService, SlidingWindowRateLimiter
from .calculations import CalculationError, calculate_trs, convert_unit, estimate_downtime_cost, safe_arithmetic
from .db import Repository
from .knowledge import CARDS

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"


class EquipmentIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(default="", max_length=120)
    hourly_rate: float = Field(default=0, ge=0)


class IncidentIn(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    category: str = Field(default="Autre", max_length=80)
    priority: str = "normale"
    status: str = "ouvert"
    equipment_id: int | None = None
    downtime_minutes: float = Field(default=0, ge=0)
    hourly_rate: float | None = Field(default=None, ge=0)
    description: str = Field(default="", max_length=1000)


class IncidentPatch(BaseModel):
    status: str | None = None
    resolution: str | None = Field(default=None, max_length=1000)


class TrsIn(BaseModel):
    availability: float
    performance: float
    quality: float


class DowntimeIn(BaseModel):
    minutes: float
    hourly_rate: float


class UnitIn(BaseModel):
    value: float
    from_unit: str
    to_unit: str


class ArithmeticIn(BaseModel):
    expression: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Le message ne peut pas être vide.")
        return value


class ChatIn(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_conversation(self):
        if self.messages[-1].role != "user":
            raise ValueError("Le dernier message doit être une question de l'utilisateur.")
        if sum(len(message.content) for message in self.messages) > 6000:
            raise ValueError("La conversation ne peut pas dépasser 6000 caractères.")
        return self


def create_app(
    db_path: str | Path | None = None,
    seed_demo: bool = True,
    ai_service: AIService | None = None,
) -> FastAPI:
    resolved = Path(db_path or os.getenv("ORINASA_DB_PATH", BASE_DIR / "data" / "orinasa.sqlite"))
    repo = Repository(resolved)
    configured_ai_service = ai_service or AIService()
    if seed_demo and os.getenv("ORINASA_DEMO_MODE", "1") != "0":
        repo.seed_demo()

    app = FastAPI(
        title="Orinasa - Assistant d'atelier",
        version="1.0.0",
        description="Suivi local d'incidents et fiches d'atelier avec recherche locale et fournisseurs IA optionnels.",
    )
    app.state.repo = repo
    app.state.ai_service = configured_ai_service
    app.state.ai_rate_limiter = SlidingWindowRateLimiter(configured_ai_service.config.requests_per_minute)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "orinasa"}

    @app.get("/api/summary")
    def summary():
        data = repo.summary()
        data["knowledge_count"] = len(CARDS)
        return data

    @app.get("/api/shift-handover")
    def shift_handover():
        incidents = repo.list_handover_incidents()
        for incident in incidents:
            missing_information = []
            if not incident["description"]:
                missing_information.append("Faits observés à préciser")
            if not incident["equipment_name"]:
                missing_information.append("Équipement à identifier")
            incident["missing_information"] = missing_information
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "open_count": len(incidents),
            "critical_count": sum(incident["priority"] == "critique" for incident in incidents),
            "incidents": incidents,
        }

    @app.get("/api/equipment")
    def equipment_list():
        return repo.list_equipment()

    @app.post("/api/equipment", status_code=201)
    def equipment_create(payload: EquipmentIn):
        try:
            return repo.add_equipment(payload.name, payload.location, payload.hourly_rate)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/incidents")
    def incidents_list(status: str | None = None, category: str | None = None, limit: int = 100):
        try:
            return repo.list_incidents(status=status, category=category, limit=limit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/incidents/export.csv", response_class=PlainTextResponse)
    def incidents_export(status: str | None = None):
        try:
            content = repo.export_csv(status=status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return PlainTextResponse(content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=orinasa_incidents.csv"})

    @app.get("/api/incidents/{incident_id}")
    def incident_detail(incident_id: int):
        try:
            return repo.get_incident(incident_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/incidents", status_code=201)
    def incident_create(payload: IncidentIn):
        try:
            return repo.add_incident(**payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.patch("/api/incidents/{incident_id}")
    def incident_update(incident_id: int, payload: IncidentPatch):
        try:
            return repo.update_incident(incident_id, status=payload.status, resolution=payload.resolution)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/knowledge")
    def knowledge():
        return CARDS

    @app.get("/api/assistant")
    def assistant(q: str = Query(min_length=1, max_length=300)):
        return answer_question(q)

    @app.get("/api/ai/status")
    def ai_status():
        return app.state.ai_service.status()

    @app.post("/api/ai/chat")
    def ai_chat(payload: ChatIn, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        if not app.state.ai_rate_limiter.allow(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Trop de demandes à l'assistant. Réessayez dans une minute.",
                headers={"Retry-After": "60"},
            )
        messages = [message.model_dump() for message in payload.messages]
        return app.state.ai_service.chat(messages)

    @app.post("/api/calculate/trs")
    def calc_trs(payload: TrsIn):
        try:
            return {"result": calculate_trs(payload.availability, payload.performance, payload.quality), "unit": "%"}
        except CalculationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/calculate/downtime")
    def calc_downtime(payload: DowntimeIn):
        try:
            return {"result": estimate_downtime_cost(payload.minutes, payload.hourly_rate), "unit": "Ar"}
        except CalculationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/calculate/unit")
    def calc_unit(payload: UnitIn):
        try:
            return {"result": convert_unit(payload.value, payload.from_unit, payload.to_unit), "unit": payload.to_unit}
        except CalculationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/calculate/arithmetic")
    def calc_arithmetic(payload: ArithmeticIn):
        try:
            return {"result": safe_arithmetic(payload.expression)}
        except CalculationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
