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

"""Project-language auto-detection for the onboarding ritual.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.2: walks ``workspace_root``
depth-bounded (max depth 3) inspecting Gemfile / Gemfile.lock /
config/application.rb / package.json / tsconfig.json /
pnpm-lock.yaml / yarn.lock / package-lock.json. Returns a
:class:`LanguageDetection` carrying the inferred primary language +
the file-signal list that drove the decision.

Detection rules (plan-doc §3 + §7):

  - ``Gemfile`` + ``config/application.rb`` → ``rails``
  - ``Gemfile`` (alone, no ``config/application.rb``) → ``ruby``
  - ``package.json`` + ``tsconfig.json`` → ``ts``
  - ``package.json`` (alone, no ``tsconfig.json``) → ``js``
  - Both ``Gemfile`` and ``package.json`` at root → ``mixed``
  - Neither → ``unknown``

Polyglot beyond simple primary-pick is deferred to v0.2.x per master
plan §7.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


# AC.ONBOARD.2 — depth-bounded walk. Depth 3 covers root + first two
# subdirectory levels (sufficient for Gemfile/package.json detection
# in monorepos with apps/<name>/ or services/<name>/ layouts; bound
# avoids walking node_modules/ + vendor/).
MAX_WALK_DEPTH: int = 3

# AC.ONBOARD.2 — file-signal set inspected by the walker. Names are
# matched case-sensitively against entries directly under each walked
# directory (no glob; explicit name lookup).
DETECTION_FILES: frozenset[str] = frozenset(
    {
        "Gemfile",
        "Gemfile.lock",
        "config/application.rb",
        "package.json",
        "tsconfig.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
    }
)


PrimaryLanguage = Literal[
    "rails", "ruby", "ts", "js", "mixed", "unknown"
]


@dataclass(frozen=True)
class LanguageDetection:
    """Result of :func:`detect_language`.

    Attributes:
        primary: One of the literal strings in :data:`PrimaryLanguage`.
        signals: Tuple of detection-file names found at workspace_root
                 (or under it within MAX_WALK_DEPTH). Sorted
                 deterministically for reproducible audit-log entries.
    """

    primary: PrimaryLanguage
    signals: tuple[str, ...]


def detect_language(workspace_root: Path) -> LanguageDetection:
    """Detect primary project language at ``workspace_root``.

    Per AC.ONBOARD.2: depth-bounded walk + Gemfile / config /
    package.json / tsconfig.json detection. Returns the shape the
    onboarding ritual needs to compose Q1 ("I detected this is X.
    Continue? Y/N" / "Which is primary?" / "What language is this?").
    """
    if not workspace_root.is_dir():
        return LanguageDetection(primary="unknown", signals=())

    found: set[str] = set()
    _walk(workspace_root, found, depth=0)

    has_gemfile = "Gemfile" in found
    has_application_rb = "config/application.rb" in found
    has_package_json = "package.json" in found
    has_tsconfig = "tsconfig.json" in found

    primary: PrimaryLanguage
    if has_gemfile and has_package_json:
        primary = "mixed"
    elif has_gemfile and has_application_rb:
        primary = "rails"
    elif has_gemfile:
        primary = "ruby"
    elif has_package_json and has_tsconfig:
        primary = "ts"
    elif has_package_json:
        primary = "js"
    else:
        primary = "unknown"

    return LanguageDetection(
        primary=primary,
        signals=tuple(sorted(found)),
    )


# AC.LD.SKIP-FRAMEWORK.1 — directories opaque to the walker. Names
# matched case-sensitively against single path components. The set
# unifies two intents:
#   (a) noise directories whose contents are not the user's app
#       (build artefacts, dependency caches, version-control internals);
#   (b) loam-harness internals inside a bootstrapped workspace
#       (specifically `framework/`, which `loam init` populates with a
#       cloned canonical that may carry archived fixtures in languages
#       different from the user's actual app — see v0.2.1 corrective F2).
# Adding a new entry requires a named-AC test demonstrating the skip.
_SKIPPED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        "vendor",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".next",
        ".turbo",
        # AC.LD.SKIP-FRAMEWORK.1 — `framework/` is loam's harness
        # scaffolding inside a bootstrapped workspace; its contents are
        # NOT the user's app and must not influence language detection.
        "framework",
    }
)


def _walk(directory: Path, found: set[str], *, depth: int) -> None:
    """Recursive directory walk capped at MAX_WALK_DEPTH.

    Records every detection-file hit (relative to workspace_root) into
    ``found``. Skips entries listed in :data:`_SKIPPED_DIRS` (noise
    directories and loam-harness internals) to keep the walk fast on
    real projects and to prevent loam's own framework/ subtree from
    leaking signals into the user's project-language detection.
    """
    if depth > MAX_WALK_DEPTH:
        return
    try:
        entries = list(directory.iterdir())
    except (PermissionError, OSError):
        return

    for entry in entries:
        # Top-level files: match against simple filename.
        if entry.is_file():
            if entry.name in DETECTION_FILES:
                found.add(entry.name)
            # Special two-component name "config/application.rb" is
            # checked below via the directory traversal.
            continue
        if entry.is_dir():
            # Skip noise dirs + loam-harness internals (AC.LD.SKIP-
            # FRAMEWORK.1).
            if entry.name in _SKIPPED_DIRS:
                continue
            # Detect the special two-component signal at depth-1
            # boundaries: <root>/config/application.rb.
            if entry.name == "config" and depth == 0:
                candidate = entry / "application.rb"
                if candidate.is_file():
                    found.add("config/application.rb")
            _walk(entry, found, depth=depth + 1)
