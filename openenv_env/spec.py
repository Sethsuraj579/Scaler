from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EnvMetadata(BaseModel):
    name: str
    version: str
    description: str
    action_schema_hint: str
    observation_schema_hint: str


class TaskInfo(BaseModel):
    task_id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    description: str
    max_steps: int


class Action(BaseModel):
    command: str = Field(..., description="Action command name")
    args: Dict[str, Any] = Field(default_factory=dict, description="Command arguments")


class Observation(BaseModel):
    task_id: str
    step_index: int
    max_steps: int
    score: float
    progress: float
    summary: str
    state_view: Dict[str, Any]
    allowed_commands: List[str]
    done: bool


class StepResult(BaseModel):
    observation: Observation
    reward: float
    terminated: bool
    truncated: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetResult(BaseModel):
    observation: Observation
    info: Dict[str, Any] = Field(default_factory=dict)


class GradeResult(BaseModel):
    task_id: str
    score: float = Field(ge=0.0, le=1.0)
    detail: Dict[str, Any] = Field(default_factory=dict)


class OpenEnvProtocol(ABC):
    @abstractmethod
    def metadata(self) -> EnvMetadata:
        raise NotImplementedError

    @abstractmethod
    def tasks(self) -> List[TaskInfo]:
        raise NotImplementedError

    @abstractmethod
    def reset(self, task_id: str, seed: Optional[int] = None) -> ResetResult:
        raise NotImplementedError

    @abstractmethod
    def step(self, action: Action) -> StepResult:
        raise NotImplementedError

    @abstractmethod
    def grade(self) -> GradeResult:
        raise NotImplementedError

    @abstractmethod
    def render(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
