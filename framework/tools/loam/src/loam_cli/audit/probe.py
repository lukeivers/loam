"""Ground-truth liveness probe (AC.SOL-PROBE.*).

Classifies a component's state from GROUND TRUTH, never from an
artefact's prose status line:

  * **built / sealed / merged** — from the git ref graph
    (``merge-base --is-ancestor`` against a seal-sidecar SHA), the
    mechanisation of ``feedback_published_state_only_from_git_refs``.
  * **wired vs dark** — for a hook: from the live runtime config
    (``settings.json`` carries a hook entry pointing at a real script),
    NOT from a claim that it is wired. Catches the IP-7 class ("hooks
    already wired" assumed true while ``settings.json`` was empty).
  * **wired vs dark for a BACKEND/service-class component** — this is
    the load-bearing F2 (plan §10 item 1). Static config alone
    MIS-classifies a backend as live: the graphiti case was
    MCP-wired + had an async-write queue (static config said "wired")
    yet the consumer was a Protocol shim that never actually ran
    (reality was DARK). So a backend-class probe does a CHEAP REAL
    PROBE — an import or a call — and classifies DARK when the real
    probe fails, even when config says wired. A "config says wired but
    it does not actually run" component is DARK, not live.

Every classifier is pure over its inputs (a repo root, a SHA, a config
dict, a probe callable) so it is independently testable; the record
renderer (:mod:`loam_cli.audit.record`) composes them.
"""

from __future__ import annotations

import enum
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class Liveness(enum.Enum):
    """The liveness verdict for a component or substrate fact.

    The string values are the tokens the record renders + the
    comparator matches a claimed status against.
    """

    #: Build/seal/merge classes (from the ref graph).
    UNBUILT = "unbuilt"
    BUILT = "built"
    SEALED = "sealed"
    MERGED = "merged"
    #: Hook/backend wired classes (from live config + real probe).
    WIRED = "wired"
    DARK = "dark"
    #: The fail-safe class — ground truth could not be determined. The
    #: audit NEVER guesses live; an indeterminate probe degrades to
    #: this, never to a false green (plan principle: fail-safe).
    UNKNOWN = "unknown"


# Tokens a claimed status may use that MAP to each Liveness class. The
# comparator uses this to decide whether a doc's "dark" claim agrees or
# diverges from a derived "merged"/"wired" verdict.
_CLAIM_SYNONYMS: dict[Liveness, frozenset[str]] = {
    Liveness.UNBUILT: frozenset(
        {"unbuilt", "not built", "not-built", "unimplemented", "planned"}
    ),
    Liveness.DARK: frozenset(
        {"dark", "not wired", "not-wired", "unwired", "inactive", "off"}
    ),
    Liveness.MERGED: frozenset(
        {"merged", "live", "shipped", "done", "active", "on"}
    ),
    Liveness.SEALED: frozenset({"sealed"}),
    Liveness.BUILT: frozenset({"built", "wired-in-config"}),
    Liveness.WIRED: frozenset({"wired", "live", "active", "on"}),
}

#: Classes that mean "the component is real and running" for the
#: agree/diverge decision. A claim of "dark"/"unbuilt" for a component
#: whose derived class is in this set is a DIVERGENCE.
LIVE_CLASSES: frozenset[Liveness] = frozenset(
    {Liveness.MERGED, Liveness.SEALED, Liveness.WIRED}
)

#: Classes that mean "the component is NOT running". A claim of
#: "live"/"merged" for a component whose derived class is in this set
#: is a DIVERGENCE.
DARK_CLASSES: frozenset[Liveness] = frozenset(
    {Liveness.DARK, Liveness.UNBUILT}
)


def normalize_claim_token(claim: str) -> Liveness | None:
    """Map a free claim token (``"dark"`` / ``"live"`` / ``"merged"``)
    to the :class:`Liveness` class it asserts, or ``None`` when the
    token is not a recognised liveness claim.

    Lower-cased + stripped before matching. Used by the comparator to
    interpret a claimed status field.
    """
    needle = claim.strip().lower()
    for liveness, synonyms in _CLAIM_SYNONYMS.items():
        if needle in synonyms:
            return liveness
    return None


def _git_is_ancestor(repo_root: Path, sha: str) -> bool | None:
    """Return True iff *sha* is an ancestor of HEAD (merged), False iff
    it is a real commit not reachable from HEAD, ``None`` iff the SHA
    is not a known object (cannot determine — fail-safe to UNKNOWN).

    ``git merge-base --is-ancestor`` returns rc=0 (ancestor), rc=1
    (known commit, not ancestor), or rc=128 (bad object / not a commit).
    The rc=128 case is the indeterminate one — we never treat it as a
    confident verdict.
    """
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    return None


def _read_seal_sidecar_sha(sidecar: Path) -> str | None:
    """Return the pinned seal SHA from a ``SEAL_COMMIT`` sidecar, or
    ``None`` when the sidecar is absent / a placeholder.

    The bare ``SEAL_COMMIT`` sidecar carries a single 40-hex SHA line
    (e.g. ``framework/loam-init/tests/SEAL_COMMIT``); a placeholder
    value of ``HEAD`` (or empty) means "not yet sealed".
    """
    if not sidecar.is_file():
        return None
    txt = sidecar.read_text(encoding="utf-8").strip()
    if not txt or txt == "HEAD":
        return None
    # First whitespace-delimited token; tolerate a trailing comment.
    token = txt.split()[0]
    return token


def classify_build_status(
    repo_root: Path,
    *,
    seal_sidecar: Path | None = None,
    seal_sha: str | None = None,
) -> Liveness:
    """Classify a component's build/seal/merge state from the ref graph.

    Resolution (ground-truth only — no prose):

      * A *seal_sha* (explicit) OR the SHA read from *seal_sidecar* is
        the seal anchor. With NO anchor available the component is
        :attr:`Liveness.UNBUILT` (no seal sidecar = never sealed).
      * If the seal SHA is an ancestor of HEAD →
        :attr:`Liveness.MERGED` (sealed AND on HEAD's history — the
        fully-shipped state).
      * If the seal SHA is a real commit not reachable from HEAD →
        :attr:`Liveness.SEALED` (sealed on a side branch, not yet
        merged into the current line).
      * If the seal SHA is not a known git object →
        :attr:`Liveness.UNKNOWN` (fail-safe: cannot determine, never a
        false green).

    This is ``feedback_published_state_only_from_git_refs`` made
    mechanical: the verdict is derived from ``merge-base
    --is-ancestor``, NOT from any status line in any doc.
    """
    sha = seal_sha
    if sha is None and seal_sidecar is not None:
        sha = _read_seal_sidecar_sha(seal_sidecar)
    if sha is None:
        return Liveness.UNBUILT
    ancestry = _git_is_ancestor(repo_root, sha)
    if ancestry is True:
        return Liveness.MERGED
    if ancestry is False:
        return Liveness.SEALED
    return Liveness.UNKNOWN


def _hook_commands(settings: dict) -> list[str]:
    """Flatten every hook command string out of a parsed settings dict.

    The ``settings.json`` ``hooks`` shape is
    ``{<Event>: [{"hooks": [{"type": "command", "command": "..."}]}]}``.
    Returns the list of every ``command`` string across all events.
    """
    out: list[str] = []
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return out
    for _event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []) or []:
                if isinstance(hook, dict):
                    cmd = hook.get("command")
                    if isinstance(cmd, str):
                        out.append(cmd)
    return out


def classify_hook_wired(
    settings: dict,
    *,
    marker: str,
    script_exists: Callable[[str], bool] | None = None,
) -> Liveness:
    """Classify a hook as WIRED vs DARK from the LIVE runtime config.

    A hook is :attr:`Liveness.WIRED` iff the live ``settings.json``
    carries a hook command whose string contains *marker* (the script
    name or module path that identifies the hook). It is
    :attr:`Liveness.DARK` when no such command is present — catching the
    IP-7 class where "hooks already wired" was assumed true while
    ``settings.json`` was empty.

    When *script_exists* is supplied, a wired-in-config command whose
    target script does NOT exist on disk degrades to
    :attr:`Liveness.DARK` (config points at a missing script — wired in
    name only, dark in reality). This is the config-side analogue of
    the backend real-probe: a config entry that cannot actually fire is
    not live.
    """
    commands = _hook_commands(settings)
    matching = [c for c in commands if marker in c]
    if not matching:
        return Liveness.DARK
    if script_exists is None:
        return Liveness.WIRED
    # At least one matching command must point at a script that exists.
    for cmd in matching:
        if script_exists(cmd):
            return Liveness.WIRED
    return Liveness.DARK


def classify_backend_liveness(
    *,
    config_says_wired: bool,
    real_probe: Callable[[], bool],
) -> Liveness:
    """Classify a BACKEND/service-class component WIRED vs DARK using a
    CHEAP REAL PROBE, not config alone (the load-bearing F2 — plan §10
    item 1).

    *config_says_wired* is the static-config verdict (e.g. an MCP server
    is declared, an async queue is present). *real_probe* is a cheap
    real check — an ``import`` or a live call — that returns True iff the
    backend ACTUALLY runs.

    Verdict:

      * config says wired AND the real probe succeeds →
        :attr:`Liveness.WIRED` (genuinely live end-to-end).
      * config says wired BUT the real probe FAILS →
        :attr:`Liveness.DARK`. **This is the graphiti case**: MCP-wired
        + async-queue present (config said wired) yet the consumer was
        a Protocol shim that never ran. The real probe catches what
        config cannot. A "config says wired but it does not actually
        run" component is DARK, not live.
      * config does NOT say wired → :attr:`Liveness.DARK` (nothing to
        probe; not even declared).

    The probe is wrapped so that an EXCEPTION from *real_probe* (an
    ``ImportError``, a connection refusal) is treated as a failed probe
    → DARK, never as an indeterminate pass. A backend the probe cannot
    reach is dark, by construction.
    """
    if not config_says_wired:
        return Liveness.DARK
    try:
        live = bool(real_probe())
    except Exception:
        live = False
    return Liveness.WIRED if live else Liveness.DARK
