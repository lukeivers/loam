"""Memory pre-warm verification surface (amendment J / AC.J.1 / AC.J.6).

Per the locked plan §11 D-1: workspace-bootstrap writes an advisory
file at ``<workspace>/.pos/ollama-prewarm-recommended.txt`` carrying
the recommended ``OLLAMA_KEEP_ALIVE`` value + operator instructions
for setting it on the Ollama daemon (server-side env, outside
pos-v2's fence per Hard Constraint 12). The persona reads this
surface to answer "is the embedding model resident?" without the
user investigating.

This module owns the persona-side read surface only. The advisory
file's content is authored by the workspace-bootstrap adapter (under
``workspace_bootstrap/adapters/first_run_scaffold.py``); this module
loads it back on demand.

Per ODD §2.5 every code path traces back to AC.J.1 / AC.J.6. The
``read_prewarm_advisory`` function returns a structured snapshot the
persona surfaces in the awareness block; it never raises on a missing
or malformed file (the fail-soft contract matches the rest of the
persona's diagnostic surfaces).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import memory_write_queue as mwq


# ---- advisory-file shape --------------------------------------------


# Default value — matches D-5 lock + Hard Constraint 12 advisory-only
# surface. Workspace-bootstrap writes this into the advisory file at
# first-run scaffold; the persona compares against the operator's live
# environment to decide whether to surface a recommendation.
RECOMMENDED_KEEP_ALIVE_VALUE = "24h"


# ---- prewarm-state snapshot -----------------------------------------


@dataclass(frozen=True)
class PrewarmState:
    """Snapshot of the workspace's pre-warm advisory + live env state.

    Fields:

    - ``advisory_path``: absolute path to
      ``<workspace>/.pos/ollama-prewarm-recommended.txt`` if present;
      ``None`` if absent.
    - ``advisory_value``: the recommended ``OLLAMA_KEEP_ALIVE`` value
      named in the advisory file's header; ``None`` if the file is
      absent or unparseable.
    - ``env_value``: the live ``OLLAMA_KEEP_ALIVE`` env var on the
      current process (None if unset). The persona surfaces a
      recommendation when this is None.
    - ``recommendation_active``: True when the advisory file exists
      AND ``env_value`` is None — i.e., the operator has not yet
      followed the advisory and the persona should remind them.
    """

    advisory_path: Path | None
    advisory_value: str | None
    env_value: str | None
    recommendation_active: bool


def read_prewarm_advisory(workspace_root: Path) -> PrewarmState:
    """Load the workspace's pre-warm advisory snapshot.

    AC.J.6: read-only diagnostic surface. The persona consumes this
    on demand (e.g., on user-prompt-submit's awareness block when the
    user asks about memory state) without the user investigating.

    Fail-soft: missing file → ``PrewarmState`` with all-None fields
    + ``recommendation_active=False``. Malformed file → same shape.
    Never raises.
    """
    # D-migration D.2 (amendment #63): advisory under
    # <workspace>/workspace/.pos/ollama-prewarm-recommended.txt.
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    advisory_path = pos_subdir(workspace_root) / "ollama-prewarm-recommended.txt"
    advisory_value: str | None = None
    if advisory_path.exists():
        try:
            text = advisory_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        # Advisory file format (workspace-bootstrap-authored):
        #   line 1 — `OLLAMA_KEEP_ALIVE=<value>`
        #   subsequent lines — operator instructions (free text)
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("OLLAMA_KEEP_ALIVE="):
                advisory_value = line.split("=", 1)[1].strip()
                break
    env_value = os.environ.get("OLLAMA_KEEP_ALIVE")
    if isinstance(env_value, str):
        env_value = env_value.strip() or None
    recommendation_active = (
        advisory_path.exists() and (env_value is None)
    )
    return PrewarmState(
        advisory_path=advisory_path if advisory_path.exists() else None,
        advisory_value=advisory_value,
        env_value=env_value,
        recommendation_active=recommendation_active,
    )
