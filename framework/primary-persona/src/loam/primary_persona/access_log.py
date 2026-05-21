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

"""Memory-file access log + power-law base-level activation (FBM T2.1).

Sidecar JSONL log + Anderson & Schooler 1991 power-law activation column
for the file-based memory retrieval ranker. The log records every
read/write/cite touch of a memory file; the activation function turns
the log's per-file event list into a single scalar that the ranker
multiplies against the BM25 column.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §14:

  - **D-T2.1.DECAY** — power-law decay constant ``d = 0.5`` (canonical
    Anderson & Schooler 1991 / ACT-R value); hard-coded at v0.1.
  - **D-T2.1.LOGFMT** — JSONL with fields ``{file, ts, op}``; op enum
    ``{read, write, cite}``. Append-only writes are atomic on POSIX
    for sub-page entries.
  - **D-T2.1.FLOOR** — when ``t_j >= now``, floor ``(now − t_j) = epsilon``
    with ``epsilon = 1.0`` second; consistent with second-precision
    ISO-8601 timestamp emit.

Public API:

  - :data:`ACCESS_LOG_FILENAME` — sidecar filename (lives at
    ``<memory_dir>/.access-log.jsonl``).
  - :data:`ACTIVATION_DECAY_D` — the ``d`` constant (0.5).
  - :data:`ACTIVATION_FLOOR_EPSILON_SECONDS` — the floor for zero-
    duration touches (1.0 second).
  - :data:`ACCESS_LOG_OPS` — closed enum of valid op tags.
  - :func:`access_log_path` — derive log path from memory_dir.
  - :func:`append_access_event` — append one event to the log.
  - :func:`read_access_log` — parse the log, returning a dict
    ``{file_path: list[datetime]}`` of timestamps per file.
  - :func:`compute_activation` — Anderson & Schooler functional form
    ``B_i = ln(Σ_j (now − t_j)^(−d))`` for one file's timestamps.

ACs delivered (per plan §4):

  - **AC.FBMT2.PLBLA.1** — :func:`append_access_event` writes a
    structured ``{file, ts, op}`` entry per memory touch.
  - **AC.FBMT2.PLBLA.3** — :func:`compute_activation` matches Anderson &
    Schooler 1991 functional form to within floating-point tolerance.
  - **AC.FBMT2.PLBLA.4** — :func:`read_access_log` returns an empty
    dict (no touches) when the log file is absent; downstream callers
    degrade to neutral activation.

Per ODD §2.5 every code path traces back to a named AC; defensive
``if`` branches without an AC anchor are not introduced.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


# ---- public constants (D-T2.1.DECAY / D-T2.1.LOGFMT / D-T2.1.FLOOR) ---

# Sidecar log filename. Lives at ``<memory_dir>/.access-log.jsonl``.
# Dot-prefixed so directory listings of the memory corpus don't pick
# it up as a memory file.
ACCESS_LOG_FILENAME = ".access-log.jsonl"

# Power-law decay constant ``d`` (D-T2.1.DECAY). Anderson & Schooler
# 1991 empirically fit ``d ≈ 0.5`` across three datasets (child-
# directed speech, NYT headlines, email logs); also the canonical
# ACT-R value (Anderson et al. 2004). Configurability deferred per
# plan-doc §10 doubt #4.
ACTIVATION_DECAY_D = 0.5

# Floor epsilon for zero-duration touches (D-T2.1.FLOOR). The formula
# ``(now − t_j)^(−d)`` is undefined at ``t_j == now``. A second-scale
# epsilon is the natural floor at the time-scale the log emits (the
# ``ts`` field is second-precision ISO-8601). The activation
# contribution for a "just now" access is ``epsilon^(−0.5) = 1.0``.
ACTIVATION_FLOOR_EPSILON_SECONDS = 1.0

# Closed enum of valid op tags (D-T2.1.LOGFMT). ``read`` and ``write``
# fire from production code at v0.1; ``cite`` is reserved for an
# explicit "file referenced in plan-doc / source edit" emit path that
# this amendment does NOT wire (per plan §6 step 2 trailing note).
ACCESS_LOG_OPS = frozenset({"read", "write", "cite"})


# ---- path derivation (AC.FBMT2.PLBLA.1) -------------------------------


def access_log_path(memory_dir: Path) -> Path:
    """Return the canonical access-log path for ``memory_dir``.

    The log lives at ``<memory_dir>/.access-log.jsonl`` (sidecar to
    the episode files; per D-T2.1.LOGFMT). The path is NOT created
    here — :func:`append_access_event` creates it lazily on first
    write, mirroring the lazy-mkdir pattern in :class:`FileMemoryStore`.
    """
    return Path(memory_dir) / ACCESS_LOG_FILENAME


# ---- writer (AC.FBMT2.PLBLA.1) ----------------------------------------


def append_access_event(
    memory_dir: Path,
    *,
    file: str,
    ts: datetime,
    op: str,
) -> None:
    """Append one ``{file, ts, op}`` event to the sidecar access log.

    Per D-T2.1.LOGFMT: JSONL one-event-per-line; ``ts`` serialised as
    ISO-8601 UTC; ``op`` validated against :data:`ACCESS_LOG_OPS`. The
    parent ``memory_dir`` is created lazily (the sidecar may be the
    first artefact written in a fresh workspace).

    Fail-closed on every boundary error — a touch event is a
    bookkeeping signal, not load-bearing for the retrieval result; a
    failed write must not propagate through to the persona (AC.MFBM.2
    fail-closed surrounding contract). Specifically:

      - Unknown ``op`` raises :class:`ValueError` (programmer error;
        the closed enum is the contract).
      - Filesystem errors (permission, disk full) propagate to the
        caller; the caller's surrounding ``try`` (in the store /
        adapter) swallows them.
    """
    if op not in ACCESS_LOG_OPS:
        raise ValueError(
            f"op must be one of {sorted(ACCESS_LOG_OPS)!r}; got {op!r}"
        )
    # Normalise ts to UTC ISO-8601 second-precision (matches the floor
    # epsilon's time-scale per D-T2.1.FLOOR).
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts_iso = ts.astimezone(timezone.utc).isoformat(timespec="seconds")
    payload = {"file": file, "ts": ts_iso, "op": op}
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    log_path = access_log_path(memory_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Append-only writes — atomic on POSIX for sub-page entries (per
    # D-T2.1.LOGFMT rationale).
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(line)


# ---- reader (AC.FBMT2.PLBLA.1 / AC.FBMT2.PLBLA.4) ---------------------


def read_access_log(memory_dir: Path) -> dict[str, list[datetime]]:
    """Parse the access log and return a dict ``{file: [ts, ...]}``.

    Per AC.FBMT2.PLBLA.4: when the log file is absent, returns an
    empty dict (no events). Downstream callers (:func:`compute_activation`)
    return the floor activation for files with no events, so the
    ranker degrades to pure-BM25 ordering on a cold workspace.

    Malformed lines are skipped silently (the log is append-only and
    a partial-write at the last line is the only realistic source of
    malformed records; skipping is the fail-soft contract).
    """
    log_path = access_log_path(memory_dir)
    if not log_path.exists():
        return {}
    out: dict[str, list[datetime]] = {}
    try:
        with log_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    # AC.FBMT2.PLBLA.4: malformed line is fail-soft;
                    # the log surface stays usable for the rest.
                    continue
                file_path = rec.get("file")
                ts_str = rec.get("ts")
                if not isinstance(file_path, str) or not isinstance(ts_str, str):
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str)
                except (ValueError, TypeError):
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                out.setdefault(file_path, []).append(ts)
    except OSError:
        # Filesystem error mid-read — return what we have so far
        # (empty dict if nothing read). AC.MFBM.2 fail-closed
        # surrounding contract.
        return out
    return out


# ---- activation computer (AC.FBMT2.PLBLA.3) ---------------------------


def compute_activation(
    timestamps: Iterable[datetime],
    *,
    now: datetime,
    d: float = ACTIVATION_DECAY_D,
    epsilon_seconds: float = ACTIVATION_FLOOR_EPSILON_SECONDS,
) -> float:
    """Anderson & Schooler 1991 power-law base-level activation.

    Formula::

        B_i = ln(Σ_j (now − t_j)^(−d))

    where ``t_j`` ranges over the timestamps of accesses to file
    ``i``. ``d`` is the decay constant (0.5 per D-T2.1.DECAY).

    Per D-T2.1.FLOOR: when ``(now − t_j) <= 0`` (a "just now" or
    future-dated touch — clock skew or test setup), floor the duration
    at ``epsilon_seconds``. The activation contribution for a single
    "just now" access is ``epsilon^(−d) = 1.0`` for the default values.

    Per AC.FBMT2.PLBLA.4: an empty timestamp iterable returns
    ``-math.inf`` — a sentinel for "no activation signal exists"
    (callers degrade to pure-BM25 in this case). The activation is
    log-of-sum-of-positives; the empty sum is zero, and ``ln(0) = -inf``.

    Pure function of its inputs (``now`` injected) so the
    AC.FBMT2.PLBLA.3 fixture and the AC.FBMT2.S smoke are
    deterministic.
    """
    ts_list = list(timestamps)
    if not ts_list:
        return -math.inf
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    total = 0.0
    for t in ts_list:
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        delta_seconds = (now - t).total_seconds()
        # D-T2.1.FLOOR — zero-duration / future floor.
        if delta_seconds < epsilon_seconds:
            delta_seconds = epsilon_seconds
        total += delta_seconds ** (-d)
    return math.log(total)
