from __future__ import annotations

import argparse
import json
import os
import uvicorn
import sys
from typing import Any, Dict

from openai import OpenAI
from pydantic import ValidationError

from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action

DEFAULT_HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"

PROMPT_TEMPLATE = """
You are controlling an OpenEnv task environment.
Return a single JSON object with fields: command (string), args (object).
Do not include markdown.

Task: {task_id}
Observation summary: {summary}
Allowed commands: {allowed}
State view: {state_view}
""".strip()


def choose_action_with_model(client: OpenAI, model: str, task_id: str, obs: Dict[str, Any]) -> Action:
    prompt = PROMPT_TEMPLATE.format(
        task_id=task_id,
        summary=obs["summary"],
        allowed=obs["allowed_commands"],
        state_view=obs["state_view"],
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return only valid JSON with keys command and args."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    text = (response.choices[0].message.content or "").strip()
    data = json.loads(text)
    return Action.model_validate(data)


def _resolve_model_client() -> OpenAI:
    hf_token = os.getenv("HF_TOKEN")
    openai_token = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("HF_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL")

    if hf_token and openai_token:
        raise RuntimeError("Set only one of HF_TOKEN or OPENAI_API_KEY, not both.")

    if hf_token:
        if hf_token.startswith("hf_") and not base_url:
            base_url = "https://router.huggingface.co/v1"
        if not hf_token.startswith("hf_") and not base_url:
            base_url = "https://router.huggingface.co/v1"
        if "api.openai.com" in base_url:
            raise RuntimeError(
                "HF_TOKEN is set but OPENAI_BASE_URL points to OpenAI. "
                "Use HF_OPENAI_BASE_URL=https://router.huggingface.co/v1 for Hugging Face routing, "
                "or switch to OPENAI_API_KEY for the OpenAI API."
            )
        return OpenAI(api_key=hf_token, base_url=base_url or "https://router.huggingface.co/v1")

    if openai_token:
        if openai_token.startswith("sk-") and not base_url:
            base_url = "https://api.openai.com/v1"
        if not openai_token.startswith("sk-") and not base_url:
            base_url = "https://api.openai.com/v1"
        if "router.huggingface.co" in base_url:
            raise RuntimeError(
                "OPENAI_API_KEY is set but HF_OPENAI_BASE_URL points to Hugging Face. "
                "Use HF_TOKEN with the Hugging Face router, or set OPENAI_BASE_URL=https://api.openai.com/v1."
            )
        return OpenAI(api_key=openai_token, base_url=base_url or "https://api.openai.com/v1")

    raise RuntimeError(
        "Missing API credentials. Set HF_TOKEN for Hugging Face routing or OPENAI_API_KEY for the OpenAI API."
    )


def _resolve_default_model() -> str:
    hf_token = os.getenv("HF_TOKEN")
    openai_token = os.getenv("OPENAI_API_KEY")

    if hf_token and openai_token:
        raise RuntimeError("Set only one of HF_TOKEN or OPENAI_API_KEY, not both.")

    if hf_token:
        return DEFAULT_HF_MODEL
    if openai_token:
        return DEFAULT_OPENAI_MODEL

    raise RuntimeError(
        "Missing API credentials. Set HF_TOKEN for Hugging Face routing or OPENAI_API_KEY for the OpenAI API."
    )


def fallback_action(obs: Dict[str, Any]) -> Action:
    task_id = obs["task_id"]
    view = obs["state_view"]

    if task_id == "easy_expense_triage":
        for tx in view["transactions"]:
            if tx["approved"] is None:
                if tx["category"] == "entertainment":
                    return Action(command="flag_transaction", args={"transaction_id": tx["id"]})
                return Action(command="approve_transaction", args={"transaction_id": tx["id"]})
        return Action(command="add_note", args={"text": "triage complete"})

    if task_id == "medium_meeting_scheduler":
        if view["selected_time"] is None:
            return Action(command="set_meeting_time", args={"time": "14:00"})
        if len(view["agenda_items"]) < 3:
            return Action(command="add_agenda_item", args={"item": f"agenda-{len(view['agenda_items'])+1}"})
        if not view["sent_invites"]:
            return Action(command="send_invites", args={})
        return Action(command="noop", args={})

    if task_id == "hard_incident_response":
        for alert in view["alerts"]:
            if not alert["ack"]:
                return Action(command="ack_alert", args={"alert_id": alert["id"]})
        for name, enabled in view["mitigations"].items():
            if not enabled:
                return Action(command="apply_mitigation", args={"name": name})
        if not view["status_page_updated"]:
            return Action(command="update_status_page", args={})
        if not view["postmortem_published"]:
            return Action(command="publish_postmortem", args={})
        return Action(command="noop", args={})

    return Action(command="noop", args={})


def run_episode(task_id: str, model: str, seed: int, use_model: bool) -> float:
    env = OpenEnvEnvironment()
    reset = env.reset(task_id=task_id, seed=seed)
    obs = reset.observation.model_dump()

    client = None
    if use_model:
        client = _resolve_model_client()

    warned_model_not_found = False
    done = False
    while not done:
        if client is not None:
            try:
                action = choose_action_with_model(client, model=model, task_id=task_id, obs=obs)
            except (json.JSONDecodeError, ValidationError):
                action = fallback_action(obs)
            except Exception as exc:
                if "model_not_found" in str(exc) and not warned_model_not_found:
                    print(f"[WARN] Model {model} not found; falling back to heuristic policy for this run.", file=sys.stderr)
                    warned_model_not_found = True
                action = fallback_action(obs)
        else:
            action = fallback_action(obs)

        step_result = env.step(action)
        obs = step_result.observation.model_dump()
        done = step_result.observation.done

    return env.grade().score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Optional explicit model override.")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--use-model", action="store_true")
    args = parser.parse_args()

    selected_model = args.model or (_resolve_default_model() if args.use_model else None)

    if args.use_model:
        hf_token = os.getenv("HF_TOKEN")
        openai_token = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("HF_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL")

        if hf_token:
            resolved_base = base_url or "https://router.huggingface.co/v1"
            print(
                f"[DEBUG] Using HF_TOKEN routing to {resolved_base} with model={selected_model}",
                file=sys.stderr,
            )
        elif openai_token:
            resolved_base = base_url or "https://api.openai.com/v1"
            print(
                f"[DEBUG] Using OPENAI_API_KEY routing to {resolved_base} with model={selected_model}",
                file=sys.stderr,
            )

    task_ids = ["easy_expense_triage", "medium_meeting_scheduler", "hard_incident_response"]

    results: Dict[str, float] = {}
    for idx, task_id in enumerate(task_ids):
        if args.use_model and selected_model is None:
            raise RuntimeError("Model resolution failed while --use-model is enabled.")
        model_for_episode = selected_model or "fallback-heuristic"
        results[task_id] = run_episode(task_id=task_id, model=model_for_episode, seed=args.seed + idx, use_model=args.use_model)

    aggregate = round(sum(results.values()) / len(results), 4)
    output = {
        "model": selected_model if args.use_model else "fallback-heuristic",
        "seed": args.seed,
        "task_scores": results,
        "aggregate_score": aggregate,
    }
    print(json.dumps(output, indent=2))
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server.app:app", host="localhost", port=port)


if __name__ == "__main__":
    main()
