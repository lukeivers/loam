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

"""Production entry-point (AC.CLP-PUSH-RENDER.4 ★) — the command the
cadence binding invokes to render the knowledge pack:

    knowledge-pack render
    knowledge-pack render --pack-root docs/capability-corpus/.pack
    knowledge-pack assert-publish-eligible --pack-root <dir>

``render`` projects the live corpus into a marketplace-shaped skills-pack
tree, validates it, and emits a ``pending`` curation-gate record (a
curator records the pass). It performs NO public action — the pack stages
in-repo; the public marketplace repo + first publish are S4c ⛔OWNER.

``assert-publish-eligible`` is the publish-path gate (AC.CLP-PUSH.5): it
exits non-zero (refusal) when the pack is not gate-passed. The S4c
⛔OWNER publish runbook calls this before any push.

Defaults resolve the corpus root against the nearest
``docs/capability-corpus/`` from the CWD (the corpus is read-only input)."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def _default_corpus_root(start: Path) -> Path:
    cur = start.resolve()
    for cand in [cur] + list(cur.parents):
        p = cand / "docs" / "capability-corpus"
        if p.is_dir():
            return p
    return start / "docs" / "capability-corpus"


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-pack",
        description="Deterministic corpus -> skills-pack marketplace render "
                    "(claude-leverage-program Slice 4a; LOCAL, no public action).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render the pack from the live corpus")
    p_render.add_argument("--corpus-root", type=Path, default=None,
                          help="corpus root (default: nearest docs/capability-corpus)")
    p_render.add_argument("--pack-root", type=Path, default=None,
                          help="output pack root (default: <corpus-root>/.pack)")
    p_render.add_argument("--gate-pass", action="store_true",
                          help="record a gate PASS at render time (operator "
                               "override / rig only; default emits 'pending')")
    p_render.add_argument("--reviewer", default=None,
                          help="reviewer identity recorded with a --gate-pass")
    p_render.add_argument("--validate", dest="validate", action="store_true",
                          default=True, help="validate the emitted tree (default on)")
    p_render.add_argument("--no-validate", dest="validate", action="store_false")

    p_pub = sub.add_parser("assert-publish-eligible",
                           help="exit non-zero if the pack is not gate-passed "
                                "(AC.CLP-PUSH.5 publish-path gate)")
    p_pub.add_argument("--pack-root", type=Path, required=True)

    args = parser.parse_args(argv)

    from knowledge_pack.render import render_pack
    from knowledge_pack.validate import validate_pack, PackValidationError
    from knowledge_pack.gate import (
        emit_gate_record,
        assert_publish_eligible,
        UngatedPublishError,
        VERDICT_PASS,
        VERDICT_PENDING,
    )

    if args.command == "render":
        corpus_root = args.corpus_root or _default_corpus_root(Path.cwd())
        if not Path(corpus_root).is_dir():
            print(f"knowledge-pack: corpus root not found: {corpus_root}",
                  file=sys.stderr)
            return 2
        pack_root = args.pack_root or (Path(corpus_root) / ".pack")
        ts = _now_ts()
        result = render_pack(Path(corpus_root), Path(pack_root), ts)

        if args.validate:
            try:
                validate_pack(pack_root)
            except PackValidationError as exc:
                print(f"knowledge-pack: rendered tree invalid: {exc}",
                      file=sys.stderr)
                return 4

        verdict = VERDICT_PASS if args.gate_pass else VERDICT_PENDING
        emit_gate_record(pack_root, result.content_hash, ts,
                         verdict=verdict, reviewer=args.reviewer)

        print(f"knowledge-pack render {ts} -> {pack_root}")
        print(f"  plugins: {', '.join(result.plugin_names)}")
        print(f"  skills: {result.skill_count}")
        print(f"  content-hash: {result.content_hash[:12]}")
        print(f"  gate verdict: {verdict}"
              + (f" (reviewer: {args.reviewer})" if args.gate_pass else
                 " — curator records the pass before publish"))
        if result.stale_entries:
            print(f"  STALE entries (carried, never silently current): "
                  f"{len(result.stale_entries)}")
            for s in result.stale_entries:
                print(f"    - {s}")
        return 0

    if args.command == "assert-publish-eligible":
        try:
            assert_publish_eligible(args.pack_root)
        except UngatedPublishError as exc:
            print(f"knowledge-pack: PUBLISH REFUSED — {exc}", file=sys.stderr)
            return 3
        print(f"knowledge-pack: pack at {args.pack_root} is publish-eligible "
              f"(recorded gate pass).")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
