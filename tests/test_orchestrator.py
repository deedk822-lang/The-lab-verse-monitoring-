import pytest
from pr_fix_agent.orchestrator import CodeReviewOrchestrator, CodeReviewFinding, FixProposal
from pr_fix_agent.ollama_agent import MockOllamaAgent
from pathlib import Path

def test_orchestrator_initialization():
    orch = CodeReviewOrchestrator()
    assert orch.reasoning_agent.model == "deepseek-r1:1.5b"
    assert orch.coding_agent.model == "qwen2.5-coder:1.5b"

def test_orchestrator_generate_proposals():
    agent = MockOllamaAgent()
    orch = CodeReviewOrchestrator()
    orch.reasoning_agent = agent

    finding = CodeReviewFinding(
        file="test.py",
        line_start=1,
        line_end=1,
        severity="medium",
        category="security",
        issue="Test issue",
        suggestion="Test suggestion"
    )

    # MockOllamaAgent uses "in prompt" check
    agent.set_response("Analyze this code review finding", "Analysis result")

    proposals = orch._generate_fix_proposals([finding])
    assert len(proposals) == 1
    assert proposals[0].finding.file == "test.py"

def test_orchestrator_implement_fixes(tmp_path):
    agent = MockOllamaAgent()
    orch = CodeReviewOrchestrator()
    orch.coding_agent = agent

    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    finding = CodeReviewFinding(
        file="test.py",
        line_start=1,
        line_end=1,
        severity="medium",
        category="security",
        issue="Test issue",
        suggestion="Test suggestion"
    )

    proposal = FixProposal(
        finding=finding,
        root_cause="test",
        fix_approach="test",
        expected_changes=["test"],
        risk_level="low",
        test_requirements=["test"]
    )

    agent.set_response("Fix the following Python code", "print('fixed')")

    fixes = orch._implement_fixes([proposal], tmp_path)
    assert len(fixes) == 1
    assert fixes[0].fixed_code == "print('fixed')"

def test_orchestrator_create_coding_prompt():
    orch = CodeReviewOrchestrator()
    finding = CodeReviewFinding("f", 1, 1, "s", "c", "i", "s")
    proposal = FixProposal(finding, "rc", "fa", [], "l", [])

    # Test truncation
    long_code = "a" * 5000
    prompt = orch._create_coding_prompt(proposal, long_code)
    assert "truncated for context" in prompt
    assert len(prompt) < 5000
