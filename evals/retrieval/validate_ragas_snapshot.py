"""Reject weekly RAGAS snapshots that contain no usable measurement surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from .ragas import RAGAS_CELL_IDS, RAGAS_METRICS


class InvalidRagasSnapshot(ValueError):
    """A snapshot exists, but its RAGAS section is absent or unmeasured."""


def validate_ragas_payload(snapshot: dict[str, Any]) -> None:
    """Validate the minimum publishable per-row and aggregate RAGAS contract."""
    ragas = snapshot.get("ragas")
    if not isinstance(ragas, dict):
        raise InvalidRagasSnapshot("snapshot has no `ragas` object")

    rows = ragas.get("per_question")
    if not isinstance(rows, list) or not rows:
        raise InvalidRagasSnapshot("RAGAS snapshot has no per-question rows")

    identities: set[tuple[str, str, str]] = set()
    row_cells: dict[str, int] = {cell: 0 for cell in RAGAS_CELL_IDS}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise InvalidRagasSnapshot(f"RAGAS row {index} is not an object")
        identity = tuple(row.get(key) for key in ("question_id", "cell", "mode"))
        if not all(isinstance(value, str) and value for value in identity):
            raise InvalidRagasSnapshot(f"RAGAS row {index} has an invalid identity")
        typed_identity = cast(tuple[str, str, str], identity)
        if typed_identity in identities:
            raise InvalidRagasSnapshot(
                f"RAGAS row {index} duplicates identity {typed_identity}"
            )
        identities.add(typed_identity)
        if typed_identity[1] in row_cells:
            row_cells[typed_identity[1]] += 1

        scores = row.get("scores")
        reasons = row.get("nan_reasons")
        if not isinstance(scores, dict) or not isinstance(reasons, dict):
            raise InvalidRagasSnapshot(
                f"RAGAS row {index} is missing scores/nan_reasons objects"
            )
        for metric in RAGAS_METRICS:
            if metric not in scores or metric not in reasons:
                raise InvalidRagasSnapshot(
                    f"RAGAS row {index} is missing metric {metric}"
                )

    if any(count == 0 for count in row_cells.values()):
        missing_cells = [cell for cell, count in row_cells.items() if count == 0]
        raise InvalidRagasSnapshot(f"RAGAS rows are missing cells {missing_cells}")
    if len(set(row_cells.values())) != 1:
        raise InvalidRagasSnapshot(
            f"RAGAS cells have different row counts: {row_cells}"
        )

    by_cell = ragas.get("aggregates", {}).get("by_cell", {})
    if not isinstance(by_cell, dict):
        raise InvalidRagasSnapshot("RAGAS snapshot has no by-cell aggregates")
    required_fields = {
        "mean_strict",
        "mean_available",
        "coverage",
        "api_errors",
    }
    for cell in RAGAS_CELL_IDS:
        cell_block = by_cell.get(cell)
        if not isinstance(cell_block, dict):
            raise InvalidRagasSnapshot(f"RAGAS snapshot is missing cell {cell}")
        for metric in RAGAS_METRICS:
            block = cell_block.get(metric)
            if not isinstance(block, dict):
                raise InvalidRagasSnapshot(
                    f"RAGAS snapshot is missing aggregate {metric} x {cell}"
                )
            missing_fields = required_fields - block.keys()
            if missing_fields:
                raise InvalidRagasSnapshot(
                    f"RAGAS aggregate {metric} x {cell} is missing "
                    f"{sorted(missing_fields)}"
                )
            coverage = block["coverage"]
            if not isinstance(coverage, (int, float)) or not 0 <= coverage <= 1:
                raise InvalidRagasSnapshot(
                    f"RAGAS aggregate {metric} x {cell} has invalid coverage"
                )
            api_errors = block["api_errors"]
            if not isinstance(api_errors, int) or api_errors < 0:
                raise InvalidRagasSnapshot(
                    f"RAGAS aggregate {metric} x {cell} has invalid api_errors"
                )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(
            "usage: python -m evals.retrieval.validate_ragas_snapshot <snapshot.json>",
            file=sys.stderr,
        )
        return 2
    path = Path(args[0])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise InvalidRagasSnapshot("snapshot root is not an object")
        validate_ragas_payload(payload)
    except (OSError, json.JSONDecodeError, InvalidRagasSnapshot) as exc:
        print(f"invalid RAGAS snapshot: {exc}", file=sys.stderr)
        return 1
    print(f"valid non-empty RAGAS snapshot: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
