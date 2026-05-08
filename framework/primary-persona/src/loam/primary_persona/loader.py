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

"""PersonaLoader (D2).

Reads a workspace-supplied persona directory on session start (or on
explicit reload), validates against the Pydantic contract, and fails
closed on any invalidity. No persona directory present in the workspace
means the session cannot start — a deterministic check, not advisory.

Additionally: a build-time check fails if any persona directory
appears in pOS-core paths. Per STATE.md rule 4 and brief constraint 6,
pOS core ships zero persona content. The check is invoked at loader
construction time with `enforce_no_personas_in_core=True` (the
default); the framework never loads a persona that lives inside the
pOS-core tree.

The loader is stateless: reloading the same directory produces
identical results given identical files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError

from . import observability as obs
from .contract import ContractFileError, PersonaContract, load_contract


# ---- errors ----------------------------------------------------------


class PersonaDirectoryNotFoundError(FileNotFoundError):
    """Raised when the workspace persona directory is missing entirely."""


class PersonaValidationError(ValueError):
    """Raised when a persona directory exists but fails validation.

    Wraps either a Pydantic ValidationError, a ContractFileError
    (parse failure), or a missing mandatory file (e.g. no `prompt.md`).
    The message names the failing directory and, where available, the
    failing field.
    """

    def __init__(self, persona_dir: Path, detail: str) -> None:
        self.persona_dir = persona_dir
        self.detail = detail
        super().__init__(f"{persona_dir}: {detail}")


class PersonaInCoreError(RuntimeError):
    """Raised at loader construction when a persona directory is found
    inside a pOS-core path. Per v1.0: pOS core ships zero personas.
    """


# ---- loaded-persona view ---------------------------------------------


@dataclass(frozen=True)
class LoadedPersona:
    """Read-only view of a loaded persona.

    The contract is validated; prose is the file contents at load time.
    Reload a directory to pick up changes (the loader is stateless).
    """

    handle: str
    directory: Path
    contract: PersonaContract
    prompt_text: str
    voice_text: str | None = None

    @property
    def given_name(self) -> str:
        return self.contract.given_name

    @property
    def is_addressable(self) -> bool:
        return self.contract.is_addressable


# ---- loader ----------------------------------------------------------


# Paths that are considered pOS-core for the "no personas in core"
# build-time check. The constant is deliberately a relative token
# matched against the path; any path containing one of these segments
# is a core path. Workspaces live outside any of them.
_CORE_PATH_SEGMENTS = (
    "pos-v2/primary-persona",
    "primary-persona/src",
    "primary-persona/templates",  # template is framework content
)


@dataclass
class PersonaLoader:
    """Stateless workspace persona loader.

    Constructed with the workspace root; `load()` reads every persona
    directory under `<workspace>/personas/` (excluding `_retired/*`)
    and validates each.
    """

    workspace_root: Path
    enforce_no_personas_in_core: bool = True

    def __post_init__(self) -> None:
        self.workspace_root = Path(self.workspace_root).resolve()
        if self.enforce_no_personas_in_core:
            self._check_no_personas_in_core()

    @property
    def personas_dir(self) -> Path:
        # D-migration D.2 (amendment #63): personas live under
        # <workspace>/workspace/personas/ post-D.2 (was
        # <workspace>/personas/ pre-D.2).
        from loam.workspace_bootstrap.workspace_paths import (
            personas_dir as _personas_dir,
        )

        return _personas_dir(self.workspace_root)

    @property
    def retired_dir(self) -> Path:
        return self.personas_dir / "_retired"

    # ---- public ----------------------------------------------------

    def load(self) -> list[LoadedPersona]:
        """Load every valid persona under the workspace personas dir.

        Failure modes:
        - no personas dir at all → PersonaDirectoryNotFoundError
        - a persona's contract.yaml invalid → PersonaValidationError
          (raised from the first failure; the loader is strict so the
          workspace fails to start rather than silently loading a
          partial roster)
        """
        if not self.personas_dir.exists():
            with obs.loader_span(str(self.personas_dir), outcome="missing_dir"):
                raise PersonaDirectoryNotFoundError(
                    f"workspace personas directory not found: {self.personas_dir} — "
                    "a workspace without a primary persona cannot start a session."
                )

        out: list[LoadedPersona] = []
        for persona_dir in self._iter_persona_dirs():
            out.append(self._load_one(persona_dir))

        if not out:
            with obs.loader_span(str(self.personas_dir), outcome="empty_dir"):
                raise PersonaDirectoryNotFoundError(
                    f"workspace personas directory {self.personas_dir} contains no "
                    "persona subdirectories — a workspace without a primary persona "
                    "cannot start a session."
                )

        # The loader does not enforce "exactly one primary persona"; a
        # workspace may have zero or more specialists. The session
        # layer picks the primary by `is_primary=True`.
        with obs.loader_span(
            str(self.personas_dir), outcome="loaded", persona_count=len(out)
        ):
            pass

        return out

    def load_one(self, handle: str) -> LoadedPersona:
        """Load a single persona by handle. Raises if not found."""
        persona_dir = self.personas_dir / handle
        if not persona_dir.exists() or not persona_dir.is_dir():
            raise PersonaValidationError(
                persona_dir, f"persona directory {handle!r} not found"
            )
        return self._load_one(persona_dir)

    def primary(self) -> LoadedPersona:
        """Return the workspace's primary persona.

        Raises `PersonaValidationError` if zero or more-than-one
        persona has `is_primary: true`. Every workspace declares
        exactly one primary.
        """
        personas = self.load()
        primaries = [p for p in personas if p.contract.is_primary]
        if len(primaries) == 0:
            raise PersonaValidationError(
                self.personas_dir,
                "no persona has `is_primary: true` — every workspace must "
                "declare exactly one primary persona.",
            )
        if len(primaries) > 1:
            names = ", ".join(sorted(p.handle for p in primaries))
            raise PersonaValidationError(
                self.personas_dir,
                f"multiple personas claim `is_primary: true` ({names}) — "
                "a workspace has exactly one primary.",
            )
        return primaries[0]

    # ---- internals --------------------------------------------------

    def _iter_persona_dirs(self) -> Iterable[Path]:
        for entry in sorted(self.personas_dir.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_"):
                continue  # _retired/, _archive/, etc.
            yield entry

    def _load_one(self, persona_dir: Path) -> LoadedPersona:
        contract_path = persona_dir / "contract.yaml"
        prompt_path = persona_dir / "prompt.md"
        voice_path = persona_dir / "voice.md"

        if not contract_path.exists():
            raise PersonaValidationError(
                persona_dir, "contract.yaml is missing (required)"
            )
        if not prompt_path.exists():
            raise PersonaValidationError(
                persona_dir, "prompt.md is missing (required)"
            )

        try:
            contract = load_contract(contract_path)
        except ValidationError as e:
            # Extract the list of missing/invalid fields from the
            # Pydantic error for a named-field message.
            fields = ", ".join(".".join(str(loc) for loc in err["loc"]) for err in e.errors())
            raise PersonaValidationError(
                persona_dir,
                f"contract.yaml failed validation; fields: [{fields}]: {e}",
            ) from e
        except ContractFileError as e:
            raise PersonaValidationError(persona_dir, str(e)) from e

        if contract.handle != persona_dir.name:
            raise PersonaValidationError(
                persona_dir,
                f"contract handle {contract.handle!r} does not match "
                f"directory name {persona_dir.name!r}",
            )

        prompt_text = prompt_path.read_text()
        voice_text = voice_path.read_text() if voice_path.exists() else None

        return LoadedPersona(
            handle=contract.handle,
            directory=persona_dir,
            contract=contract,
            prompt_text=prompt_text,
            voice_text=voice_text,
        )

    def _check_no_personas_in_core(self) -> None:
        """Walk the framework's own tree and fail if a persona dir
        appears inside pOS-core paths. Framework-side enforcement for
        v1.0's "no persona content in core".

        Scope: the check scans the package this loader lives in for
        subdirectories that look like personas (contain `contract.yaml`).
        The templates directory is intentionally a template — the
        check does not treat `persona-template` as a persona because
        its handle shape is `example-persona` (reserved placeholder)
        rather than a committed persona identity.
        """
        this_pkg = Path(__file__).resolve().parent
        # Walk upward to locate the repo root (anywhere containing
        # `primary-persona/` as a sibling of `scope-of-work/`).
        # For tests and user-run checks, only scan the `primary-persona`
        # tree; anything else is out of scope of core.
        core_root = this_pkg.parent  # primary-persona/src/.. → primary-persona/
        for dirpath, _dirs, files in os.walk(core_root):
            if "contract.yaml" not in files:
                continue
            if any(segment in dirpath for segment in _CORE_PATH_SEGMENTS):
                # Allow template directories IFF they are clearly marked
                # as templates — the sentinel is the `example-persona`
                # handle.
                try:
                    c = load_contract(Path(dirpath) / "contract.yaml")
                except Exception:
                    # A malformed contract file in core fails the check
                    # too — core has no business shipping contract files.
                    raise PersonaInCoreError(
                        f"persona directory inside pOS-core path: {dirpath}"
                    )
                if c.handle == "example-persona":
                    continue
                raise PersonaInCoreError(
                    f"persona {c.handle!r} found in pOS-core path {dirpath}; "
                    "pOS core ships zero personas (brief constraint 6, v1.0 core primitives)."
                )

    def reload(self, handle: str) -> LoadedPersona:
        """Re-read a single persona from disk. Stateless — the loader
        does not cache; this is a convenience naming for callers."""
        return self.load_one(handle)
