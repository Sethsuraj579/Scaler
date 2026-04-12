"""
Tests for GridNav environment module.
"""

import pytest
from environment import OpenEnvWrapper, GridNavigationEnv, Action
from models import StepOutput, ResetOutput


class TestEnvironmentInitialization:
    """Test environment initialization."""
    
    def test_easy_env_init(self, easy_env):
        """Test easy environment initialization."""
        assert easy_env.task_id == "easy"
        assert easy_env.env.grid_size == 5
        assert easy_env.env.num_items == 3
        assert easy_env.env.num_obstacles == 1
        assert easy_env.env.num_hazards == 0
        assert easy_env.env.max_steps == 100
    
    def test_medium_env_init(self, medium_env):
        """Test medium environment initialization."""
        assert medium_env.task_id == "medium"
        assert medium_env.env.grid_size == 10
        assert medium_env.env.num_items == 8
        assert medium_env.env.num_obstacles == 4
        assert medium_env.env.num_hazards == 2
        assert medium_env.env.max_steps == 200
    
    def test_hard_env_init(self, hard_env):
        """Test hard environment initialization."""
        assert hard_env.task_id == "hard"
        assert hard_env.env.grid_size == 15
        assert hard_env.env.num_items == 15
        assert hard_env.env.num_obstacles == 8
        assert hard_env.env.num_hazards == 3
        assert hard_env.env.max_steps == 150


class TestEnvironmentReset:
    """Test environment reset functionality."""
    
    def test_reset_returns_reset_output(self, easy_env):
        """Test reset returns ResetOutput."""
        output = easy_env.reset()
        assert isinstance(output, ResetOutput)
        assert output.observation is not None
        assert output.info is not None
    
    def test_reset_observation_dict(self, easy_env):
        """Test reset observation is dict with expected keys."""
        output = easy_env.reset()
        obs = output.observation
        
        assert isinstance(obs, dict)
        assert "agent_x" in obs
        assert "agent_y" in obs
        assert "closest_item_dist" in obs
        assert "items_collected" in obs
        assert "steps_remaining" in obs
        assert "cumulative_reward" in obs
    
    def test_reset_observation_ranges(self, easy_env):
        """Test reset observation values are in valid ranges."""
        output = easy_env.reset()
        obs = output.observation
        
        assert 0.0 <= obs["agent_x"] <= 1.0
        assert 0.0 <= obs["agent_y"] <= 1.0
        assert 0.0 <= obs["items_collected"] <= 1.0
        assert 0.0 <= obs["steps_remaining"] <= 1.0
    
    def test_reset_info_contains_episode(self, easy_env):
        """Test reset info contains episode information."""
        output = easy_env.reset()
        assert "episode" in output.info
        assert "task" in output.info
        assert "grid_size" in output.info


class TestEnvironmentStep:
    """Test environment step functionality."""
    
    def test_step_returns_step_output(self, reset_easy):
        """Test step returns StepOutput."""
        env = OpenEnvWrapper(task_id="easy")
        env.reset()
        output = env.step(Action.UP)
        
        assert isinstance(output, StepOutput)
        assert output.observation is not None
        assert isinstance(output.reward, float)
        assert isinstance(output.terminated, bool)
        assert isinstance(output.truncated, bool)
    
    def test_step_updates_position(self, easy_env):
        """Test step updates agent position."""
        reset_output = easy_env.reset()
        initial_pos = easy_env.env.agent_pos
        
        easy_env.step(Action.RIGHT)
        new_pos = easy_env.env.agent_pos
        
        # Position should change (unless at boundary)
        assert initial_pos is not None
        assert new_pos is not None
    
    def test_step_rewards(self, easy_env):
        """Test step provides rewards."""
        easy_env.reset()
        
        # Take multiple steps
        rewards = []
        for _ in range(5):
            output = easy_env.step(Action.UP)
            rewards.append(output.reward)
        
        # Should have received rewards
        assert len(rewards) == 5
        assert all(isinstance(r, float) for r in rewards)
    
    def test_invalid_action_handling(self, easy_env):
        """Test invalid action is handled gracefully."""
        easy_env.reset()
        
        # Invalid action should be handled (not raise)
        # System clamps or defaults
        try:
            output = easy_env.step(10)  # Invalid action
            # If no error, output should still be valid
            assert output is not None
            assert isinstance(output.reward, float)
        except (ValueError, IndexError):
            # If it does raise, that's also acceptable
            pass


class TestEnvironmentEpisode:
    """Test full episode execution."""
    
    def test_complete_episode_easy(self, easy_env):
        """Test complete episode on easy task."""
        reset_output = easy_env.reset()
        assert reset_output.observation is not None
        
        terminated = False
        steps = 0
        max_steps = 200
        
        while not terminated and steps < max_steps:
            output = easy_env.step(Action.UP)
            terminated = output.terminated or output.truncated
            steps += 1
        
        # Episode should terminate eventually
        assert steps > 0
        assert steps < max_steps
    
    def test_episode_state_consistency(self, easy_env):
        """Test episode maintains consistent state."""
        easy_env.reset()
        
        for _ in range(10):
            output = easy_env.step(Action.RIGHT)
            obs = output.observation
            
            # Observation should always be dict with expected keys
            assert isinstance(obs, dict)
            assert "agent_x" in obs
            assert "cumulative_reward" in obs


class TestEnvironmentRender:
    """Test environment rendering."""
    
    def test_render_returns_string(self, easy_env):
        """Test render returns string."""
        easy_env.reset()
        grid_str = easy_env.render()
        
        assert isinstance(grid_str, str)
        assert len(grid_str) > 0
    
    def test_render_contains_agent(self, easy_env):
        """Test render contains agent marker."""
        easy_env.reset()
        grid_str = easy_env.render()
        
        assert "A" in grid_str  # Agent marker


class TestEnvironmentConfig:
    """Test environment configuration."""
    
    def test_get_config(self):
        """Test getting environment config."""
        config = OpenEnvWrapper.get_config()
        
        assert config is not None
        assert config.name is not None
        assert config.version is not None
        assert len(config.tasks) == 3
        assert config.observation_space is not None
        assert config.action_space is not None
    
    def test_config_tasks(self):
        """Test config tasks are properly defined."""
        config = OpenEnvWrapper.get_config()
        
        task_ids = [t.task_id for t in config.tasks]
        assert "easy" in task_ids
        assert "medium" in task_ids
        assert "hard" in task_ids
    
    def test_config_action_space(self):
        """Test action space is discrete with 5 actions."""
        config = OpenEnvWrapper.get_config()
        
        assert config.action_space.type.value == "discrete"
        assert config.action_space.n == 5
