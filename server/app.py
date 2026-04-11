from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action

app = FastAPI(title="OpenEnv Real-World Tasks", version="0.1.0")
env = OpenEnvEnvironment()


class ResetRequest(BaseModel):
    task_id: str
    seed: int | None = None


class StepRequest(BaseModel):
    action: Action


@app.get("/")
def home() -> dict:
    return {
        "message": "OpenEnv environment is running",
        "metadata": env.metadata().model_dump(),
        "tasks": [t.model_dump() for t in env.tasks()],
    }


@app.get("/metadata")
def metadata() -> dict:
    return env.metadata().model_dump()


@app.get("/tasks")
def tasks() -> list[dict]:
    return [t.model_dump() for t in env.tasks()]


@app.post("/reset/{task_id}")
def reset(task_id: str, seed: int | None = None) -> dict:
    try:
        result = env.reset(task_id=task_id, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/reset")
def reset_openenv(request: dict[str, Any] | None = None) -> dict:
    request = request or {}
    task_id = (
        request.get("task_id")
        or request.get("task")
        or request.get("task_name")
        or request.get("id")
        or "easy_expense_triage"
    )
    seed = request.get("seed")

    try:
        result = env.reset(task_id=task_id, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/step")
def step(payload: dict[str, Any] | None = None) -> dict:
    payload = payload or {}
    action_payload: dict[str, Any]
    if "command" in payload:
        action_payload = payload
    elif isinstance(payload.get("action"), dict):
        action_payload = payload["action"]
    else:
        raise HTTPException(status_code=422, detail="Expected action payload with command/args")

    try:
        action = Action.model_validate(action_payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid action payload: {exc}") from exc

    try:
        result = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/grade")
def grade_post() -> dict:
    return grade()


@app.get("/grade")
def grade() -> dict:
    try:
        result = env.grade()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


def main() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server.app:app", host=host, port=port)
