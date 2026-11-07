"""Base agent interface.

M2 contract:
- Agent.execute(scenario) -> list[Event]
- Agent returns events only and must not mutate a Run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentlab.core.models import Event, Scenario


class Agent(ABC):
    """Abstract base class for agents under test."""

    @abstractmethod
    def execute(self, scenario: Scenario) -> list[Event]:
        """Execute a scenario and return recorded events.

        The agent must not mutate any Run object; the Runner owns Run lifecycle
        and records returned events via run.add_event().
        """
        raise NotImplementedError
