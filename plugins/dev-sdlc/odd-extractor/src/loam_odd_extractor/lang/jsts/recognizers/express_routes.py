"""Express-route recognizer.

Per AC.JSTS.2 — detects Express route declarations:

- ``app.get('/path', handler)``
- ``app.post('/path', handler)``
- ``app.put/delete/patch/use/all/head/options(...)``
- ``router.get/post/...(...)`` (Express Router pattern)
- ``server.<method>(...)`` (alternative naming used in Eric's stack)

Each route emits one PLAUSIBLE-band :class:`BandedAC` per AC.JSTS.5.
Middleware functions inserted between the path and final handler are
captured in the AC text (the auth-middleware heuristic in
:mod:`heuristic_inferences` consumes this).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from ..._common.slugs import file_slug, slugify
from .._ast_utils import (
    call_callee_object,
    call_first_arg_string,
    find_call_expressions,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


# Express HTTP-verb method names (lowercased). Includes router +
# server + app receivers.
_EXPRESS_VERBS = frozenset(
    {
        "get", "post", "put", "delete", "patch",
        "options", "head", "all", "use",
    }
)

# Common receiver-object names for Express. Heuristic — covers
# `app`, `router`, `server`, `api`, plus camel/PascalCase variants.
_EXPRESS_RECEIVERS = frozenset(
    {
        "app", "router", "server", "api",
        "App", "Router", "Server", "Api",
    }
)


def recognize_express_routes(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every Express route declared
    in the file.

    Detection:
    - The call's callee is a member expression ``X.<verb>(...)``.
    - ``X`` is one of the recognized Express-receiver names.
    - ``<verb>`` is one of the recognized HTTP verbs.

    The first string argument is treated as the route path (e.g.,
    ``'/users'``).
    """
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    seen: set[str] = set()

    for call_node in find_call_expressions(tree.root_node):
        obj, prop = call_callee_object(call_node, source)
        if obj is None or prop is None:
            continue
        if prop.lower() not in _EXPRESS_VERBS:
            continue
        # Receiver match: exact-or-suffix (e.g., `userRouter` ends
        # in `Router`). Lower-case stem-suffix check captures common
        # patterns like `apiRouter`, `userApp`.
        receiver_match = (
            obj in _EXPRESS_RECEIVERS
            or any(
                obj.endswith(r) or obj.endswith(r.lower())
                for r in _EXPRESS_RECEIVERS
            )
        )
        if not receiver_match:
            continue

        path_str = call_first_arg_string(call_node, source)
        if path_str is None:
            # use(middleware) without a path — common pattern; we
            # still record it as a middleware mount.
            path_str = "(middleware-mount)"

        # Skip mount-only `app.use(middleware)` calls without a path
        # leading character (these are typically global middleware).
        if prop.lower() == "use" and not path_str.startswith("/") and path_str != "(middleware-mount)":
            # `app.use(express.json())` — treat as middleware mount.
            path_str = f"(use:{path_str[:40]})"

        line = node_line(call_node)
        # Slug includes path + verb + file for cross-slice uniqueness.
        path_slug = slugify(path_str) or "root"
        ac_id = (
            f"AC.JSTS.express.{prop.lower()}.{path_slug}.{fslug}"
        )
        # Dedup within a single file — the same route declared
        # multiple times gets the suffix-line.
        if ac_id in seen:
            ac_id = f"{ac_id}.line{line}"
        seen.add(ac_id)

        # Collect middleware names (subsequent identifier args
        # before the final handler). Useful for the auth-middleware
        # heuristic in heuristic_inferences.
        from .._ast_utils import call_arguments

        all_args = call_arguments(call_node, source)
        # Drop the first arg (path string) and last arg (handler);
        # middleware sits between.
        middlewares: list[str] = []
        if len(all_args) >= 3:
            for mid in all_args[1:-1]:
                # Strip any function-expression / arrow-function
                # mid-arguments — they're inline handlers, not
                # named middleware.
                stripped = mid.strip()
                if "=>" in stripped or stripped.startswith("function"):
                    continue
                if stripped.startswith("(") or stripped.startswith("{"):
                    continue
                # Limit to bare identifier-like names (no calls).
                if "(" not in stripped and ")" not in stripped:
                    middlewares.append(stripped)

        text_parts = [
            f"Express route {prop.upper()} {path_str}",
        ]
        if middlewares:
            text_parts.append(
                f"with middleware [{', '.join(middlewares)}]"
            )

        out.append(
            BandedAC(
                ac_id=ac_id,
                text=" ".join(text_parts),
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=[f"{file_rel}:{line}"],
                    repo_sha=repo_sha,
                ),
                backing_files=[file_rel],
            )
        )

    return out
