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
    task_id: Optional[str] = "easy"
    session_id: Optional[str] = None


class StepRequest(BaseModel):
    """Request to step environment."""
    action: Optional[int] = None
    session_id: Optional[str] = None


class GradeRequest(BaseModel):
    """Request to grade an episode."""
    task_id: Optional[str] = "easy"
    cumulative_reward: float = 0.0
    items_collected: int = 0
    total_items: int = 3
    steps_taken: int = 0
    max_steps: int = 100
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
def reset_environment(task_id: Optional[str] = None, session_id: Optional[str] = None):
    """
    Reset the environment and start a new episode.
    
    Args:
        task_id: Task difficulty ("easy", "medium", "hard"), default is "easy"
        session_id: Optional session identifier
    
    Returns:
        Initial observation and episode info
    """
    task = task_id or "easy"
    sid = session_id or f"session_{len(environments)}"
    
    try:
        env = OpenEnvWrapper(task_id=task)
        reset_output = env.reset()
        
        # Store environment for this session
        environments[sid] = env
        
        return {
            "session_id": sid,
            "observation": reset_output.observation,
            "info": {
                **reset_output.info,
                "session_id": sid
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task_id: {str(e)}")


@app.post("/step")
def step_environment(action: Optional[int] = None, session_id: Optional[str] = None):
    """
    Execute one step in the environment.
    
    Args:
        action: Action to take (0-4), default is 0
        session_id: Session identifier (uses latest if not specified)
    
    Returns:
        Observation, reward, done flags, and info
    """
    sid = session_id
    
    # Use latest session if not specified
    if not sid:
        if not environments:
            raise HTTPException(status_code=404, detail="No session available. Call /reset first.")
        sid = list(environments.keys())[-1]
    
    if sid not in environments:
        raise HTTPException(status_code=404, detail=f"Session not found: {sid}")
    
    # Default to action 0 if not specified
    act = action if action is not None else 0
    
    try:
        if act < 0 or act > 4:
            raise ValueError(f"Invalid action: {act}. Must be 0-4.")
        
        env = environments[sid]
        step_output = env.step(act)
        
        return {
            "session_id": sid,
            "observation": step_output.observation,
            "reward": step_output.reward,
            "terminated": step_output.terminated,
            "truncated": step_output.truncated,
            "info": step_output.info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/grade")
def grade_episode(
    task_id: Optional[str] = "easy",
    cumulative_reward: float = 0.0,
    items_collected: int = 0,
    total_items: int = 3,
    steps_taken: int = 0,
    max_steps: int = 100,
    hit_hazard: bool = False
):
    """
    Grade an episode performance.
    
    Args:
        task_id: Task difficulty (easy, medium, hard)
        cumulative_reward: Total reward earned
        items_collected: Number of items collected
        total_items: Total items available
        steps_taken: Number of steps taken
        max_steps: Maximum steps allowed
        hit_hazard: Whether agent hit a hazard
    
    Returns:
        Score (0.0-1.0) and feedback
    """
    try:
        grade_output = TaskGrader.grade_episode(
            task_id=task_id,
            cumulative_reward=cumulative_reward,
            items_collected=items_collected,
            total_items=total_items,
            steps_taken=steps_taken,
            max_steps=max_steps,
            hit_hazard=hit_hazard
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


@app.get("/state/{session_id}")
def get_state(session_id: Optional[str] = None):
    """
    Get current environment state without taking a step.
    
    Args:
        session_id: Session identifier (uses latest if not provided)
    
    Returns:
        Current observation, env info, and metadata
    """
    sid = session_id
    
    # Use latest session if not specified
    if not sid:
        if not environments:
            raise HTTPException(status_code=404, detail="No session available. Call /reset first.")
        sid = list(environments.keys())[-1]
    
    if sid not in environments:
        raise HTTPException(status_code=404, detail=f"Session not found: {sid}")
    
    env = environments[sid]
    return {
        "session_id": sid,
        "observation": env.env._get_observation(),
        "info": {
            "step": env.env.step_count,
            "task": env.task_id,
            "grid_size": env.env.grid_size,
            "agent_pos": env.env.agent_pos,
            "items_collected": env.env.collected_items,
            "total_items": env.env.num_items,
            "steps_remaining": max(0, env.env.max_steps - env.env.step_count) / env.env.max_steps
        }
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


if __name__ == "__main__":
    """Run the FastAPI application locally."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info"
    )