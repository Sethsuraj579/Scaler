#!/usr/bin/env python3
"""
API Integration Test Suite

Tests all OpenEnv API endpoints with real requests.
Run with: python api_test.py
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:7860"


def test_health() -> bool:
    """Test health check endpoint."""
    print("Testing /health...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("  ✓ Health check passed")
    return True


def test_config() -> bool:
    """Test config endpoint."""
    print("Testing /config...")
    response = requests.get(f"{BASE_URL}/config")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "tasks" in data
    assert len(data["tasks"]) == 3  # easy, medium, hard
    print("  ✓ Config retrieved (3 tasks)")
    return True


def test_reset_empty_body() -> Dict[str, Any]:
    """Test reset with empty body (uses default 'easy')."""
    print("Testing /reset with empty body...")
    response = requests.post(
        f"{BASE_URL}/reset",
        json={}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "observation" in data
    assert "info" in data
    print(f"  ✓ Reset successful (session: {data['session_id']})")
    return data


def test_reset_with_task(task_id: str) -> Dict[str, Any]:
    """Test reset with specific task."""
    print(f"Testing /reset with task_id='{task_id}'...")
    response = requests.post(
        f"{BASE_URL}/reset",
        json={"task_id": task_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    print(f"  ✓ Reset {task_id} successful")
    return data


def test_step(session_id: str, action: int) -> Dict[str, Any]:
    """Test step endpoint."""
    print(f"Testing /step (action={action}, session={session_id})...")
    response = requests.post(
        f"{BASE_URL}/step",
        json={"action": action, "session_id": session_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "observation" in data
    assert "reward" in data
    assert "terminated" in data
    assert "truncated" in data
    print(f"  ✓ Step successful (reward: {data['reward']:.2f})")
    return data


def test_grade() -> Dict[str, Any]:
    """Test grade endpoint."""
    print("Testing /grade...")
    response = requests.post(
        f"{BASE_URL}/grade",
        json={
            "task_id": "easy",
            "cumulative_reward": 2.5,
            "items_collected": 3,
            "total_items": 3,
            "steps_taken": 45,
            "max_steps": 100,
            "hit_hazard": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "feedback" in data
    assert 0.0 <= data["score"] <= 1.0
    print(f"  ✓ Grade successful (score: {data['score']:.3f})")
    return data


def test_render(session_id: str) -> bool:
    """Test render endpoint."""
    print(f"Testing /render/{session_id}...")
    response = requests.get(f"{BASE_URL}/render/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data
    print(f"  ✓ Render successful")
    return True


def test_invalid_session() -> bool:
    """Test error handling for invalid session."""
    print("Testing error handling (invalid session)...")
    response = requests.post(
        f"{BASE_URL}/step",
        json={"action": 0, "session_id": "invalid_session_xyz"}
    )
    assert response.status_code == 404
    print("  ✓ Error handling works correctly")
    return True


def test_invalid_action() -> bool:
    """Test error handling for invalid action."""
    print("Testing error handling (invalid action)...")
    response = requests.post(
        f"{BASE_URL}/reset",
        json={}
    )
    session_id = response.json()["session_id"]
    
    response = requests.post(
        f"{BASE_URL}/step",
        json={"action": 99, "session_id": session_id}
    )
    assert response.status_code == 400
    print("  ✓ Invalid action rejected")
    return True


def run_full_episode(task_id: str = "easy", num_steps: int = 10) -> Dict[str, Any]:
    """Run a complete episode."""
    print(f"\n{'='*60}")
    print(f"Running full episode: {task_id} ({num_steps} steps)")
    print(f"{'='*60}")
    
    # Reset
    reset_data = test_reset_with_task(task_id)
    session_id = reset_data["session_id"]
    observation = reset_data["observation"]
    cumulative_reward = 0.0
    
    # Steps
    for step_num in range(num_steps):
        # Simple greedy agent: move right if space available
        action = 3 if observation.get("agent_x", 0) < 0.9 else 0
        step_data = test_step(session_id, action)
        
        cumulative_reward += step_data["reward"]
        observation = step_data["observation"]
        
        if step_data["terminated"] or step_data["truncated"]:
            print(f"  → Episode ended at step {step_num + 1}")
            break
    
    # Grade
    info = step_data["info"] if "info" in step_data else {}
    grade_data = requests.post(
        f"{BASE_URL}/grade",
        json={
            "task_id": task_id,
            "cumulative_reward": cumulative_reward,
            "items_collected": info.get("collected_items", 0),
            "total_items": info.get("total_items", 3),
            "steps_taken": info.get("step", num_steps),
            "max_steps": 100 if task_id == "easy" else 200,
        }
    ).json()
    
    print(f"  Final Score: {grade_data['score']:.3f}")
    print(f"  Items Collected: {info.get('collected_items', 0)}")
    print(f"  Cumulative Reward: {cumulative_reward:.2f}")
    print(f"  Feedback: {grade_data['feedback']}")
    
    return grade_data


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("OpenEnv API Integration Tests")
    print("="*60 + "\n")
    
    try:
        # Basic functionality tests
        test_health()
        test_config()
        
        # Reset tests
        reset_data = test_reset_empty_body()
        session_id = reset_data["session_id"]
        
        # Step tests
        test_step(session_id, 0)  # UP
        test_step(session_id, 3)  # RIGHT
        
        # Grade test
        test_grade()
        
        # Render test
        test_render(session_id)
        
        # Error handling
        test_invalid_session()
        test_invalid_action()
        
        # Full episodes
        run_full_episode("easy", num_steps=10)
        run_full_episode("medium", num_steps=20)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API server at", BASE_URL)
        print("Make sure uvicorn is running: python -m uvicorn app:app --port 7860\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
