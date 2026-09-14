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
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent

# These modules have no offline assertions. Mixed unit/integration modules are
# not listed: PURVIA_OFFLINE_TESTS=1 makes them run only their unit layer.
INTEGRATION_ONLY: dict[str, str] = {
    "test_au4_auth_attacks.py": "requires local Supabase, Postgres, and OpenAI",
    "test_conversation_status_machine.py": "requires local Postgres migrations",
    "test_llamaparse_smoke.py": "requires a LlamaCloud credential and live API",
    "test_permissions.py": "requires local Supabase and Postgres",
    "test_sec_rls_hardening.py": "requires local Supabase and Postgres",
    "test_share_api.py": "requires local Supabase and Postgres",
    "test_us066_conversations_rls.py": "requires local Supabase and Postgres",
    "test_us070_bot_retrieval_integration.py": "requires local Supabase and Postgres",
}

# A test module that only says SKIP has not produced an offline verdict. Requiring
# the suite's established PASS/OK marker makes a new live-only module fail CI
# until it is explicitly classified above.
_VERDICT_RE = re.compile(r"(?:^|\n)\s*(?:PASS|OK):", re.MULTILINE)

_LIVE_ENV_KEYS = {
    "REDIS_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_JWT_SECRET",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_URL",
}


def discover_test_modules(
    backend_dir: Path = BACKEND_DIR,
    integration_only: dict[str, str] = INTEGRATION_ONLY,
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
    """Return a subprocess environment with live-service credentials removed."""
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
    return env


def main() -> int:
    try:
        modules = discover_test_modules()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Discovered {len(modules)} offline backend test modules")
    print(f"Classified {len(INTEGRATION_ONLY)} integration-only modules:")
    for filename, reason in sorted(INTEGRATION_ONLY.items()):
        print(f"  - backend.{Path(filename).stem}: {reason}")

    failures: list[str] = []
    env = offline_environment()
    for module in modules:
        print(f"\n=== {module} ===", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, "-m", module],
                cwd=BACKEND_DIR.parent,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=180,
            )
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
        elif not _VERDICT_RE.search(result.stdout):
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
