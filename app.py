from __future__ import annotations

from fastapi import FastAPI, HTTPException

from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action

app = FastAPI(title="OpenEnv Real-World Tasks", version="0.1.0")
env = OpenEnvEnvironment()


@app.get("/")
def home() -> dict:
    return {
        "message": "OpenEnv environment is running",
        "metadata": env.metadata().model_dump(),
        "tasks": [t.model_dump() for t in env.tasks()],
    }


@app.post("/reset/{task_id}")
def reset(task_id: str, seed: int | None = None) -> dict:
    try:
        result = env.reset(task_id=task_id, seed=seed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@app.post("/step")
def step(action: Action) -> dict:
    try:
        result = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()


@app.get("/grade")
def grade() -> dict:
    try:
        result = env.grade()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump()
