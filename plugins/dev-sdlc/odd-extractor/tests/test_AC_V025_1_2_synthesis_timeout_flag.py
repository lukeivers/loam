"""AC.V025-1.2 — Configurable synthesis subprocess timeout.

Per v0.2.5.1 corrective (F-TIMEOUT closure): the synthesis-subprocess
timeout is configurable via the ``--synthesis-timeout`` CLI flag and
the ``timeout_seconds`` kwarg on ``build_default_synthesis_client``.
Default raised from 180s → 600s (Eric's rd-automation run hit the
180s ceiling).

Four unit tests cover the surface:

- ``test_shim_ctor_default_timeout_is_600s``
  — the post-corrective default reflects the bump from 180s to 600s.
- ``test_shim_ctor_accepts_timeout_seconds_kwarg``
  — explicit kwarg propagates to the stored attribute.
- ``test_build_default_synthesis_client_threads_timeout_seconds``
  — the builder forwards the kwarg to the constructor.
- ``test_cli_parses_synthesis_timeout_flag``
  — argparse accepts the new flag and produces a Namespace with
  ``synthesis_timeout=<float>``.
- ``test_cli_help_text_mentions_synthesis_timeout``
  — `loam odd-extract --help` stdout contains the new flag's help
  text (verified via the standalone main() entry point).
"""

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout

import pytest


def test_shim_ctor_default_timeout_is_600s() -> None:
    """The default ctor timeout reflects the v0.2.5.1 bump."""
    pytest.importorskip("loam_odd_extractor.claude_print_synthesis_client")
    from loam_odd_extractor.claude_print_synthesis_client import (
        ClaudePrintAnthropicShimClient,
    )
    import shutil

    if shutil.which("claude") is None:
        pytest.skip(
            "ClaudePrintAnthropicShimClient ctor requires claude on PATH"
        )
    client = ClaudePrintAnthropicShimClient()
    assert client._timeout_seconds == 600.0, (
        f"Default timeout must be 600.0s post-v0.2.5.1; got "
        f"{client._timeout_seconds}"
    )


def test_shim_ctor_accepts_timeout_seconds_kwarg() -> None:
    """Explicit kwarg propagates to the stored attribute."""
    from loam_odd_extractor.claude_print_synthesis_client import (
        ClaudePrintAnthropicShimClient,
    )
    import shutil

    if shutil.which("claude") is None:
        pytest.skip(
            "ClaudePrintAnthropicShimClient ctor requires claude on PATH"
        )
    client = ClaudePrintAnthropicShimClient(timeout_seconds=42.0)
    assert client._timeout_seconds == 42.0


def test_build_default_synthesis_client_threads_timeout_seconds() -> None:
    """The builder forwards the timeout_seconds kwarg to the ctor."""
    from loam_odd_extractor.claude_print_synthesis_client import (
        build_default_synthesis_client,
    )
    import shutil

    if shutil.which("claude") is None:
        pytest.skip("build_default_synthesis_client requires claude on PATH")
    # Explicit 90.0 — must propagate.
    client = build_default_synthesis_client(timeout_seconds=90.0)
    assert client._timeout_seconds == 90.0
    # None → ctor default (600.0).
    client_default = build_default_synthesis_client(timeout_seconds=None)
    assert client_default._timeout_seconds == 600.0


def test_cli_parses_synthesis_timeout_flag() -> None:
    """argparse parses --synthesis-timeout into Namespace.synthesis_timeout."""
    from loam_odd_extractor.cli import build_odd_extract_subcommand

    parser = argparse.ArgumentParser(prog="test")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)
    ns = parser.parse_args(
        [
            "odd-extract",
            "/tmp/some-repo",
            "--synthesis-timeout",
            "1200",
        ]
    )
    assert hasattr(ns, "synthesis_timeout"), (
        "Namespace must carry .synthesis_timeout attribute"
    )
    assert ns.synthesis_timeout == 1200.0
    # Default (no flag) → None.
    ns_default = parser.parse_args(["odd-extract", "/tmp/some-repo"])
    assert ns_default.synthesis_timeout is None


def test_cli_help_text_mentions_synthesis_timeout() -> None:
    """--help stdout contains the new flag's help text."""
    from loam_odd_extractor.cli import build_odd_extract_subcommand

    parser = argparse.ArgumentParser(prog="test")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)

    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            parser.parse_args(["odd-extract", "--help"])
        except SystemExit:
            pass
    help_text = buf.getvalue()
    assert "--synthesis-timeout" in help_text, (
        f"--help must mention --synthesis-timeout; got: {help_text[:500]}"
    )
    assert "AC.V025-1.2" in help_text, (
        "--help must reference the AC ID for traceability"
    )
