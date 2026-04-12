"""
Tests for grading system.
"""

import pytest
from graders import TaskGrader
from models import GradeOutput


class TestGrading:
    """Test episode grading functionality."""
    
    def test_grade_perfect_episode(self):
        """Test grading a perfect episode."""
        grade = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=10,
            max_steps=100,
            hit_hazard=False
        )
        
        assert isinstance(grade, GradeOutput)
        assert grade.score >= 0.9
        assert grade.score <= 1.0
        assert "Perfect" in grade.feedback or "perfect" in grade.feedback
    
    def test_grade_partial_episode(self):
        """Test grading a partial collection episode."""
        grade = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=1.5,
            items_collected=2,
            total_items=3,
            steps_taken=50,
            max_steps=100,
            hit_hazard=False
        )
        
        assert isinstance(grade, GradeOutput)
        assert 0.0 <= grade.score <= 1.0
        assert grade.feedback is not None
    
    def test_grade_failed_episode(self):
        """Test grading a failed episode."""
        grade = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=-5.0,
            items_collected=0,
            total_items=3,
            steps_taken=100,
            max_steps=100,
            hit_hazard=True
        )
        
        assert isinstance(grade, GradeOutput)
        assert 0.0 <= grade.score <= 1.0
        assert grade.score < 0.5  # Should be low score
    
    def test_grade_efficiency_score(self):
        """Test efficiency scoring."""
        # Fast episode
        grade_fast = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=10,
            max_steps=100,
            hit_hazard=False
        )
        
        # Slow episode
        grade_slow = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=90,
            max_steps=100,
            hit_hazard=False
        )
        
        # Fast should score higher
        assert grade_fast.score > grade_slow.score
    
    def test_grade_collection_impact(self):
        """Test collection score impact."""
        # Full collection
        grade_full = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=50,
            max_steps=100,
            hit_hazard=False
        )
        
        # Partial collection
        grade_partial = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=1.5,
            items_collected=1,
            total_items=3,
            steps_taken=50,
            max_steps=100,
            hit_hazard=False
        )
        
        # Full collection should score much higher
        assert grade_full.score > grade_partial.score
    
    def test_grade_hazard_impact(self):
        """Test hazard hit impact on score."""
        # No hazard
        grade_safe = TaskGrader.grade_episode(
            task_id="medium",
            cumulative_reward=2.0,
            items_collected=6,
            total_items=8,
            steps_taken=100,
            max_steps=200,
            hit_hazard=False
        )
        
        # Hit hazard
        grade_danger = TaskGrader.grade_episode(
            task_id="medium",
            cumulative_reward=-5.0,
            items_collected=6,
            total_items=8,
            steps_taken=100,
            max_steps=200,
            hit_hazard=True
        )
        
        # Safe should score higher
        assert grade_safe.score > grade_danger.score
    
    def test_grade_details(self):
        """Test grade details are populated."""
        grade = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=10,
            max_steps=100,
            hit_hazard=False
        )
        
        assert grade.details is not None
        assert "collection_score" in grade.details
        assert "efficiency_score" in grade.details
        assert "risk_score" in grade.details
        assert "items_collected" in grade.details
    
    def test_grade_score_bounds(self):
        """Test grade score is always between 0 and 1."""
        test_cases = [
            (3, 3, 10, False),
            (0, 3, 100, True),
            (2, 3, 50, False),
            (1, 3, 100, True),
        ]
        
        for items, total, steps, hazard in test_cases:
            grade = TaskGrader.grade_episode(
                task_id="easy",
                cumulative_reward=items,
                items_collected=items,
                total_items=total,
                steps_taken=steps,
                max_steps=100,
                hit_hazard=hazard
            )
            
            assert 0.0 <= grade.score <= 1.0
    
    def test_grade_feedback_format(self):
        """Test feedback is properly formatted."""
        grade = TaskGrader.grade_episode(
            task_id="easy",
            cumulative_reward=2.95,
            items_collected=3,
            total_items=3,
            steps_taken=10,
            max_steps=100,
            hit_hazard=False
        )
        
        assert isinstance(grade.feedback, str)
        assert len(grade.feedback) > 0
        assert "|" in grade.feedback  # Contains separators


class TestDifferentTasks:
    """Test grading across different task difficulties."""
    
    def test_grade_medium_task(self):
        """Test grading medium difficulty task."""
        grade = TaskGrader.grade_episode(
            task_id="medium",
            cumulative_reward=4.0,
            items_collected=6,
            total_items=8,
            steps_taken=100,
            max_steps=200,
            hit_hazard=False
        )
        
        assert 0.0 <= grade.score <= 1.0
        assert isinstance(grade.feedback, str)
    
    def test_grade_hard_task(self):
        """Test grading hard difficulty task."""
        grade = TaskGrader.grade_episode(
            task_id="hard",
            cumulative_reward=5.0,
            items_collected=10,
            total_items=15,
            steps_taken=140,
            max_steps=150,
            hit_hazard=False
        )
        
        assert 0.0 <= grade.score <= 1.0
        assert isinstance(grade.feedback, str)
