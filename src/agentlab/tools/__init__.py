"""Mock tool framework for AgentLab M3 (deterministic, no external side effects)."""

from .base import MockTool, ToolExecutionError
from .builtin_mocks import CalculatorAddTool, EchoTextTool
from .registry import MockToolRegistry

__all__ = [
    "CalculatorAddTool",
    "EchoTextTool",
    "MockTool",
    "MockToolRegistry",
    "ToolExecutionError",
]
