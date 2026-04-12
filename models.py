"""Pydantic models for OpenEnv specification compliance."""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class SpaceType(str, Enum):
    """Supported observation/action space types."""
    DISCRETE = "discrete"
    BOX = "box"
    MULTI_DISCRETE = "multi_discrete"
    MULTI_BINARY = "multi_binary"
    TUPLE = "tuple"
    DICT = "dict"


class Space(BaseModel):
    """Represents an observation or action space."""
    model_config = ConfigDict(extra="allow")
    
    type: SpaceType
    shape: Optional[List[int]] = None
    low: Optional[Union[int, float, List]] = None
    high: Optional[Union[int, float, List]] = None
    n: Optional[int] = None  # For discrete spaces
    dtype: str = "float32"


class TaskDefinition(BaseModel):
    """Definition of a task environment."""
    model_config = ConfigDict(extra="allow")
    
    task_id: str
    name: str
    description: str
    difficulty: str = Field(..., description="easy, medium, or hard")
    max_steps: int = Field(default=1000, description="Maximum episode length")
    max_restarts: int = Field(default=0, description="Maximum environment resets")


class StepOutput(BaseModel):
    """Output from environment.step()."""
    observation: Union[int, float, Dict, List]
    reward: float
    terminated: bool
    truncated: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetOutput(BaseModel):
    """Output from environment.reset()."""
    observation: Union[int, float, Dict, List]
    info: Dict[str, Any] = Field(default_factory=dict)


class GradeOutput(BaseModel):
    """Output from grading an episode."""
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    feedback: str = Field(default="", description="Human-readable feedback on performance")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional grading details")


class EnvironmentConfig(BaseModel):
    """Configuration for the environment."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    version: str
    observation_space: Space
    action_space: Space
    tasks: List[TaskDefinition]
    tags: List[str] = ["openenv"]
