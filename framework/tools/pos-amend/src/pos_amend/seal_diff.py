"""Locate + widen the ``allowed_prefixes`` tuple + ``allowed_files`` set
inside a seal-diff test.

Design note: the test files are hand-authored Python with a wide range
of stylistic shapes (multi-line tuples, single-line sets, empty ``set()``
calls, typed + untyped annotations). Rather than rewrite via AST (which
would lose comments and formatting), we locate the named binding,
extract its current literal bracket-balanced, parse the current entries,
union with the new entries, and re-emit a deterministic formatted
literal. Comments adjacent to the binding are preserved by anchoring
replacements strictly on the literal's bracket range.

T7 requires: widen ``allowed_prefixes`` tuple with new entries,
de-duplicated, with new entries sorted alphabetically among themselves
and appended after existing entries (existing order preserved).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


_ASSIGN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<name>allowed_prefixes|allowed_files|allowed)"
    r"(?P<annotation>\s*:\s*[^=]+?)?\s*=\s*(?P<rhs_start>.*)$",
    re.MULTILINE,
)


class BindingNotFound(Exception):
    """Raised when the target binding is absent in the file."""


_OPEN_CLOSE = {"(": ")", "[": "]", "{": "}"}


def _find_literal_span(text: str, start: int) -> tuple[int, int] | None:
    """Find the bracket-balanced span starting at/after *start*.

    Returns ``(start_idx, end_idx)`` such that ``text[start_idx:end_idx]``
    is the full literal including outer brackets. Returns ``None`` if no
    bracket-opening character is found (e.g. ``= set()`` — handled separately).
    """
    # Skip whitespace to find first significant char
    i = start
    while i < len(text) and text[i] in " \t":
        i += 1
    if i >= len(text):
        return None
    opener = text[i]
    if opener not in _OPEN_CLOSE:
        return None
    closer = _OPEN_CLOSE[opener]
    stack = [closer]
    j = i + 1
    while j < len(text) and stack:
        c = text[j]
        # Skip over string literals (handle basic cases; these test files
        # use plain double-quoted strings with no escapes inside the
        # bracket region).
        if c == '"' or c == "'":
            quote = c
            j += 1
            while j < len(text) and text[j] != quote:
                if text[j] == "\\":
                    j += 2
                    continue
                j += 1
            j += 1
            continue
        if c == "#":
            # comment — skip to newline
            while j < len(text) and text[j] != "\n":
                j += 1
            continue
        if c in _OPEN_CLOSE:
            stack.append(_OPEN_CLOSE[c])
            j += 1
            continue
        if c == stack[-1]:
            stack.pop()
            j += 1
            continue
        j += 1
    if stack:
        return None
    return (i, j)


def _parse_literal_entries(literal: str) -> list[str]:
    """Parse the string-entry contents of a tuple/set literal.

    ``set()`` returns []; ``{"a"}`` returns ["a"]; ``("a", "b",)`` returns
    ["a", "b"]. Non-string elements raise ValueError.
    """
    literal = literal.strip()
    if literal == "set()":
        return []
    try:
        value = ast.literal_eval(literal)
    except (ValueError, SyntaxError) as exc:
        raise ValueError(f"cannot parse literal: {literal!r}") from exc
    if isinstance(value, (tuple, set, frozenset, list)):
        entries = list(value)
    else:
        raise ValueError(f"unexpected literal type: {type(value).__name__}")
    for e in entries:
        if not isinstance(e, str):
            raise ValueError(f"non-string entry in literal: {e!r}")
    return list(entries)


def _format_tuple(entries: list[str], indent: str) -> str:
    """Emit a multi-line tuple literal matching the project style."""
    if not entries:
        return "()"
    inner_indent = indent + "    "
    lines = ["("]
    for e in entries:
        lines.append(f'{inner_indent}"{e}",')
    lines.append(f"{indent})")
    return "\n".join(lines)


def _format_set(entries: list[str], indent: str) -> str:
    """Emit a set literal matching the project style.

    Short sets inline on one line to match the hand-authored shape;
    longer sets break multi-line.
    """
    if not entries:
        return "set()"
    single = "{" + ", ".join(f'"{e}"' for e in entries) + "}"
    if len(single) <= 80:
        return single
    inner_indent = indent + "    "
    lines = ["{"]
    for e in entries:
        lines.append(f'{inner_indent}"{e}",')
    lines.append(f"{indent}}}")
    return "\n".join(lines)


def _locate_binding(text: str, name: str) -> tuple[re.Match, int, int] | None:
    """Find the assignment for *name* in *text* and return
    ``(match, literal_start, literal_end)``.

    ``match`` is the assignment's regex match (indent/name/annotation).
    ``literal_start`` / ``literal_end`` are the span of the RHS literal
    including its outer brackets, or for ``set()`` the span of ``set()``.
    """
    for m in _ASSIGN_RE.finditer(text):
        if m.group("name") != name:
            continue
        rhs_start_idx = m.start("rhs_start")
        rhs_text = text[rhs_start_idx:]
        # Handle `set()` specially — not bracketed as {...}.
        stripped = rhs_text.lstrip(" \t")
        if stripped.startswith("set()"):
            ws = len(rhs_text) - len(stripped)
            return m, rhs_start_idx + ws, rhs_start_idx + ws + len("set()")
        span = _find_literal_span(text, rhs_start_idx)
        if span is None:
            continue
        return m, span[0], span[1]
    return None


def read_entries(path: Path, name: str) -> list[str]:
    """Return the current entries in ``<name>`` binding within *path*."""
    text = path.read_text(encoding="utf-8")
    loc = _locate_binding(text, name)
    if loc is None:
        raise BindingNotFound(f"{path}: {name!r} binding not found")
    _m, start, end = loc
    return _parse_literal_entries(text[start:end])


def _insert_binding_after(
    text: str, anchor_name: str, new_name: str, new_literal: str, indent: str
) -> str | None:
    """Insert ``<indent><new_name> = <new_literal>`` immediately after the
    line containing ``<anchor_name> = ...`` (or its multi-line literal's
    closing bracket).

    Returns the new text or None if the anchor is absent. The inserted
    line uses the anchor's literal bracket range to find insertion point.
    """
    for m in _ASSIGN_RE.finditer(text):
        if m.group("name") != anchor_name:
            continue
        rhs_start_idx = m.start("rhs_start")
        rhs_text = text[rhs_start_idx:]
        stripped = rhs_text.lstrip(" \t")
        if stripped.startswith("set()"):
            ws = len(rhs_text) - len(stripped)
            end = rhs_start_idx + ws + len("set()")
        else:
            span = _find_literal_span(text, rhs_start_idx)
            if span is None:
                continue
            end = span[1]
        # Find the newline after the closing bracket
        nl = text.find("\n", end)
        if nl == -1:
            nl = len(text)
        insertion = f"\n{indent}{new_name} = {new_literal}"
        return text[:nl] + insertion + text[nl:]
    return None


def _insert_entries_before_close(
    text: str, start: int, end: int, additions: list[str], indent: str, mode: str
) -> str:
    """Insert *additions* into the literal at ``text[start:end]`` by
    placing them on their own lines immediately before the closing
    bracket. Preserves all existing whitespace and comments inside the
    literal.

    Handles three shapes:
      - multi-line literal ending ``\\n<indent>)`` or ``<indent>}``
      - single-line literal ``("a",)`` / ``{"a"}``
      - ``set()`` — replaced with a synthesized set literal
    """
    literal = text[start:end]
    stripped = literal.strip()
    inner_indent = indent + "    "
    if stripped == "set()":
        # Synthesize a new set literal with the additions.
        if mode == "set":
            body = ", ".join(f'"{e}"' for e in additions)
            new_literal = "{" + body + "}"
        else:
            body = "".join(f'\n{inner_indent}"{e}",' for e in additions)
            new_literal = f"({body}\n{indent})"
        return text[:start] + new_literal + text[end:]

    close_char = literal[-1]
    if close_char not in ")}]":
        raise ValueError(f"unexpected close char in literal: {literal!r}")

    # Find insertion point: just before the close bracket. The close
    # bracket is at index (end-1) relative to the global text. We insert
    # a block of lines with the same indent as the literal's inner content.
    # Detect whether the literal is multi-line (newline before close) or
    # single-line.
    body_before_close = text[start : end - 1].rstrip(" \t")
    has_trailing_newline = body_before_close.endswith("\n")

    # Build the addition block.
    lines_to_insert = []
    for e in additions:
        lines_to_insert.append(f'{inner_indent}"{e}",')

    if has_trailing_newline:
        # Multi-line: insert lines between the last entry and the close.
        # Ensure our lines end with a newline before the close-line indent.
        insertion = "\n".join(lines_to_insert) + "\n"
        insertion_point = end - 1
        # Find the indent of the closing bracket line.
        # Back up from insertion_point to the last newline.
        nl = text.rfind("\n", 0, insertion_point)
        close_indent = text[nl + 1 : insertion_point]
        # Keep close_indent as-is; prepend our insertion after it? Actually
        # we want to insert BEFORE the close-line. So insertion goes before
        # the close-line's start (nl+1).
        return text[: nl + 1] + insertion + text[nl + 1 :]
    else:
        # Single-line literal, e.g. ``("a", "b")`` or ``{"a"}``.
        # Convert to multi-line for readability.
        # Parse existing entries from the single-line literal (keeping
        # order), then emit a new multi-line literal preserving existing
        # entries + appending additions.
        existing = _parse_literal_entries(literal)
        combined = existing + [a for a in additions if a not in existing]
        lines = []
        for e in combined:
            lines.append(f'{inner_indent}"{e}",')
        open_char = literal[0]
        new_literal = open_char + "\n" + "\n".join(lines) + f"\n{indent}{close_char}"
        return text[:start] + new_literal + text[end:]


def widen_binding(
    path: Path,
    name: str,
    additions: list[str],
    *,
    mode: str,
    create_if_missing_after: str | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Add *additions* to the existing *name* binding in *path*.

    *mode* is ``"tuple"`` (allowed_prefixes — ordered append) or
    ``"set"`` (allowed_files — order-insensitive but we still append).

    Returns ``(changed, new_entries, added_entries)``. Inserts new
    entries immediately before the literal's closing bracket, preserving
    all existing whitespace + inline comments inside the literal.
    """
    if mode not in ("tuple", "set"):
        raise ValueError(f"mode must be 'tuple' or 'set', got {mode!r}")
    text = path.read_text(encoding="utf-8")
    loc = _locate_binding(text, name)
    if loc is None:
        if create_if_missing_after is not None:
            anchor_loc = _locate_binding(text, create_if_missing_after)
            if anchor_loc is None:
                raise BindingNotFound(
                    f"{path}: neither {name!r} nor anchor "
                    f"{create_if_missing_after!r} found"
                )
            indent = anchor_loc[0].group("indent") or ""
            empty_literal = "set()" if mode == "set" else "()"
            new_text = _insert_binding_after(
                text, create_if_missing_after, name, empty_literal, indent
            )
            if new_text is None:
                raise BindingNotFound(
                    f"{path}: could not insert {name!r} after "
                    f"{create_if_missing_after!r}"
                )
            path.write_text(new_text, encoding="utf-8")
            text = new_text
            loc = _locate_binding(text, name)
            if loc is None:
                raise BindingNotFound(
                    f"{path}: synthesized {name!r} binding not re-locatable"
                )
        else:
            raise BindingNotFound(f"{path}: {name!r} binding not found")
    m, start, end = loc
    current = _parse_literal_entries(text[start:end])
    current_set = set(current)
    added = sorted({a for a in additions if a not in current_set})
    if not added:
        return False, current, []
    indent = m.group("indent") or ""
    new_text = _insert_entries_before_close(
        text, start, end, added, indent, mode
    )
    path.write_text(new_text, encoding="utf-8")
    new_entries = current + added
    return True, new_entries, added
