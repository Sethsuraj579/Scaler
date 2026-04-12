"""OpenEnv Mini-Game: Grid Navigation & Item Collection"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import IntEnum
import random

from models import (
    Space, SpaceType, TaskDefinition, StepOutput, ResetOutput, 
    GradeOutput, EnvironmentConfig
)


class Action(IntEnum):
    """Discrete action space."""
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    COLLECT = 4


@dataclass
class GridObject:
    """Represents an object on the grid."""
    x: int
    y: int
    object_type: str  # "item", "obstacle", "hazard"
    value: float = 1.0  # Reward value if it's an item


class GridNavigationEnv:
    """
    OpenEnv Mini-Game: GridNav - Navigate a 2D grid to collect items.
    
    Three difficulty levels:
    - Easy: 5x5 grid, 3 items, 1 obstacle, unlimited steps
    - Medium: 10x10 grid, 8 items, 4 obstacles, hazards, 200 steps
    - Hard: 15x15 grid, 15 items, 8 obstacles, 3 hazards, 150 steps
    """
    
    def __init__(self, task_id: str = "easy"):
        self.task_id = task_id
        self._configure_task()
        self.reset_agent = True
        self.current_episode = 0
        
    def _configure_task(self):
        """Configure environment parameters based on task difficulty."""
        configs = {
            "easy": {
                "grid_size": 5,
                "num_items": 3,
                "num_obstacles": 1,
                "num_hazards": 0,
                "max_steps": 100,
                "item_values": [1.0] * 3,
            },
            "medium": {
                "grid_size": 10,
                "num_items": 8,
                "num_obstacles": 4,
                "num_hazards": 2,
                "max_steps": 200,
                "item_values": [1.0] * 8,
            },
            "hard": {
                "grid_size": 15,
                "num_items": 15,
                "num_obstacles": 8,
                "num_hazards": 3,
                "max_steps": 150,
                "item_values": [0.5 + i*0.1 for i in range(15)],  # Increasing values
            },
        }
        
        config = configs.get(self.task_id, configs["easy"])
        self.grid_size = config["grid_size"]
        self.num_items = config["num_items"]
        self.num_obstacles = config["num_obstacles"]
        self.num_hazards = config["num_hazards"]
        self.max_steps = config["max_steps"]
        self.item_values = config["item_values"]
        
        # State tracking
        self.agent_pos = None
        self.items = []
        self.obstacles = []
        self.hazards = []
        self.collected_items = 0
        self.step_count = 0
        self.cumulative_reward = 0.0
        
    def reset(self) -> ResetOutput:
        """Reset the environment and generate a new episode."""
        self.reset_agent = False
        self.current_episode += 1
        self.step_count = 0
        self.collected_items = 0
        self.cumulative_reward = 0.0
        
        # Place agent at random position
        self.agent_pos = self._get_random_position()
        
        # Generate items, obstacles, and hazards
        self.items = []
        self.obstacles = set()
        self.hazards = set()
        
        # Place items
        while len(self.items) < self.num_items:
            pos = self._get_random_position()
            if pos != self.agent_pos:
                self.items.append({
                    "pos": pos,
                    "collected": False,
                    "value": self.item_values[len(self.items)]
                })
        
        # Place obstacles
        while len(self.obstacles) < self.num_obstacles:
            pos = self._get_random_position()
            if pos != self.agent_pos and not any(item["pos"] == pos for item in self.items):
                self.obstacles.add(pos)
        
        # Place hazards
        while len(self.hazards) < self.num_hazards:
            pos = self._get_random_position()
            if (pos != self.agent_pos and pos not in self.obstacles and 
                not any(item["pos"] == pos for item in self.items)):
                self.hazards.add(pos)
        
        obs = self._get_observation()
        return ResetOutput(
            observation=obs,
            info={
                "episode": self.current_episode,
                "task": self.task_id,
                "grid_size": self.grid_size,
                "items_available": self.num_items,
            }
        )
    
    def step(self, action: int) -> StepOutput:
        """Execute one step of the environment."""
        if self.reset_agent:
            raise RuntimeError("Must call reset() before step()")
        
        self.step_count += 1
        reward = 0.0
        terminated = False
        truncated = False
        
        # Movement actions
        if action in [Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT]:
            reward, hit_hazard = self._move_agent(action)
            if hit_hazard:
                terminated = True  # Episode ends on hazard
        
        # Collection action
        elif action == Action.COLLECT:
            reward = self._try_collect()
        
        self.cumulative_reward += reward
        
        # Check termination conditions
        if self.step_count >= self.max_steps:
            truncated = True
        
        # Win condition: collect all items
        if self.collected_items == self.num_items:
            terminated = True
            reward += 5.0  # Bonus for completing the task
        
        obs = self._get_observation()
        
        return StepOutput(
            observation=obs,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info={
                "step": self.step_count,
                "collected_items": self.collected_items,
                "total_items": self.num_items,
                "cumulative_reward": self.cumulative_reward,
                "agent_pos": self.agent_pos,
            }
        )
    
    def _move_agent(self, action: int) -> Tuple[float, bool]:
        """Move the agent and return reward and hazard collision status."""
        old_pos = self.agent_pos
        dx, dy = 0, 0
        
        if action == Action.UP:
            dy = -1
        elif action == Action.DOWN:
            dy = 1
        elif action == Action.LEFT:
            dx = -1
        elif action == Action.RIGHT:
            dx = 1
        
        new_x = max(0, min(self.grid_size - 1, self.agent_pos[0] + dx))
        new_y = max(0, min(self.grid_size - 1, self.agent_pos[1] + dy))
        new_pos = (new_x, new_y)
        
        # Check for invalid moves (obstacles)
        if new_pos in self.obstacles:
            return -0.1, False  # Small penalty for hitting obstacle
        
        # Check for hazards
        if new_pos in self.hazards:
            self.agent_pos = new_pos
            return -5.0, True  # Large penalty and termination
        
        self.agent_pos = new_pos
        
        # Small reward for movement to encourage exploration
        reward = -0.01 if old_pos != new_pos else 0.0
        
        return reward, False
    
    def _try_collect(self) -> float:
        """Try to collect an item at current position."""
        for item in self.items:
            if not item["collected"] and item["pos"] == self.agent_pos:
                item["collected"] = True
                self.collected_items += 1
                return item["value"]
        
        return 0.0  # No item to collect
    
    def _get_observation(self) -> Dict[str, Any]:
        """Generate observation vector (dict-based for flexibility)."""
        # Agent position (normalized)
        agent_obs = {
            "agent_x": self.agent_pos[0] / self.grid_size,
            "agent_y": self.agent_pos[1] / self.grid_size,
        }
        
        # Closest uncollected item
        uncollected = [item for item in self.items if not item["collected"]]
        if uncollected:
            closest = min(uncollected, key=lambda i: self._distance(self.agent_pos, i["pos"]))
            dist = self._distance(self.agent_pos, closest["pos"])
            agent_obs["closest_item_x"] = closest["pos"][0] / self.grid_size
            agent_obs["closest_item_y"] = closest["pos"][1] / self.grid_size
            agent_obs["closest_item_dist"] = dist / (2 * self.grid_size)
        else:
            agent_obs["closest_item_dist"] = 0.0
        
        # Stats
        agent_obs["items_collected"] = self.collected_items / self.num_items
        agent_obs["steps_remaining"] = (self.max_steps - self.step_count) / self.max_steps
        agent_obs["cumulative_reward"] = self.cumulative_reward
        
        return agent_obs
    
    def _get_random_position(self) -> Tuple[int, int]:
        """Get a random position on the grid."""
        return (random.randint(0, self.grid_size - 1), 
                random.randint(0, self.grid_size - 1))
    
    @staticmethod
    def _distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def render(self) -> str:
        """Return a string representation of the current grid state."""
        grid = [['.' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Place obstacles
        for obs_pos in self.obstacles:
            grid[obs_pos[1]][obs_pos[0]] = '#'
        
        # Place hazards
        for haz_pos in self.hazards:
            grid[haz_pos[1]][haz_pos[0]] = 'X'
        
        # Place items
        for i, item in enumerate(self.items):
            if not item["collected"]:
                grid[item["pos"][1]][item["pos"][0]] = f'{i}'
        
        # Place agent
        grid[self.agent_pos[1]][self.agent_pos[0]] = 'A'
        
        return '\n'.join([''.join(row) for row in grid])


class OpenEnvWrapper:
    """Wrapper to provide OpenEnv-compliant interface."""
    
    ENVIRONMENT_CONFIG = EnvironmentConfig(
        name="GridNav - Grid Navigation & Item Collection",
        version="1.0.0",
        observation_space=Space(
            type=SpaceType.DICT,
            dtype="float32"
        ),
        action_space=Space(
            type=SpaceType.DISCRETE,
            n=5
        ),
        tasks=[
            TaskDefinition(task_id="easy", name="Easy Navigation", 
                          description="Navigate 5x5 grid, collect 3 items", 
                          difficulty="easy", max_steps=100),
            TaskDefinition(task_id="medium", name="Medium Navigation", 
                          description="Navigate 10x10 grid, collect 8 items with obstacles", 
                          difficulty="medium", max_steps=200),
            TaskDefinition(task_id="hard", name="Hard Navigation", 
                          description="Navigate 15x15 grid, collect 15 items with hazards", 
                          difficulty="hard", max_steps=150),
        ],
        tags=["openenv", "gridworld", "navigation", "item-collection"]
    )
    
    def __init__(self, task_id: str = "easy"):
        self.env = GridNavigationEnv(task_id)
        self.task_id = task_id
    
    def reset(self) -> ResetOutput:
        """Reset following OpenEnv interface."""
        return self.env.reset()
    
    def step(self, action: int) -> StepOutput:
        """Step following OpenEnv interface."""
        return self.env.step(action)
    
    def render(self) -> str:
        """Return visual representation."""
        return self.env.render()
    
    @classmethod
    def get_config(cls) -> EnvironmentConfig:
        """Get environment configuration."""
        return cls.ENVIRONMENT_CONFIG
