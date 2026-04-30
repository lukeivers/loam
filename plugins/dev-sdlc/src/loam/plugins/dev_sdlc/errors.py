"""Plugin-typed errors.

Each error carries enough structured context that the persona's
exception-handling path can translate the failure into natural-
language guidance for the user (per plan §4 AC.OSS-M6.4 + §8 risk
#3 mitigation).
"""

from __future__ import annotations


class DevSdlcError(Exception):
    """Base class for Dev/SDLC plugin errors."""


class ProjectNotFoundError(DevSdlcError):
    """Raised when a project slug doesn't resolve to any tracked project."""

    def __init__(self, slug: str) -> None:
        super().__init__(f"project not found: {slug!r}")
        self.slug = slug


class ProjectAlreadyExistsError(DevSdlcError):
    """Raised when `start_project` is called for a slug that already
    exists in the workspace."""

    def __init__(self, slug: str) -> None:
        super().__init__(f"project already exists: {slug!r}")
        self.slug = slug


class StageGateFailedError(DevSdlcError):
    """Raised when a stage advance fails the structural gate
    (AC.OSS-M6.4)."""

    # Stable string codes — the persona's exception handler matches on
    # `reason` to translate to user-facing prose. Adding new reason
    # codes is additive (any unknown reason falls through to a default
    # "gate failed" message).
    REASON_ARTEFACT_NOT_FOUND = "artefact_not_found"
    REASON_NO_OBJECTIVE = "no_objective"
    REASON_NO_AC = "no_ac"
    REASON_TERMINAL_STAGE = "terminal_stage"

    def __init__(self, *, reason: str, project: str, stage: str) -> None:
        super().__init__(
            f"stage gate failed for {project!r} at stage {stage!r}: {reason}"
        )
        self.reason = reason
        self.project = project
        self.stage = stage


class TerminalStageError(DevSdlcError):
    """Raised when `advance_stage` is called on a project whose stage
    is already the last in the methodology's chain."""

    def __init__(self, slug: str, stage: str) -> None:
        super().__init__(
            f"project {slug!r} is at terminal stage {stage!r}; cannot advance"
        )
        self.slug = slug
        self.stage = stage


class UnsupportedMethodologyError(DevSdlcError):
    """Raised when a methodology string is not one of the registered
    methodologies (`odd`, `tdd`, `bdd`, `adhoc`)."""

    def __init__(self, methodology: str) -> None:
        super().__init__(
            f"unsupported methodology: {methodology!r}; "
            f"supported: odd, tdd, bdd, adhoc"
        )
        self.methodology = methodology
