"""Built-in deterministic mock tools for M3 scenarios/tests."""

from __future__ import annotations

from typing import Any

from .base import MockTool, ToolExecutionError


class CalculatorAddTool(MockTool):
    name = "calculator_add"

    def invoke(self, args: dict[str, Any]) -> Any:
        if not isinstance(args, dict):
            raise ToolExecutionError("args must be a dictionary")
        if "a" not in args or "b" not in args:
            raise ToolExecutionError("calculator_add requires numeric args: a, b")
        a, b = args["a"], args["b"]
        if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ToolExecutionError("calculator_add args a,b must be numbers (bool not allowed)")
        return {"sum": a + b}


class EchoTextTool(MockTool):
    name = "echo_text"

    def invoke(self, args: dict[str, Any]) -> Any:
        if not isinstance(args, dict):
            raise ToolExecutionError("args must be a dictionary")
        if "text" not in args:
            raise ToolExecutionError("echo_text requires arg: text")
        if not isinstance(args["text"], str):
            raise ToolExecutionError("echo_text arg text must be a string")
        return {"text": args["text"]}
