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

"""Workspace-local ``.mcp.json`` writer (Amendment #47).

Writes ``<workspace>/.mcp.json`` registering the per-workspace
memory-graphiti FastMCP service as an MCP server under the
streamable-HTTP transport. Claude Code reads this file at
session-load to discover and bind the per-workspace memory-system's
MCP tools, making them callable as ``mcp__memory-graphiti__<tool>``
during turns.

The file shape follows Claude Code's ``.mcp.json`` schema (per
``https://code.claude.com/docs/en/mcp`` §4.3 — project-scoped
``mcpServers`` map). The literal JSON value for the streamable-HTTP
transport's ``type`` field is ``"http"`` (the CLI flag value
``"streamable-http"`` is a CLI-only spelling and does NOT appear in
the JSON). FastMCP serves the streamable-HTTP transport at the
default mount path ``/mcp`` (verified against
``mcp.server.fastmcp.FastMCP().settings.streamable_http_path``).

The ``(host, port)`` pair is supplied by ``first_run_scaffold``,
which resolves it from the workspace's ``<pos_root>/memory.yaml``
via ``_resolve_memory_host_port`` (the same value already feeding
the launchd plist's ``EnvironmentVariables`` dict — amendment #29).

Behaviour summary (per AC47.1 / AC47.2 / AC47.3):

- AC47.1: fresh-clone first-run writes the file with one
  ``mcpServers`` entry (``memory-graphiti``).
- AC47.2: re-running on a workspace whose ``.mcp.json`` already
  contains user-added entries deep-merges the ``memory-graphiti``
  entry without removing or modifying user entries.
- AC47.3: write failure (malformed pre-existing JSON, permission
  denied, etc.) is fail-soft — the writer surfaces a structured
  ``MCPJsonWriteResult`` and the scaffold proceeds.

Atomic write via ``.tmp`` + ``os.rename`` mirrors amendment #37's
``agent_file_authoring`` pattern. Equal-content idempotent re-run
skips the rename (no mtime churn) — mirrors amendment #36's
persona-directory and #37's agent-file idempotency contracts.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---- AC47.1 / AC47.2 constants ---------------------------------------


# Server name registered under ``mcpServers`` (umbrella plan §4b
# objective + D-build.3). Tools become callable as
# ``mcp__memory-graphiti__<tool>`` per Claude Code convention.
MEMORY_GRAPHITI_SERVER_NAME = "memory-graphiti"

# Workspace-local file Claude Code reads at session-load (per
# Claude Code MCP scope table — project-scoped servers).
MCP_JSON_FILENAME = ".mcp.json"

# FastMCP's default streamable-HTTP mount path. Confirmed against
# ``mcp.server.fastmcp.FastMCP().settings.streamable_http_path``.
# The memory-system service constructs ``FastMCP(...)`` without
# overriding ``streamable_http_path``, so the default applies.
STREAMABLE_HTTP_PATH = "/mcp"

# Reserved literal value for the JSON ``type`` field per Claude
# Code MCP docs §4.3. The CLI flag value ``"streamable-http"``
# does NOT appear in the JSON.
_TRANSPORT_TYPE = "http"


# ---- AC47.1 / AC47.3 result dataclass --------------------------------


@dataclass(frozen=True)
class MCPJsonWriteResult:
    """Structured outcome of a ``write_mcp_json`` invocation.

    AC47.1 / AC47.3: ``wrote`` is True iff the file content
    changed; False on idempotent no-op or skipped failure.
    ``reason`` carries one of:

    - ``"fresh_write"`` — file did not exist; written from scratch.
    - ``"merged"`` — file existed; merged + written.
    - ``"already_current"`` — file existed and content was already
      byte-equal to the merged target; no write performed.
    - ``"skipped_malformed_existing"`` — pre-existing file failed
      JSON parse or its top-level was not a dict; skipped to
      preserve user content.
    - ``"skipped_io_error"`` — IO/permissions error during write;
      scaffold continues, session degrades.
    - ``"skipped_v0_1_0_no_graphiti"`` — FBE.7 (v0.1.0 foldback):
      the scaffold doesn't invoke the writer at v0.1.0 because the
      M-FBM file-based memory substrate replaced the graphiti runtime
      path. ``path`` is ``None`` for this reason; M-GMP restores the
      writer post-v0.1.0.

    ``path`` is the absolute path to the target ``.mcp.json`` — or
    ``None`` when the writer was not invoked (FBE.7
    ``skipped_v0_1_0_no_graphiti``).
    """

    wrote: bool
    reason: str
    path: Path | None


# ---- AC47.1 pure-function builders -----------------------------------


def build_memory_graphiti_entry(*, host: str, port: int) -> dict[str, Any]:
    """Return the JSON entry for the memory-graphiti MCP server.

    Pure; no IO. Shape per Claude Code MCP docs §4.3:
    ``{"type": "http", "url": "http://<host>:<port>/mcp"}``. The
    URL composes ``host`` + ``port`` + the FastMCP default
    streamable-HTTP mount path. AC47.1 checks the URL's port
    matches the workspace's allocated memory-sidecar port; this
    function is the constructor.
    """
    url = f"http://{host}:{port}{STREAMABLE_HTTP_PATH}"
    return {"type": _TRANSPORT_TYPE, "url": url}


def merge_mcp_json(
    existing: dict[str, Any], *, host: str, port: int
) -> dict[str, Any]:
    """Return a deep-merged copy of ``existing`` with the
    memory-graphiti entry installed under ``mcpServers``.

    Pure; no IO. AC47.2 contract:

    - Other top-level keys in ``existing`` are preserved.
    - Other entries under ``mcpServers`` are preserved.
    - The ``memory-graphiti`` entry is set to the current
      ``build_memory_graphiti_entry`` output (overwriting any
      stale value, e.g. an older port — the framework owns the
      identity of this key).

    The input ``existing`` is not mutated; a shallow-copied
    top-level dict + a shallow-copied ``mcpServers`` dict are
    returned so the caller can write the result without the
    original surface seeing the mutation.
    """
    # AC47.2: shallow-copy preserves user top-level keys by
    # reference (lists/dicts the user owns).
    merged: dict[str, Any] = dict(existing)
    servers_in = existing.get("mcpServers")
    if isinstance(servers_in, dict):
        servers_out: dict[str, Any] = dict(servers_in)
    else:
        # AC47.1: fresh write OR a malformed prior ``mcpServers``
        # value (non-dict). The malformed-existing case is caught
        # earlier in ``write_mcp_json``; if a caller invokes
        # ``merge_mcp_json`` directly with a non-dict ``mcpServers``
        # value, we still produce a well-formed output rather
        # than re-raise inside a pure function.
        servers_out = {}
    servers_out[MEMORY_GRAPHITI_SERVER_NAME] = build_memory_graphiti_entry(
        host=host, port=port
    )
    merged["mcpServers"] = servers_out
    return merged


# ---- AC47.1 / AC47.2 / AC47.3 IO entrypoint --------------------------


def _serialise(data: dict[str, Any]) -> str:
    """Render a merged dict as the canonical ``.mcp.json`` text.

    Two-space indent + trailing newline matches the format
    Claude Code emits when ``claude mcp add`` writes the file —
    keeps diff churn against hand-edits minimal. Sort keys at the
    top level so re-merges are byte-stable for the idempotent
    no-op check (AC47.1's ``already_current`` reason).
    """
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_mcp_json(
    *, workspace_root: Path, host: str, port: int
) -> MCPJsonWriteResult:
    """Write or deep-merge ``<workspace_root>/.mcp.json``.

    AC47.1: on a fresh workspace (no prior file), writes the JSON
    and returns ``wrote=True, reason="fresh_write"``.

    AC47.2: on a workspace with a pre-existing file, deep-merges
    the memory-graphiti entry and returns ``wrote=True,
    reason="merged"`` (or ``wrote=False, reason="already_current"``
    if the merged content was byte-equal to the on-disk content —
    idempotency).

    AC47.3: on a malformed pre-existing file (parse error or
    non-dict root), returns ``wrote=False,
    reason="skipped_malformed_existing"`` and preserves the user's
    file unmodified. On any IO/permissions failure during write,
    returns ``wrote=False, reason="skipped_io_error"`` and emits a
    diagnostic line to stderr; the scaffold proceeds.

    Atomic write semantics: serialise to a sibling
    ``.mcp.json.<random>.tmp`` file under the same dir, then
    ``os.rename`` into final position. This avoids a torn-file
    state if the write is interrupted mid-flight.
    """
    from ..workspace_paths import mcp_json_path as _mcp_json_path

    workspace_root = Path(workspace_root).resolve()
    target = _mcp_json_path(workspace_root)
    target.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any]
    pre_existed = target.exists()
    if pre_existed:
        # AC47.3 malformed-existing path: parse failures + non-
        # dict roots short-circuit before any write attempt so
        # user content survives.
        try:
            raw = target.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(
                f"workspace-bootstrap: mcp_json_writer skipped — "
                f"could not read {target}: {exc!r}\n"
            )
            return MCPJsonWriteResult(
                wrote=False, reason="skipped_io_error", path=target
            )
        try:
            loaded = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as exc:
            sys.stderr.write(
                f"workspace-bootstrap: mcp_json_writer skipped — "
                f"existing {target} is not valid JSON: {exc!r}\n"
            )
            return MCPJsonWriteResult(
                wrote=False,
                reason="skipped_malformed_existing",
                path=target,
            )
        if not isinstance(loaded, dict):
            sys.stderr.write(
                f"workspace-bootstrap: mcp_json_writer skipped — "
                f"existing {target} top-level is not a JSON object\n"
            )
            return MCPJsonWriteResult(
                wrote=False,
                reason="skipped_malformed_existing",
                path=target,
            )
        existing = loaded
    else:
        existing = {}

    merged = merge_mcp_json(existing, host=host, port=port)
    serialised = _serialise(merged)

    # AC47.1 idempotency-on-equal: byte-equal serialised output
    # vs on-disk content → skip the write to avoid mtime churn.
    if pre_existed:
        try:
            current_bytes = target.read_bytes()
        except OSError:
            current_bytes = b""
        if current_bytes == serialised.encode("utf-8"):
            return MCPJsonWriteResult(
                wrote=False, reason="already_current", path=target
            )

    # AC47.3 IO-failure path: any write failure (permissions, disk
    # full, malformed parent dir) surfaces as a structured result.
    try:
        # Atomic write via .tmp + os.rename in the same dir.
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(target.parent),
            prefix=".mcp.json.",
            suffix=".tmp",
            delete=False,
        ) as fh:
            fh.write(serialised)
            tmp_path = Path(fh.name)
        os.replace(tmp_path, target)
    except OSError as exc:
        sys.stderr.write(
            f"workspace-bootstrap: mcp_json_writer skipped — "
            f"could not write {target}: {exc!r}\n"
        )
        # Best-effort cleanup of the .tmp if it leaked.
        try:
            if "tmp_path" in locals() and tmp_path.exists():  # type: ignore[has-type]
                tmp_path.unlink()  # type: ignore[has-type]
        except OSError:
            pass
        return MCPJsonWriteResult(
            wrote=False, reason="skipped_io_error", path=target
        )

    reason = "merged" if pre_existed else "fresh_write"
    return MCPJsonWriteResult(wrote=True, reason=reason, path=target)
