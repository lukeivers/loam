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

"""SUB-ITEM 3 — migration auto-detect / auto-upgrade trigger (AC.UPGR.*).

A NEW fail-soft SessionStart CONTRIBUTOR composed onto the existing
``pos_session_start.py`` hook chain (the same shape KP7's
``session_surface.py`` uses): a workspace whose applied-migration cursor
is BEHIND the migrations shipped with the installed loam version is
NOTICED at session-start (AC.UPGR.1), the pending migrations are replayed
THROUGH the sealed ``loam migrate`` engine wrapped in the existing
``reversibility-primitive`` backup-verify-rollback envelope (AC.UPGR.2 —
a THIN consumer; ZERO re-implementation of any apply/replay/backup path),
and the result is surfaced in PLAIN language (AC.UPGR.3 — no SHAs / cursor
internals / AC-IDs; on a failure the rollback fires and the user is told
the state was RESTORED, not left half-migrated).

**Compose points (Lens 1 — every line leans on the SEALED engine):**

  * detection ............ ``cursor.read_cursor`` + ``schema.load_migration_dir``
                           + ``replay.enumerate_pending`` (the engine's own
                           pending-set computation — AC.UPGR.1).
  * wrapped replay ....... the SAME envelope construction the sealed
                           ``loam migrate`` verb performs
                           (``ReversibilityStore`` + ``MigrationSafetyEnvelope``
                           → ``replay.replay``). The backup-first /
                           protection-floor / rollback-on-failure safety
                           is INHERITED, never re-built (AC.UPGR.2).

**The live SessionStart ARM is OWNER-GATED (plan §8.4).** This module is
BUILT + PROVEN here, but it is NOT wired into ``pos_session_start.py``'s
``main()`` — registering an always-on auto-upgrade that mutates user-state
on every session is a runtime-behaviour flip in the same owner-class as
the FBM / KP7 live activations. The wiring step is surfaced for the owner;
the build does not flip it live. ``run_auto_upgrade`` is shaped EXACTLY as
the fail-soft contributor ``main()`` would call (mirrors
``_emit_keep_pace_surface``): it NEVER raises, so a broken auto-upgrade
contributor can never break SessionStart.

Importable so tests (and the outcome-altitude AC.UPGR.S) exercise it
without subprocess.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
import tempfile


# --- compose surface (the SEALED migration engine + reversibility envelope) ---
#
# These imports are the WHOLE of the apply/replay/backup machinery. This
# module adds detection-at-session-start + a plain-language surface around
# them; it re-implements none of them (plan §8.3 — the #1 boundary-leak
# risk). Reached via a best-effort lazy import inside ``run_auto_upgrade`` so
# a stranger workspace that has not installed the engine degrades to
# "no surface" rather than breaking the live SessionStart hook (the fail-soft
# contract the whole hook chain holds).


def _default_migrations_dir(repo_root: Path) -> Path:
    """The tracked declared-migration contract home (``docs/state-migrations/``).

    Mirrors the sealed verb's ``cli._default_migrations_dir`` (same path, same
    semantics) so the auto-detect reads the SAME contract the manual
    ``loam migrate`` reads — single source of truth for "what migrations ship
    with this loam version."
    """
    return repo_root / "docs" / "state-migrations"


def _loam_root() -> Path:
    """The workspace root that holds the ``framework/`` tree.

    ``framework/orchestrator/scripts/auto_upgrade.py`` → parents[3] is the
    workspace root (mirrors ``pos_session_start.py`` / ``session_surface.py``).
    """
    return Path(__file__).resolve().parents[3]


@dataclass
class AutoUpgradeResult:
    """Outcome of one ``run_auto_upgrade`` call.

    ``detected`` — True iff a behind-cursor gap was found (pending set
        non-empty). When False, ``surface`` is ``None`` (nothing to tell the
        user — a session-start with no upgrade is silent).
    ``applied`` — the ordered slugs applied THIS run (empty on a detect-only
        / dry-run / rolled-back / failed-import call).
    ``rolled_back`` — True iff a replay failure triggered the envelope's
        restore (the user-state is back to its pre-upgrade bytes).
    ``failure`` — the failure reason string when something went wrong
        (replay failure OR a fail-soft degrade like a missing engine import);
        ``None`` on a clean run.
    ``surface`` — the PLAIN-language text for the user (no SHAs / cursor
        internals / AC-IDs), or ``None`` when there is nothing to surface.
    """

    detected: bool = False
    applied: list[str] = field(default_factory=list)
    rolled_back: bool = False
    failure: str | None = None
    surface: str | None = None


def detect_pending(
    workspace_root: str | Path,
    *,
    migrations_dir: str | Path | None = None,
) -> list:
    """AC.UPGR.1 — read the cursor + enumerate the pending declared migrations.

    Composes the SEALED engine's own pending-set computation
    (``read_cursor`` → ``load_migration_dir`` → ``enumerate_pending``): the
    pending set is every shipped migration the workspace's cursor has NOT
    applied, in release-version order. A fresh / up-to-date workspace yields
    an empty list. No user-state is mutated — this is the read-only
    detection half (AC.UPGR.1 is "noticed without the user running anything").

    Returns the engine's ``list[DeclaredMigration]``. Raises only what the
    sealed enumerate path raises (e.g. ``MigrationOrderError`` on an unstamped
    pending migration — a release-time gap surfaced rather than guessed);
    ``run_auto_upgrade`` wraps this in the fail-soft envelope.
    """
    from loam.state_migration_engine.cursor import read_cursor
    from loam.state_migration_engine.schema import load_migration_dir
    from loam.state_migration_engine.replay import enumerate_pending

    workspace_root = Path(workspace_root)
    mdir = (
        Path(migrations_dir)
        if migrations_dir is not None
        else _default_migrations_dir(_loam_root())
    )
    cursor = read_cursor(workspace_root)
    migrations = load_migration_dir(mdir)
    return enumerate_pending(cursor, migrations)


def render_surface(result: "AutoUpgradeResult") -> str | None:
    """AC.UPGR.3 — render the PLAIN-language surface from a result.

    NO internal vocabulary: no commit SHAs, no cursor version strings, no
    migration slugs, no AC-IDs — only what a non-technical user needs to
    understand what happened to THEIR saved settings.

      * a successful upgrade → "loam brought your saved settings up to date
        (N update(s) applied). Your existing work was preserved."
      * a rolled-back / failed upgrade → "An update to your saved settings
        couldn't finish, so loam put everything back exactly as it was —
        nothing was left half-changed. You can keep working."
      * nothing detected → ``None`` (a quiet session-start; no surface).
    """
    if result.rolled_back or (result.failure is not None and not result.applied):
        return (
            "An update to your saved settings couldn't finish, so loam put "
            "everything back exactly as it was — nothing was left "
            "half-changed. You can keep working."
        )
    if result.applied:
        n = len(result.applied)
        plural = "update" if n == 1 else "updates"
        return (
            f"loam brought your saved settings up to date ({n} {plural} "
            "applied). Your existing work was preserved."
        )
    return None


def run_auto_upgrade(
    workspace_root: str | Path,
    *,
    migrations_dir: str | Path | None = None,
) -> AutoUpgradeResult:
    """The fail-soft SessionStart contributor (AC.UPGR.1/.2/.3).

    Sequence (every load-bearing step composes the SEALED engine/envelope):

      1. DETECT (AC.UPGR.1) — read the cursor + enumerate pending. Empty →
         return a quiet, un-detected result (no surface).
      2. WRAPPED REPLAY (AC.UPGR.2) — build the envelope EXACTLY as the
         sealed ``loam migrate`` verb does (``ReversibilityStore`` +
         ``MigrationSafetyEnvelope`` over a temp snapshot root) and call the
         sealed ``replay.replay``. Backup-first / protection-floor /
         rollback-on-failure are INHERITED. No apply/replay/backup logic is
         re-implemented here.
      3. SURFACE (AC.UPGR.3) — render the plain-language outcome (success or
         restored-on-failure).

    **Fail-soft (the live-hook contract).** Like ``_emit_keep_pace_surface``,
    this NEVER raises: any failure — a missing engine import on a stranger
    workspace, a replay exception (which the envelope has ALREADY rolled back
    before re-raising), an unstamped-migration order error — is caught and
    reported as a degraded result so a broken auto-upgrade contributor can
    never wedge SessionStart. On a replay failure the engine's envelope has
    already restored the pre-upgrade bytes (``ReplayResult.rolled_back``); the
    surface tells the user their state was put back.

    The ``snapshot_root`` defaults to a temp dir (mirrors the sealed verb's
    default); the per-replay backup the envelope writes there is the
    reversibility envelope's own work, not this module's.
    """
    try:
        pending = detect_pending(workspace_root, migrations_dir=migrations_dir)
    except Exception as exc:  # noqa: BLE001 — fail-soft: never break the hook
        return AutoUpgradeResult(detected=False, failure=f"detect: {exc}")

    if not pending:
        # Up-to-date or fresh — a quiet session-start, nothing to surface.
        return AutoUpgradeResult(detected=False)

    result = AutoUpgradeResult(detected=True)

    try:
        from loam.reversibility_primitive import ReversibilityStore
        from loam.state_migration_engine.envelope import MigrationSafetyEnvelope
        from loam.state_migration_engine.replay import replay

        workspace_root = Path(workspace_root)
        mdir = (
            Path(migrations_dir)
            if migrations_dir is not None
            else _default_migrations_dir(_loam_root())
        )
        # Build the envelope EXACTLY as the sealed verb (cli.dispatch) does —
        # composing it, not re-implementing it. The temp snapshot root holds
        # the envelope's own pre-replay backup.
        snapshot_root = Path(tempfile.mkdtemp(prefix="loam-auto-upgrade-snapshot-"))
        store = ReversibilityStore(snapshot_root / "reversibility.sqlite")
        envelope = MigrationSafetyEnvelope(
            store=store, snapshot_root=snapshot_root
        )

        replay_result = replay(
            workspace_root,
            migrations_dir=mdir,
            envelope=envelope,
        )
    except Exception as exc:  # noqa: BLE001 — fail-soft: never break the hook
        # An exception escaping the wrapped replay is itself a degrade. The
        # sealed replay catches its OWN apply failures and rolls back inside
        # ``replay`` (returning rolled_back=True, not raising); reaching here
        # means a construction/setup failure, which mutated nothing.
        result.failure = f"replay: {exc}"
        result.surface = render_surface(result)
        return result

    result.applied = list(replay_result.applied)
    result.rolled_back = replay_result.rolled_back
    result.failure = replay_result.failure
    result.surface = render_surface(result)
    return result


def emit_auto_upgrade_surface(
    workspace_root: str | Path | None = None,
) -> None:
    """OWNER-GATED live entry-point — the SessionStart contributor shape.

    This is shaped EXACTLY as ``pos_session_start.py``'s ``main()`` would call
    it (mirrors ``_emit_keep_pace_surface``): run the auto-upgrade, and if it
    produced a plain-language surface, ``print`` it as an additionalContext
    line. It is fail-soft end to end.

    **It is NOT called from ``main()`` in this amendment.** Wiring this into
    the live SessionStart hook flips an always-on runtime behaviour (an
    auto-upgrade that mutates user-state on every session of every workspace)
    — owner-class, surfaced for sign-off, NOT flipped here (plan §8.4). The
    function exists so the owner-gated wiring is a one-line addition to
    ``main()`` when ruled, and so the contributor shape is provable now.
    """
    try:
        ws = Path(workspace_root) if workspace_root is not None else _loam_root()
        result = run_auto_upgrade(ws)
        if result.surface:
            print(result.surface)
    except BaseException:  # noqa: BLE001 — fail-soft: never break the hook
        return


if __name__ == "__main__":  # pragma: no cover — manual smoke only
    emit_auto_upgrade_surface()
