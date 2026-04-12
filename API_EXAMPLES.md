# API Usage Examples

## Overview
The GridNav API requires specific JSON request bodies for POST endpoints. The error you're seeing means you're missing a required field.

## Endpoints & Required Fields

### 1. **GET /health** (No body required)
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

### 2. **GET /config** (No body required)
```bash
curl http://localhost:7860/config
```

**Response:** OpenEnv specification with task definitions

---

### 3. **POST /reset** (Body required)
**Required fields:**
- `task_id`: string ("easy", "medium", or "hard")
- `session_id`: optional string

**Example:**
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'
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

### Using requests library:
```python
import requests

BASE_URL = "http://localhost:7860"

# Reset environment
reset_response = requests.post(
    f"{BASE_URL}/reset",
    json={"task_id": "easy"}
)
session_id = reset_response.json()["session_id"]

# Step environment
step_response = requests.post(
    f"{BASE_URL}/step",
    json={"action": 0, "session_id": session_id}
)

# Grade episode
grade_response = requests.post(
    f"{BASE_URL}/grade",
    json={
        "task_id": "easy",
        "cumulative_reward": 2.5,
        "items_collected": 3,
        "total_items": 3,
        "steps_taken": 45,
        "max_steps": 100
    }
)
```

### Using JavaScript/Fetch:
```javascript
const BASE_URL = "http://localhost:7860";

// Reset environment
const resetRes = await fetch(`${BASE_URL}/reset`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ task_id: "easy" })
});
const { session_id } = await resetRes.json();

// Step environment
const stepRes = await fetch(`${BASE_URL}/step`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ action: 0, session_id })
});

// Grade episode
const gradeRes = await fetch(`${BASE_URL}/grade`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    task_id: "easy",
    cumulative_reward: 2.5,
    items_collected: 3,
    total_items: 3,
    steps_taken: 45,
    max_steps: 100
  })
});
```

---

## Common Errors

### "Field required" Error
**Problem:** Missing required field in JSON body

**Solution:** Check that you're including all required fields for that endpoint:
- `/reset` → needs `task_id`
- `/step` → needs `action` and `session_id`
- `/grade` → needs all performance metrics

### "Session not found"
**Problem:** `session_id` doesn't exist or expired

**Solution:** Call `/reset` first to get a valid session_id

### "Invalid action"
**Problem:** Action is not 0-4

**Solution:** Use only: 0 (UP), 1 (DOWN), 2 (LEFT), 3 (RIGHT), 4 (COLLECT)

### "Invalid task_id"
**Problem:** task_id is not recognized

**Solution:** Use only: "easy", "medium", or "hard"
