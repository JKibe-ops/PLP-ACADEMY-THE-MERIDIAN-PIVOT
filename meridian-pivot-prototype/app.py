from __future__ import annotations

import asyncio
import os
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "local-demo-secret")

ATTENDEES = {
    "SOL-001": {"id": "SOL-001", "name": "Maya Chen", "status": "ready"},
    "SOL-002": {"id": "SOL-002", "name": "Jon Bell", "status": "ready"},
    "SOL-003": {"id": "SOL-003", "name": "Priya Shah", "status": "ready"},
}
PRINT_QUEUE: deque[dict[str, str]] = deque()
EVENTS: list[dict[str, str]] = []


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.heartbeat = asyncio.create_task(queue_heartbeat())
    yield
    application.state.heartbeat.cancel()


app = FastAPI(
    title="Meridian Pivot Async Check-in Prototype",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


class ScanRequest(BaseModel):
    attendee_id: str


class PrintCallback(BaseModel):
    job_id: str
    attendee_id: str
    outcome: Literal["completed", "failed"]


def record(event: str, detail: str) -> None:
    EVENTS.insert(0, {
        "event": event,
        "detail": detail,
        "at": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "async-check-in"}


@app.get("/")
def browser_app() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/attendees")
def attendees() -> list[dict[str, str]]:
    return list(ATTENDEES.values())


@app.get("/events")
def events() -> list[dict[str, str]]:
    return EVENTS


@app.get("/queue")
def queue() -> list[dict[str, str]]:
    return list(PRINT_QUEUE)


@app.post("/scan", status_code=status.HTTP_202_ACCEPTED)
def scan(request: ScanRequest) -> dict[str, object]:
    attendee = ATTENDEES.get(request.attendee_id)
    if attendee is None:
        raise HTTPException(status_code=404, detail="Attendee not found")

    if attendee["status"] != "ready":
        record("duplicate_scan_blocked", f"{request.attendee_id} is already {attendee['status']}")
        return {
            "accepted": False,
            "duplicate": True,
            "message": "No second badge will be printed.",
            "attendee": attendee,
        }

    job = {"job_id": f"job-{uuid4().hex[:8]}", "attendee_id": request.attendee_id}
    attendee["status"] = "pending"
    PRINT_QUEUE.append(job)
    record("print_request_published", f"{job['job_id']} queued for {attendee['name']}")
    return {
        "accepted": True,
        "duplicate": False,
        "message": "Print request published; awaiting webhook confirmation.",
        "job": job,
        "attendee": attendee,
    }


@app.post("/vendor/complete", status_code=status.HTTP_202_ACCEPTED)
def vendor_complete(callback: PrintCallback) -> dict[str, str]:
    """Simulate the vendor sending a callback after a print job completes."""
    return webhook(callback, WEBHOOK_SECRET)


@app.post("/webhooks/print-complete", status_code=status.HTTP_200_OK)
def webhook(callback: PrintCallback, x_webhook_secret: str | None = Header(default=None)) -> dict[str, str]:
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    attendee = ATTENDEES.get(callback.attendee_id)
    if attendee is None:
        raise HTTPException(status_code=404, detail="Attendee not found")

    remaining_jobs = [job for job in PRINT_QUEUE if job["job_id"] != callback.job_id]
    PRINT_QUEUE.clear()
    PRINT_QUEUE.extend(remaining_jobs)
    if attendee["status"] == "checked-in":
        record("webhook_replayed", f"{callback.job_id} ignored; attendee is already checked in")
        return {"status": "ignored", "message": "Callback already processed."}

    attendee["status"] = "checked-in" if callback.outcome == "completed" else "ready"
    record("webhook_received", f"{callback.job_id} marked {attendee['status']}")
    return {"status": "processed", "attendee_status": attendee["status"]}


@app.post("/reset")
def reset() -> dict[str, str]:
    for attendee in ATTENDEES.values():
        attendee["status"] = "ready"
    PRINT_QUEUE.clear()
    EVENTS.clear()
    return {"status": "reset"}


async def queue_heartbeat() -> None:
    while True:
        await asyncio.sleep(60)


