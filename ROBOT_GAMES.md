# 🤖 Robot Factory Mini-Games

A collection of interactive fabrication and production management games designed for AI agents to learn resource optimization, quality control, and decision-making under constraints.

## Games Overview

### 1. 🟢 Easy Robot Assembly
**Difficulty:** Easy | **Max Steps:** 10

Simple robot assembly game where agents collect parts and assemble complete robots.

**Objective:**
- Assemble 3 robots using available parts
- Maintain high quality standards

**Available Actions:**
- `add_part`: Add a specific part type (arms, legs, heads, batteries) to current assembly
- `complete_robot`: Finish a robot and earn points
- `check_quality`: Quality inspection that improves score

**State Variables:**
- `robots_completed`: Number of finished robots
- `target_robots`: Goal number (3)
- `available_parts`: Inventory of each part type
- `current_assembly`: Parts waiting to be assembled
- `quality_score`: Overall quality rating (0.0-1.0)

**Scoring:**
- 60% for robot completion (robots/target)
- 40% for quality maintenance
- Final score ranges 0.0-1.0

**Example Strategy:**
```python
Action(command="add_part", args={"part_type": "heads"})
Action(command="add_part", args={"part_type": "arms"})
Action(command="add_part", args={"part_type": "legs"})
Action(command="add_part", args={"part_type": "batteries"})
Action(command="complete_robot", args={})
```

---

### 2. 🟡 Medium Robot Factory
**Difficulty:** Medium | **Max Steps:** 12

Production management game combining assembly with quality control under moderate time pressure.

**Objective:**
- Assemble 5 robots
- Maintain quality standards
- Balance speed and quality

**Available Actions:**
- `add_part`: Add part type to assembly
- `complete_robot`: Finish and test a robot
- `test_quality`: Run quality inspection (random outcome 70% pass rate)
- `increase_speed`: Boost production efficiency but risk more defects

**State Variables:**
- `robots_completed`: Number of finished robots
- `target_robots`: Goal number (5)
- `defective_units`: Faulty robots produced
- `parts_inventory`: Available parts for assembly
- `quality_tests_passed`: Tests with passing results
- `quality_tests_failed`: Tests with failing results
- `assembly_efficiency`: Production speed metric (0.0-1.0)

**Scoring:**
- 40% for robot completion
- 30% for quality test pass rate (threshold: 80%)
- 20% for assembly efficiency
- 10% baseline + defect penalties

**Key Mechanics:**
- 20% chance of defect when completing robots
- Quality testing has variable outcomes
- Speed boost costs action but increases efficiency
- Defects directly penalize score

**Example Strategy:**
```python
# Build and test sequence
for i in range(5):
    Action(command="add_part", args={"part_type": "arms"})
    Action(command="add_part", args={"part_type": "legs"})
    Action(command="add_part", args={"part_type": "heads"})
    Action(command="add_part", args={"part_type": "batteries"})
    Action(command="add_part", args={"part_type": "circuits"})
    Action(command="test_quality", args={})
    Action(command="complete_robot", args={})
```

---

### 3. 🔴 Hard Robot Optimization
**Difficulty:** Hard | **Max Steps:** 15

Advanced production game with strict resource constraints, complex part requirements, and strategic decision-making.

**Objective:**
- Assemble 8 robots
- Keep defect rate ≤ 15%
- Manage energy budget (100 units max)
- Optimize cost and efficiency

**Available Actions:**
- `add_part`: Add part (each type costs different energy: arms=5, legs=5, heads=8, batteries=10, circuits=12, processors=15)
- `complete_robot`: Finish robot (costs 20 energy)
- `test_quality`: Quality inspection (costs 5 energy)
- `increase_speed`: Speed boost (costs 8 energy)
- `repair_station`: Fix defective units (costs 15 energy, converts defect to completion)

**State Variables:**
- `robots_completed`: Number of finished robots
- `target_robots`: Goal number (8)
- `defective_units`: Faulty robots
- `max_defect_rate`: Threshold (0.15 or 15%)
- `energy_budget`: Total available (100 units)
- `energy_used`: Energy consumed
- `parts_inventory`: 6 different part types
- `quality_score`: Quality rating
- `efficiency_bonus`: Bonus for staying efficient (0.0-1.0)
- `cost_per_robot`: Average energy cost
- `maintenance_repairs`: Number of repairs performed

**Scoring:**
- 35% for robot completion (robots/target)
- 30% for quality (defect rate vs threshold)
- 20% for energy efficiency (unused budget ratio)
- 15% for efficiency bonus

**Key Mechanics:**
- **Energy cost system**: Each action consumes energy
- **Defect scaling**: Defect chance increases under energy pressure (0.1 + (used/budget)*0.1)
- **Repair option**: Can recover defects but costs significant energy
- **Efficiency bonus**: Awarded for low defects (≤10%) and high completion
- **Cost optimization**: Track energy per robot ratio

**Example Strategy (Energy-Conscious):**
```python
# Prioritize energy efficiency
for i in range(8):
    # Add cheaper parts first
    Action(command="add_part", args={"part_type": "arms"})       # 5 energy
    Action(command="add_part", args={"part_type": "legs"})       # 5 energy
    # Add expensive parts strategically
    Action(command="add_part", args={"part_type": "heads"})      # 8 energy
    Action(command="add_part", args={"part_type": "batteries"})  # 10 energy
    Action(command="add_part", args={"part_type": "circuits"})   # 12 energy
    Action(command="add_part", args={"part_type": "processors"}) # 15 energy
    # Test quality (5 energy) before completion
    Action(command="test_quality", args={})
    # Complete robot (20 energy)
    Action(command="complete_robot", args={})
```

---

## Playing the Games

### Using the Demo Script

Run the included demo to see all three games in action:

```bash
python robot_game_demo.py
```

### Programmatic Access

```python
from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action

# Create environment
env = OpenEnvEnvironment()

# List available tasks
tasks = env.tasks()
for task in tasks:
    if "robot" in task.task_id:
        print(f"{task.task_id}: {task.title} ({task.difficulty})")

# Play easy game
obs_result = env.reset(task_id="easy_robot_assembly", seed=42)
obs = obs_result.observation

# Take actions
action = Action(command="add_part", args={"part_type": "heads"})
result = env.step(action)

print(f"Score: {result.observation.score}")
print(f"Reward: {result.reward}")

# Check final grade
grade = env.grade()
print(f"Final Score: {grade.score}")

env.close()
```

## Integration with AI Agents

These games are compatible with any RL framework:

```python
# Pseudocode for RL agent training
agent = RLAgent(env)

for episode in range(1000):
    obs = env.reset(task_id="medium_robot_factory")
    done = False
    
    while not done:
        action = agent.select_action(obs)
        result = env.step(action)
        reward = result.reward
        
        agent.update(reward, result.observation)
        
        obs = result.observation
        done = result.observation.done
```

## Task Difficulty Progression

| Aspect | Easy | Medium | Hard |
|--------|------|--------|------|
| Target Robots | 3 | 5 | 8 |
| Max Steps | 10 | 12 | 15 |
| Part Types | 4 | 5 | 6 |
| Resource Constraints | None | Time | Energy+Defects |
| Quality Control | Optional | Required | Critical |
| Complexity | Linear | Moderate | High (multi-objective) |

## Tips for AI Agents

### Easy Level
- Simply follow the recipe: collect 4 parts → complete robot
- Quality checks provide bonuses
- Time is not a constraint

### Medium Level
- Balance speed and quality: faster production risks defects
- Quality testing helps identify issues
- 12 steps is tight; prioritize actions carefully
- Track defect rate; it directly impacts score

### Hard Level
- **Energy is the critical resource** - most important constraint
- Calculate optimal energy per robot: ~52 energy per robot with 100 budget
- Prioritize: Complete robots > Test quality > Speed boost > Repairs
- Keep defect rate low to unlock efficiency bonus
- Repair station is expensive but prevents score penalties

## Game Files

- `openenv_env/tasks.py` - Task definitions and grading functions
- `openenv_env/environment.py` - Game logic and action handlers
- `robot_game_demo.py` - Demonstration script
- `tests/test_environment.py` - Unit tests (can be extended for robot games)

## Creating Custom Agents

Extend these games for your AI agent research:

```python
class MyRobotAgent:
    def __init__(self):
        self.env = OpenEnvEnvironment()
    
    def train_on_easy(self, episodes=100):
        for _ in range(episodes):
            obs = self.env.reset(task_id="easy_robot_assembly")
            while not obs.done:
                # Your strategy here
                action = self.select_best_action(obs)
                obs = self.env.step(action).observation
    
    def select_best_action(self, observation):
        # Implement your decision logic
        pass
```

## Contribution

Found bugs or want to add features? Extend the games by:
1. Adding new part types
2. Introducing new constraints
3. Creating additional tasks at different difficulty levels
4. Implementing new action types

## License

MIT
