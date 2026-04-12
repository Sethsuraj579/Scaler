"""Baseline inference script using OpenAI API for GridNav environment."""

import os
import json
import argparse
from typing import Optional

from environment import OpenEnvWrapper, Action
from graders import TaskGrader


def get_api_key() -> str:
    """Get OpenAI API key from environment (HF_TOKEN or OPENAI_API_KEY)."""
    # Try HF_TOKEN first (for Hugging Face Spaces compatibility)
    api_key = os.getenv("HF_TOKEN")
    if api_key:
        return api_key
    
    # Fall back to OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    raise ValueError(
        "No API key found. Please set either HF_TOKEN or OPENAI_API_KEY environment variable."
    )


class BaselineAgent:
    """Baseline agent using OpenAI API for decision making."""
    
    def __init__(self, model: str = "gpt-4", use_api: bool = True):
        """
        Initialize baseline agent.
        
        Args:
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            use_api: Whether to actually call the API (True) or use fallback logic
        """
        self.model = model
        self.use_api = use_api
        
        if use_api:
            try:
                import openai
                self.client = openai.OpenAI(api_key=get_api_key())
            except ImportError:
                print("⚠ OpenAI package not installed. Using heuristic fallback.")
                self.use_api = False
            except Exception as e:
                print(f"⚠ Failed to initialize OpenAI client: {e}. Using heuristic fallback.")
                self.use_api = False
    
    def decide_action(self, observation: dict, context: str = "") -> int:
        """
        Decide next action using OpenAI API or heuristic fallback.
        
        Args:
            observation: Current environment observation
            context: Additional context about the episode
        
        Returns:
            Action index (0-4)
        """
        if self.use_api:
            return self._decide_with_api(observation, context)
        else:
            return self._decide_with_heuristic(observation, context)
    
    def _decide_with_api(self, observation: dict, context: str) -> int:
        """Use OpenAI API to decide action."""
        action_descriptions = {
            0: "UP - Move up on grid",
            1: "DOWN - Move down on grid",
            2: "LEFT - Move left on grid",
            3: "RIGHT - Move right on grid",
            4: "COLLECT - Attempt to collect item at current position",
        }
        
        prompt = f"""You are an AI agent playing a grid navigation game.

Current Observation:
- Agent position: ({observation.get('agent_x', 0):.2f}, {observation.get('agent_y', 0):.2f})
- Closest item position: ({observation.get('closest_item_x', 0):.2f}, {observation.get('closest_item_y', 0):.2f})
- Items collected: {observation.get('items_collected', 0):.2%}
- Steps remaining: {observation.get('steps_remaining', 1):.2%}
- Distance to closest item: {observation.get('closest_item_dist', 0):.2f}

{f"Additional context: {context}" if context else ""}

Available actions:
{chr(10).join([f"  {k}: {v}" for k, v in action_descriptions.items()])}

Choose the best action (respond with ONLY the action number 0-4, nothing else):"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10,
            )
            
            action_text = response.choices[0].message.content.strip()
            action = int(action_text)
            return max(0, min(4, action))  # Clamp to valid range
        except Exception as e:
            print(f"⚠ API call failed: {e}. Falling back to heuristic.")
            return self._decide_with_heuristic(observation, context)
    
    def _decide_with_heuristic(self, observation: dict, context: str) -> int:
        """Use heuristic fallback logic when API is unavailable."""
        # If we collected all items, we're done
        if observation.get("items_collected", 0) >= 0.99:
            return Action.COLLECT
        
        # If there's a closest item
        if observation.get("closest_item_dist", float('inf')) > 0.0:
            agent_x = observation.get("agent_x", 0)
            agent_y = observation.get("agent_y", 0)
            item_x = observation.get("closest_item_x", 0)
            item_y = observation.get("closest_item_y", 0)
            
            # Move towards the item
            if abs(agent_x - item_x) > abs(agent_y - item_y):
                # Horizontal distance is larger
                if item_x > agent_x:
                    return Action.RIGHT
                else:
                    return Action.LEFT
            else:
                # Vertical distance is larger
                if item_y > agent_y:
                    return Action.DOWN
                else:
                    return Action.UP
        
        # Default: random exploration
        import random
        return random.randint(0, 3)  # One of the movement actions


def run_episode(
    env: OpenEnvWrapper,
    agent: BaselineAgent,
    task_id: str,
    max_steps: Optional[int] = None,
    verbose: bool = True
) -> dict:
    """
    Run a single episode with the baseline agent.
    
    Returns:
        Dictionary with episode results
    """
    reset_output = env.reset()
    observation = reset_output.observation
    info = reset_output.info
    
    episode_data = {
        "task_id": task_id,
        "steps": 0,
        "cumulative_reward": 0.0,
        "items_collected": 0,
        "hit_hazard": False,
        "terminated": False,
        "truncated": False,
        "actions": [],
    }
    
    step_limit = max_steps or env.env.max_steps
    
    while True:
        action = agent.decide_action(observation)
        episode_data["actions"].append(int(action))
        
        step_output = env.step(action)
        observation = step_output.observation
        reward = step_output.reward
        terminated = step_output.terminated
        truncated = step_output.truncated
        step_info = step_output.info
        
        episode_data["steps"] = step_info["step"]
        episode_data["cumulative_reward"] = step_info["cumulative_reward"]
        episode_data["items_collected"] = step_info["collected_items"]
        
        if verbose and episode_data["steps"] % 10 == 0:
            print(f"  Step {episode_data['steps']}: Reward={reward:+.2f}, "
                  f"Collected={episode_data['items_collected']}/{step_info['total_items']}")
        
        if terminated or truncated:
            episode_data["terminated"] = terminated
            episode_data["truncated"] = truncated
            break
        
        if episode_data["steps"] >= step_limit:
            episode_data["truncated"] = True
            break
    
    # Check if we hit a hazard (negative reward from hazard)
    episode_data["hit_hazard"] = reward == -5.0
    
    return episode_data


def evaluate_baseline(
    task_id: str = "easy",
    num_episodes: int = 3,
    use_api: bool = True,
    model: str = "gpt-4",
    verbose: bool = True
) -> dict:
    """
    Evaluate baseline agent performance on a task.
    
    Args:
        task_id: Task to evaluate ("easy", "medium", "hard")
        num_episodes: Number of episodes to run
        use_api: Whether to use OpenAI API
        model: OpenAI model to use
        verbose: Whether to print progress
    
    Returns:
        Evaluation results with scores and feedback
    """
    env = OpenEnvWrapper(task_id=task_id)
    agent = BaselineAgent(model=model, use_api=use_api)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Evaluating Baseline Agent on Task: {task_id.upper()}")
        print(f"{'='*60}")
        if use_api:
            print(f"Using OpenAI API ({model})")
        else:
            print("Using heuristic fallback (API disabled)")
        print()
    
    episodes = []
    scores = []
    grade_outputs = []
    
    for ep_num in range(num_episodes):
        if verbose:
            print(f"Episode {ep_num + 1}/{num_episodes}:")
        
        episode_data = run_episode(env, agent, task_id, verbose=verbose)
        episodes.append(episode_data)
        
        # Grade the episode
        grade = TaskGrader.grade_episode(
            task_id=task_id,
            cumulative_reward=episode_data["cumulative_reward"],
            items_collected=episode_data["items_collected"],
            total_items=env.env.num_items,
            steps_taken=episode_data["steps"],
            max_steps=env.env.max_steps,
            hit_hazard=episode_data["hit_hazard"]
        )
        
        scores.append(grade.score)
        grade_outputs.append(grade)
        
        if verbose:
            print(f"  Score: {grade.score:.3f}")
            print(f"  Feedback: {grade.feedback}")
            print()
    
    # Calculate aggregate results
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    results = {
        "task_id": task_id,
        "num_episodes": num_episodes,
        "use_api": use_api,
        "model": model if use_api else "heuristic",
        "average_score": avg_score,
        "individual_scores": scores,
        "episodes": episodes,
        "grades": [
            {
                "score": g.score,
                "feedback": g.feedback,
                "details": g.details
            }
            for g in grade_outputs
        ],
    }
    
    if verbose:
        print(f"{'='*60}")
        print(f"RESULTS FOR {task_id.upper()}")
        print(f"{'='*60}")
        print(f"Average Score: {avg_score:.3f} / 1.0")
        print(f"Episodes Run: {num_episodes}")
        if scores:
            print(f"Score Range: {min(scores):.3f} - {max(scores):.3f}")
        print()
    
    return results


def main():
    """Main entry point for baseline evaluation."""
    parser = argparse.ArgumentParser(
        description="Baseline inference script for GridNav OpenEnv environment"
    )
    parser.add_argument(
        "--task",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Task difficulty (default: easy)"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of episodes to run (default: 3)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="OpenAI model to use (default: gpt-4)"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Use heuristic fallback instead of OpenAI API"
    )
    parser.add_argument(
        "--output",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # Evaluate on specified task
    results = evaluate_baseline(
        task_id=args.task,
        num_episodes=args.episodes,
        use_api=not args.no_api,
        model=args.model,
        verbose=not args.quiet
    )
    
    # Save results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Also evaluate other tasks if running with API
    if not args.no_api and args.task == "easy":
        print("\n" + "="*60)
        print("BONUS: Evaluating all difficulty levels")
        print("="*60 + "\n")
        
        all_results = {"easy": results}
        for task in ["medium", "hard"]:
            all_results[task] = evaluate_baseline(
                task_id=task,
                num_episodes=1,  # Single episode for speed
                use_api=not args.no_api,
                model=args.model,
                verbose=not args.quiet
            )
        
        if args.output:
            output_base = args.output.replace(".json", "")
            with open(f"{output_base}_all_tasks.json", "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"\nAll results saved to {output_base}_all_tasks.json")


if __name__ == "__main__":
    main()
