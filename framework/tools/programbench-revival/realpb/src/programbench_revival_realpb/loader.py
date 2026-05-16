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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.RPB.2 / AC.RPB.4 — the frozen REAL-public-ProgramBench task-set
loader.

The real-PB subset selection (which digest-pinned real instance-ids
run) + the per-task plain-language non-tech statement + the per-task
positive-real-outcome floor threshold ``theta`` over the GRADED
upstream score + the frozen pass rule + the frozen ``k_min`` small-k
floor are authored and CONTENT-HASH-PINNED in ``tasks/tasks.json``
BEFORE any arm runs (the proven freeze-before-any-sub-agent /
contamination spine, REUSED from v2's loader shape — Lens 1). This
module is the read path: it loads ``tasks/tasks.json``, computes its
sha256, and exposes an immutable handle. A loader that silently
tolerated a post-freeze content change would destroy the contamination
control — :func:`load_frozen_realpb_set` pins the hash and the run
records it so the headline is reproducible from the preserved
evidence (AC.RPB.6).

The real task IMAGES + the HF blobs are NOT vendored: they are large
pre-existing read-only host artefacts, referenced by digest /
instance-id, never copied into the tree (plan §2 placement). This
module pins the SELECTION + the per-task statement + the frozen
thresholds; the images/blobs are resolved at run time from the host
(D-RPB-7 real-PB plumbing reuse).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

TASKS_DIR = Path(__file__).resolve().parents[2] / "tasks"
TASKS_JSON = TASKS_DIR / "tasks.json"


@dataclass(frozen=True)
class RealPBTask:
    """One frozen REAL public ProgramBench task.

    ``statement`` is the ONLY thing either arm receives (the
    non-technical user's plain-language intent — zero-interaction
    parity, AC.RPB.1). ``instance_id`` / ``image`` / ``image_digest``
    / ``filter_regex`` bind this task to the REAL upstream public
    ProgramBench instance (scored by the REAL upstream ``programbench
    eval``, AC.RPB.2). ``floor_theta`` is the FROZEN per-task positive-
    real-outcome floor over the GRADED upstream score (D-RPB-2).
    ``setup_files`` are written into a fresh per-(arm,task) work dir
    (environment isolation — AC.RPB.1).
    """

    id: str
    instance_id: str
    image: str
    image_digest: str
    filter_regex: str
    statement: str
    floor_theta: float
    setup_files: dict[str, str]
    expected_real_outcome: str


@dataclass(frozen=True)
class RealPBTaskSet:
    """The whole frozen real-PB set + the pinned content hash.

    ``content_sha256`` pins ``tasks.json`` at freeze time; the run
    records it so re-running the frozen scorer over the preserved
    per-task evidence (incl. the real upstream ``*.eval.json``) yields
    the same verdict (AC.RPB.6 reproducibility). ``k_min`` is the
    FROZEN small-k floor on the baseline-miss denominator (D-RPB-1,
    the named v2 task-#44 defect fix).
    """

    task_set_id: str
    is_real_public_programbench: bool
    content_sha256: str
    hf_dataset: str
    hf_revision_snapshot: str
    upstream_eval: dict
    frozen_pass_rule: str
    frozen_floor_theta_default: float
    k_min: int
    frozen_failure_taxonomy: tuple[str, ...]
    tasks: tuple[RealPBTask, ...]
    tasks_dir: str

    def task_by_id(self, tid: str) -> RealPBTask:
        for t in self.tasks:
            if t.id == tid:
                return t
        raise KeyError(tid)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_frozen_realpb_set(
    tasks_json: Path | None = None,
) -> RealPBTaskSet:
    """Load + content-hash-pin the frozen REAL-public-PB task set
    (AC.RPB.2 / AC.RPB.4 / AC.RPB.5).

    The sha is computed over the EXACT bytes on disk; any post-freeze
    edit changes the recorded hash and is therefore visible in the
    evidence (the contamination-prevention property, not a silent
    tolerate). Asserts the set is flagged as the REAL public
    ProgramBench (NOT the v2 substitute) and that ``k_min >= 2`` (the
    frozen small-k floor invariant — D-RPB-1).
    """
    path = Path(tasks_json) if tasks_json else TASKS_JSON
    raw = path.read_text(encoding="utf-8")
    sha = _sha256(raw)
    doc = json.loads(raw)

    if not doc.get("is_real_public_programbench"):
        raise ValueError(
            "tasks.json is not flagged is_real_public_programbench: "
            "this harness measures the REAL public ProgramBench, NOT "
            "the v2 substitute (AC.RPB.2)."
        )
    k_min = int(doc["frozen_k_min"])
    if k_min < 2:
        raise ValueError(
            f"frozen_k_min must be >= 2 (D-RPB-1 small-k floor); got "
            f"{k_min}. A degenerate baseline-miss denominator must "
            f"never read as a determinate loss/win."
        )

    default_theta = float(doc["frozen_floor_theta_default"])
    tasks = tuple(
        RealPBTask(
            id=t["id"],
            instance_id=t["instance_id"],
            image=t["image"],
            image_digest=t["image_digest"],
            filter_regex=t["filter_regex"],
            statement=t["statement"],
            floor_theta=float(t.get("floor_theta", default_theta)),
            setup_files=dict(t.get("setup", {}).get("files", {})),
            expected_real_outcome=t.get("expected_real_outcome", ""),
        )
        for t in doc["tasks"]
    )
    return RealPBTaskSet(
        task_set_id=doc["task_set_id"],
        is_real_public_programbench=True,
        content_sha256=sha,
        hf_dataset=doc["hf_dataset"],
        hf_revision_snapshot=doc["hf_revision_snapshot"],
        upstream_eval=dict(doc["upstream_eval"]),
        frozen_pass_rule=doc["frozen_pass_rule"],
        frozen_floor_theta_default=default_theta,
        k_min=k_min,
        frozen_failure_taxonomy=tuple(doc["frozen_failure_taxonomy"]),
        tasks=tasks,
        tasks_dir=str(path.parent),
    )
