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

"""AC.SBB.3 (part 1) — the floor ``.gitignore`` for a generated project.

A project loam generates must carry a ``.gitignore`` that keeps two
classes of path out of version control:

* **harness runtime state** — the scratch tree, the per-workspace memory
  queues, and the tracker SQLite DBs loam writes into a workspace while it
  runs;
* **secrets** — ``.env`` files and the credential-file family.

This module is the single source of truth for that floor set.
``missing_floor_entries`` reports which floor entries a project's existing
``.gitignore`` does not yet cover — the artifact-cleanliness sweep
(``artifact_sweep``) is the runtime enforcement that keeps the paths out
even when the ``.gitignore`` is incomplete or absent.
"""

from __future__ import annotations


# The floor ``.gitignore`` entries, grouped for the rendered file. Each
# entry is a gitignore glob line. Keep in lockstep with
# ``artifact_sweep.RUNTIME_STATE_GLOBS`` (the sweep enforces the same set
# at the commit boundary).
HARNESS_RUNTIME_STATE_ENTRIES: tuple[str, ...] = (
    ".scratch/",
    ".loam/memory/queue/",
    ".loam/memory/*.sqlite",
    ".loam/*.sqlite",
    "**/*.sqlite",
    ".pos/",
)

SECRET_ENTRIES: tuple[str, ...] = (
    ".env",
    ".env.*",
    "!.env.example",
    "!.env.sample",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    ".npmrc",
    ".pypirc",
)

# The set a project's .gitignore must COVER for the floor to be satisfied.
# The negated allow-lines (``!.env.example``) are documentation, not
# coverage requirements, so they are excluded from the required set.
REQUIRED_FLOOR_ENTRIES: tuple[str, ...] = tuple(
    e
    for e in (*HARNESS_RUNTIME_STATE_ENTRIES, *SECRET_ENTRIES)
    if not e.startswith("!")
)


def render_gitignore() -> str:
    """Render the floor ``.gitignore`` content a generated project carries."""
    lines = [
        "# --- loam secure-build baseline (AC.SBB.3) ---------------------",
        "# Harness runtime state — never commit the scratch tree, the",
        "# per-workspace memory queues, or tracker SQLite DBs.",
        *HARNESS_RUNTIME_STATE_ENTRIES,
        "",
        "# Secrets — never commit credentials or .env files (sample/example",
        "# files are explicitly allowed back in).",
        *SECRET_ENTRIES,
        "# --------------------------------------------------------------",
    ]
    return "\n".join(lines) + "\n"


def _normalise(entry: str) -> str:
    return entry.strip().rstrip("/")


def missing_floor_entries(gitignore_text: str | None) -> list[str]:
    """Return the REQUIRED floor entries not covered by *gitignore_text*.

    Coverage is matched leniently: a project's ``.gitignore`` line covers a
    floor entry when, ignoring a trailing slash and surrounding whitespace,
    the lines are equal. An absent / empty ``.gitignore`` means every floor
    entry is missing.
    """
    if not gitignore_text or not gitignore_text.strip():
        return list(REQUIRED_FLOOR_ENTRIES)
    present = {
        _normalise(ln)
        for ln in gitignore_text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    }
    return [
        e for e in REQUIRED_FLOOR_ENTRIES if _normalise(e) not in present
    ]
