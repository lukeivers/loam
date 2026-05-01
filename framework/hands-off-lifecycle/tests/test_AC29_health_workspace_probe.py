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

"""Amendment #29 AC29.5 probe-side — phase-4b verifies workspace
identity on /health responses.

Two outcome-shaped tests:
  * mismatched workspace_root → probe reports not-healthy.
  * matching workspace_root → probe reports healthy.

Both tests spin up a stub ``http.server.BaseHTTPRequestHandler`` on
an ephemeral 127.0.0.1 port that returns 200 with a JSON body
containing the configured ``workspace_root`` — exercising the exact
protocol contract the real memory-sidecar obeys.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_helper import _probe_http_with_identity  # noqa: E402


# ---- stub server ----------------------------------------------------


def _make_health_handler(body_workspace_root: str) -> type[BaseHTTPRequestHandler]:
    """Return a handler class that serves ``GET /health`` with a
    JSON body containing the configured ``workspace_root`` value."""

    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (library shape)
            if self.path != "/health":
                self.send_response(404)
                self.end_headers()
                return
            payload = json.dumps(
                {"status": "ok", "workspace_root": body_workspace_root}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt: str, *args: object) -> None:  # noqa: D401
            # Silence stdlib access log; tests capture their own output.
            return

    return _HealthHandler


def _start_server(body_workspace_root: str) -> tuple[HTTPServer, int, threading.Thread]:
    handler_cls = _make_health_handler(body_workspace_root)
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port, thread


def _stop_server(server: HTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


# ---- AC29.5 (probe-side) --------------------------------------------


def test_AC29_5_probe_fails_on_workspace_identity_mismatch() -> None:
    """The stub returns 200 with ``workspace_root=/tmp/beta``; the
    probe is invoked with ``expected_workspace_root=/tmp/alpha``. The
    probe reports not-healthy because the identity does not match."""
    server, port, thread = _start_server(body_workspace_root="/tmp/beta")
    try:
        healthy = _probe_http_with_identity(
            host="127.0.0.1",
            port=port,
            path="/health",
            timeout_s=2.0,
            expected_workspace_root="/tmp/alpha",
        )
    finally:
        _stop_server(server, thread)
    assert healthy is False


def test_AC29_5_probe_succeeds_on_workspace_identity_match() -> None:
    """The stub returns 200 with ``workspace_root=/tmp/alpha``; the
    probe is invoked with ``expected_workspace_root=/tmp/alpha``. The
    probe reports healthy."""
    server, port, thread = _start_server(body_workspace_root="/tmp/alpha")
    try:
        healthy = _probe_http_with_identity(
            host="127.0.0.1",
            port=port,
            path="/health",
            timeout_s=2.0,
            expected_workspace_root="/tmp/alpha",
        )
    finally:
        _stop_server(server, thread)
    assert healthy is True
