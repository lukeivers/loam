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

"""Production entry-point (AC.CLP-CUR.3/4) — the exact command the
cadence binding (cloud routine / launchd fallback) invokes:

    capability-refresh --cadence-class high-velocity
    capability-refresh --cadence-class long-form

Defaults resolve against the current working directory's repo
(``docs/capability-corpus/sources.yaml``); a workspace overrides by
passing ``--sources`` (sources are data — D-CUR.3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_sources(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur] + list(cur.parents):
        p = cand / "docs" / "capability-corpus" / "sources.yaml"
        if p.is_file():
            return p
    return start / "docs" / "capability-corpus" / "sources.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="capability-refresh",
        description="Deterministic Class A capability-corpus refresh "
                    "(fetch -> project -> partition -> auto-land/review).",
    )
    parser.add_argument("--sources", type=Path, default=None,
                        help="source manifest (default: nearest "
                             "docs/capability-corpus/sources.yaml)")
    parser.add_argument("--corpus-root", type=Path, default=None,
                        help="corpus root (default: the manifest's directory)")
    parser.add_argument("--repo-root", type=Path, default=None,
                        help="repo root for internal: sources "
                             "(default: corpus root's ../..)")
    parser.add_argument("--cadence-class", default="all",
                        choices=["all", "high-velocity", "long-form", "on-merge"],
                        help="run only sources in this locked cadence class")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch + diff + partition, write nothing")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="print the full structured delta as JSON")
    args = parser.parse_args(argv)

    sources = args.sources or _default_sources(Path.cwd())
    if not Path(sources).is_file():
        print(f"capability-refresh: source manifest not found: {sources}",
              file=sys.stderr)
        return 2

    from capability_refresh.refresh import run_refresh
    from capability_refresh.sources import SourceManifestError

    try:
        report = run_refresh(
            sources_path=sources,
            corpus_root=args.corpus_root,
            repo_root=args.repo_root,
            cadence_class=args.cadence_class,
            dry_run=args.dry_run,
        )
    except SourceManifestError as exc:
        print(f"capability-refresh: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"capability-refresh run {report['run_ts']} "
              f"(cadence={report['cadence_class']}, dry_run={report['dry_run']})")
        for rec in report["sources"]:
            extras = []
            if rec["auto_landed"]:
                extras.append(f"auto-landed={len(rec['auto_landed'])}")
            if rec["review"]:
                extras.append(f"review={len(rec['review'])}")
            if rec.get("pending_delta"):
                extras.append(f"pending-delta={rec['pending_delta']}")
            if rec.get("error"):
                extras.append(f"error={rec['error']}")
            # Model-lineup delta (AC.CLP-MDL.2): surface added/removed IDs.
            md = rec.get("model_delta")
            if md is not None:
                if md.get("no_prior"):
                    extras.append("model-lineup: initialized")
                else:
                    parts = []
                    if md.get("added"):
                        parts.append(
                            f"+{len(md['added'])} added "
                            f"({', '.join(md['added'])})"
                        )
                    if md.get("removed"):
                        parts.append(
                            f"-{len(md['removed'])} removed "
                            f"({', '.join(md['removed'])})"
                        )
                    if parts:
                        extras.append(f"model-delta: {'; '.join(parts)}")
            suffix = (" — " + ", ".join(extras)) if extras else ""
            print(f"  [{rec['status']}] {rec['id']}{suffix}")
        if "report_path" in report:
            print(f"  structured delta: {report['report_path']}")

    # A refusal (cross-class write attempt) is a configuration defect the
    # operator must see; fetch failures are handled outcomes (stale-mark).
    refused = [r for r in report["sources"]
               if r["status"] == "refused-cross-class-write"]
    return 3 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
