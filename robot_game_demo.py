#!/usr/bin/env python3
"""
Robot Factory Mini-Game Demo
Demonstrates how an AI agent can play the three robot manufacturing tasks.
"""

from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action
import json


def print_observation(obs):
    """Pretty print the observation."""
    print(f"\n{'='*60}")
    print(f"Task: {obs.task_id}")
    print(f"Step: {obs.step_index}/{obs.max_steps}")
    print(f"Score: {obs.score:.2f} | Progress: {obs.progress:.2f}")
    print(f"Status: {obs.summary}")
    print(f"Allowed Commands: {', '.join(obs.allowed_commands)}")
    print(f"{'='*60}")
    print(f"State View:\n{json.dumps(obs.state_view, indent=2)}")


def play_easy_robot_assembly():
    """Play the easy robot assembly game."""
    print("\n" + "="*60)
    print("EASY ROBOT ASSEMBLY - Assemble robots from available parts")
    print("="*60)
    
    env = OpenEnvEnvironment()
    obs_result = env.reset(task_id="easy_robot_assembly", seed=42)
    obs = obs_result.observation
    
    print_observation(obs)
    
    # Strategy: Add all required parts, then complete robots
    actions = [
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "arms"}),
        Action(command="add_part", args={"part_type": "legs"}),
        Action(command="add_part", args={"part_type": "batteries"}),
        Action(command="complete_robot", args={}),
        Action(command="check_quality", args={}),
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "arms"}),
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"\nStep {i}: Executing {action.command} {action.args}")
        result = env.step(action)
        print(f"  ✓ Success: {result.info['applied']} | Reward: {result.reward}")
        print(f"  Score: {result.observation.score:.2f}")
        
        if i % 4 == 0:
            print_observation(result.observation)
    
    final_grade = env.grade()
    print(f"\n✓ Final Score: {final_grade.score:.2f}")
    env.close()


def play_medium_robot_factory():
    """Play the medium robot factory game."""
    print("\n" + "="*60)
    print("MEDIUM ROBOT FACTORY - Manage quality control and production")
    print("="*60)
    
    env = OpenEnvEnvironment()
    obs_result = env.reset(task_id="medium_robot_factory", seed=42)
    obs = obs_result.observation
    
    print_observation(obs)
    
    # Strategy: Build robots and test quality
    actions = [
        Action(command="add_part", args={"part_type": "arms"}),
        Action(command="add_part", args={"part_type": "legs"}),
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "batteries"}),
        Action(command="add_part", args={"part_type": "circuits"}),
        Action(command="test_quality", args={}),
        Action(command="complete_robot", args={}),
        Action(command="increase_speed", args={}),
        Action(command="add_part", args={"part_type": "arms"}),
        Action(command="add_part", args={"part_type": "legs"}),
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "batteries"}),
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"\nStep {i}: Executing {action.command} {action.args}")
        result = env.step(action)
        print(f"  ✓ Success: {result.info['applied']} | Reward: {result.reward}")
        print(f"  Score: {result.observation.score:.2f}")
    
    final_grade = env.grade()
    print(f"\n✓ Final Score: {final_grade.score:.2f}")
    print(f"  Robots Completed: {env._state['robots_completed']}")
    print(f"  Defective Units: {env._state['defective_units']}")
    print(f"  Quality Tests: {env._state['quality_tests_passed']} passed, {env._state['quality_tests_failed']} failed")
    env.close()


def play_hard_robot_optimization():
    """Play the hard robot optimization game."""
    print("\n" + "="*60)
    print("HARD ROBOT OPTIMIZATION - Maximize output with limited resources")
    print("="*60)
    
    env = OpenEnvEnvironment()
    obs_result = env.reset(task_id="hard_robot_optimization", seed=42)
    obs = obs_result.observation
    
    print_observation(obs)
    
    # Strategy: Balance energy usage with production speed
    actions = [
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "arms"}),
        Action(command="add_part", args={"part_type": "legs"}),
        Action(command="add_part", args={"part_type": "batteries"}),
        Action(command="add_part", args={"part_type": "circuits"}),
        Action(command="test_quality", args={}),
        Action(command="add_part", args={"part_type": "processors"}),
        Action(command="complete_robot", args={}),
        Action(command="test_quality", args={}),
        Action(command="increase_speed", args={}),
        Action(command="add_part", args={"part_type": "heads"}),
        Action(command="add_part", args={"part_type": "arms"}),
        Action(command="add_part", args={"part_type": "legs"}),
        Action(command="add_part", args={"part_type": "batteries"}),
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"\nStep {i}: Executing {action.command} {action.args}")
        result = env.step(action)
        print(f"  ✓ Success: {result.info['applied']} | Reward: {result.reward}")
        print(f"  Score: {result.observation.score:.2f}")
        print(f"  Energy: {env._state['energy_used']}/{env._state['energy_budget']}")
    
    final_grade = env.grade()
    print(f"\n✓ Final Score: {final_grade.score:.2f}")
    print(f"  Robots Completed: {env._state['robots_completed']}")
    print(f"  Defective Units: {env._state['defective_units']}")
    print(f"  Energy Used: {env._state['energy_used']}/{env._state['energy_budget']}")
    print(f"  Cost per Robot: {env._state['cost_per_robot']:.2f}")
    print(f"  Quality Score: {env._state['quality_score']:.2f}")
    print(f"  Efficiency Bonus: {env._state['efficiency_bonus']:.2f}")
    env.close()


def main():
    """Run all three robot games."""
    print("\n" + "🤖"*20)
    print("ROBOT FACTORY MINI-GAMES FOR AI AGENTS")
    print("🤖"*20)
    
    # Play easy game
    play_easy_robot_assembly()
    
    # Play medium game
    play_medium_robot_factory()
    
    # Play hard game
    play_hard_robot_optimization()
    
    print("\n" + "="*60)
    print("All games completed! 🎉")
    print("="*60)


if __name__ == "__main__":
    main()
