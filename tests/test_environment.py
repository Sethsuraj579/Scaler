from __future__ import annotations

import unittest

from baseline_inference import fallback_action
from openenv_env.environment import OpenEnvEnvironment
from openenv_env.spec import Action


class TestOpenEnvEnvironment(unittest.TestCase):
    def setUp(self) -> None:
        self.env = OpenEnvEnvironment()

    def tearDown(self) -> None:
        self.env.close()

    def test_tasks_exist_with_expected_difficulties(self) -> None:
        tasks = self.env.tasks()
        self.assertEqual(len(tasks), 3)
        difficulties = {t.task_id: t.difficulty for t in tasks}
        self.assertEqual(difficulties["easy_expense_triage"], "easy")
        self.assertEqual(difficulties["medium_meeting_scheduler"], "medium")
        self.assertEqual(difficulties["hard_incident_response"], "hard")

    def test_seed_reproducibility_for_easy_task(self) -> None:
        first = self.env.reset(task_id="easy_expense_triage", seed=77)
        order_one = [tx["id"] for tx in first.observation.state_view["transactions"]]

        second = self.env.reset(task_id="easy_expense_triage", seed=77)
        order_two = [tx["id"] for tx in second.observation.state_view["transactions"]]

        self.assertEqual(order_one, order_two)

    def test_invalid_action_penalty(self) -> None:
        self.env.reset(task_id="medium_meeting_scheduler", seed=1)
        step = self.env.step(Action(command="invalid_command", args={}))

        self.assertFalse(step.info["applied"])
        self.assertLess(step.reward, -0.05)

    def test_undesirable_action_penalty(self) -> None:
        self.env.reset(task_id="hard_incident_response", seed=1)
        step = self.env.step(Action(command="ignore_incident", args={}))

        self.assertFalse(step.info["applied"])
        self.assertLessEqual(step.reward, -0.25)

    def test_baseline_policy_completes_all_tasks(self) -> None:
        task_ids = ["easy_expense_triage", "medium_meeting_scheduler", "hard_incident_response"]

        for offset, task_id in enumerate(task_ids):
            reset = self.env.reset(task_id=task_id, seed=100 + offset)
            obs = reset.observation.model_dump()
            done = False

            while not done:
                action = fallback_action(obs)
                result = self.env.step(action)
                obs = result.observation.model_dump()
                done = result.observation.done

            score = self.env.grade().score
            self.assertGreaterEqual(score, 0.99)
            self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
