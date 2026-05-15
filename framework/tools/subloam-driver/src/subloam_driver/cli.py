"""CLI entry-point for subloam-driver.

Usage::

    subloam-driver \
        --scratch-root /tmp/pb-subloam-<task>-<ts> \
        --from /Users/lukeivers/loam \
        --slug pb-subloam-<task>-<ts> \
        --prompt-file <frozen-build-prompt.txt>

Stands up a fresh persona-active scratch sub-loam workspace, drives an
interactive ``claude`` session in it with the frozen prompt fed as the
first user turn over a PTY, prints the captured transcript + a JSON
summary (effective turns, FILE-block count, spawn argv + isolated
config dir), and tears the scratch workspace down.

The frozen prompt is fed UNCHANGED (owner constraint — bench + paper
integrity; no substitution, no ``--append-system-prompt``). NO
Anthropic API key — the real ``claude`` binary, default Sonnet.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .driver import (
    IsolationConfig,
    SubLoamDriver,
    write_empty_mcp_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subloam-driver",
        description=(
            "Drive an interactive claude session in an isolated "
            "scratch sub-loam workspace (one isolation mechanism "
            "protects the operator's session + yields a clean bench "
            "measurement)."
        ),
    )
    parser.add_argument(
        "--scratch-root",
        required=True,
        type=Path,
        help="Per-run scratch root (e.g. /tmp/pb-subloam-<task>-<ts>).",
    )
    parser.add_argument(
        "--from",
        dest="canonical_source",
        required=True,
        help="Canonical loam source (absolute local path or URL).",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help=(
            "Namespaced workspace slug (its launchd labels are "
            "com.loam.<slug>.<kind> so they cannot bootout the "
            "operator's services)."
        ),
    )
    parser.add_argument(
        "--prompt-file",
        required=True,
        type=Path,
        help="File carrying the FROZEN build_prompt (fed unchanged).",
    )
    parser.add_argument(
        "--model",
        default="sonnet",
        help="Model alias (default sonnet; no API key — subscription).",
    )
    parser.add_argument(
        "--idle-timeout-s",
        type=float,
        default=90.0,
        help="Idle-window seconds before the PTY read loop stops.",
    )
    parser.add_argument(
        "--hard-timeout-s",
        type=float,
        default=600.0,
        help="Hard wall-clock cap for the driven session.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    scratch_root = Path(args.scratch_root)
    config_dir = scratch_root / ".claude-home"
    empty_mcp = scratch_root / "empty.mcp.json"
    write_empty_mcp_config(empty_mcp)

    isolation = IsolationConfig(
        claude_config_dir=config_dir,
        empty_mcp_config_path=empty_mcp,
        workspace_slug=args.slug,
        model=args.model,
    )

    prompt = Path(args.prompt_file).read_text(encoding="utf-8")

    started = time.monotonic()
    with SubLoamDriver(
        scratch_root=scratch_root,
        canonical_source=args.canonical_source,
        isolation=isolation,
    ) as driver:
        result = driver.drive(
            prompt,
            idle_timeout_s=args.idle_timeout_s,
            hard_timeout_s=args.hard_timeout_s,
        )

    summary = {
        "effective_turns": result.effective_turns,
        "is_multi_turn": result.is_multi_turn,
        "file_block_count": len(result.file_blocks),
        "exit_status": result.exit_status,
        "timed_out": result.timed_out,
        "spawn_argv": list(result.spawn_argv),
        "spawn_env_config_dir": result.spawn_env_config_dir,
        "wall_clock_s": round(time.monotonic() - started, 1),
    }
    sys.stdout.write("=== transcript ===\n")
    sys.stdout.write(result.transcript)
    sys.stdout.write("\n=== summary ===\n")
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
