"""Tests for M2 agent interface and sample agent."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents.base import Agent
from agentlab.agents.sample_agent import SampleAgent
from agentlab.core.models import Event, Scenario


class TestSampleAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = Scenario(
            id="scen-hello",
            name="Hello",
            description="d",
            task="Say hello",
            metadata={"expected_output": "Hello, world!"},
        )

    def test_execute_returns_events_only(self) -> None:
        agent = SampleAgent(agent_id="sample-agent")
        events = agent.execute(self.scenario)
        self.assertIsInstance(events, list)
        self.assertTrue(events)
        self.assertTrue(all(isinstance(e, Event) for e in events))

    def test_deterministic_output(self) -> None:
        agent = SampleAgent(agent_id="sample-agent")
        e1 = [e.to_dict() for e in agent.execute(self.scenario)]
        e2 = [e.to_dict() for e in agent.execute(self.scenario)]
        self.assertEqual(e1, e2)

    def test_includes_expected_output_evidence(self) -> None:
        agent = SampleAgent()
        events = agent.execute(self.scenario)
        texts = []
        for e in events:
            texts.extend(str(v) for v in e.content.values())
        self.assertTrue(any("Hello, world!" in t for t in texts))

    def test_is_agent_subclass(self) -> None:
        self.assertIsInstance(SampleAgent(), Agent)


if __name__ == "__main__":
    unittest.main()
