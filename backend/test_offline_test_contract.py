"""Regression guard for the self-updating backend offline-test CI contract."""

from __future__ import annotations

import shlex
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tiktoken
import yaml  # type: ignore[import-untyped]

from backend.offline_test_bootstrap import (
    BlockedSocketPathError,
    install_offline_runtime,
)
from backend.run_offline_tests import (
    INTEGRATION_ONLY,
    discover_test_modules,
    execute_test_module,
    has_offline_verdict,
    has_skip_verdict,
    offline_environment,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "backend-unit-tests.yml"


@dataclass(frozen=True)
class WorkflowStep:
    uses: str | None
    commands: tuple[tuple[str, ...], ...]
    settings: dict[str, str]
    condition: str | None


@dataclass(frozen=True)
class WorkflowJob:
    condition: str | None
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class WorkflowContract:
    triggers: dict[str, Any]
    jobs: dict[str, WorkflowJob]


def _workflow_contract() -> WorkflowContract:
    document = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    jobs = {
        name: WorkflowJob(
            condition=job.get("if"),
            steps=tuple(
                WorkflowStep(
                    uses=step.get("uses"),
                    commands=tuple(
                        tuple(shlex.split(line))
                        for line in (step.get("run") or "").splitlines()
                        if line.strip()
                    ),
                    settings=dict(step.get("with") or {}),
                    condition=step.get("if"),
                )
                for step in job.get("steps", [])
            ),
        )
        for name, job in document["jobs"].items()
    }
    return WorkflowContract(triggers=dict(document["on"]), jobs=jobs)


def test_new_module_is_discovered_without_an_allowlist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        backend = Path(tmp)
        (backend / "test_new_offline_behavior.py").touch()
        assert discover_test_modules(backend, integration_only={}) == [
            "backend.test_new_offline_behavior"
        ]


def test_integration_only_classifications_have_no_offline_verdict() -> None:
    assert INTEGRATION_ONLY
    env = offline_environment()
    for filename, dependencies in INTEGRATION_ONLY.items():
        assert dependencies
        result = execute_test_module(
            f"backend.{Path(filename).stem}", env=env, timeout=30
        )
        assert result.returncode == 0, result.stdout
        assert has_skip_verdict(result.stdout), result.stdout
        assert not has_offline_verdict(result.stdout), result.stdout


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
    assert env == {
        "PATH": "/bin",
        "PURVIA_OFFLINE_TESTS": "1",
        "HF_DATASETS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }


def test_workflow_runs_the_discovery_command_on_every_pr() -> None:
    workflow = _workflow_contract()
    assert set(workflow.triggers) == {"pull_request"}
    pull_request = workflow.triggers["pull_request"]
    assert pull_request == {"branches": ["main"]}
    assert set(workflow.jobs) == {"backend-unit-tests"}
    job = workflow.jobs["backend-unit-tests"]
    assert job.condition is None

    setup_steps = [step for step in job.steps if step.uses == "actions/setup-python@v5"]
    assert len(setup_steps) == 1
    assert setup_steps[0].condition is None
    assert setup_steps[0].settings["cache"] == "pip"
    assert (
        setup_steps[0].settings["cache-dependency-path"]
        == "backend/requirements-test.txt"
    )

    install_command = ("pip", "install", "-r", "backend/requirements-test.txt")
    install_steps = [step for step in job.steps if install_command in step.commands]
    assert len(install_steps) == 1
    assert install_steps[0].condition is None

    discovery_command = ("python", "-m", "backend.run_offline_tests")
    run_steps = [step for step in job.steps if discovery_command in step.commands]
    assert len(run_steps) == 1
    assert run_steps[0].condition is None
    assert run_steps[0].commands == (discovery_command,)


def test_offline_runtime_uses_local_tokenizer_and_blocks_python_socket_path() -> None:
    install_offline_runtime()
    encoding = tiktoken.get_encoding("cl100k_base")
    text = "offline tokenizer — 世界"
    assert encoding.decode(encoding.encode(text)) == text
    try:
        socket.create_connection(("example.com", 443))
    except BlockedSocketPathError as exc:
        assert str(exc) == (
            "offline test blocked Python socket path: socket.create_connection"
        )
    else:
        raise AssertionError("offline runtime allowed the guarded socket path")


def main() -> int:
    tests = (
        test_new_module_is_discovered_without_an_allowlist,
        test_integration_only_classifications_have_no_offline_verdict,
        test_offline_environment_removes_live_credentials,
        test_workflow_runs_the_discovery_command_on_every_pr,
        test_offline_runtime_uses_local_tokenizer_and_blocks_python_socket_path,
    )
    for test in tests:
        test()
        print(f"  ok: {test.__name__}")
    print(f"PASS: {len(tests)} offline-test CI contract checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
