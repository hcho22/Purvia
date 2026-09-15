"""Discover and execute every offline-capable backend test module.

Backend tests are executable ``python -m backend.test_*`` modules rather than a
pytest collection.  Discovery is therefore deliberately filename-based and
default-on: every new ``backend/test_*.py`` module runs unless it is listed in
``INTEGRATION_ONLY`` with a narrow reason.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Mapping
from enum import Enum
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent

class IntegrationDependency(str, Enum):
    LLAMA_CLOUD = "LlamaCloud credential and live API"
    OPENAI = "OpenAI credential and live API"
    POSTGRES = "local Postgres"
    SUPABASE = "local Supabase"


INTEGRATION_ONLY: dict[str, frozenset[IntegrationDependency]] = {
    "test_au4_auth_attacks.py": frozenset(
        {
            IntegrationDependency.OPENAI,
            IntegrationDependency.POSTGRES,
            IntegrationDependency.SUPABASE,
        }
    ),
    "test_conversation_status_machine.py": frozenset(
        {IntegrationDependency.POSTGRES}
    ),
    "test_llamaparse_smoke.py": frozenset({IntegrationDependency.LLAMA_CLOUD}),
    "test_permissions.py": frozenset(
        {IntegrationDependency.POSTGRES, IntegrationDependency.SUPABASE}
    ),
    "test_sec_rls_hardening.py": frozenset(
        {IntegrationDependency.POSTGRES, IntegrationDependency.SUPABASE}
    ),
    "test_share_api.py": frozenset(
        {IntegrationDependency.POSTGRES, IntegrationDependency.SUPABASE}
    ),
    "test_us066_conversations_rls.py": frozenset(
        {IntegrationDependency.POSTGRES, IntegrationDependency.SUPABASE}
    ),
    "test_us070_bot_retrieval_integration.py": frozenset(
        {IntegrationDependency.POSTGRES, IntegrationDependency.SUPABASE}
    ),
}

# A test module that only says SKIP has not produced an offline verdict. Requiring
# the suite's established PASS/OK marker makes a new live-only module fail CI
# until it is explicitly classified above.
_VERDICT_RE = re.compile(r"(?:^|\n)\s*(?:PASS|OK):", re.MULTILINE)
_SKIP_RE = re.compile(r"(?:^|\n)\s*SKIP:", re.MULTILINE)

_LIVE_ENV_KEYS = {
    "REDIS_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_URL",
}


def discover_test_modules(
    backend_dir: Path = BACKEND_DIR,
    integration_only: Mapping[str, object] = INTEGRATION_ONLY,
) -> list[str]:
    """Return every unclassified backend test module, sorted by filename."""
    paths = sorted(backend_dir.glob("test_*.py"))
    found = {path.name for path in paths}
    stale = sorted(set(integration_only) - found)
    if stale:
        raise RuntimeError(
            "integration-only classification names missing modules: " + ", ".join(stale)
        )
    return [f"backend.{path.stem}" for path in paths if path.name not in integration_only]


def offline_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Configure the current suite's known offline dependency paths."""
    env = dict(os.environ if source is None else source)
    for key in tuple(env):
        if (
            key in _LIVE_ENV_KEYS
            or key.startswith("SUPABASE_")
            or key.endswith("_API_KEY")
            or key.endswith("DATABASE_URL")
        ):
            env.pop(key)
    env["PURVIA_OFFLINE_TESTS"] = "1"
    env["HF_DATASETS_OFFLINE"] = "1"
    env["HF_HUB_DISABLE_TELEMETRY"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    return env


def has_offline_verdict(output: str) -> bool:
    return _VERDICT_RE.search(output) is not None


def has_skip_verdict(output: str) -> bool:
    return _SKIP_RE.search(output) is not None


def execute_test_module(
    module: str,
    *,
    env: Mapping[str, str] | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "backend.offline_test_bootstrap", module],
        cwd=BACKEND_DIR.parent,
        env=dict(offline_environment() if env is None else env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


def main() -> int:
    try:
        modules = discover_test_modules()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Discovered {len(modules)} offline backend test modules")
    print(f"Classified {len(INTEGRATION_ONLY)} integration-only modules:")
    for filename, dependencies in sorted(INTEGRATION_ONLY.items()):
        reason = ", ".join(sorted(dependencies))
        print(f"  - backend.{Path(filename).stem}: requires {reason}")

    failures: list[str] = []
    env = offline_environment()
    for module in modules:
        print(f"\n=== {module} ===", flush=True)
        try:
            result = execute_test_module(module, env=env)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            print(output, end="")
            print(f"FAIL: {module} exceeded the 180s offline-test timeout")
            failures.append(module)
            continue

        print(result.stdout, end="")
        if result.returncode != 0:
            print(f"FAIL: {module} exited {result.returncode}")
            failures.append(module)
        elif not has_offline_verdict(result.stdout):
            print(
                f"FAIL: {module} produced no PASS:/OK: offline verdict; "
                "classify it as integration-only if it intentionally requires live services"
            )
            failures.append(module)

    if failures:
        print(f"\nFAIL: {len(failures)} offline backend module(s) failed:")
        for module in failures:
            print(f"  - {module}")
        return 1

    print(f"\nPASS: all {len(modules)} offline backend test modules passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
