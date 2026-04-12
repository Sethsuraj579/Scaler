"""
Inference script for GridNav OpenEnv environment.

Provides utilities for running inference, testing agents, and interactive gameplay.
Supports OpenAI API integration via HF_TOKEN environment variable or custom api_base_url.
"""

import argparse
import json
import os
from typing import Dict, List, Optional, Callable, Any
import time
from datetime import datetime

from environment import OpenEnvWrapper, Action
from graders import TaskGrader
from models import GradeOutput


# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


class InferenceRunner:
    """Run inference episodes and collect statistics."""
    
    def __init__(self, task_id: str = "easy", verbose: bool = True):
        """
        Initialize inference runner.
        
        Args:
            task_id: Task difficulty ("easy", "medium", "hard")
            verbose: Print progress to console
        """
        self.task_id = task_id
        self.verbose = verbose
        self.env = OpenEnvWrapper(task_id=task_id)
        self.episode_count = 0
        self.total_reward = 0.0
        
    def run_episode(
        self,
        action_fn: Callable[[Dict], int],
        max_steps: Optional[int] = None,
        render: bool = False,
        episode_name: str = "Episode"
    ) -> Dict[str, Any]:
        """
        Run a single episode with a given action function.
        
        Args:
            action_fn: Function that takes observation dict and returns action (0-4)
            max_steps: Override max steps for episode
            render: Print grid visualization each step
            episode_name: Name for logging
        
        Returns:
            Episode statistics dictionary
        """
        self.episode_count += 1
        
        # Reset environment
        reset_output = self.env.reset()
        observation = reset_output.observation
        episode_info = reset_output.info
        
        episode_data = {
            "episode": self.episode_count,
            "task_id": self.task_id,
            "episode_name": episode_name,
            "timestamp": datetime.now().isoformat(),
            "steps": 0,
            "cumulative_reward": 0.0,
            "items_collected": 0,
            "terminated": False,
            "truncated": False,
            "actions": [],
            "rewards": [],
            "observations": [observation],
            "max_steps": max_steps or self.env.env.max_steps,
        }
        
        if self.verbose:
            print(f"\n{'-'*60}")
            print(f"{episode_name} (Task: {self.task_id})")
            print(f"{'-'*60}")
            if render:
                print(self.env.render())
                print()
        
        # Run episode
        while True:
            try:
                # Get action from function
                action = action_fn(observation)
                
                # Validate action
                if not isinstance(action, int) or action < 0 or action > 4:
                    raise ValueError(f"Invalid action: {action}. Must be int 0-4.")
                
                episode_data["actions"].append(int(action))
                
                # Step environment
                step_output = self.env.step(action)
                observation = step_output.observation
                reward = step_output.reward
                terminated = step_output.terminated
                truncated = step_output.truncated
                step_info = step_output.info
                
                episode_data["steps"] = step_info["step"]
                episode_data["cumulative_reward"] = step_info["cumulative_reward"]
                episode_data["items_collected"] = step_info["collected_items"]
                episode_data["rewards"].append(reward)
                episode_data["observations"].append(observation)
                
                # Log progress
                if self.verbose and episode_data["steps"] % 20 == 0:
                    action_name = {0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT", 4: "COLLECT"}[action]
                    print(f"Step {episode_data['steps']:3d} | Action: {action_name:8s} | "
                          f"Reward: {reward:+6.2f} | Items: {episode_data['items_collected']}")
                
                # Render if requested
                if render:
                    action_name = {0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT", 4: "COLLECT"}[action]
                    print(f"\nStep {episode_data['steps']} - Action: {action_name}, Reward: {reward:+.2f}")
                    print(self.env.render())
                    print()
                
                # Check termination
                if terminated or truncated:
                    episode_data["terminated"] = terminated
                    episode_data["truncated"] = truncated
                    break
                
                if episode_data["steps"] >= episode_data["max_steps"]:
                    episode_data["truncated"] = True
                    break
                    
            except KeyboardInterrupt:
                print("\n[Interrupted by user]")
                episode_data["truncated"] = True
                break
            except Exception as e:
                print(f"[Error during episode: {e}]")
                episode_data["truncated"] = True
                break
        
        # Grade episode
        grade = TaskGrader.grade_episode(
            task_id=self.task_id,
            cumulative_reward=episode_data["cumulative_reward"],
            items_collected=episode_data["items_collected"],
            total_items=self.env.env.num_items,
            steps_taken=episode_data["steps"],
            max_steps=episode_data["max_steps"],
            hit_hazard=False  # Check from negative rewards
        )
        
        episode_data["score"] = grade.score
        episode_data["feedback"] = grade.feedback
        episode_data["grade_details"] = grade.details
        
        # Print summary
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Episode Summary")
            print(f"{'='*60}")
            print(f"Steps: {episode_data['steps']} / {episode_data['max_steps']}")
            print(f"Items Collected: {episode_data['items_collected']} / {self.env.env.num_items}")
            print(f"Cumulative Reward: {episode_data['cumulative_reward']:.3f}")
            print(f"Score: {episode_data['score']:.3f}")
            print(f"Feedback: {episode_data['feedback']}")
            print(f"{'='*60}\n")
        
        self.total_reward += episode_data["cumulative_reward"]
        return episode_data
    
    def run_multiple(
        self,
        action_fn: Callable[[Dict], int],
        num_episodes: int = 3,
        render: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Run multiple episodes.
        
        Args:
            action_fn: Action decision function
            num_episodes: Number of episodes to run
            render: Render grid visualization
        
        Returns:
            List of episode statistics
        """
        episodes = []
        
        for i in range(num_episodes):
            episode_data = self.run_episode(
                action_fn=action_fn,
                render=render,
                episode_name=f"Episode {i+1}/{num_episodes}"
            )
            episodes.append(episode_data)
        
        # Print aggregate statistics
        if self.verbose and num_episodes > 1:
            print(f"\n{'='*60}")
            print(f"Aggregate Results ({num_episodes} episodes)")
            print(f"{'='*60}")
            
            scores = [ep["score"] for ep in episodes]
            rewards = [ep["cumulative_reward"] for ep in episodes]
            collections = [ep["items_collected"] for ep in episodes]
            steps = [ep["steps"] for ep in episodes]
            
            print(f"Average Score: {sum(scores)/len(scores):.3f} ± {self._std(scores):.3f}")
            print(f"Average Reward: {sum(rewards)/len(rewards):.3f} ± {self._std(rewards):.3f}")
            print(f"Average Items Collected: {sum(collections)/len(collections):.1f}")
            print(f"Average Steps: {sum(steps)/len(steps):.1f}")
            print(f"Score Range: {min(scores):.3f} - {max(scores):.3f}")
            print(f"{'='*60}\n")
        
        return episodes
    
    @staticmethod
    def _std(values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


class SimpleAgents:
    """Collection of simple agent strategies for testing."""
    
    @staticmethod
    def random_agent(observation: Dict) -> int:
        """Agent that takes random actions."""
        import random
        return random.randint(0, 4)
    
    @staticmethod
    def greedy_agent(observation: Dict) -> int:
        """Agent that greedily moves towards closest item."""
        agent_x = observation.get("agent_x", 0)
        agent_y = observation.get("agent_y", 0)
        item_x = observation.get("closest_item_x", 0)
        item_y = observation.get("closest_item_y", 0)
        
        # If at item location, collect
        if abs(agent_x - item_x) < 0.1 and abs(agent_y - item_y) < 0.1:
            return Action.COLLECT
        
        # Move towards item
        if abs(agent_x - item_x) > abs(agent_y - item_y):
            if item_x > agent_x:
                return Action.RIGHT
            else:
                return Action.LEFT
        else:
            if item_y > agent_y:
                return Action.DOWN
            else:
                return Action.UP
    
    @staticmethod
    def exploring_agent(observation: Dict) -> int:
        """Agent that explores while moving towards items."""
        import random
        
        agent_x = observation.get("agent_x", 0)
        agent_y = observation.get("closest_item_y", 0)
        item_x = observation.get("closest_item_x", 0)
        item_y = observation.get("closest_item_y", 0)
        
        # 70% follow greedy, 30% explore
        if random.random() < 0.7:
            return SimpleAgents.greedy_agent(observation)
        else:
            return random.randint(0, 3)  # Random movement
    
    @staticmethod
    def corner_cleaner(observation: Dict) -> int:
        """Agent that systematically clears grid corners first."""
        agent_x = observation.get("agent_x", 0)
        agent_y = observation.get("agent_y", 0)
        
        # Move to corners in order
        # Target current corner
        if agent_x < 0.25 and agent_y < 0.25:  # Top-left
            return SimpleAgents.greedy_agent(observation)
        elif agent_x > 0.75 and agent_y < 0.25:  # Top-right
            return SimpleAgents.greedy_agent(observation)
        elif agent_x > 0.75 and agent_y > 0.75:  # Bottom-right
            return SimpleAgents.greedy_agent(observation)
        else:  # Move to nearest corner
            if agent_x < 0.5:
                return Action.LEFT
            else:
                return Action.RIGHT


class HFAgent:
    """Agent that uses HuggingFace Inference API for decision making."""
    
    def __init__(
        self,
        model: str = "meta-llama/Llama-2-7b-chat-hf",
        hf_token: Optional[str] = None
    ):
        """
        Initialize HuggingFace agent.
        
        Args:
            model: HuggingFace model ID
            hf_token: HuggingFace token (auto-detected if not provided)
        """
        self.model = model
        self.hf_token = hf_token or HF_TOKEN
        
        if not self.hf_token:
            raise ValueError(
                "No HF_TOKEN found. Set HF_TOKEN environment variable or provide via --hf-token"
            )
        
        # Initialize HuggingFace client
        try:
            from huggingface_hub import InferenceClient  # type: ignore[import]
            self.client = InferenceClient(
                model=model,
                token=self.hf_token
            )
            self.available = True
        except ImportError:
            print("⚠ huggingface-hub package not installed.")
            print("  Install: pip install huggingface-hub")
            self.available = False
        except Exception as e:
            print(f"⚠ Failed to initialize HF client: {e}")
            self.available = False
    
    def __call__(self, observation: Dict) -> int:
        """Decide action using HuggingFace Inference API or fallback."""
        if not self.available:
            # Fallback to greedy strategy
            return SimpleAgents.greedy_agent(observation)
        
        try:
            action_descriptions = {
                0: "UP - Move up on grid",
                1: "DOWN - Move down on grid",
                2: "LEFT - Move left on grid",
                3: "RIGHT - Move right on grid",
                4: "COLLECT - Attempt to collect item",
            }
            
            prompt = f"""You are an AI agent in a grid navigation game. Choose the best action.

Current State:
- Agent: ({observation.get('agent_x', 0):.2f}, {observation.get('agent_y', 0):.2f})
- Target: ({observation.get('closest_item_x', 0):.2f}, {observation.get('closest_item_y', 0):.2f})
- Progress: {observation.get('items_collected', 0):.1%}

Actions: 0=UP, 1=DOWN, 2=LEFT, 3=RIGHT, 4=COLLECT

Best action number (0-4):"""
            
            response = self.client.text_generation(
                prompt,
                max_new_tokens=5,
                temperature=0.3
            )
            
            # Extract first digit from response
            for char in response:
                if char.isdigit():
                    action = int(char)
                    return max(0, min(4, action))
            
            return SimpleAgents.greedy_agent(observation)
            
        except Exception as e:
            print(f"⚠ HF API error: {e}. Using greedy fallback.")
            return SimpleAgents.greedy_agent(observation)


class APIAgent:
    """Agent that uses OpenAI API for decision making."""
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        api_base: str = "https://api.openai.com/v1",
        hf_token: Optional[str] = None
    ):
        """
        Initialize API agent.
        
        Args:
            model: OpenAI model to use
            api_key: OpenAI API key (auto-detected if not provided)
            api_base: API base URL (default: OpenAI)
            hf_token: HuggingFace token (used as fallback for api_key)
        """
        self.model = model
        self.api_base = api_base
        
        # Determine API key
        self.api_key = api_key or OPENAI_API_KEY or hf_token or HF_TOKEN
        
        if not self.api_key:
            raise ValueError(
                "No API key found. Set OPENAI_API_KEY, HF_TOKEN, or provide via --api-key"
            )
        
        # Initialize OpenAI client
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=api_base
            )
            self.available = True
        except ImportError:
            print("⚠ OpenAI package not installed. Will use fallback mode.")
            self.available = False
        except Exception as e:
            print(f"⚠ Failed to initialize OpenAI client: {e}")
            self.available = False
    
    def __call__(self, observation: Dict) -> int:
        """Decide action using API or fallback."""
        if not self.available:
            # Fallback to greedy strategy
            return SimpleAgents.greedy_agent(observation)
        
        try:
            action_descriptions = {
                0: "UP - Move up on grid",
                1: "DOWN - Move down on grid",
                2: "LEFT - Move left on grid",
                3: "RIGHT - Move right on grid",
                4: "COLLECT - Attempt to collect item",
            }
            
            prompt = f"""You are an AI agent in a grid navigation game.

Current State:
- Agent position: ({observation.get('agent_x', 0):.2f}, {observation.get('agent_y', 0):.2f})
- Closest item: ({observation.get('closest_item_x', 0):.2f}, {observation.get('closest_item_y', 0):.2f})
- Items collected: {observation.get('items_collected', 0):.1%}
- Steps remaining: {observation.get('steps_remaining', 1):.1%}
- Distance to item: {observation.get('closest_item_dist', 0):.2f}

Available actions:
{chr(10).join([f"  {k}: {v}" for k, v in action_descriptions.items()])}

Choose the BEST action. Respond with ONLY the action number (0-4):"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=5,
                timeout=10.0
            )
            
            action_text = response.choices[0].message.content.strip()
            action = int(action_text)
            return max(0, min(4, action))
            
        except Exception as e:
            print(f"⚠ API error: {e}. Using greedy fallback.")
            return SimpleAgents.greedy_agent(observation)


def interactive_mode(task_id: str = "easy"):
    """
    Run interactive mode where user controls agent.
    """
    env = OpenEnvWrapper(task_id=task_id)
    reset_output = env.reset()
    observation = reset_output.observation
    
    print(f"\n{'='*60}")
    print(f"Interactive GridNav - {task_id.upper()}")
    print(f"{'='*60}")
    print("\nControls:")
    print("  0 = UP,  1 = DOWN,  2 = LEFT,  3 = RIGHT,  4 = COLLECT")
    print("  q = quit\n")
    
    print(env.render())
    print()
    
    while True:
        try:
            action_input = input("Enter action (0-4) or 'q' to quit: ").strip().lower()
            
            if action_input == 'q':
                print("Exiting...")
                break
            
            action = int(action_input)
            if action < 0 or action > 4:
                print("Invalid action. Use 0-4.")
                continue
            
            step_output = env.step(action)
            observation = step_output.observation
            reward = step_output.reward
            terminated = step_output.terminated
            truncated = step_output.truncated
            info = step_output.info
            
            action_names = ["UP", "DOWN", "LEFT", "RIGHT", "COLLECT"]
            print(f"\nAction: {action_names[action]}")
            print(f"Reward: {reward:+.2f}")
            print(f"Items Collected: {info['collected_items']}/{info['total_items']}")
            print()
            print(env.render())
            print()
            
            if terminated or truncated:
                print("\nEpisode ended!")
                grade = TaskGrader.grade_episode(
                    task_id=task_id,
                    cumulative_reward=info["cumulative_reward"],
                    items_collected=info["collected_items"],
                    total_items=info["total_items"],
                    steps_taken=info["step"],
                    max_steps=env.env.max_steps,
                )
                print(f"Final Score: {grade.score:.3f}")
                print(f"Feedback: {grade.feedback}")
                break
                
        except ValueError:
            print("Please enter a number (0-4) or 'q'.")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inference runner for GridNav OpenEnv environment"
    )
    parser.add_argument(
        "--task",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Task difficulty (default: easy)"
    )
    parser.add_argument(
        "--agent",
        choices=["random", "greedy", "exploring", "corner", "api", "hf"],
        default="greedy",
        help="Agent strategy to use (default: greedy)"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Number of episodes to run (default: 1)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (manual control)"
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render grid visualization at each step"
    )
    parser.add_argument(
        "--output",
        help="Save episode data to JSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    # API configuration
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (auto-detected from OPENAI_API_KEY or HF_TOKEN if not provided)"
    )
    parser.add_argument(
        "--api-base",
        default=OPENAI_API_BASE,
        help=f"OpenAI API base URL (default: {OPENAI_API_BASE})"
    )
    parser.add_argument(
        "--hf-token",
        help="HuggingFace token (used as fallback for API key)"
    )
    parser.add_argument(
        "--model",
        default="meta-llama/Llama-2-7b-chat-hf",
        help="Model to use: 'gpt-4' for OpenAI API agent, or HuggingFace model ID for HF agent"
    )
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive:
        interactive_mode(task_id=args.task)
        return
    
    # Automated inference
    runner = InferenceRunner(task_id=args.task, verbose=not args.quiet)
    
    # Select agent
    if args.agent == "hf":
        try:
            agent_fn = HFAgent(
                model=args.model,
                hf_token=args.hf_token
            )
            if not args.quiet:
                print(f"🤗 Using HuggingFace Agent (Model: {args.model})\n")
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
    elif args.agent == "api":
        try:
            agent_fn = APIAgent(
                model=args.model,
                api_key=args.api_key,
                api_base=args.api_base,
                hf_token=args.hf_token
            )
            if not args.quiet:
                print(f"📡 Using API Agent (Model: {args.model}, Base: {args.api_base})\n")
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Set OPENAI_API_KEY or HF_TOKEN environment variable, or use --api-key")
            return
    else:
        agents = {
            "random": SimpleAgents.random_agent,
            "greedy": SimpleAgents.greedy_agent,
            "exploring": SimpleAgents.exploring_agent,
            "corner": SimpleAgents.corner_cleaner,
        }
        agent_fn = agents[args.agent]
        if not args.quiet:
            print(f"🤖 Using {args.agent.capitalize()} Agent\n")
    
    # Run episodes
    episodes = runner.run_multiple(
        action_fn=agent_fn,
        num_episodes=args.episodes,
        render=args.render
    )
    
    # Save results
    if args.output:
        # Remove observation/action lists for JSON serialization (they can be large)
        clean_episodes = []
        for ep in episodes:
            clean_ep = {k: v for k, v in ep.items() 
                       if k not in ["observations", "actions", "rewards"]}
            clean_ep["num_actions"] = len(ep["actions"])
            clean_ep["num_observations"] = len(ep["observations"])
            clean_episodes.append(clean_ep)
        
        results = {
            "task_id": args.task,
            "agent": args.agent,
            "num_episodes": args.episodes,
            "timestamp": datetime.now().isoformat(),
            "api_config": {
                "api_base": args.api_base,
                "hf_token_set": bool(args.hf_token or HF_TOKEN),
                "api_key_set": bool(args.api_key or OPENAI_API_KEY),
            } if args.agent == "api" else None,
            "hf_config": {
                "model": args.model,
                "hf_token_set": bool(args.hf_token or HF_TOKEN),
            } if args.agent == "hf" else None,
            "episodes": clean_episodes,
        }
        
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Results saved to {args.output}")


if __name__ == "__main__":
    main()
