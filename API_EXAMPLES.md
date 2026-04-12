# API Usage Examples

## Overview
The GridNav API uses **query parameters** (not JSON bodies) for flexibility. All POST endpoints accept optional query parameters with sensible defaults.

## Endpoints

### 1. **GET /health** ✅
```bash
curl http://localhost:7860/health
```

**Response:**
```json
{
  "status": "healthy",
  "ready": true
}
```

---

### 2. **GET /config** ✅
```bash
curl http://localhost:7860/config
```

**Response:** OpenEnv specification with task definitions

---

### 3. **POST /reset** - ✅ NO BODY REQUIRED
Reset environment with optional query parameters.

**Query parameters:**
- `task_id`: "easy" | "medium" | "hard" (default: "easy")
- `session_id`: custom session identifier (default: auto-generated)

**Examples:**
```bash
# Reset with defaults
curl -X POST http://localhost:7860/reset

# Reset with specific task
curl -X POST "http://localhost:7860/reset?task_id=medium"

# Reset with custom session ID
curl -X POST "http://localhost:7860/reset?task_id=hard&session_id=my_game_1"
```

**Response:**
```json
{
  "session_id": "session_0",
  "observation": {
    "agent_x": 0.1,
    "agent_y": 0.1,
    "closest_item_x": 0.5,
    "closest_item_y": 0.5,
    "items_collected": 0,
    "steps_remaining": 0.99
  },
  "info": {
    "session_id": "session_0",
    "step": 0,
    "total_items": 3
  }
}
```

---

### 4. **POST /step** - ✅ NO BODY REQUIRED
Execute one step in the environment.

**Query parameters:**
- `action`: 0 (UP) | 1 (DOWN) | 2 (LEFT) | 3 (RIGHT) | 4 (COLLECT) (default: 0)
- `session_id`: session identifier (default: uses latest session)

**Examples:**
```bash
# Step with defaults (action 0, latest session)
curl -X POST http://localhost:7860/step

# Step with specific action
curl -X POST "http://localhost:7860/step?action=3"

# Step with action and session
curl -X POST "http://localhost:7860/step?action=4&session_id=session_0"
```

**Response:**
```json
{
  "session_id": "session_0",
  "observation": {...},
  "reward": -0.01,
  "terminated": false,
  "truncated": false,
  "info": {
    "step": 1,
    "cumulative_reward": -0.01,
    "collected_items": 0
  }
}
```

---

### 5. **POST /grade** - ✅ NO BODY REQUIRED
Grade an episode performance.

**Query parameters:**
- `task_id`: "easy" | "medium" | "hard" (default: "easy")
- `cumulative_reward`: float (default: 0.0)
- `items_collected`: integer (default: 0)
- `total_items`: integer (default: 3)
- `steps_taken`: integer (default: 0)
- `max_steps`: integer (default: 100)
- `hit_hazard`: boolean (default: false)

**Examples:**
```bash
# Grade with defaults
curl -X POST http://localhost:7860/grade

# Grade with basic stats
curl -X POST "http://localhost:7860/grade?cumulative_reward=2.5&items_collected=3&total_items=3&steps_taken=45&max_steps=100"

# Grade hard task with ful stats
curl -X POST "http://localhost:7860/grade?task_id=hard&cumulative_reward=5.0&items_collected=15&total_items=15&steps_taken=100&max_steps=150&hit_hazard=false"
```

**Response:**
```json
{
  "score": 0.95,
  "feedback": "Excellent performance! High collection rate and efficiency.",
  "details": {
    "collection_score": 1.0,
    "efficiency_score": 0.9,
    "risk_score": 1.0
  }
}
```

---

### 6. **GET /state/{session_id}** ✅
Get current environment state without stepping.

```bash
curl http://localhost:7860/state/session_0
```

**Response:**
```json
{
  "session_id": "session_0",
  "observation": {...},
  "info": {
    "step": 5,
    "task": "easy",
    "grid_size": 5,
    "agent_pos": [2, 2],
    "items_collected": 1,
    "total_items": 3,
    "steps_remaining": 0.95
  }
}
```

---

### 7. **GET /render/{session_id}** ✅
    "closest_item_x": 0.5,
    "closest_item_y": 0.5,
    "items_collected": 0,
    "steps_remaining": 0.99
  },
  "info": {
    "session_id": "session_0",
    "step": 0,
    "total_items": 3
  }
}
```

---

### 4. **POST /step** (Body required)
**Required fields:**
- `action`: integer (0-4)
  - 0 = UP
  - 1 = DOWN
  - 2 = LEFT
  - 3 = RIGHT
  - 4 = COLLECT
- `session_id`: string (from the reset response)

**Example:**
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": 0, "session_id": "session_0"}'
```

**Response:**
```json
{
  "observation": {...},
  "reward": -0.01,
  "terminated": false,
  "truncated": false,
  "info": {
    "step": 1,
    "cumulative_reward": -0.01,
    "collected_items": 0
  }
}
```

---

### 5. **POST /grade** (Body required)
**Required fields:**
- `task_id`: string ("easy", "medium", "hard")
- `cumulative_reward`: float
- `items_collected`: integer
- `total_items`: integer
- `steps_taken`: integer
- `max_steps`: integer
- `hit_hazard`: boolean (optional, default false)

**Example:**
```bash
curl -X POST http://localhost:7860/grade \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "easy",
    "cumulative_reward": 2.5,
    "items_collected": 3,
    "total_items": 3,
    "steps_taken": 45,
    "max_steps": 100,
    "hit_hazard": false
  }'
```

**Response:**
```json
{
  "score": 0.95,
  "feedback": "Excellent performance! High collection rate and efficiency.",
  "details": {
    "collection_score": 1.0,
    "efficiency_score": 0.9,
    "risk_score": 1.0
  }
}
```

---

### 6. **GET /render** (Optional session_id parameter)
```bash
curl "http://localhost:7860/render?session_id=session_0"
```

**Response:** ASCII grid visualization

---

## Python Examples

### Using requests library (Query Parameters):
```python
import requests

BASE_URL = "http://localhost:7860"

# Reset environment (no body needed!)
reset_response = requests.post(f"{BASE_URL}/reset?task_id=easy")
session_id = reset_response.json()["session_id"]
observation = reset_response.json()["observation"]

# Step environment (can use defaults)
step_response = requests.post(f"{BASE_URL}/step?action=3&session_id={session_id}")
observation = step_response.json()["observation"]
reward = step_response.json()["reward"]

# Get current state
state_response = requests.get(f"{BASE_URL}/state/{session_id}")
current_obs = state_response.json()["observation"]

# Grade episode (minimal params example)
grade_response = requests.post(
    f"{BASE_URL}/grade",
    params={
        "task_id": "easy",
        "cumulative_reward": 2.5,
        "items_collected": 3,
        "total_items": 3,
        "steps_taken": 45,
        "max_steps": 100
    }
)
score = grade_response.json()["score"]
```

### Using JavaScript/Fetch (Query Parameters):
```javascript
const BASE_URL = "http://localhost:7860";

// Reset environment
const resetRes = await fetch(`${BASE_URL}/reset?task_id=easy`, {
  method: "POST"
});
const { session_id } = await resetRes.json();

// Step environment
const stepRes = await fetch(`${BASE_URL}/step?action=3&session_id=${session_id}`, {
  method: "POST"
});
const stepData = await stepRes.json();

// Get state
const stateRes = await fetch(`${BASE_URL}/state/${session_id}`);
const stateData = await stateRes.json();

// Grade episode
const gradeRes = await fetch(
  `${BASE_URL}/grade?task_id=easy&cumulative_reward=2.5&items_collected=3&total_items=3&steps_taken=45&max_steps=100`,
  { method: "POST" }
);
const { score } = await gradeRes.json();
```

---

## Common Errors

### ✅ "Field required" Error - NOW FIXED!
**Old Problem:** Missing required field in JSON body

**Solution:** Use **query parameters** instead! All endpoints are now flexible:
- `/reset` → `?task_id=easy` (optional)
- `/step` → `?action=3` (optional, can omit for defaults)
- `/grade` → all params optional with sensible defaults

### "Session not found"
**Problem:** `session_id` doesn't exist or expired

**Solution:** Call `/reset` first to get a valid session_id

### "Invalid action"
**Problem:** Action is not 0-4

**Solution:** Use only: 0 (UP), 1 (DOWN), 2 (LEFT), 3 (RIGHT), 4 (COLLECT)

### "Invalid task_id"
**Problem:** task_id is not recognized

**Solution:** Use only: "easy", "medium", or "hard"
