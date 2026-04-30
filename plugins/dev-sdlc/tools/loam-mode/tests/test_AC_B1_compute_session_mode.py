"""Sub-plan B — AC.B1.

Mode-selector reads ``dev_intent`` from the workspace-local
resolver. ``compute_session_mode(dev_intent_value)`` returns
``"dev"`` iff the input is ``"yes"``, else ``"user"`` (the absent /
unknown / ``"no"`` cases all map to ``"user"`` per locked owner
ruling D-MASTER.4).
"""

from __future__ import annotations

from pathlib import Path

from loam_mode.session_start import (
    compute_session_mode,
    read_dev_intent_safe,
)


def test_AC_B1_compute_session_mode_yes_returns_dev() -> None:
    assert compute_session_mode("yes") == "dev"


def test_AC_B1_compute_session_mode_no_returns_user() -> None:
    assert compute_session_mode("no") == "user"


def test_AC_B1_compute_session_mode_absent_returns_user() -> None:
    assert compute_session_mode("absent") == "user"


def test_AC_B1_compute_session_mode_none_returns_user() -> None:
    """Per AC.B1 + AC.B5 fail-soft: any non-yes input maps to user."""
    assert compute_session_mode(None) == "user"


def test_AC_B1_compute_session_mode_unexpected_returns_user() -> None:
    """Defensive: unknown tokens default to user mode."""
    assert compute_session_mode("maybe") == "user"
    assert compute_session_mode("") == "user"


def test_AC_B1_read_dev_intent_safe_yes(tmp_path: Path) -> None:
    """Fixture workspace whose primary contract has ``dev_intent: yes``
    → reader returns ``"yes"``."""
    (tmp_path / "workspace" / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "workspace" / "personas" / "primary" / "contract.yaml").write_text(
        "handle: primary\nis_primary: true\ndev_intent: yes\n",
        encoding="utf-8",
    )
    assert read_dev_intent_safe(tmp_path) == "yes"


def test_AC_B1_read_dev_intent_safe_no(tmp_path: Path) -> None:
    (tmp_path / "workspace" / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "workspace" / "personas" / "primary" / "contract.yaml").write_text(
        "handle: primary\nis_primary: true\ndev_intent: no\n",
        encoding="utf-8",
    )
    assert read_dev_intent_safe(tmp_path) == "no"


def test_AC_B1_read_dev_intent_safe_absent(tmp_path: Path) -> None:
    """No personas dir → ``"absent"``."""
    assert read_dev_intent_safe(tmp_path) == "absent"


def test_AC_B1_compute_session_mode_chained_with_reader(
    tmp_path: Path,
) -> None:
    """End-to-end: dev_intent on disk → reader → compute → mode.
    AC.B1 is satisfiable as a pipeline; this smoke-tests the chain."""
    (tmp_path / "workspace" / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "workspace" / "personas" / "primary" / "contract.yaml").write_text(
        "handle: primary\nis_primary: true\ndev_intent: yes\n",
        encoding="utf-8",
    )
    intent = read_dev_intent_safe(tmp_path)
    mode = compute_session_mode(intent)
    assert mode == "dev"
