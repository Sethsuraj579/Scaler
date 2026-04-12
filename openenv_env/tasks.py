from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


Difficulty = Literal["easy", "medium", "hard"]


def _normalize_score(score: float) -> float:
    """Ensure score is strictly between 0 and 1 (open interval).
    
    Maps [0, 1] to (0, 1): 0 → 0.01, 0.5 → 0.50, 1 → 0.99
    This ensures scores never reach the boundaries, satisfying validator requirements.
    """
    clamped = max(0.0, min(1.0, score))
    return round(0.01 + clamped * 0.98, 4)


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
    TaskDefinition(
        task_id="easy_robot_assembly",
        title="Robot Assembly Line",
        difficulty="easy",
        description=(
            "Assemble robots by collecting parts and following instructions. Complete as many robots as possible."
        ),
        max_steps=10,
        initial_state={
            "robots_completed": 0,
            "target_robots": 3,
            "available_parts": {
                "arms": 5,
                "legs": 5,
                "heads": 5,
                "batteries": 5,
            },
            "current_assembly": {"arms": 0, "legs": 0, "heads": 0, "batteries": 0},
            "quality_score": 1.0,
            "assembly_log": [],
        },
    ),
    TaskDefinition(
        task_id="medium_robot_factory",
        title="Robot Factory Manager",
        difficulty="medium",
        description=(
            "Manage a robot factory: assemble robots, maintain quality control, and maximize output under time pressure."
        ),
        max_steps=12,
        initial_state={
            "robots_completed": 0,
            "target_robots": 5,
            "defective_units": 0,
            "quality_threshold": 0.8,
            "parts_inventory": {
                "arms": 8,
                "legs": 8,
                "heads": 8,
                "batteries": 8,
                "circuits": 5,
            },
            "current_assembly": {"arms": 0, "legs": 0, "heads": 0, "batteries": 0, "circuits": 0},
            "quality_tests_passed": 0,
            "quality_tests_failed": 0,
            "assembly_efficiency": 0.0,
        },
    ),
    TaskDefinition(
        task_id="hard_robot_optimization",
        title="Advanced Robot Production",
        difficulty="hard",
        description=(
            "Optimize robot production with limited resources, manage defect rates, and balance speed vs. quality."
        ),
        max_steps=15,
        initial_state={
            "robots_completed": 0,
            "target_robots": 8,
            "defective_units": 0,
            "max_defect_rate": 0.15,
            "energy_budget": 100,
            "energy_used": 0,
            "parts_inventory": {
                "arms": 12,
                "legs": 12,
                "heads": 12,
                "batteries": 12,
                "circuits": 8,
                "processors": 4,
            },
            "current_assembly": {"arms": 0, "legs": 0, "heads": 0, "batteries": 0, "circuits": 0, "processors": 0},
            "quality_score": 1.0,
            "efficiency_bonus": 0.0,
            "cost_per_robot": 0.0,
            "maintenance_repairs": 0,
            "assembly_log": [],
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

    score = max(0.0, min(1.0, 0.4 * approvals_done + 0.3 * budget_score + 0.3 * risk_score))
    return _normalize_score(score)


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

    score = max(0.0, min(1.0, 0.5 * time_score + 0.3 * invite_score + 0.2 * agenda_score))
    return _normalize_score(score)


def grade_hard_incident(state: Dict[str, Any]) -> float:
    alerts = state["alerts"]
    ack_ratio = sum(1 for a in alerts if a["ack"]) / len(alerts)

    mitigations = state["mitigations"]
    mitigation_ratio = sum(1 for v in mitigations.values() if v) / len(mitigations)

    impact_score = {"high": 0.0, "medium": 0.5, "low": 1.0}[state["customer_impact"]]
    status_score = 1.0 if state["status_page_updated"] else 0.0
    postmortem_score = 1.0 if state["postmortem_published"] else 0.0

    score = max(
        0.0,
        min(1.0, 0.25 * ack_ratio + 0.25 * mitigation_ratio + 0.2 * impact_score + 0.15 * status_score + 0.15 * postmortem_score),
    )
    return _normalize_score(score)


def grade_easy_robot_assembly(state: Dict[str, Any]) -> float:
    """Grade the easy robot assembly task based on robots completed and quality."""
    robots_done = state["robots_completed"]
    target = state["target_robots"]
    quality = state["quality_score"]
    
    completion_score = min(1.0, robots_done / target)
    quality_score = quality
    
    score = max(0.0, min(1.0, 0.6 * completion_score + 0.4 * quality_score))
    return _normalize_score(score)


def grade_medium_robot_factory(state: Dict[str, Any]) -> float:
    """Grade the medium robot factory task based on output, quality, and efficiency."""
    robots_done = state["robots_completed"]
    target = state["target_robots"]
    quality_threshold = state["quality_threshold"]
    
    tests_passed = state["quality_tests_passed"]
    tests_failed = state["quality_tests_failed"]
    total_tests = tests_passed + tests_failed
    
    completion_score = min(1.0, robots_done / target)
    
    if total_tests > 0:
        pass_rate = tests_passed / total_tests
        quality_score = 1.0 if pass_rate >= quality_threshold else max(0.0, pass_rate - 0.2)
    else:
        quality_score = 0.5
    
    defect_penalty = max(0.0, -state["defective_units"] * 0.1)
    efficiency = state["assembly_efficiency"]
    
    score = max(0.0, min(1.0, 0.4 * completion_score + 0.3 * quality_score + 0.2 * efficiency + 0.1 + defect_penalty))
    return _normalize_score(score)


def grade_hard_robot_optimization(state: Dict[str, Any]) -> float:
    """Grade the hard robot optimization task based on output, defect rate, energy efficiency, and cost."""
    robots_done = state["robots_completed"]
    target = state["target_robots"]
    max_defect_rate = state["max_defect_rate"]
    
    completion_score = min(1.0, robots_done / target)
    
    if robots_done > 0:
        defect_rate = state["defective_units"] / (robots_done + state["defective_units"])
        quality_score = 1.0 if defect_rate <= max_defect_rate else max(0.0, 1.0 - (defect_rate - max_defect_rate) * 2)
    else:
        quality_score = 1.0
    
    energy_efficiency = 1.0 - min(1.0, state["energy_used"] / state["energy_budget"]) if state["energy_budget"] > 0 else 0.5
    
    efficiency_bonus = state["efficiency_bonus"]
    
    score = max(0.0, min(1.0, 0.35 * completion_score + 0.3 * quality_score + 0.2 * energy_efficiency + 0.15 * efficiency_bonus))
    return _normalize_score(score)


def grade_task(task_id: str, state: Dict[str, Any]) -> float:
    if task_id == "easy_expense_triage":
        return grade_easy_expense(state)
    if task_id == "medium_meeting_scheduler":
        return grade_medium_scheduler(state)
    if task_id == "hard_incident_response":
        return grade_hard_incident(state)
    if task_id == "easy_robot_assembly":
        return grade_easy_robot_assembly(state)
    if task_id == "medium_robot_factory":
        return grade_medium_robot_factory(state)
    if task_id == "hard_robot_optimization":
        return grade_hard_robot_optimization(state)
    return 0.0
