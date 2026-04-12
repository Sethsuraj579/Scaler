"""
Tests for inference agents and runner.
"""

import pytest
from inference import SimpleAgents, InferenceRunner
from environment import OpenEnvWrapper


class TestSimpleAgents:
    """Test simple agent strategies."""
    
    def test_random_agent_returns_valid_action(self):
        """Test random agent returns valid action."""
        env = OpenEnvWrapper(task_id="easy")
        env.reset()
        obs = env.env._get_observation()
        
        action = SimpleAgents.random_agent(obs)
        
        assert isinstance(action, int)
        assert 0 <= action <= 4
    
    def test_greedy_agent_returns_valid_action(self):
        """Test greedy agent returns valid action."""
        env = OpenEnvWrapper(task_id="easy")
        env.reset()
        obs = env.env._get_observation()
        
        action = SimpleAgents.greedy_agent(obs)
        
        assert isinstance(action, int)
        assert 0 <= action <= 4
    
    def test_exploring_agent_returns_valid_action(self):
        """Test exploring agent returns valid action."""
        env = OpenEnvWrapper(task_id="easy")
        env.reset()
        obs = env.env._get_observation()
        
        action = SimpleAgents.exploring_agent(obs)
        
        assert isinstance(action, int)
        assert 0 <= action <= 4
    
    def test_corner_cleaner_returns_valid_action(self):
        """Test corner cleaner returns valid action."""
        env = OpenEnvWrapper(task_id="easy")
        env.reset()
        obs = env.env._get_observation()
        
        action = SimpleAgents.corner_cleaner(obs)
        
        assert isinstance(action, int)
        assert 0 <= action <= 4


class TestInferenceRunner:
    """Test InferenceRunner functionality."""
    
    def test_runner_initialization(self):
        """Test inference runner initialization."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        
        assert runner.task_id == "easy"
        assert runner.episode_count == 0
        assert runner.total_reward == 0.0
    
    def test_run_single_episode(self):
        """Test running single episode."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        
        episode_data = runner.run_episode(
            action_fn=SimpleAgents.greedy_agent,
            episode_name="Test"
        )
        
        assert episode_data is not None
        assert "steps" in episode_data
        assert "score" in episode_data
        assert "cumulative_reward" in episode_data
        assert 0.0 <= episode_data["score"] <= 1.0
    
    def test_run_multiple_episodes(self):
        """Test running multiple episodes."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        
        episodes = runner.run_multiple(
            action_fn=SimpleAgents.greedy_agent,
            num_episodes=2
        )
        
        assert len(episodes) == 2
        assert all("score" in ep for ep in episodes)
        assert all(0.0 <= ep["score"] <= 1.0 for ep in episodes)
    
    def test_episode_increments_counter(self):
        """Test episode counter increments."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        
        assert runner.episode_count == 0
        runner.run_episode(action_fn=SimpleAgents.greedy_agent)
        assert runner.episode_count == 1
        runner.run_episode(action_fn=SimpleAgents.greedy_agent)
        assert runner.episode_count == 2
    
    def test_episode_data_completeness(self):
        """Test episode data contains all expected fields."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        
        episode = runner.run_episode(
            action_fn=SimpleAgents.greedy_agent
        )
        
        required_fields = [
            "episode", "task_id", "steps", "cumulative_reward",
            "items_collected", "terminated", "truncated",
            "score", "feedback", "grade_details"
        ]
        
        for field in required_fields:
            assert field in episode


class TestAgentPerformance:
    """Test agent performance characteristics."""
    
    def test_greedy_solves_easy(self):
        """Test greedy agent achieves good score on easy task."""
        runner = InferenceRunner(task_id="easy", verbose=False)
        episode = runner.run_episode(
            action_fn=SimpleAgents.greedy_agent
        )
        
        # Greedy should get reasonable score on easy (better than average)
        assert episode["score"] > 0.4, f"Expected score > 0.4, got {episode['score']}"
        assert episode["items_collected"] >= 1, "Should collect at least 1 item"
    
    def test_random_vs_greedy_easy(self):
        """Test greedy outperforms random on easy."""
        runner_greedy = InferenceRunner(task_id="easy", verbose=False)
        ep_greedy = runner_greedy.run_episode(
            action_fn=SimpleAgents.greedy_agent
        )
        
        runner_random = InferenceRunner(task_id="easy", verbose=False)
        ep_random = runner_random.run_episode(
            action_fn=SimpleAgents.random_agent
        )
        
        # Greedy should score better
        assert ep_greedy["score"] > ep_random["score"]


class TestInferenceIntegration:
    """Integration tests for inference system."""
    
    def test_full_inference_workflow(self):
        """Test full inference workflow."""
        runner = InferenceRunner(task_id="medium", verbose=False)
        
        # Run multiple episodes with different agents
        episodes_greedy = runner.run_multiple(
            action_fn=SimpleAgents.greedy_agent,
            num_episodes=2
        )
        
        runner_exploring = InferenceRunner(task_id="medium", verbose=False)
        episodes_exploring = runner_exploring.run_multiple(
            action_fn=SimpleAgents.exploring_agent,
            num_episodes=2
        )
        
        # Both should produce valid results
        assert len(episodes_greedy) == 2
        assert len(episodes_exploring) == 2
        
        # Both should have scores
        for ep in episodes_greedy + episodes_exploring:
            assert 0.0 <= ep["score"] <= 1.0
    
    def test_different_tasks_with_runner(self):
        """Test runner with different difficulty levels."""
        for task_id in ["easy", "medium", "hard"]:
            runner = InferenceRunner(task_id=task_id, verbose=False)
            episode = runner.run_episode(
                action_fn=SimpleAgents.greedy_agent
            )
            
            assert episode["task_id"] == task_id
            assert 0.0 <= episode["score"] <= 1.0
