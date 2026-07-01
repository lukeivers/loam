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

"""The refresh cycle — the production path the cadence binding invokes.

One run (AC.CLP-CUR.3/4/5/6/7), per source in the selected cadence
class:

  1. fetch the canonical upstream (failure -> entry marked STALE,
     nothing else touched — AC.CLP-CUR.5);
  2. normalise deterministically;
  3. first sighting -> initialise the snapshot + stamp the entry
     (no delta yet — there is nothing to diff against);
  4. subsequent sighting -> diff against the stored snapshot, partition
     per D-CUR.4 (partition.py), auto-land same-statement re-projections
     via in-place substitution (corpus.py), surface every review-class
     item as a pending-delta file under
     ``<corpus>/pending-deltas/`` (AC.CLP-CUR.6);
  5. advance the snapshot + stamp ``source_fetch_ts`` (AC.CLP-CUR.5);
  6. emit the structured delta at ``<corpus>/.refresh/last-run.json``.

Snapshots live at ``<corpus>/.refresh/snapshots/<source-id>.txt`` —
verbatim-normalised upstream mirrors used as diff baselines. They are
machine state, NOT reference docs (a stale upstream statement appearing
in a mirror is upstream's reality, not a corpus claim).

A cross-class write attempt (hostile/wrong sources.yaml naming a
Class B entry, traversal, absolute path) is REFUSED per source and
recorded in the run report; the run continues for well-formed sources
(AC.CLP-CUR.7).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import List, Optional

from capability_refresh.corpus import (
    CrossClassWriteError,
    apply_reprojection,
    mark_stale,
    resolve_entry_path,
    resolve_state_path,
    stamp_source,
)
from capability_refresh.fetch import FetchError, fetch_source, normalize
from capability_refresh.partition import DeltaItem, partition_delta
from capability_refresh.sources import Source, filter_by_cadence, load_sources


def _utc_now_iso(now: Optional[_dt.datetime] = None) -> str:
    dt = now or _dt.datetime.now(_dt.timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_pending_delta(corpus_root: Path, source: Source, items: List[DeltaItem],
                         ts: str) -> Path:
    day = ts[:10]
    path = resolve_state_path(corpus_root, "pending-deltas", f"{day}-{source.id}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if not path.exists():
        lines.append(f"# Pending delta — {source.id}")
        lines.append("")
        lines.append(f"> Review-class upstream changes surfaced by capability-refresh.")
        lines.append(f"> Source: `{source.url}`")
        target = source.entry if source.kind == "entry" else "(watch source — no projection target)"
        lines.append(f"> Projection target: `{target}`")
        lines.append(
            "> These do NOT auto-land (D-CUR.4): new claims, removals, overlay"
        )
        lines.append(
            "> touches, contradiction-suspects, and curated-divergences need review."
        )
        lines.append("")
    lines.append(f"## Run {ts}")
    lines.append("")
    for it in items:
        lines.append(f"- **{it.kind}** — {it.reason}")
        if it.old:
            lines.append(f"  - was: {it.old}")
        if it.new:
            lines.append(f"  - now: {it.new}")
    lines.append("")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


def run_refresh(
    sources_path: Path,
    corpus_root: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    cadence_class: str = "all",
    dry_run: bool = False,
    now: Optional[_dt.datetime] = None,
) -> dict:
    """Run one refresh cycle. Returns the structured delta (also written
    to ``<corpus>/.refresh/last-run.json`` unless dry_run)."""
    sources_path = Path(sources_path).resolve()
    corpus_root = Path(corpus_root).resolve() if corpus_root else sources_path.parent
    repo_root = Path(repo_root).resolve() if repo_root else corpus_root.parent.parent
    ts = _utc_now_iso(now)

    report = {
        "run_ts": ts,
        "cadence_class": cadence_class,
        "sources_manifest": str(sources_path),
        "dry_run": dry_run,
        "sources": [],
    }

    selected = filter_by_cadence(load_sources(sources_path), cadence_class)
    for source in selected:
        rec = {
            "id": source.id,
            "kind": source.kind,
            "url": source.url,
            "cadence": source.cadence,
            "entry": source.entry,
            "model_parse": source.model_parse,
            "status": None,
            "auto_landed": [],
            "review": [],
            "pending_delta": None,
            "model_delta": None,  # populated when model_parse is True (AC.CLP-MDL.2)
        }
        report["sources"].append(rec)

        # Class guard FIRST — a hostile entry path never reaches a write
        # (AC.CLP-CUR.7).
        entry_path = None
        if source.kind == "entry":
            try:
                entry_path = resolve_entry_path(corpus_root, source.entry)
            except CrossClassWriteError as exc:
                rec["status"] = "refused-cross-class-write"
                rec["error"] = str(exc)
                continue
            if not entry_path.is_file():
                rec["status"] = "entry-missing"
                rec["error"] = f"corpus entry not found: {source.entry}"
                continue

        try:
            raw = fetch_source(source.url, repo_root)
        except FetchError as exc:
            rec["status"] = "fetch-failed"
            rec["error"] = str(exc)
            if entry_path is not None and not dry_run:
                mark_stale(entry_path, "fetch failed", ts)
                rec["stale_marked"] = True
            continue

        norm = normalize(raw)

        # Model-lineup tracking (AC.CLP-MDL.1/2). Runs on raw text (not norm)
        # so backtick-quoted IDs are present regardless of HTML stripping.
        if source.model_parse:
            from capability_refresh.models import (
                compute_model_delta,
                extract_model_ids,
                load_model_lineup,
                save_model_lineup,
            )
            current_ids = extract_model_ids(raw)
            prior_ids = load_model_lineup(corpus_root, source.id)
            if prior_ids is None:
                rec["model_delta"] = {"added": [], "removed": [], "no_prior": True}
            else:
                rec["model_delta"] = compute_model_delta(prior_ids, current_ids)
            if not dry_run:
                save_model_lineup(corpus_root, source.id, current_ids, ts)

        snap_path = resolve_state_path(corpus_root, ".refresh", "snapshots",
                                       f"{source.id}.txt")
        if not snap_path.exists():
            rec["status"] = "initialized"
            if not dry_run:
                snap_path.parent.mkdir(parents=True, exist_ok=True)
                snap_path.write_text(norm, encoding="utf-8")
                if entry_path is not None:
                    stamp_source(entry_path, source.url, ts)
            continue

        old_lines = snap_path.read_text(encoding="utf-8").splitlines()
        new_lines = norm.splitlines()
        items = partition_delta(old_lines, new_lines)

        review_items: List[DeltaItem] = []
        for it in items:
            if it.kind == "reprojection" and source.kind == "entry":
                if dry_run:
                    it.disposition = "auto-land (dry-run)"
                    rec["auto_landed"].append(it.as_dict())
                    continue
                outcome = apply_reprojection(entry_path, it.old, it.new)
                if outcome == "auto-landed":
                    it.disposition = "auto-landed"
                    rec["auto_landed"].append(it.as_dict())
                else:
                    it.kind = outcome  # overlay-touch | curated-divergence
                    it.disposition = "review"
                    it.reason = (
                        "upstream same-statement update could not auto-land: "
                        + ("touches the curated [user-intent phrasings] overlay"
                           if outcome == "overlay-touch"
                           else "entry body has curatorially diverged from upstream")
                    )
                    review_items.append(it)
                    rec["review"].append(it.as_dict())
            else:
                # watch sources: ALL deltas review-class by construction.
                if it.disposition != "review":
                    it.disposition = "review"
                review_items.append(it)
                rec["review"].append(it.as_dict())

        rec["status"] = "delta" if items else "unchanged"
        if not dry_run:
            snap_path.write_text(norm, encoding="utf-8")
            if entry_path is not None:
                stamp_source(entry_path, source.url, ts)
            if review_items:
                rec["pending_delta"] = str(
                    _write_pending_delta(corpus_root, source, review_items, ts)
                )

    if not dry_run:
        out = resolve_state_path(corpus_root, ".refresh", "last-run.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report["report_path"] = str(out)
    return report
