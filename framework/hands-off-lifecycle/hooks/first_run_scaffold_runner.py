# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Thin CLI runner for ``run_first_run_scaffold`` under the shared venv.

Added by the 2026-04-22 pyyaml-reachability amendment (#5).

## Why this exists

``first_run_helper.py`` runs as the detached first-run worker under the
system (or Homebrew) Python 3.13 interpreter that ``first-run.sh``
detected on PATH. The helper is stdlib-only by design — see the module
docstring at the top of ``first_run_helper.py`` ("Stdlib-only.").

The Phase-4a scaffold invocation, however, is implemented in the
``workspace-bootstrap`` component as ``run_first_run_scaffold``. That
function's *own* body only touches stdlib + file templates — but it
lives in a package whose ``__init__.py`` transitively imports
``yaml``, ``pydantic``, and ``opentelemetry`` (via ``manifest.py``,
``spec.py``, and ``host.py`` respectively). Those live only in the
shared venv populated during Phase 3b; the system interpreter the
worker runs under has none of them.

Pre-amendment, ``_invoke_first_run_scaffold`` imported the adapter
in-process under the system interpreter. On a fresh clone this raised
``ModuleNotFoundError: No module named 'yaml'`` before the scaffold
function body ever executed — Luke's S4 validator scenario hit this.

## Fix

This runner is a tiny CLI that takes the scaffold's flags on the
command line, imports the adapter, invokes ``run_first_run_scaffold``,
and reports via exit code + stderr JSON. The helper spawns it as a
subprocess under the *shared venv* Python (``.venv/bin/python``),
which by Phase 4a has all of the workspace-bootstrap package's
transitive runtime deps installed. The package imports succeed; the
scaffold runs; the helper captures the outcome.

## Reporting protocol

Exit 0 — scaffold succeeded (wrote files, short-circuited on
already-scaffolded, or completed partial recovery). Stdout carries a
short human-readable summary; stderr is quiet.

Exit 1 — scaffold raised. stderr holds a single JSON line:
``{"type": "<ExceptionClass>", "message": "<str>", "code": <int|null>}``.
The caller parses and re-raises with the same class + message so the
existing ``_emit_diag`` path in the helper continues to work without
change to its error-surfacing semantics.

Exit 2 — runner itself failed before invoking the scaffold (bad CLI
args, missing adapter module). stderr holds a plain-text diagnostic.

## Stdlib-only

This runner is part of hands-off-lifecycle and must also be stdlib-only
up to the point where it imports the adapter — the adapter itself
lives in the shared venv and brings its own pyyaml etc. The runner's
own imports are ``argparse``, ``json``, ``sys``, ``traceback``, and
``pathlib``.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="pos-v2 first-run scaffold runner (amendment #5).",
    )
    parser.add_argument(
        "--pos-root",
        required=True,
        help="The ~/.loam/ directory the scaffold writes into.",
    )
    parser.add_argument(
        "--workspace-root",
        required=True,
        help="The pos-v2 workspace root (for service-manager templating).",
    )
    parser.add_argument(
        "--service-bootstrap",
        choices=("true", "false"),
        default="true",
        help="Whether to invoke launchctl after writing files.",
    )
    parser.add_argument(
        "--service-manager-dir-override",
        default=None,
        help="Override LaunchAgents dir (tests only).",
    )
    parser.add_argument(
        "--partial-recovery",
        choices=("true", "false"),
        default="true",
        help="Partial-recovery path for re-run after mid-scaffold crash.",
    )
    parser.add_argument(
        "--dry-run",
        choices=("true", "false"),
        default="false",
        help="Dry-run mode — no side effects.",
    )
    return parser.parse_args(argv)


def _emit_failure_payload(exc: BaseException) -> None:
    """Serialise the exception as one JSON line on stderr.

    The caller parses this to reconstruct a best-effort exception
    description for its own diagnostic emission. We keep the payload
    deliberately small — type name, str(exc), and any `.code` attribute
    carried by BootstrapError subclasses. A full traceback would bloat
    the ~/.loam/first-run.log noise; the traceback is printed in plain
    text after the JSON so a human reading the log still gets it.
    """
    code = getattr(exc, "code", None)
    payload = {
        "type": type(exc).__name__,
        "message": str(exc),
        "code": int(code) if isinstance(code, int) else None,
    }
    # JSON on stderr line 1 — machine readable.
    sys.stderr.write(json.dumps(payload) + "\n")
    # Human-readable traceback below — diagnostic value without
    # complicating the parser.
    sys.stderr.write("--- scaffold traceback ---\n")
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    sys.stderr.flush()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        # Import late so that argument-parsing errors report cleanly
        # without requiring the adapter's dependencies to resolve.
        from loam.workspace_bootstrap.adapters.first_run_scaffold import (  # type: ignore
            run_first_run_scaffold,
        )
    except Exception as e:  # pragma: no cover — environment-dependent
        sys.stderr.write(
            "first_run_scaffold_runner: could not import scaffold adapter.\n"
            "This usually means the shared venv is missing a runtime dep\n"
            "that workspace-bootstrap declares. Reopen claude to retry;\n"
            "the next session's Phase 3b install will attempt to heal.\n"
            f"Import error: {type(e).__name__}: {e}\n"
        )
        return 2

    try:
        run_first_run_scaffold(
            pos_root=Path(args.pos_root),
            dry_run=(args.dry_run == "true"),
            service_bootstrap=(args.service_bootstrap == "true"),
            service_manager_dir_override=(
                Path(args.service_manager_dir_override)
                if args.service_manager_dir_override
                else None
            ),
            workspace_root=Path(args.workspace_root),
            partial_recovery=(args.partial_recovery == "true"),
        )
    except Exception as e:
        _emit_failure_payload(e)
        return 1

    # Unbuffered-friendly success marker — gives the worker log a
    # clear "scaffold done" line even when the scaffold is silent.
    sys.stdout.write("first_run_scaffold_runner: scaffold complete\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
