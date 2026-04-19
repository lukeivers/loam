"""Unix-domain-socket JSON-RPC server/client (D3).

Wire format: newline-delimited JSON. Each line is one request or
response envelope.

Request:
    {"id": "<string>", "method": "<name>", "params": {...}}

Response:
    {"id": "<string>", "result": <any>}           (success)
    {"id": "<string>", "error": {"code": <int>, "message": <str>}}

Codes follow JSON-RPC 2.0 conventions loosely:
    -32601 method not found
    -32602 invalid params
    -32603 internal error
    -32000..-32099 application error

Permissions: the socket is created 0600 (user-private) per brief D3.

Single-writer per connection is enforced; a connection lock serialises
writes when multiple handlers reply to the same client in rapid
succession (e.g. awareness pull races heartbeat).
"""

from __future__ import annotations

import asyncio
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable


# Method handler signature: async def handler(params: dict) -> dict
MethodHandler = Callable[[dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class RPCError:
    code: int
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            d["data"] = self.data
        return d


class MethodNotFound(Exception):
    pass


class InvalidParams(Exception):
    pass


class ApplicationError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


class IPCServer:
    """Async Unix-socket server that dispatches JSON-RPC to handlers."""

    def __init__(
        self,
        socket_path: Path,
        *,
        socket_mode: int = 0o600,
    ) -> None:
        self._socket_path = Path(socket_path)
        self._socket_mode = socket_mode
        self._handlers: dict[str, MethodHandler] = {}
        self._server: asyncio.base_events.Server | None = None
        self._clients: set[asyncio.StreamWriter] = set()

    @property
    def socket_path(self) -> Path:
        return self._socket_path

    def register(self, method: str, handler: MethodHandler) -> None:
        self._handlers[method] = handler

    async def start(self) -> None:
        # Clean up orphan socket files from a previous non-graceful
        # exit — brief D3: "orphaned socket files are removed on
        # startup."
        try:
            if self._socket_path.exists() or self._socket_path.is_symlink():
                self._socket_path.unlink()
        except FileNotFoundError:
            pass
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)

        self._server = await asyncio.start_unix_server(
            self._handle_client, path=str(self._socket_path)
        )
        # Tighten permissions.
        os.chmod(str(self._socket_path), self._socket_mode)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for w in list(self._clients):
            try:
                w.close()
            except Exception:
                pass
        self._clients.clear()
        try:
            if self._socket_path.exists():
                self._socket_path.unlink()
        except FileNotFoundError:
            pass

    def verify_permissions(self) -> int:
        """Return the current mode bits on the socket (mask 0o777).
        Useful for assertions in tests."""
        st = os.stat(str(self._socket_path))
        return stat.S_IMODE(st.st_mode)

    # -- connection + protocol --------------------------------------

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._clients.add(writer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    req = json.loads(line.decode("utf-8"))
                except Exception as e:
                    await self._write_error(writer, None, -32700, f"parse error: {e}")
                    continue
                await self._dispatch(writer, req)
        except (asyncio.CancelledError, ConnectionResetError):
            pass
        except Exception:
            # Never kill the server on a single bad client.
            pass
        finally:
            self._clients.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _dispatch(
        self,
        writer: asyncio.StreamWriter,
        req: dict[str, Any],
    ) -> None:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        if not isinstance(method, str):
            await self._write_error(writer, req_id, -32600, "invalid request")
            return
        handler = self._handlers.get(method)
        if handler is None:
            await self._write_error(writer, req_id, -32601, f"method not found: {method}")
            return
        if not isinstance(params, dict):
            await self._write_error(writer, req_id, -32602, "params must be object")
            return
        try:
            result = await handler(params)
        except MethodNotFound as e:
            await self._write_error(writer, req_id, -32601, str(e))
        except InvalidParams as e:
            await self._write_error(writer, req_id, -32602, str(e))
        except ApplicationError as e:
            await self._write_error(writer, req_id, e.code, str(e), data=e.data)
        except Exception as e:
            await self._write_error(writer, req_id, -32603, f"internal: {e}")
        else:
            await self._write_result(writer, req_id, result)

    async def _write_result(
        self,
        writer: asyncio.StreamWriter,
        req_id: Any,
        result: Any,
    ) -> None:
        body = json.dumps({"id": req_id, "result": result}) + "\n"
        writer.write(body.encode("utf-8"))
        try:
            await writer.drain()
        except Exception:
            pass

    async def _write_error(
        self,
        writer: asyncio.StreamWriter,
        req_id: Any,
        code: int,
        message: str,
        *,
        data: Any = None,
    ) -> None:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        body = json.dumps({"id": req_id, "error": error}) + "\n"
        writer.write(body.encode("utf-8"))
        try:
            await writer.drain()
        except Exception:
            pass


class IPCClient:
    """Minimal async JSON-RPC client — used in tests and by the
    peer session for awareness pulls."""

    def __init__(self, socket_path: Path) -> None:
        self._socket_path = Path(socket_path)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._counter = 0
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_unix_connection(
            path=str(self._socket_path)
        )

    async def close(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> Any:
        assert self._writer is not None and self._reader is not None, "connect first"
        async with self._lock:
            self._counter += 1
            req_id = f"c{self._counter}"
            body = json.dumps(
                {"id": req_id, "method": method, "params": params or {}}
            ) + "\n"
            self._writer.write(body.encode("utf-8"))
            await self._writer.drain()
            line_future = self._reader.readline()
            line = (
                await asyncio.wait_for(line_future, timeout)
                if timeout is not None
                else await line_future
            )
        if not line:
            raise ConnectionError("server closed connection")
        resp = json.loads(line.decode("utf-8"))
        if "error" in resp:
            err = resp["error"]
            raise ApplicationError(
                int(err.get("code", -32603)),
                str(err.get("message", "unknown")),
                err.get("data"),
            )
        return resp.get("result")
