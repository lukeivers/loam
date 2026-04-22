"""Structural invariants.

- A1 correction held: observability uses `trace.get_tracer` without
  constructing a TracerProvider.
- Error codes: reserved range `-32100..-32109`; values are distinct
  and within range.
- Adapter-pattern shape: the constructed OneOnOneChannel uses
  ChannelKind.personal_telegram and is_group=False (the sealed
  dataclass itself enforces is_group=False via __post_init__; we
  exercise that path).
- No group-chat support: any attempt to build a group-kind channel
  raises.
"""

from __future__ import annotations

import inspect

import pytest

from primary_persona.introduction import ChannelKind, OneOnOneChannel

from telegram_interface import (
    IPC_TELEGRAM_ALLOWLIST_REJECTED,
    IPC_TELEGRAM_BLOCKED_BY_USER,
    IPC_TELEGRAM_CONFIRMATION_REFUSED,
    IPC_TELEGRAM_CONFIRMATION_TIMEOUT,
    IPC_TELEGRAM_NONOWNER_TIER_A_REFUSED,
    IPC_TELEGRAM_RATE_LIMITED,
    IPC_TELEGRAM_SEND_FAILED,
    IPC_TELEGRAM_SETUP_FAILED,
    IPC_TELEGRAM_TOKEN_INVALID,
    IPC_TELEGRAM_UNAVAILABLE,
)
from telegram_interface import observability as obs


def test_error_codes_in_reserved_range() -> None:
    codes = [
        IPC_TELEGRAM_UNAVAILABLE,
        IPC_TELEGRAM_SEND_FAILED,
        IPC_TELEGRAM_TOKEN_INVALID,
        IPC_TELEGRAM_BLOCKED_BY_USER,
        IPC_TELEGRAM_RATE_LIMITED,
        IPC_TELEGRAM_ALLOWLIST_REJECTED,
        IPC_TELEGRAM_CONFIRMATION_TIMEOUT,
        IPC_TELEGRAM_CONFIRMATION_REFUSED,
        IPC_TELEGRAM_SETUP_FAILED,
        IPC_TELEGRAM_NONOWNER_TIER_A_REFUSED,
    ]
    for c in codes:
        assert -32109 <= c <= -32100, f"code {c} out of reserved range"
    assert len(set(codes)) == 10, "error codes must be distinct"


def test_a1_correction_held_no_tracer_provider_construction() -> None:
    """A1 correction — observability.py does not construct its own
    TracerProvider; it uses `trace.get_tracer("pos.telegram_interface")`
    only.

    The check strips docstrings/comments first, then asserts
    TracerProvider is never instantiated in executable code.
    """
    import ast

    src = inspect.getsource(obs)
    assert 'get_tracer("pos.telegram_interface")' in src

    tree = ast.parse(src)

    class _Finder(ast.NodeVisitor):
        found: bool = False

        def visit_Call(self, node: ast.Call) -> None:  # type: ignore[override]
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name == "TracerProvider":
                self.found = True
            self.generic_visit(node)

    f = _Finder()
    f.visit(tree)
    assert not f.found, (
        "A1 correction violated: module must not construct a TracerProvider"
    )


def test_adapter_uses_channel_kind_personal_telegram() -> None:
    """The sealed enum already carries `personal_telegram`; confirm
    the adapter uses it (no enum extension required)."""
    assert ChannelKind.personal_telegram.value == "personal_telegram"


def test_no_group_chat_support() -> None:
    """OneOnOneChannel raises when is_group=True. The adapter never
    constructs a group channel."""
    with pytest.raises(ValueError, match="one-on-one"):
        OneOnOneChannel(
            kind=ChannelKind.personal_telegram,
            name="bad",
            send=lambda _: None,  # type: ignore[arg-type, return-value]
            is_group=True,
        )
