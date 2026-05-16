"""Frozen-unseen independent + anti-overfit verifier.

Maps to AC.A.2 (frozen unseen done) and AC.A.3 (independent +
adversarial verification), carried THROUGH the packaging (not
hand-added as the probe did).

The honesty spine the Tier-0 probe proved load-bearing:

  * The machine-checkable acceptance is authored and FROZEN before
    any sub-agent runs (`freeze_acceptance`), content-hash pinned,
    and written to a path no sub-agent brief and no per-sub-task
    judge ever receives.  `FrozenAcceptance.assert_unseen_by` is the
    structural guard: if any brief/judge text contains the frozen
    acceptance body or its path, that is a freeze-isolation breach
    and verification refuses to run (a refusal is honest; a silent
    pass would be the failure the probe forbids).

  * "done" is decided by an INDEPENDENT tool-executing check on the
    produced artefact (`verify`), exit-code verified — never the
    sub-agent's self-report.

  * An ANTI-OVERFIT check runs the same artefact against held-out
    inputs that appear in no brief and no judge.  Both the primary
    check and the anti-overfit check must pass for a positive
    "done"; either failing yields a definite, evidence-carrying
    negative (which is a valid AC-satisfying outcome, never retried).

This module is pure stdlib + subprocess (the `claude` constraint is
upstream in orchestrator.py; verification itself runs the produced
artefact's own check command, not a model).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FrozenAcceptance:
    """A machine-checkable acceptance, frozen before any sub-agent.

    `check_argv` is the independent tool-executing check (e.g.
    ``["python3", "verify_test.py"]``) run in `work_dir`; exit 0 ==
    done, non-zero == not done.  `held_out_argv` is the anti-overfit
    check using inputs absent from every brief + judge.  `content`
    is the human-frozen acceptance text; `content_sha256` pins it.
    """

    acceptance_id: str
    content: str
    content_sha256: str
    check_argv: list[str]
    held_out_argv: list[str] = field(default_factory=list)
    frozen_path: str = ""

    def assert_unseen_by(self, *texts: str) -> None:
        """Refuse if the frozen acceptance leaked into any brief/judge.

        AC.A.2 structural guard.  A leak (the acceptance body or its
        frozen path appearing in a sub-agent brief or per-sub-task
        judge) destroys the Tier-0 honesty control — the loop could
        have been steered to the test.  Refusing is honest; passing
        anyway is the exact self-report-trust failure the probe
        proved must not happen.
        """
        needles = [self.content.strip()]
        if self.frozen_path:
            needles.append(self.frozen_path)
        for text in texts:
            if text is None:
                continue
            for needle in needles:
                if needle and needle in text:
                    raise FreezeIsolationBreach(
                        f"Frozen acceptance {self.acceptance_id!r} leaked "
                        f"into a sub-agent brief or judge — Tier-0 honesty "
                        f"control destroyed; verification refuses to run."
                    )


class FreezeIsolationBreach(RuntimeError):
    """Raised when the frozen acceptance leaked to a sub-agent/judge."""


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of independent + anti-overfit verification.

    `done` is True only when BOTH the independent check and the
    anti-overfit check exit 0.  Either failing -> `done` False with
    evidence (exit codes + captured tails) — a definite negative,
    valid per AC.A.3 / AC.A.4, never retried.
    """

    done: bool
    primary_exit: int
    held_out_exit: int | None
    primary_tail: str
    held_out_tail: str
    acceptance_id: str
    acceptance_sha256: str

    def as_evidence(self) -> dict:
        return {
            "done": self.done,
            "primary_exit": self.primary_exit,
            "held_out_exit": self.held_out_exit,
            "acceptance_id": self.acceptance_id,
            "acceptance_sha256": self.acceptance_sha256,
            "primary_tail": self.primary_tail[-800:],
            "held_out_tail": self.held_out_tail[-800:],
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def freeze_acceptance(
    *,
    acceptance_id: str,
    content: str,
    check_argv: list[str],
    held_out_argv: list[str] | None = None,
    freeze_dir: Path,
) -> FrozenAcceptance:
    """Author + freeze + hash-pin the acceptance BEFORE any sub-agent.

    AC.A.2.  Writes the acceptance body to ``freeze_dir/
    <acceptance_id>.frozen`` (a path the orchestrator keeps out of
    every sub-agent brief and every per-sub-task judge) and a sidecar
    ``.sha256`` so a later read can re-verify the freeze was not
    mutated.  Returns a frozen, immutable handle.
    """
    freeze_dir = Path(freeze_dir)
    freeze_dir.mkdir(parents=True, exist_ok=True)
    sha = _sha256(content)
    frozen_path = freeze_dir / f"{acceptance_id}.frozen"
    frozen_path.write_text(content, encoding="utf-8")
    (freeze_dir / f"{acceptance_id}.sha256").write_text(sha, encoding="utf-8")
    return FrozenAcceptance(
        acceptance_id=acceptance_id,
        content=content,
        content_sha256=sha,
        check_argv=list(check_argv),
        held_out_argv=list(held_out_argv or []),
        frozen_path=str(frozen_path),
    )


def _run(argv: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, f"TIMEOUT after {timeout}s: {exc}"
    tail = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, tail


def verify(
    frozen: FrozenAcceptance,
    *,
    work_dir: Path,
    timeout: int = 120,
    reload_freeze_check: bool = True,
) -> VerifyResult:
    """Run the independent + anti-overfit check on the produced artefact.

    AC.A.3.  The sub-agent's self-report is NOT consulted here — only
    the exit code of the independent check (and, if defined, the
    held-out anti-overfit check) decides `done`.  Both must exit 0
    for a positive done; either non-zero -> definite negative with
    evidence.

    `reload_freeze_check`: re-read the on-disk frozen acceptance and
    compare its sha to the pinned hash; a mismatch means the freeze
    was mutated between author-time and verify-time (a Tier-0
    integrity breach) and verification refuses.
    """
    work_dir = Path(work_dir)
    if reload_freeze_check and frozen.frozen_path:
        fp = Path(frozen.frozen_path)
        if fp.exists():
            on_disk = fp.read_text(encoding="utf-8")
            if _sha256(on_disk) != frozen.content_sha256:
                raise FreezeIsolationBreach(
                    f"Frozen acceptance {frozen.acceptance_id!r} mutated "
                    f"after freeze (sha mismatch) — Tier-0 integrity "
                    f"breach; verification refuses."
                )

    primary_exit, primary_tail = _run(
        frozen.check_argv, work_dir, timeout
    )

    held_out_exit: int | None = None
    held_out_tail = ""
    if frozen.held_out_argv:
        held_out_exit, held_out_tail = _run(
            frozen.held_out_argv, work_dir, timeout
        )

    done = primary_exit == 0 and (
        held_out_exit is None or held_out_exit == 0
    )
    return VerifyResult(
        done=done,
        primary_exit=primary_exit,
        held_out_exit=held_out_exit,
        primary_tail=primary_tail,
        held_out_tail=held_out_tail,
        acceptance_id=frozen.acceptance_id,
        acceptance_sha256=frozen.content_sha256,
    )


def write_verdict(result: VerifyResult, dest: Path) -> None:
    """Persist verification evidence as JSON for the verdict table."""
    Path(dest).write_text(
        json.dumps(result.as_evidence(), indent=2), encoding="utf-8"
    )
