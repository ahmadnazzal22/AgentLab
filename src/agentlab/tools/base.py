"""Base interfaces for deterministic mock tools (M3).

Mock tools MUST be safe and deterministic:
- no network access
- no file/process execution
- no external side effects
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolExecutionError(Exception):
    """Raised when a mock tool cannot execute the given arguments deterministically."""


class MockTool(ABC):
    """Abstract deterministic mock tool."""

    name: str

    @abstractmethod
    def invoke(self, args: dict[str, Any]) -> Any:
        """Execute the tool with validated/expected args and return a JSON-compatible result."""
        raise NotImplementedError
