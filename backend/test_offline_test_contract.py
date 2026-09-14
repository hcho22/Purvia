"""Regression guard for the self-updating backend offline-test CI contract."""

from __future__ import annotations

import tempfile
from pathlib import Path

from backend.run_offline_tests import (
    INTEGRATION_ONLY,
    discover_test_modules,
    offline_environment,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "backend-unit-tests.yml"


def test_new_module_is_discovered_without_an_allowlist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = Path(tmp)
        (backend / "test_new_offline_behavior.py").touch()
        assert discover_test_modules(backend, integration_only={}) == [
            "backend.test_new_offline_behavior"
        ]


def test_integration_only_reasons_are_narrow_and_nonempty() -> None:
    assert INTEGRATION_ONLY
    for filename, reason in INTEGRATION_ONLY.items():
        assert filename.startswith("test_") and filename.endswith(".py")
        assert "requires " in reason and len(reason) > len("requires ")


def test_offline_environment_removes_live_credentials() -> None:
    env = offline_environment(
        {
            "PATH": "/bin",
            "OPENAI_API_KEY": "secret",
            "JUDGE_API_KEY": "secret",
            "DATABASE_URL": "postgresql://live",
            "WIDGET_FANOUT_DATABASE_URL": "postgresql://live",
            "SUPABASE_SERVICE_ROLE_KEY": "secret",
            "REDIS_URL": "redis://live",
        }
    )
    assert env == {"PATH": "/bin", "PURVIA_OFFLINE_TESTS": "1"}


def test_workflow_runs_the_discovery_command_on_every_pr() -> None:
    source = WORKFLOW.read_text()
    assert "pull_request:" in source
    assert "paths:" not in source
    assert "python -m backend.run_offline_tests" in source
    assert "python -m backend.test_" not in source
    assert "cache: pip" in source
    assert "cache-dependency-path: backend/requirements-test.txt" in source


def main() -> int:
    tests = (
        test_new_module_is_discovered_without_an_allowlist,
        test_integration_only_reasons_are_narrow_and_nonempty,
        test_offline_environment_removes_live_credentials,
        test_workflow_runs_the_discovery_command_on_every_pr,
    )
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"PASS: {len(tests)} offline-test CI contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
