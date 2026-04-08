---
title: OpenEnv Real-World RL Environment
emoji: ""
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - environment
---

# OpenEnv Real-World RL Environment

![CI](https://img.shields.io/badge/CI-GitHub_Actions-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![Docker](https://img.shields.io/badge/Deploy-Docker-2496ED)
![OpenEnv](https://img.shields.io/badge/Tag-openenv-2E8B57)

Replace the CI badge with your repository-specific workflow badge after pushing:

`https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg`

This repository implements a reinforcement learning environment aligned with an OpenEnv-style interface.
It simulates realistic operational tasks and includes programmatic graders with continuous scores from 0.0 to 1.0.

## Environment Overview

The environment focuses on practical decision-making workflows:
- Easy: expense triage under budget and risk constraints.
- Medium: cross-team meeting scheduling with availability and process constraints.
- Hard: production incident response with mitigation, communication, and closure requirements.

The implementation provides:
- A complete environment interface (`metadata`, `tasks`, `reset`, `step`, `grade`, `render`, `close`).
- Pydantic models for actions, observations, steps, reset responses, and grading outputs.
- Reward shaping that promotes incremental progress and penalizes low-quality behavior.
- A baseline inference script using the OpenAI Python client with credentials read from `HF_TOKEN`.

## Action Space

Actions are JSON objects with this schema:

```json
{
  "command": "string",
  "args": {}
}
```

Command set varies by task and is surfaced in each observation as `allowed_commands`.

## Observation Space

Each step returns a typed observation with:
- `task_id`, `step_index`, `max_steps`
- `score` and `progress` in [0.0, 1.0]
- `summary` of current state
- `state_view` with task-specific structured state
- `allowed_commands`
- `done`

## Reward Function

At each step, reward is computed as:

```text
reward = 1.8 * (new_score - previous_score) + invalid_penalty + harmful_penalty - 0.01
```

Key shaping behavior:
- Positive reward for score improvements.
- Slight per-step cost to encourage shorter successful trajectories.
- Penalty for invalid actions.
- Stronger penalty for explicitly undesirable behavior (for example `approve_all`, `ignore_incident`, `delete_data`).
- Small completion bonus on successful termination.
- Extra dense shaping on the hard task to reward intermediate incident-response milestones (acknowledgements, mitigations, impact reduction, communication) and penalize stalling with `noop` during active impact.

## Tasks and Graders

### Easy: Expense Triage (`easy_expense_triage`)
- Goal: classify transactions and maintain budget health.
- Grader combines:
  - Completion ratio of reviewed transactions.
  - Budget compliance score.
  - Proper handling of risky entertainment expense.

### Medium: Meeting Scheduler (`medium_meeting_scheduler`)
- Goal: choose a feasible meeting time, create an agenda, send invites.
- Grader combines:
  - Time feasibility for required participants.
  - Invite completion.
  - Agenda completeness.

### Hard: Incident Response Drill (`hard_incident_response`)
- Goal: acknowledge alerts, apply mitigations, reduce customer impact, communicate, and publish postmortem.
- Grader combines:
  - Alert acknowledgment ratio.
  - Mitigation completion ratio.
  - Customer impact reduction.
  - Status page communication.
  - Postmortem publication.

All graders return values in [0.0, 1.0].

## Project Structure

- `openenv_env/spec.py`: OpenEnv interface and Pydantic models.
- `openenv_env/tasks.py`: task definitions and programmatic graders.
- `openenv_env/environment.py`: environment dynamics, transitions, and reward shaping.
- `app.py`: FastAPI server entrypoint for deployment.
- `baseline_inference.py`: reproducible baseline evaluator.
- `Dockerfile`: container definition for Hugging Face Space (docker SDK).

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Quick local check:

```bash
python -m unittest discover -s tests -v
python baseline_inference.py --seed 1337
```

Run local API server:

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

Docker run:

```bash
docker build -t openenv-realworld .
docker run --rm -p 7860:7860 openenv-realworld
```

## Baseline Inference and Reproducible Score

Heuristic baseline (deterministic):

```bash
python baseline_inference.py --seed 1337
```

Model-driven baseline (OpenAI client):

```bash
set HF_TOKEN=<your_api_key>   # Windows PowerShell: $env:HF_TOKEN="..."
python baseline_inference.py --use-model --model gpt-4.1-mini --seed 1337
```

If you omit `--model`, the script chooses a provider-appropriate default automatically:
- `HF_TOKEN` -> `meta-llama/Meta-Llama-3.1-8B-Instruct`
- `OPENAI_API_KEY` -> `gpt-4.1-mini`

By default, the script uses:
- OpenAI Python client with chat-completions.
- API key from `HF_TOKEN` or `OPENAI_API_KEY`.
- Automatic provider detection from token prefix.
- No base URL required in the common case.
- Hugging Face tokens default to `https://router.huggingface.co/v1`.
- OpenAI keys default to `https://api.openai.com/v1`.
- Deterministic decoding (`temperature=0`) and fixed seeds.

If you want to override the endpoint explicitly, set `HF_OPENAI_BASE_URL` or `OPENAI_BASE_URL`.

The script now validates these combinations up front:
- `HF_TOKEN` starting with `hf_` routes to Hugging Face automatically
- `OPENAI_API_KEY` starting with `sk-` routes to OpenAI automatically
- You can still override either endpoint with `HF_OPENAI_BASE_URL` or `OPENAI_BASE_URL`

Output format:

```json
{
  "model": "...",
  "seed": 1337,
  "task_scores": {
    "easy_expense_triage": 1.0,
    "medium_meeting_scheduler": 1.0,
    "hard_incident_response": 1.0
  },
  "aggregate_score": 1.0
}
```

## Hugging Face Space Deployment (Docker)

This repo is configured for containerized Spaces via README front matter (`sdk: docker`) and a working `Dockerfile`.

On Hugging Face:
1. Create a new Space.
2. Choose Docker SDK.
3. Push this repository.
4. Ensure Space secret `HF_TOKEN` is set if running model-based baseline inside the Space.

The container serves on port `7860` and exposes environment endpoints:
- `GET /`
- `POST /reset/{task_id}`
- `POST /step`
- `GET /grade`

## Tests and CI

Unit tests are in `tests/test_environment.py` and cover:
- interface/task availability,
- seed reproducibility,
- invalid/undesirable action penalties,
- baseline policy completion across all tasks.

GitHub Actions workflow in `.github/workflows/ci.yml` runs:
1. `ruff check .`
2. `python -m unittest discover -s tests -v`
3. `python baseline_inference.py --seed 1337`
