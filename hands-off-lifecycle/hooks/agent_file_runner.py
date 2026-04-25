"""Thin CLI runner for ``primary_persona.agent_md.to_agent_md`` under the shared venv.

Added by amendment #37 (hands-off-lifecycle Claude-Code default-agent
wiring). Mirrors the established ``first_run_scaffold_runner.py``
pattern: the first-run helper runs under the system Python interpreter
(stdlib-only), but the renderer in ``primary_persona.agent_md`` lives
in a package whose ``__init__.py`` transitively imports ``pydantic``,
``pyyaml``, ``opentelemetry``, and ``pyee`` — runtime deps installed
only in the shared venv (Phase 3b).

The helper spawns this runner as a subprocess under
``<workspace>/.venv/bin/python``; the runner imports
``primary_persona.PersonaLoader`` + ``primary_persona.agent_md.
to_agent_md``, loads the workspace's primary persona, reads its
``prompt.md`` body, calls the renderer, and writes a JSON envelope to
stdout: ``{"handle": "<handle>", "body": "<rendered>"}``. The handle
is the loader-resolved primary so the stdlib-only caller does not
need to peek at ``personas/`` itself.

Exit codes:
  0 — JSON envelope on stdout (handle + rendered body).
  1 — JSON failure payload on stderr; caller treats as agent-file
      authorship failure → graceful-degradation per AC37.4.
  2 — runner framework failure (bad CLI args, missing adapter
      module).

Stdlib-only up to the import of ``primary_persona``; the adapter
itself brings its own runtime deps from the shared venv.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "pos-v2 agent-file renderer (amendment #37). Loads the "
            "workspace's primary persona and prints the to_agent_md() "
            "body to stdout. The first stdout line is the resolved "
            "handle (so the stdlib-only caller can route the on-disk "
            "write); the rest of stdout is the rendered body."
        ),
    )
    parser.add_argument(
        "--workspace-root",
        required=True,
        help="The pos-v2 workspace root containing the personas/ dir.",
    )
    return parser.parse_args(argv)


def _emit_failure_payload(exc: BaseException) -> None:
    """Serialise the exception as one JSON line on stderr.

    Matches the ``first_run_scaffold_runner.py`` reporting protocol.
    The caller parses this to construct its own diagnostic; the
    traceback is printed in plain text after the JSON for log
    visibility.
    """
    code = getattr(exc, "code", None)
    payload = {
        "type": type(exc).__name__,
        "message": str(exc),
        "code": int(code) if isinstance(code, int) else None,
    }
    sys.stderr.write(json.dumps(payload) + "\n")
    sys.stderr.write("--- agent-file render traceback ---\n")
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    sys.stderr.flush()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    workspace_root = Path(args.workspace_root).resolve()

    try:
        # Late imports so argparse failures report cleanly without
        # requiring the adapter's runtime deps to resolve.
        from primary_persona import PersonaLoader  # type: ignore
        from primary_persona.agent_md import to_agent_md  # type: ignore
    except Exception as e:  # pragma: no cover — environment-dependent
        sys.stderr.write(
            "agent_file_runner: could not import primary_persona.\n"
            "This usually means the shared venv is missing a runtime "
            "dep that primary-persona declares. Reopen claude to "
            "retry; the next session's Phase 3b install will heal.\n"
            f"Import error: {type(e).__name__}: {e}\n"
        )
        return 2

    try:
        loader = PersonaLoader(workspace_root=workspace_root)
        loaded = loader.primary()
        prompt_text: str | None = loaded.prompt_text
        body = to_agent_md(loaded.contract, prompt_text=prompt_text)
    except Exception as e:
        _emit_failure_payload(e)
        return 1

    sys.stdout.write(json.dumps({"handle": loaded.handle, "body": body}))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
