"""Task graders for OpenEnv mini-game."""

from models import GradeOutput
from typing import Dict, Any


class TaskGrader:
    """Grades agent performance on tasks."""
    
    @staticmethod
    def grade_episode(
        task_id: str,
        cumulative_reward: float,
        items_collected: int,
        total_items: int,
        steps_taken: int,
        max_steps: int,
        hit_hazard: bool = False
    ) -> GradeOutput:
        """
        Grade an episode with scoring from 0.0 to 1.0.
        
        Scoring Criteria:
        1. Collection Rate: How many items were collected (weight: 50%)
        2. Efficiency: How efficiently steps were used (weight: 30%)
        3. Risk Management: Avoiding hazards (weight: 20%)
        """
        
        # Collection score (0-1)
        collection_score = items_collected / max(1, total_items)
        
        # Efficiency score (penalize wasted steps)
        min_steps = max(1, total_items * 2)  # Rough minimum for collection
        efficiency_ratio = min(steps_taken / max_steps, 1.0)
        efficiency_score = 1.0 - (efficiency_ratio * 0.5)  # Max 0.5 penalty for using all steps
        
        # Risk management score
        risk_score = 0.0 if hit_hazard else 1.0
        
        # Weighted combination
        final_score = (
            collection_score * 0.5 +
            efficiency_score * 0.3 +
            risk_score * 0.2
        )
        
        # Extra bonus for perfect (or near-perfect) collection
        if collection_score >= 0.8:
            final_score = min(1.0, final_score * 1.1)
        
        final_score = max(0.0, min(1.0, final_score))
        
        # Generate feedback
        feedback = _generate_feedback(
            task_id, collection_score, efficiency_score, risk_score, final_score
        )
        
        details = {
            "collection_score": collection_score,
            "efficiency_score": efficiency_score,
            "risk_score": risk_score,
            "items_collected": items_collected,
            "total_items": total_items,
            "steps_taken": steps_taken,
            "max_steps": max_steps,
            "hit_hazard": hit_hazard,
        }
        
        return GradeOutput(
            score=final_score,
            feedback=feedback,
            details=details
        )


def _generate_feedback(
    task_id: str,
    collection_score: float,
    efficiency_score: float,
    risk_score: float,
    final_score: float
) -> str:
    """Generate human-readable feedback based on performance."""
    messages = []
    
    # Collection feedback
    if collection_score >= 1.0:
        messages.append("✓ Perfect item collection!")
    elif collection_score >= 0.8:
        messages.append(f"✓ Good item collection ({collection_score*100:.0f}%)")
    elif collection_score >= 0.5:
        messages.append(f"◐ Moderate collection ({collection_score*100:.0f}%)")
    else:
        messages.append(f"✗ Low collection ({collection_score*100:.0f}%)")
    
    # Efficiency feedback
    if efficiency_score >= 0.9:
        messages.append("✓ Excellent step efficiency")
    elif efficiency_score >= 0.7:
        messages.append("◐ Decent step efficiency")
    else:
        messages.append("✗ Poor step efficiency, wasted many steps")
    
    # Risk feedback
    if risk_score >= 1.0:
        messages.append("✓ Avoided all hazards")
    else:
        messages.append("✗ Hit a hazard, episode terminated early")
    
    # Overall feedback
    if final_score >= 0.9:
        messages.append("★ Outstanding performance!")
    elif final_score >= 0.7:
        messages.append("★ Good performance")
    elif final_score >= 0.5:
        messages.append("◇ Room for improvement")
    else:
        messages.append("◇ Needs more practice")
    
    return " | ".join(messages)
