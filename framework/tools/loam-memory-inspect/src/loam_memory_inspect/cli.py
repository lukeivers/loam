"""CLI entry-point for loam-memory-inspect.

Usage::

    loam-memory-inspect <workspace-root>

Reports kuzu_db file size, WAL size, sibling artefact presence, a
best-effort byte-scan for ``episode_uuid`` substrings inside the
binary kuzu_db file, and an ``episodes.json`` record count when
that test-fixture file is present. Read-only; never modifies state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _format_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def inspect_workspace(workspace_root: Path) -> dict[str, Any]:
    """Return a structured report of the kuzu_db state.

    The kuzu_db file lives at ``<workspace>/workspace/data/memory-
    system/kuzu_db``; the test-fixture episodes.json lives in the
    same dir. Both are inspected when present; missing files are
    reported as ``None``.
    """
    data_dir = workspace_root / "workspace" / "data" / "memory-system"
    kuzu_path = data_dir / "kuzu_db"
    wal_path = data_dir / "kuzu_db.wal"
    log_path = data_dir / "graphiti-service.log"
    err_log_path = data_dir / "graphiti-service.err.log"
    episodes_json = data_dir / "episodes.json"

    report: dict[str, Any] = {
        "workspace_root": str(workspace_root),
        "data_dir": str(data_dir),
        "data_dir_exists": data_dir.exists(),
    }

    def _file_info(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "size_human": _format_bytes(path.stat().st_size),
        }

    report["kuzu_db"] = _file_info(kuzu_path)
    report["kuzu_db_wal"] = _file_info(wal_path)
    report["graphiti_service_log"] = _file_info(log_path)
    report["graphiti_service_err_log"] = _file_info(err_log_path)

    # Best-effort episode count: scan the kuzu_db binary for unique
    # ``episode_uuid`` substrings. Not authoritative (kuzu's binary
    # format may chunk strings across pages), but useful as a
    # sanity-check proxy when a kuzu client is unavailable.
    episode_uuid_count: int | None = None
    if kuzu_path.exists():
        try:
            raw = kuzu_path.read_bytes()
            episode_uuid_count = raw.count(b"episode_uuid")
        except OSError:
            episode_uuid_count = None
    report["episode_uuid_byte_occurrences"] = episode_uuid_count

    # Test-fixture episodes.json: a structured record-count check.
    # Note: this file is the test-fixture, NOT the live runtime data.
    episodes_json_count: int | None = None
    if episodes_json.exists():
        try:
            data = json.loads(episodes_json.read_text(encoding="utf-8"))
            if isinstance(data, list):
                episodes_json_count = len(data)
            elif isinstance(data, dict) and "episodes" in data:
                eps = data.get("episodes")
                if isinstance(eps, list):
                    episodes_json_count = len(eps)
        except (OSError, ValueError):
            episodes_json_count = None
    report["episodes_json_record_count"] = episodes_json_count

    return report


def render_report(report: dict[str, Any]) -> str:
    lines = ["loam-memory-inspect — kuzu_db pre-discard inspection", ""]
    lines.append(f"workspace_root:    {report['workspace_root']}")
    lines.append(f"data_dir:          {report['data_dir']}")
    lines.append(f"data_dir_exists:   {report['data_dir_exists']}")
    lines.append("")
    for key in (
        "kuzu_db",
        "kuzu_db_wal",
        "graphiti_service_log",
        "graphiti_service_err_log",
    ):
        info = report.get(key)
        if info is None:
            lines.append(f"{key:30s} (not present)")
        else:
            lines.append(
                f"{key:30s} {info['size_human']:>10s}  {info['path']}"
            )
    lines.append("")
    epc = report.get("episode_uuid_byte_occurrences")
    if epc is None:
        lines.append("episode_uuid byte-occurrences:   (kuzu_db not readable)")
    else:
        lines.append(f"episode_uuid byte-occurrences:   {epc}")
    ejc = report.get("episodes_json_record_count")
    if ejc is None:
        lines.append("episodes.json record count:      (not present)")
    else:
        lines.append(f"episodes.json record count:      {ejc} (test fixture)")
    lines.append("")
    lines.append(
        "Note: episode_uuid byte-occurrences is a proxy for retrievable-"
        "episode count when no kuzu client is on PATH; not authoritative. "
        "Run with a kuzu binary client for an exact count."
    )
    lines.append(
        "Per D-Q.MFBM.6 ruling: the kuzu_db state is DISCARDED at v0.1.0. "
        "If this report contradicts research §5's '1 episode after weeks' "
        "evidence, halt-trigger §9.8 fires and the owner re-rules."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam-memory-inspect",
        description=(
            "One-shot pre-discard kuzu_db inspection. Reports file sizes, "
            "best-effort episode_uuid count, episodes.json fixture record "
            "count. Read-only."
        ),
    )
    parser.add_argument(
        "workspace_root",
        nargs="?",
        default=".",
        help="Path to the workspace root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    workspace_root = Path(args.workspace_root).resolve()
    if not workspace_root.exists():
        print(
            f"loam-memory-inspect: workspace root does not exist: "
            f"{workspace_root}",
            file=sys.stderr,
        )
        return 2

    report = inspect_workspace(workspace_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
