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

"""AC.LOCAL.1 — a LOCAL build produces an Acceptance record in the P0 shape,
judged by an independent check the builder did not control.

This is the LOCAL-tier producer of the canonical Acceptance record defined in
the P0 shared contract (``docs/design/dev-build-deploy-shared-contract.md``
§2). The record carries every field the contract names —
``id`` / ``statement`` / ``check`` / ``frozen`` / ``altitude`` / ``ladder`` —
so a LOCAL build's "done" can be referenced by a later deploy gate (the §4
bridge) and traced to the prime objective.

The load-bearing property (preserved verbatim from both dev-sdlc ODD and
hands-off-loop): the verdict is **independent of the producer**. This module
NEVER lets a caller assert ``met``; ``met`` is derived solely from RUNNING the
independent ``check``. A check that fails yields an honest negative — never
retried-to-green, never softened. A leak of a frozen criterion is structurally
impossible here because the producer reads the check only to run it, never to
inspect or rewrite it.

Method (the dataclass encoding, the check being a Python callable vs a
subprocess) is the builder's call per the contract §7; the *shape* is the
load-bearing part.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable


# The prime-objective rungs every Acceptance ladders up to
# (``docs/VALUE_PROPOSITION.md`` AC.PO.1 reduce-translation-burden,
# AC.PO.2 add-to-persona-toolkit).
PRIME_OBJECTIVE_LADDER: tuple[str, ...] = ("AC.PO.1", "AC.PO.2")


@dataclass(frozen=True)
class CheckResult:
    """The verdict an independent check returns. ``passed`` is the only
    authority for whether an Acceptance is met; ``detail`` is the
    plain-language evidence carried alongside it (an honest-negative names
    WHY it failed)."""

    passed: bool
    detail: str = ""


# An independent check: a zero-argument callable returning a CheckResult. The
# producer runs it; it does not construct the verdict. The callable is the
# builder's chosen form (a pytest invocation, a subprocess exit code, a probe).
Check = Callable[[], CheckResult]


@dataclass(frozen=True)
class Acceptance:
    """The canonical P0 Acceptance record, produced by a LOCAL build.

    Every field maps to the shared contract §2 table. ``met`` is NOT a
    constructor input a caller can set to a convenient value — it is populated
    only by :func:`produce_acceptance`, which derives it from running the
    independent check. The ``check_fingerprint`` pins the criterion that was
    run so a later gate can confirm the same criterion (frozen-unseen)."""

    id: str
    statement: str
    frozen: bool
    altitude: bool
    ladder: tuple[str, ...]
    met: bool
    detail: str
    check_fingerprint: str

    # Internal guard: instances are minted only through produce_acceptance,
    # so ``met`` always reflects a real check run (never a self-report).
    _minted_by_producer: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        if not self._minted_by_producer:
            raise RuntimeError(
                "Acceptance must be produced via produce_acceptance() so its "
                "verdict comes from an independent check, not a self-report."
            )

    @property
    def is_honest_negative(self) -> bool:
        """A definite 'not met, here is the evidence' is a complete result —
        never retried-to-green (hands-off-loop honest-negative, preserved)."""
        return not self.met and bool(self.detail)


def _fingerprint(statement: str, check: Check) -> str:
    """A stable identity for the criterion that was run, so a downstream gate
    can assert the same Acceptance (the §4 bridge's frozen-criterion check).
    The fingerprint covers the outcome statement + the check's qualified
    identity — it does not require seeing the check's internals."""
    name = getattr(check, "__qualname__", getattr(check, "__name__", repr(check)))
    module = getattr(check, "__module__", "")
    seed = f"{statement}\x00{module}.{name}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def produce_acceptance(
    *,
    id: str,
    statement: str,
    check: Check,
    altitude: bool = False,
    frozen: bool = True,
    ladder: tuple[str, ...] = PRIME_OBJECTIVE_LADDER,
) -> Acceptance:
    """Produce a P0-shape Acceptance by RUNNING the independent *check*.

    The verdict (``met``) is whatever the check returns — the producer cannot
    fabricate it. A passing check yields ``met=True``; a failing check yields
    an honest negative (``met=False`` carrying the check's plain-language
    detail), never a retry. ``frozen`` defaults ``True`` (any dispatched /
    hands-off build's criterion is hash-pinned before any sub-agent sees it);
    ``altitude`` marks the outcome-altitude record per the contract §2.

    Raises ``TypeError`` if *check* is not callable — a non-runnable check
    cannot produce an independent verdict, so refusing is fail-closed."""
    if not callable(check):
        raise TypeError("check must be a callable returning a CheckResult")
    if not isinstance(id, str) or not id:
        raise ValueError("id must be a non-empty scope-descriptive string")
    if not isinstance(statement, str) or not statement:
        raise ValueError("statement must be a non-empty plain-language outcome")

    result = check()
    if not isinstance(result, CheckResult):
        raise TypeError(
            "the independent check must return a CheckResult; got "
            f"{type(result).__name__}"
        )

    return Acceptance(
        id=id,
        statement=statement,
        frozen=frozen,
        altitude=altitude,
        ladder=tuple(ladder),
        met=result.passed,
        detail=result.detail,
        check_fingerprint=_fingerprint(statement, check),
        _minted_by_producer=True,
    )
