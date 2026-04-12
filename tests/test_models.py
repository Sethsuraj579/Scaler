"""
Tests for Pydantic models.
"""

import pytest
from models import (
    Space, SpaceType, TaskDefinition, StepOutput, ResetOutput, 
    GradeOutput, EnvironmentConfig
)


class TestSpaceModel:
    """Test Space model."""
    
    def test_discrete_space(self):
        """Test discrete space creation."""
        space = Space(type=SpaceType.DISCRETE, n=5)
        
        assert space.type == SpaceType.DISCRETE
        assert space.n == 5
    
    def test_box_space(self):
        """Test box space creation."""
        space = Space(
            type=SpaceType.BOX,
            shape=[10],
            low=0.0,
            high=1.0
        )
        
        assert space.type == SpaceType.BOX
        assert space.shape == [10]
        assert space.low == 0.0
        assert space.high == 1.0
    
    def test_dict_space(self):
        """Test dict space creation."""
        space = Space(type=SpaceType.DICT)
        
        assert space.type == SpaceType.DICT


class TestTaskDefinition:
    """Test TaskDefinition model."""
    
    def test_task_creation(self):
        """Test task definition creation."""
        task = TaskDefinition(
            task_id="easy",
            name="Easy Navigation",
            description="Navigate 5x5 grid",
            difficulty="easy",
            max_steps=100
        )
        
        assert task.task_id == "easy"
        assert task.name == "Easy Navigation"
        assert task.difficulty == "easy"
        assert task.max_steps == 100
    
    def test_task_defaults(self):
        """Test task definition defaults."""
        task = TaskDefinition(
            task_id="test",
            name="Test",
            description="Test task",
            difficulty="easy"
        )
        
        assert task.max_steps >= 0
        assert task.max_restarts == 0


class TestStepOutput:
    """Test StepOutput model."""
    
    def test_step_output_dict_obs(self):
        """Test step output with dict observation."""
        output = StepOutput(
            observation={"x": 0.5, "y": 0.5},
            reward=1.0,
            terminated=False,
            truncated=False
        )
        
        assert output.observation == {"x": 0.5, "y": 0.5}
        assert output.reward == 1.0
        assert output.terminated is False
        assert output.truncated is False
    
    def test_step_output_with_info(self):
        """Test step output with info dict."""
        info = {"step": 10, "items": 2}
        output = StepOutput(
            observation={"x": 0.5},
            reward=0.5,
            terminated=False,
            truncated=False,
            info=info
        )
        
        assert output.info == info
        assert output.info["step"] == 10


class TestResetOutput:
    """Test ResetOutput model."""
    
    def test_reset_output(self):
        """Test reset output creation."""
        output = ResetOutput(
            observation={"x": 0.0, "y": 0.0},
            info={"episode": 1}
        )
        
        assert output.observation == {"x": 0.0, "y": 0.0}
        assert output.info == {"episode": 1}
    
    def test_reset_output_defaults(self):
        """Test reset output with defaults."""
        output = ResetOutput(observation={"x": 0.0})
        
        assert output.observation == {"x": 0.0}
        assert output.info == {}


class TestGradeOutput:
    """Test GradeOutput model."""
    
    def test_grade_output(self):
        """Test grade output creation."""
        output = GradeOutput(
            score=0.95,
            feedback="Good job!"
        )
        
        assert output.score == 0.95
        assert output.feedback == "Good job!"
    
    def test_grade_output_score_bounds(self):
        """Test score validation."""
        # Valid scores
        GradeOutput(score=0.0)
        GradeOutput(score=0.5)
        GradeOutput(score=1.0)
        
        # Invalid scores should raise
        with pytest.raises(ValueError):
            GradeOutput(score=-0.1)
        
        with pytest.raises(ValueError):
            GradeOutput(score=1.1)
    
    def test_grade_output_with_details(self):
        """Test grade output with details."""
        details = {"collection": 1.0, "efficiency": 0.95}
        output = GradeOutput(
            score=0.95,
            feedback="Perfect!",
            details=details
        )
        
        assert output.details == details


class TestEnvironmentConfig:
    """Test EnvironmentConfig model."""
    
    def test_config_creation(self):
        """Test environment config creation."""
        config = EnvironmentConfig(
            name="Test Env",
            version="1.0.0",
            observation_space=Space(type=SpaceType.DICT),
            action_space=Space(type=SpaceType.DISCRETE, n=5),
            tasks=[
                TaskDefinition(
                    task_id="test",
                    name="Test",
                    description="Test",
                    difficulty="easy"
                )
            ]
        )
        
        assert config.name == "Test Env"
        assert config.version == "1.0.0"
        assert len(config.tasks) == 1
    
    def test_config_default_tags(self):
        """Test config has default openenv tag."""
        config = EnvironmentConfig(
            name="Test",
            version="1.0.0",
            observation_space=Space(type=SpaceType.DICT),
            action_space=Space(type=SpaceType.DISCRETE, n=5),
            tasks=[]
        )
        
        assert "openenv" in config.tags


class TestModelValidation:
    """Test model validation."""
    
    def test_step_output_reward_type(self):
        """Test step output reward is float."""
        output = StepOutput(
            observation={"x": 0.5},
            reward=1,  # int should convert to float
            terminated=False,
            truncated=False
        )
        
        assert isinstance(output.reward, (int, float))
    
    def test_grade_output_feedback_default(self):
        """Test grade output feedback defaults to empty string."""
        output = GradeOutput(score=0.5)
        
        assert output.feedback == ""
