"""PinoBio MVP-4 /v1 serving layer — FastAPI implementation of the SciACA
workbench job contract (Default Project/specs/orchestrator.md §10–11).

Design rules in force:
- G7  honest results only: tools return `pending` (not fabricated) when a backend
      isn't ready; `measured` flags whether a response is a real computed result.
- G8  no secrets in code; GET /v1/* is auth-free (read-only); upstream keys via env.
- G9  scope: only the §10.2 task→tool mapping is served; unknown task ⇒ 400 validation.

In-memory job store (MVP). Jobs run synchronously in a thread so the tiny demo
backends stay simple; swap for a queue when real GPU backends land.
"""
from __future__ import annotations

import time
import uuid
from threading import Lock, Thread

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from serving.models_catalog import MODELS, model_by_id
from serving.tools import TASK_TOOL

app = FastAPI(title="PinoBio MVP-4 /v1", version="0.1.0")

# CORS so the SciACA dev server (vite :5173 / electron) can call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # read-only + demo-safe; tighten per deployment
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_JOBS: dict[str, dict] = {}
_LOCK = Lock()

PROJECTS = [
    {"id": "rice", "name": "Rice-first crop arm", "kind": "agri"},
    {"id": "demo", "name": "Demo project", "kind": "demo"},
]


class JobCreate(BaseModel):
    task: str
    model: str | None = None
    project: str | None = None
    inputs: dict = Field(default_factory=dict)


def _run_job(job_id: str) -> None:
    with _LOCK:
        job = _JOBS[job_id]
        job["status"] = "running"
        job["progress"] = 0.4
    tool = TASK_TOOL[job["task"]]
    try:
        result = tool(job["inputs"])
        status = "succeeded"
    except Exception as e:  # noqa: BLE001 — surface the failure honestly (G7)
        result = {"status": "error", "error": repr(e), "measured": False}
        status = "failed"
    with _LOCK:
        job = _JOBS[job_id]
        job["result"] = result
        job["status"] = status
        job["progress"] = 1.0
        job["runtime"] = round(time.time() - job["_t0"], 2)


@app.get("/v1/models")
def list_models() -> list[dict]:
    return MODELS


@app.get("/v1/models/{model_id}")
def get_model(model_id: str) -> dict:
    card = model_by_id(model_id)
    if card is None:
        raise HTTPException(status_code=404, detail="unknown model")
    return card


@app.get("/v1/projects")
def list_projects() -> list[dict]:
    return PROJECTS


@app.get("/v1/jobs")
def list_jobs() -> list[dict]:
    with _LOCK:
        return [_public(j) for j in _JOBS.values()]


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        return _public(job)


@app.post("/v1/jobs")
def create_job(body: JobCreate) -> dict:
    if body.task not in TASK_TOOL:
        # §11: unknown task ⇒ validation error
        raise HTTPException(
            status_code=400,
            detail={"error": "validation", "message": f"unknown task '{body.task}'",
                    "allowed": sorted(TASK_TOOL)},
        )
    job_id = "J-" + uuid.uuid4().hex[:8].upper()
    job = {
        "id": job_id,
        "task": body.task,
        "model": body.model,
        "project": body.project,
        "inputs": body.inputs,
        "status": "queued",
        "progress": 0.0,
        "result": None,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "_t0": time.time(),
    }
    with _LOCK:
        _JOBS[job_id] = job
    Thread(target=_run_job, args=(job_id,), daemon=True).start()
    return {"id": job_id, "status": "queued"}


def _public(job: dict) -> dict:
    return {k: v for k, v in job.items() if not k.startswith("_")}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "models": len(MODELS), "jobs": len(_JOBS)}
