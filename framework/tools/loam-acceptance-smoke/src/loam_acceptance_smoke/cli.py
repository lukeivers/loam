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

"""``loam-acceptance-smoke`` CLI — runs the full 1.0 acceptance smoke and
writes the readiness report.

Usage:
    loam-acceptance-smoke --canonical <loam-tree> --out <report.md>
        [--variants A,B,C] [--keep-workspaces]

Re-runnable + self-cleaning (AC.SMOKE.5): each variant runs in a throwaway
temp workspace + isolated global home removed on exit; the only residue is the
report file the operator asked for.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .judge import run_smoke
from .report import render_report
from .runner import run_variant
from .variants import VARIANTS, variant_by_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loam-acceptance-smoke",
        description=(
            "Run the loam 1.0 acceptance smoke: drive the real fresh loam init "
            "+ first-run intake through three role-played non-technical users, "
            "judge the end-state against the prime-objective promise, write a "
            "1.0-readiness report."
        ),
    )
    parser.add_argument(
        "--canonical",
        type=Path,
        required=True,
        help="Path to the canonical loam git tree (the --from for loam init).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Where to write the 1.0-readiness report (markdown).",
    )
    parser.add_argument(
        "--variants",
        default="A,B,C",
        help="Comma-separated variant keys to run (default: A,B,C).",
    )
    parser.add_argument(
        "--keep-workspaces",
        action="store_true",
        help="Do NOT delete the throwaway workspaces (debugging only).",
    )
    args = parser.parse_args(argv)

    keys = [k.strip().upper() for k in args.variants.split(",") if k.strip()]
    specs = [variant_by_key(k) for k in keys] if keys else list(VARIANTS)

    canonical = args.canonical.resolve()
    if not (canonical / ".git").exists():
        print(
            f"[smoke] --canonical {canonical} is not a git tree (no .git/).",
            file=sys.stderr,
        )
        return 2

    runs = []
    for spec in specs:
        print(
            f"[smoke] running variant {spec.key} ({spec.role_label}, "
            f"{spec.onboarding_path}) ...",
            file=sys.stderr,
        )
        run = run_variant(
            spec,
            canonical_source=canonical,
            keep_workspace=args.keep_workspaces,
        )
        if run.error:
            print(f"[smoke]   variant {spec.key} error: {run.error}", file=sys.stderr)
        else:
            print(
                f"[smoke]   variant {spec.key} done: turns={len(run.transcript)} "
                f"confirmed={run.confirmed} "
                f"deep_research_invoked={run.invoked_deep_research}",
                file=sys.stderr,
            )
        runs.append(run)

    print("[smoke] judging transcripts on named dimensions ...", file=sys.stderr)
    report = run_smoke(runs)

    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report, runs), encoding="utf-8")
    print(
        f"[smoke] verdict={report.top_line} "
        f"spawn_all_isolated={report.spawn_all_isolated} "
        f"({report.spawn_count} spawns); report -> {out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
