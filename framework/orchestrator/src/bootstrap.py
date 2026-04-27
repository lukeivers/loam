"""Workspace bootstrap loader.

The orchestrator's restart story assumes scope callbacks must be
re-registered on every cold start. Callbacks live in workspace
Python code (a persona handler, a custom observer, a notification
hook), so the orchestrator core cannot hard-code them.

Convention: `~/.pos/bootstrap.py` (path configurable) is a workspace-
authored Python file that exposes a single function:

    def register(orchestrator) -> None:
        # wire callbacks into the orchestrator's scope runtime,
        # objective tracker, notification channels, etc.

pOS core defines the contract; the workspace authors the file.

Failure posture (Luke's ruling, brief §"Luke's decisions"): on a
missing or erroring bootstrap file, the orchestrator refuses to
start. Matches the primary-persona loader's fail-closed posture.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Callable, Protocol

from .errors import BootstrapError, BootstrapMissing


class _Registerable(Protocol):
    def register(self, orchestrator: object) -> None:  # pragma: no cover - structural
        ...


def load_and_register(bootstrap_path: Path, orchestrator: object) -> None:
    """Import the workspace bootstrap and run its `register()` hook.

    Raises:
      BootstrapMissing: bootstrap_path does not exist.
      BootstrapError: import failed, `register` is missing, or the
        call to `register` raised.
    """
    if not bootstrap_path.exists():
        raise BootstrapMissing(
            f"workspace bootstrap not found at {bootstrap_path}; "
            "orchestrator refuses to start (fail-closed)"
        )

    module_name = f"_pos_workspace_bootstrap_{abs(hash(str(bootstrap_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, bootstrap_path)
    if spec is None or spec.loader is None:
        raise BootstrapError(
            f"could not load bootstrap spec from {bootstrap_path}"
        )

    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules so a module-level importlib machinery
    # (e.g. dataclass module discovery) can find it.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise BootstrapError(
            f"bootstrap import failed: {e}\n{traceback.format_exc()}"
        ) from e

    register_fn: Callable[[object], None] | None = getattr(
        module, "register", None
    )
    if register_fn is None or not callable(register_fn):
        raise BootstrapError(
            f"bootstrap at {bootstrap_path} must define "
            "`def register(orchestrator) -> None`"
        )
    try:
        register_fn(orchestrator)
    except Exception as e:
        raise BootstrapError(
            f"bootstrap register() raised: {e}\n{traceback.format_exc()}"
        ) from e
