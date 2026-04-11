from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional

from .spec import Action, EnvMetadata, GradeResult, Observation, OpenEnvProtocol, ResetResult, StepResult, TaskInfo
from .tasks import TASKS, grade_task


class OpenEnvEnvironment(OpenEnvProtocol):
    def __init__(self) -> None:
        self._task_lookup = {t.task_id: t for t in TASKS}
        self._current_task_id: Optional[str] = None
        self._state: Dict[str, Any] = {}
        self._step_index: int = 0
        self._last_score: float = 0.0
        self._last_hard_aux_progress: float = 0.0
        self._rng = random.Random(0)

    def metadata(self) -> EnvMetadata:
        return EnvMetadata(
            name="real-world-openenv",
            version="0.1.0",
            description="OpenEnv-compatible environment for realistic decision-making tasks.",
            action_schema_hint='{"command": "string", "args": {"...": "..."}}',
            observation_schema_hint='{"summary": "string", "state_view": {...}, "progress": 0.0}',
        )

    def tasks(self) -> List[TaskInfo]:
        return [
            TaskInfo(
                task_id=t.task_id,
                title=t.title,
                difficulty=t.difficulty,
                description=t.description,
                max_steps=t.max_steps,
            )
            for t in TASKS
        ]

    def reset(self, task_id: str, seed: Optional[int] = None) -> ResetResult:
        if task_id not in self._task_lookup:
            raise ValueError(f"Unknown task_id: {task_id}")

        if seed is not None:
            self._rng.seed(seed)

        task = self._task_lookup[task_id]
        self._current_task_id = task_id
        self._state = copy.deepcopy(task.initial_state)
        self._step_index = 0
        self._last_score = grade_task(task_id, self._state)
        self._last_hard_aux_progress = self._hard_aux_progress() if task_id == "hard_incident_response" else 0.0

        # Lightweight stochasticity for realism while preserving seed reproducibility.
        if task_id == "easy_expense_triage":
            self._rng.shuffle(self._state["transactions"])

        obs = self._build_observation(done=False)
        return ResetResult(observation=obs, info={"task": task_id})

    def step(self, action: Action) -> StepResult:
        if self._current_task_id is None:
            raise RuntimeError("Call reset(task_id=...) before step(...)")

        self._step_index += 1
        invalid_penalty = 0.0
        harmful_penalty = 0.0

        applied = self._apply_action(action)
        if not applied:
            invalid_penalty -= 0.08

        if action.command in {"delete_data", "ignore_incident", "approve_all"}:
            harmful_penalty -= 0.2

        new_score = grade_task(self._current_task_id, self._state)
        progress_delta = new_score - self._last_score

        reward = 1.8 * progress_delta + invalid_penalty + harmful_penalty - 0.01

        if self._current_task_id == "hard_incident_response":
            aux_now = self._hard_aux_progress()
            aux_delta = aux_now - self._last_hard_aux_progress
            reward += 0.5 * aux_delta
            self._last_hard_aux_progress = aux_now

            # Encourage meaningful response actions and discourage stalling.
            if applied and action.command != "noop":
                reward += 0.015
            if action.command == "noop" and self._state.get("customer_impact") in {"high", "medium"}:
                reward -= 0.03

        task = self._task_lookup[self._current_task_id]
        terminated = new_score >= 0.99
        truncated = self._step_index >= task.max_steps and not terminated
        done = terminated or truncated

        if done and terminated:
            reward += 0.15

        self._last_score = new_score
        obs = self._build_observation(done=done)

        return StepResult(
            observation=obs,
            reward=round(reward, 4),
            terminated=terminated,
            truncated=truncated,
            info={
                "applied": applied,
                "progress_delta": round(progress_delta, 4),
                "score": new_score,
            },
        )

    def grade(self) -> GradeResult:
        if self._current_task_id is None:
            raise RuntimeError("No active task to grade")
        score = grade_task(self._current_task_id, self._state)
        return GradeResult(task_id=self._current_task_id, score=score, detail={"steps": self._step_index})

    def render(self) -> Dict[str, Any]:
        if self._current_task_id is None:
            return {"status": "idle"}
        return {
            "task_id": self._current_task_id,
            "step_index": self._step_index,
            "state": self._state,
            "score": grade_task(self._current_task_id, self._state),
        }

    def close(self) -> None:
        self._current_task_id = None
        self._state = {}
        self._step_index = 0
        self._last_score = 0.0
        self._last_hard_aux_progress = 0.0

    def _hard_aux_progress(self) -> float:
        alerts = self._state.get("alerts", [])
        if not alerts:
            return 0.0

        ack_ratio = sum(1 for a in alerts if a.get("ack")) / len(alerts)
        mitigations = self._state.get("mitigations", {})
        mitigation_ratio = (
            sum(1 for enabled in mitigations.values() if enabled) / len(mitigations) if mitigations else 0.0
        )
        impact_map = {"high": 0.0, "medium": 0.6, "low": 1.0}
        impact_progress = impact_map.get(self._state.get("customer_impact", "high"), 0.0)
        status_progress = 1.0 if self._state.get("status_page_updated") else 0.0

        return 0.4 * ack_ratio + 0.35 * mitigation_ratio + 0.15 * impact_progress + 0.1 * status_progress

    def _build_observation(self, done: bool) -> Observation:
        task = self._task_lookup[self._current_task_id]  # type: ignore[index]
        score = grade_task(self._current_task_id, self._state)  # type: ignore[arg-type]

        return Observation(
            task_id=task.task_id,
            step_index=self._step_index,
            max_steps=task.max_steps,
            score=score,
            progress=score,
            summary=self._summary(task.task_id),
            state_view=self._public_state_view(task.task_id),
            allowed_commands=self._allowed_commands(task.task_id),
            done=done,
        )

    def _allowed_commands(self, task_id: str) -> List[str]:
        common = ["noop"]
        if task_id == "easy_expense_triage":
            return common + ["approve_transaction", "flag_transaction", "add_note"]
        if task_id == "medium_meeting_scheduler":
            return common + ["set_meeting_time", "add_agenda_item", "send_invites"]
        if task_id == "hard_incident_response":
            return common + ["ack_alert", "apply_mitigation", "update_status_page", "publish_postmortem"]
        if task_id == "easy_robot_assembly":
            return common + ["add_part", "complete_robot", "check_quality"]
        if task_id == "medium_robot_factory":
            return common + ["add_part", "test_quality", "complete_robot", "increase_speed"]
        if task_id == "hard_robot_optimization":
            return common + ["add_part", "test_quality", "complete_robot", "increase_speed", "repair_station"]
        return common

    def _summary(self, task_id: str) -> str:
        if task_id == "easy_expense_triage":
            decided = sum(1 for t in self._state["transactions"] if t["approved"] is not None)
            return f"Reviewed {decided}/{len(self._state['transactions'])} transactions."
        if task_id == "medium_meeting_scheduler":
            return (
                f"Meeting time: {self._state['selected_time']}; "
                f"agenda items: {len(self._state['agenda_items'])}; "
                f"invites sent: {self._state['sent_invites']}"
            )
        if task_id == "hard_incident_response":
            acked = sum(1 for a in self._state["alerts"] if a["ack"])
            return (
                f"Acknowledged alerts: {acked}/{len(self._state['alerts'])}; "
                f"impact: {self._state['customer_impact']}; "
                f"postmortem: {self._state['postmortem_published']}"
            )
        if task_id == "easy_robot_assembly":
            return (
                f"Robots completed: {self._state['robots_completed']}/{self._state['target_robots']}; "
                f"quality: {self._state['quality_score']:.2f}"
            )
        if task_id == "medium_robot_factory":
            return (
                f"Robots completed: {self._state['robots_completed']}/{self._state['target_robots']}; "
                f"defective: {self._state['defective_units']}; "
                f"quality pass rate: {self._state['quality_tests_passed']}/{self._state['quality_tests_passed'] + self._state['quality_tests_failed']}"
            )
        if task_id == "hard_robot_optimization":
            defect_rate = (self._state['defective_units'] / (self._state['robots_completed'] + self._state['defective_units'])) if (self._state['robots_completed'] + self._state['defective_units']) > 0 else 0
            return (
                f"Robots completed: {self._state['robots_completed']}/{self._state['target_robots']}; "
                f"defect rate: {defect_rate:.2%}; "
                f"energy used: {self._state['energy_used']}/{self._state['energy_budget']}"
            )
        return ""

    def _public_state_view(self, task_id: str) -> Dict[str, Any]:
        if task_id == "easy_expense_triage":
            return {
                "budget_limit": self._state["budget_limit"],
                "transactions": self._state["transactions"],
                "notes_count": len(self._state["notes"]),
            }
        if task_id == "medium_meeting_scheduler":
            return {
                "participants": self._state["participants"],
                "required": self._state["required"],
                "selected_time": self._state["selected_time"],
                "agenda_items": self._state["agenda_items"],
                "sent_invites": self._state["sent_invites"],
            }
        if task_id == "hard_incident_response":
            return {
                "alerts": self._state["alerts"],
                "mitigations": self._state["mitigations"],
                "customer_impact": self._state["customer_impact"],
                "status_page_updated": self._state["status_page_updated"],
                "postmortem_published": self._state["postmortem_published"],
            }
        if task_id == "easy_robot_assembly":
            return {
                "robots_completed": self._state["robots_completed"],
                "target_robots": self._state["target_robots"],
                "available_parts": self._state["available_parts"],
                "current_assembly": self._state["current_assembly"],
                "quality_score": self._state["quality_score"],
            }
        if task_id == "medium_robot_factory":
            return {
                "robots_completed": self._state["robots_completed"],
                "target_robots": self._state["target_robots"],
                "defective_units": self._state["defective_units"],
                "parts_inventory": self._state["parts_inventory"],
                "current_assembly": self._state["current_assembly"],
                "quality_tests_passed": self._state["quality_tests_passed"],
                "quality_tests_failed": self._state["quality_tests_failed"],
            }
        if task_id == "hard_robot_optimization":
            return {
                "robots_completed": self._state["robots_completed"],
                "target_robots": self._state["target_robots"],
                "defective_units": self._state["defective_units"],
                "energy_used": self._state["energy_used"],
                "energy_budget": self._state["energy_budget"],
                "parts_inventory": self._state["parts_inventory"],
                "current_assembly": self._state["current_assembly"],
                "quality_score": self._state["quality_score"],
                "cost_per_robot": self._state["cost_per_robot"],
            }
        return {}

    def _apply_action(self, action: Action) -> bool:
        task_id = self._current_task_id
        if task_id == "easy_expense_triage":
            return self._apply_easy(action)
        if task_id == "medium_meeting_scheduler":
            return self._apply_medium(action)
        if task_id == "hard_incident_response":
            return self._apply_hard(action)
        if task_id == "easy_robot_assembly":
            return self._apply_easy_robot(action)
        if task_id == "medium_robot_factory":
            return self._apply_medium_robot(action)
        if task_id == "hard_robot_optimization":
            return self._apply_hard_robot(action)
        return False

    def _apply_easy(self, action: Action) -> bool:
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        if cmd == "approve_transaction":
            tx_id = args.get("transaction_id")
            for tx in self._state["transactions"]:
                if tx["id"] == tx_id:
                    tx["approved"] = True
                    return True
            return False
        if cmd == "flag_transaction":
            tx_id = args.get("transaction_id")
            for tx in self._state["transactions"]:
                if tx["id"] == tx_id:
                    tx["approved"] = False
                    return True
            return False
        if cmd == "add_note":
            text = args.get("text")
            if not isinstance(text, str) or not text.strip():
                return False
            self._state["notes"].append(text.strip())
            return True
        return False

    def _apply_medium(self, action: Action) -> bool:
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        if cmd == "set_meeting_time":
            time = args.get("time")
            if not isinstance(time, str):
                return False
            self._state["selected_time"] = time
            return True
        if cmd == "add_agenda_item":
            item = args.get("item")
            if not isinstance(item, str) or not item.strip():
                return False
            self._state["agenda_items"].append(item.strip())
            return True
        if cmd == "send_invites":
            self._state["sent_invites"] = True
            return True
        return False

    def _apply_hard(self, action: Action) -> bool:
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        if cmd == "ack_alert":
            alert_id = args.get("alert_id")
            for alert in self._state["alerts"]:
                if alert["id"] == alert_id:
                    alert["ack"] = True
                    return True
            return False
        if cmd == "apply_mitigation":
            mitigation = args.get("name")
            if mitigation not in self._state["mitigations"]:
                return False
            self._state["mitigations"][mitigation] = True
            if mitigation in {"rollback", "feature_flag_off"}:
                self._state["customer_impact"] = "medium"
            if all(self._state["mitigations"].values()):
                self._state["customer_impact"] = "low"
            return True
        if cmd == "update_status_page":
            self._state["status_page_updated"] = True
            return True
        if cmd == "publish_postmortem":
            if self._state["customer_impact"] != "low":
                return False
            self._state["postmortem_published"] = True
            return True
        return False

    def _apply_easy_robot(self, action: Action) -> bool:
        """Handle actions for easy robot assembly task."""
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        
        if cmd == "add_part":
            part_type = args.get("part_type")
            if part_type not in self._state["current_assembly"]:
                return False
            if self._state["available_parts"].get(part_type, 0) <= 0:
                return False
            self._state["current_assembly"][part_type] += 1
            self._state["available_parts"][part_type] -= 1
            return True
        
        if cmd == "complete_robot":
            assembly = self._state["current_assembly"]
            # Check if robot has all required parts
            required_parts = {"arms": 1, "legs": 1, "heads": 1, "batteries": 1}
            if not all(assembly.get(part, 0) >= count for part, count in required_parts.items()):
                return False
            
            self._state["robots_completed"] += 1
            for part in assembly:
                assembly[part] = 0
            
            # Add slight quality degradation for multiple robots
            self._state["quality_score"] = max(0.7, self._state["quality_score"] - 0.05)
            self._state["assembly_log"].append(f"Robot {self._state['robots_completed']} completed")
            return True
        
        if cmd == "check_quality":
            # Quality check improves score
            self._state["quality_score"] = min(1.0, self._state["quality_score"] + 0.1)
            return True
        
        return False

    def _apply_medium_robot(self, action: Action) -> bool:
        """Handle actions for medium robot factory task."""
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        
        if cmd == "add_part":
            part_type = args.get("part_type")
            if part_type not in self._state["current_assembly"]:
                return False
            if self._state["parts_inventory"].get(part_type, 0) <= 0:
                return False
            self._state["current_assembly"][part_type] += 1
            self._state["parts_inventory"][part_type] -= 1
            return True
        
        if cmd == "complete_robot":
            assembly = self._state["current_assembly"]
            required_parts = {"arms": 1, "legs": 1, "heads": 1, "batteries": 1, "circuits": 1}
            if not all(assembly.get(part, 0) >= count for part, count in required_parts.items()):
                return False
            
            self._state["robots_completed"] += 1
            for part in assembly:
                assembly[part] = 0
            
            # Random chance of defect
            if self._rng.random() < 0.2:
                self._state["defective_units"] += 1
            
            self._state["assembly_efficiency"] = min(1.0, self._state["assembly_efficiency"] + 0.08)
            return True
        
        if cmd == "test_quality":
            # Run quality test
            if self._rng.random() < 0.7:
                self._state["quality_tests_passed"] += 1
            else:
                self._state["quality_tests_failed"] += 1
            return True
        
        if cmd == "increase_speed":
            # Increase speed but risk more defects
            self._state["assembly_efficiency"] = min(1.0, self._state["assembly_efficiency"] + 0.15)
            return True
        
        return False

    def _apply_hard_robot(self, action: Action) -> bool:
        """Handle actions for hard robot optimization task."""
        cmd = action.command
        args = action.args

        if cmd == "noop":
            return True
        
        if cmd == "add_part":
            part_type = args.get("part_type")
            if part_type not in self._state["current_assembly"]:
                return False
            if self._state["parts_inventory"].get(part_type, 0) <= 0:
                return False
            
            # Energy cost for adding parts
            energy_cost = {"arms": 5, "legs": 5, "heads": 8, "batteries": 10, "circuits": 12, "processors": 15}.get(part_type, 5)
            if self._state["energy_used"] + energy_cost > self._state["energy_budget"]:
                return False
            
            self._state["current_assembly"][part_type] += 1
            self._state["parts_inventory"][part_type] -= 1
            self._state["energy_used"] += energy_cost
            return True
        
        if cmd == "complete_robot":
            assembly = self._state["current_assembly"]
            required_parts = {"arms": 1, "legs": 1, "heads": 1, "batteries": 1, "circuits": 1, "processors": 1}
            if not all(assembly.get(part, 0) >= count for part, count in required_parts.items()):
                return False
            
            # Energy cost for completing
            if self._state["energy_used"] + 20 > self._state["energy_budget"]:
                return False
            
            self._state["robots_completed"] += 1
            self._state["energy_used"] += 20
            
            for part in assembly:
                assembly[part] = 0
            
            # Higher chance of defects under pressure
            defect_chance = min(0.3, 0.1 + (self._state["energy_used"] / self._state["energy_budget"]) * 0.1)
            if self._rng.random() < defect_chance:
                self._state["defective_units"] += 1
            
            # Calculate cost per robot
            cost = self._state["energy_used"] / max(1, self._state["robots_completed"])
            self._state["cost_per_robot"] = cost
            
            # Efficiency bonus for staying under budget and low defects
            if self._state["robots_completed"] > 0:
                defect_rate = self._state["defective_units"] / self._state["robots_completed"]
                if defect_rate <= 0.1:
                    self._state["efficiency_bonus"] = min(1.0, self._state["efficiency_bonus"] + 0.15)
            return True
        
        if cmd == "test_quality":
            # Quality testing uses some energy
            if self._state["energy_used"] + 5 > self._state["energy_budget"]:
                return False
            
            self._state["energy_used"] += 5
            if self._rng.random() < 0.75:
                self._state["quality_score"] = min(1.0, self._state["quality_score"] + 0.05)
            else:
                self._state["quality_score"] = max(0.0, self._state["quality_score"] - 0.1)
            return True
        
        if cmd == "increase_speed":
            # Increase speed but consume more energy
            if self._state["energy_used"] + 8 > self._state["energy_budget"]:
                return False
            self._state["energy_used"] += 8
            return True
        
        if cmd == "repair_station":
            # Repair damaged units
            if self._state["defective_units"] <= 0:
                return False
            if self._state["energy_used"] + 15 > self._state["energy_budget"]:
                return False
            
            self._state["defective_units"] -= 1
            self._state["robots_completed"] += 1
            self._state["energy_used"] += 15
            self._state["maintenance_repairs"] += 1
            return True
        
        return False
