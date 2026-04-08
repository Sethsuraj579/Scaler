from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


Difficulty = Literal["easy", "medium", "hard"]


@dataclass
class TaskDefinition:
    task_id: str
    title: str
    difficulty: Difficulty
    description: str
    max_steps: int
    initial_state: Dict[str, Any]


TASKS: List[TaskDefinition] = [
    TaskDefinition(
        task_id="easy_expense_triage",
        title="Expense Triage",
        difficulty="easy",
        description=(
            "Classify company expenses into approved or flagged categories and keep the monthly budget in range."
        ),
        max_steps=8,
        initial_state={
            "budget_limit": 2000,
            "transactions": [
                {"id": "t1", "amount": 450, "category": "office", "approved": None},
                {"id": "t2", "amount": 1200, "category": "travel", "approved": None},
                {"id": "t3", "amount": 950, "category": "entertainment", "approved": None},
            ],
            "notes": [],
        },
    ),
    TaskDefinition(
        task_id="medium_meeting_scheduler",
        title="Meeting Scheduler",
        difficulty="medium",
        description=(
            "Schedule a cross-functional launch meeting that satisfies participant constraints and minimizes conflicts."
        ),
        max_steps=10,
        initial_state={
            "participants": {
                "eng": ["09:00", "10:00", "14:00"],
                "design": ["10:00", "11:00", "14:00"],
                "sales": ["11:00", "14:00", "15:00"],
            },
            "required": ["eng", "design", "sales"],
            "selected_time": None,
            "sent_invites": False,
            "agenda_items": [],
        },
    ),
    TaskDefinition(
        task_id="hard_incident_response",
        title="Incident Response Drill",
        difficulty="hard",
        description=(
            "Contain and recover from a production outage by triaging alerts, mitigating impact, and publishing a postmortem."
        ),
        max_steps=14,
        initial_state={
            "alerts": [
                {"id": "a1", "service": "api", "severity": "high", "ack": False},
                {"id": "a2", "service": "db", "severity": "critical", "ack": False},
                {"id": "a3", "service": "cache", "severity": "medium", "ack": False},
            ],
            "mitigations": {
                "rollback": False,
                "scale_up": False,
                "feature_flag_off": False,
            },
            "customer_impact": "high",
            "status_page_updated": False,
            "postmortem_published": False,
        },
    ),
]


def grade_easy_expense(state: Dict[str, Any]) -> float:
    transactions = state["transactions"]
    approved_total = sum(t["amount"] for t in transactions if t.get("approved") is True)
    budget = state["budget_limit"]

    approvals_done = sum(1 for t in transactions if t.get("approved") is not None) / len(transactions)
    budget_score = 1.0 if approved_total <= budget else max(0.0, 1.0 - (approved_total - budget) / budget)

    risky = [t for t in transactions if t["category"] == "entertainment"]
    risk_score = 1.0 if all(t.get("approved") is False for t in risky) else 0.0

    return round(max(0.0, min(1.0, 0.4 * approvals_done + 0.3 * budget_score + 0.3 * risk_score)), 4)


def grade_medium_scheduler(state: Dict[str, Any]) -> float:
    selected_time = state["selected_time"]
    sent_invites = state["sent_invites"]
    agenda_len = len(state["agenda_items"])

    if selected_time is None:
        time_score = 0.0
    else:
        required = state["required"]
        availability = state["participants"]
        all_available = all(selected_time in availability[p] for p in required)
        time_score = 1.0 if all_available else 0.3

    invite_score = 1.0 if sent_invites else 0.0
    agenda_score = min(1.0, agenda_len / 3)

    return round(max(0.0, min(1.0, 0.5 * time_score + 0.3 * invite_score + 0.2 * agenda_score)), 4)


def grade_hard_incident(state: Dict[str, Any]) -> float:
    alerts = state["alerts"]
    ack_ratio = sum(1 for a in alerts if a["ack"]) / len(alerts)

    mitigations = state["mitigations"]
    mitigation_ratio = sum(1 for v in mitigations.values() if v) / len(mitigations)

    impact_score = {"high": 0.0, "medium": 0.5, "low": 1.0}[state["customer_impact"]]
    status_score = 1.0 if state["status_page_updated"] else 0.0
    postmortem_score = 1.0 if state["postmortem_published"] else 0.0

    return round(
        max(
            0.0,
            min(1.0, 0.25 * ack_ratio + 0.25 * mitigation_ratio + 0.2 * impact_score + 0.15 * status_score + 0.15 * postmortem_score),
        ),
        4,
    )


def grade_task(task_id: str, state: Dict[str, Any]) -> float:
    if task_id == "easy_expense_triage":
        return grade_easy_expense(state)
    if task_id == "medium_meeting_scheduler":
        return grade_medium_scheduler(state)
    if task_id == "hard_incident_response":
        return grade_hard_incident(state)
    return 0.0
