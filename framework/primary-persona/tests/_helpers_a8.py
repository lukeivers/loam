"""Shared test helpers for amendment #52 (A8 R1) — dispatch wrapper.

Provides a stub `IPCClient` that records calls, a workspace-root
fixture builder that seeds the orchestrator socket sentinel + the
ambient-objective seed, and an Agent-runner stub.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class StubIPCClient:
    """Minimal in-memory IPCClient stub.

    Records every `call(...)` invocation in `self.calls`. The
    `set_response(method, value)` / `set_exception(method, exc)`
    methods configure per-method outcomes. Connect / close are
    no-ops; the wrapper's `await client.connect()` /
    `await client.close()` calls succeed.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._responses: dict[str, Any] = {}
        self._exceptions: dict[str, BaseException] = {}
        self._connected = False
        self._closed = False
        self.connect_exc: BaseException | None = None

    def __init_subclass__(cls, **kwargs):  # pragma: no cover
        super().__init_subclass__(**kwargs)

    def __new__(cls, *args, **kwargs):
        # Allow IPCClient(socket_path) shape for monkeypatch swap.
        return super().__new__(cls)

    def __init_with_path__(self, socket_path):  # pragma: no cover
        self.__init__()

    def set_response(self, method: str, value: Any) -> None:
        self._responses[method] = value

    def set_exception(self, method: str, exc: BaseException) -> None:
        self._exceptions[method] = exc

    def set_connect_exception(self, exc: BaseException) -> None:
        self.connect_exc = exc

    async def connect(self) -> None:
        if self.connect_exc is not None:
            raise self.connect_exc
        self._connected = True

    async def close(self) -> None:
        self._closed = True

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> Any:
        params = dict(params or {})
        self.calls.append((method, params))
        if method in self._exceptions:
            raise self._exceptions[method]
        return self._responses.get(method, {})


def build_stub_ipc_client_factory(client: StubIPCClient):
    """Return a callable matching `IPCClient(socket_path)` shape that
    yields `client` regardless of the path argument."""

    def _factory(socket_path):  # noqa: ARG001 — path ignored
        return client

    return _factory


def make_workspace(
    tmp_path: Path,
    *,
    socket_present: bool = True,
    ambient_objective: str | None = "obj-ambient",
) -> Path:
    """Build a workspace root with optional socket sentinel and
    ambient-objective seed."""
    root = tmp_path / "ws"
    pos_dir = root / ".pos"
    pos_dir.mkdir(parents=True, exist_ok=True)
    if socket_present:
        # The socket file is just touched — the wrapper checks
        # `socket_path.exists()`. The actual connect is monkeypatched.
        (pos_dir / "orchestrator.sock").touch()
    if ambient_objective is not None:
        (pos_dir / "ambient-objective-id").write_text(ambient_objective)
    return root


async def stub_agent_runner_ok(payload: dict[str, Any]) -> dict[str, Any]:
    """Default agent stub — returns a small token count."""
    return {"result": "ok", "total_tokens": 1234, "payload": payload}


async def stub_agent_runner_no_tokens(
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {"result": "ok"}


def make_agent_runner_raising(exc: BaseException):
    async def _runner(payload):  # noqa: ARG001
        raise exc

    return _runner
