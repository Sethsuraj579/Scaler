"""
Pytest configuration and shared fixtures for OpenEnv tests.
"""

import pytest
from environment import OpenEnvWrapper
from inference import SimpleAgents


@pytest.fixture
def easy_env():
    """Fixture: Easy environment."""
    return OpenEnvWrapper(task_id="easy")


@pytest.fixture
def medium_env():
    """Fixture: Medium environment."""
    return OpenEnvWrapper(task_id="medium")


@pytest.fixture
def hard_env():
    """Fixture: Hard environment."""
    return OpenEnvWrapper(task_id="hard")


@pytest.fixture
def reset_easy():
    """Fixture: Reset easy environment and return observation."""
    env = OpenEnvWrapper(task_id="easy")
    return env.reset()


@pytest.fixture
def reset_medium():
    """Fixture: Reset medium environment and return observation."""
    env = OpenEnvWrapper(task_id="medium")
    return env.reset()
