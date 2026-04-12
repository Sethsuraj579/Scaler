"""OpenEnv API Server for GridNav Environment."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from environment import OpenEnvWrapper, Action
from models import StepOutput, ResetOutput, EnvironmentConfig
from graders import TaskGrader


# Initialize FastAPI app
app = FastAPI(
    title="GridNav - OpenEnv Environment",
    description="Grid Navigation & Item Collection Environment",
    version="1.0.0"
)

# Add CORS middleware for Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active environments (in production, use proper session management)
environments: Dict[str, OpenEnvWrapper] = {}


# Request/Response Models
class ResetRequest(BaseModel):
    """Request to reset environment."""
    task_id: str = "easy"
    session_id: Optional[str] = None


class StepRequest(BaseModel):
    """Request to step environment."""
    action: int
    session_id: str


class GradeRequest(BaseModel):
    """Request to grade an episode."""
    task_id: str
    cumulative_reward: float
    items_collected: int
    total_items: int
    steps_taken: int
    max_steps: int
    hit_hazard: bool = False


# Routes

@app.get("/")
def root():
    """Root endpoint returns environment info."""
    return {
        "name": "GridNav - Grid Navigation & Item Collection",
        "version": "1.0.0",
        "description": "An OpenEnv environment where AI agents navigate grids to collect items",
        "endpoints": {
            "config": "/config",
            "reset": "/reset",
            "step": "/step",
            "grade": "/grade",
            "render": "/render",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "ready": True}


@app.get("/config")
def get_config():
    """Get environment configuration (OpenEnv spec)."""
    config = OpenEnvWrapper.get_config()
    return config.dict()


@app.post("/reset")
def reset_environment(request: ResetRequest):
    """
    Reset the environment and start a new episode.
    
    Args:
        request: Reset request with task_id and optional session_id
    
    Returns:
        Initial observation and episode info
    """
    session_id = request.session_id or f"session_{len(environments)}"
    
    try:
        env = OpenEnvWrapper(task_id=request.task_id)
        reset_output = env.reset()
        
        # Store environment for this session
        environments[session_id] = env
        
        return {
            "session_id": session_id,
            "observation": reset_output.observation,
            "info": {
                **reset_output.info,
                "session_id": session_id
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task_id: {str(e)}")


@app.post("/step")
def step_environment(request: StepRequest):
    """
    Execute one step in the environment.
    
    Args:
        request: Step request with action and session_id
    
    Returns:
        Observation, reward, done flags, and info
    """
    if request.session_id not in environments:
        raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")
    
    try:
        if request.action < 0 or request.action > 4:
            raise ValueError(f"Invalid action: {request.action}. Must be 0-4.")
        
        env = environments[request.session_id]
        step_output = env.step(request.action)
        
        return {
            "observation": step_output.observation,
            "reward": step_output.reward,
            "terminated": step_output.terminated,
            "truncated": step_output.truncated,
            "info": step_output.info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/grade")
def grade_episode(request: GradeRequest):
    """
    Grade an episode performance.
    
    Args:
        request: Grading request with episode stats
    
    Returns:
        Score (0.0-1.0) and feedback
    """
    try:
        grade_output = TaskGrader.grade_episode(
            task_id=request.task_id,
            cumulative_reward=request.cumulative_reward,
            items_collected=request.items_collected,
            total_items=request.total_items,
            steps_taken=request.steps_taken,
            max_steps=request.max_steps,
            hit_hazard=request.hit_hazard
        )
        
        return {
            "score": grade_output.score,
            "feedback": grade_output.feedback,
            "details": grade_output.details
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/render/{session_id}")
def render_environment(session_id: str):
    """
    Get a text-based rendering of the current grid state.
    
    Args:
        session_id: Session identifier
    
    Returns:
        ASCII art representation of the grid
    """
    if session_id not in environments:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    
    env = environments[session_id]
    grid_render = env.render()
    
    return {
        "session_id": session_id,
        "grid": grid_render,
        "task": env.task_id,
        "step": env.env.step_count,
        "agent_pos": env.env.agent_pos
    }


@app.get("/tasks")
def list_tasks():
    """List all available tasks."""
    config = OpenEnvWrapper.get_config()
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "name": t.name,
                "description": t.description,
                "difficulty": t.difficulty,
                "max_steps": t.max_steps
            }
            for t in config.tasks
        ]
    }


@app.get("/action-space")
def get_action_space():
    """Get information about the action space."""
    return {
        "type": "discrete",
        "n": 5,
        "actions": {
            "0": "UP - Move agent up",
            "1": "DOWN - Move agent down",
            "2": "LEFT - Move agent left",
            "3": "RIGHT - Move agent right",
            "4": "COLLECT - Attempt to collect item at current position"
        }
    }


@app.get("/observation-space")
def get_observation_space():
    """Get information about the observation space."""
    return {
        "type": "dict",
        "keys": {
            "agent_x": "Agent X position (normalized 0-1)",
            "agent_y": "Agent Y position (normalized 0-1)",
            "closest_item_x": "Closest item X position (normalized 0-1)",
            "closest_item_y": "Closest item Y position (normalized 0-1)",
            "closest_item_dist": "Distance to closest uncollected item (normalized)",
            "items_collected": "Fraction of items collected (0-1)",
            "steps_remaining": "Fraction of episode steps remaining (0-1)",
            "cumulative_reward": "Total reward accumulated so far"
        }
    }