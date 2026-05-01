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

"""Stdlib-only YAML-subset parser for first-run-inventory.yaml.

Eve inference #5 (challenged): parsing YAML with only the stdlib.
Alternatives considered:
  * Author the inventory in JSON. Rejected — operators benefit from
    inline comments, which JSON does not support.
  * Use ast.literal_eval with a JSON-compatible YAML form. Rejected —
    requires the author to write `[...]` and `{...}` inline, which
    looks unlike YAML.
  * Ship a minimal subset parser. Chosen — handles the declarative
    schema needed for this component without pulling in pyyaml, uv,
    or any heavyweight bootstrap dep.

The subset supported:
  * top-level keys with scalar values (strings, ints, floats, true/false/null)
  * top-level keys with list values
  * list items that are mappings (indent-delimited blocks)
  * line comments (``#`` to end of line, outside strings)
  * double-quoted strings and bare scalars
  * two-space indentation

Not supported (structurally halts with a named diagnostic rather than
silently parsing wrong):
  * block literal scalars (``|`` / ``>``)
  * anchor/alias (``&`` / ``*``)
  * flow-style collections (``[a, b]``, ``{k: v}``)
  * tabs as indentation

Halt error: ``InventoryParseError``. The caller surfaces a ``-32099
hands-off-lifecycle-internal:inventory-parse-failed`` diagnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class InventoryParseError(Exception):
    """Raised when the inventory file cannot be parsed by the subset."""


@dataclass(frozen=True)
class InventoryPosition:
    line: int
    col: int


def _strip_comment(line: str) -> str:
    """Strip trailing ``#`` comment, respecting double-quoted strings."""
    out: list[str] = []
    in_dq = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and in_dq and i + 1 < len(line):
            out.append(c)
            out.append(line[i + 1])
            i += 2
            continue
        if c == '"':
            in_dq = not in_dq
            out.append(c)
            i += 1
            continue
        if c == "#" and not in_dq:
            break
        out.append(c)
        i += 1
    return "".join(out).rstrip()


def _parse_scalar(raw: str, line_no: int) -> Any:
    """Parse a scalar value: null, bool, int, float, or string."""
    s = raw.strip()
    if s == "" or s.lower() in ("null", "~"):
        return None
    if s.lower() in ("true", "yes"):
        return True
    if s.lower() in ("false", "no"):
        return False
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        # Handle minimal escapes: \" and \\
        inner = s[1:-1]
        result: list[str] = []
        i = 0
        while i < len(inner):
            if inner[i] == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                if nxt == "n":
                    result.append("\n")
                elif nxt == "t":
                    result.append("\t")
                elif nxt == '"':
                    result.append('"')
                elif nxt == "\\":
                    result.append("\\")
                else:
                    result.append(nxt)
                i += 2
                continue
            result.append(inner[i])
            i += 1
        return "".join(result)
    # Try numerics.
    try:
        if "." not in s and "e" not in s and "E" not in s:
            return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _indent_of(line: str) -> int:
    """Return the count of leading spaces. Tabs halt."""
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            raise InventoryParseError(
                "tab indentation is not supported; use two spaces per level"
            )
        else:
            break
    return n


def _parse_block(
    lines: list[str],
    start: int,
    base_indent: int,
) -> tuple[Any, int]:
    """Parse a mapping or list block starting at ``lines[start]``.

    Returns (value, next_index_after_block).
    """
    if start >= len(lines):
        return {}, start

    # Peek to determine mapping vs list vs empty.
    first_data_idx = start
    while first_data_idx < len(lines):
        stripped = _strip_comment(lines[first_data_idx])
        if stripped.strip() == "":
            first_data_idx += 1
            continue
        break
    if first_data_idx >= len(lines):
        return {}, first_data_idx

    first = _strip_comment(lines[first_data_idx])
    first_indent = _indent_of(first)

    if first_indent < base_indent:
        # Block is empty at this level.
        return {}, start

    if first.lstrip().startswith("- "):
        return _parse_list(lines, start, first_indent)
    return _parse_mapping(lines, start, first_indent)


def _parse_mapping(
    lines: list[str],
    start: int,
    block_indent: int,
) -> tuple[dict[str, Any], int]:
    out: dict[str, Any] = {}
    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            i += 1
            continue
        indent = _indent_of(stripped)
        if indent < block_indent:
            break
        if indent > block_indent:
            raise InventoryParseError(
                f"unexpected extra indent at line {i + 1}: {raw!r}"
            )
        content = stripped[block_indent:]
        if content.startswith("- "):
            raise InventoryParseError(
                f"list item inside mapping at line {i + 1}: {raw!r}"
            )
        if ":" not in content:
            raise InventoryParseError(
                f"mapping key missing ':' at line {i + 1}: {raw!r}"
            )
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            # Nested block.
            nested, j = _parse_block(lines, i + 1, block_indent + 2)
            out[key] = nested
            i = j
            continue
        out[key] = _parse_scalar(rest, i + 1)
        i += 1
    return out, i


def _parse_list(
    lines: list[str],
    start: int,
    block_indent: int,
) -> tuple[list[Any], int]:
    out: list[Any] = []
    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            i += 1
            continue
        indent = _indent_of(stripped)
        if indent < block_indent:
            break
        if indent > block_indent:
            raise InventoryParseError(
                f"unexpected extra indent in list at line {i + 1}: {raw!r}"
            )
        content = stripped[block_indent:]
        if not content.startswith("- "):
            break
        item_body = content[2:]
        if item_body == "":
            # Nested mapping on following lines.
            nested, j = _parse_block(lines, i + 1, block_indent + 2)
            out.append(nested)
            i = j
            continue
        if ":" in item_body and not item_body.startswith('"'):
            # First-line of a mapping item. The rest of the mapping is
            # on subsequent indented lines at block_indent + 2.
            key, _, rest = item_body.partition(":")
            key = key.strip()
            rest = rest.strip()
            item_dict: dict[str, Any] = {}
            if rest != "":
                item_dict[key] = _parse_scalar(rest, i + 1)
            else:
                nested_val, j2 = _parse_block(lines, i + 1, block_indent + 4)
                item_dict[key] = nested_val
                # Continue accumulating keys from subsequent lines.
                rest_dict, j3 = _parse_mapping(lines, j2, block_indent + 2)
                item_dict.update(rest_dict)
                out.append(item_dict)
                i = j3
                continue
            rest_dict, j = _parse_mapping(lines, i + 1, block_indent + 2)
            item_dict.update(rest_dict)
            out.append(item_dict)
            i = j
            continue
        out.append(_parse_scalar(item_body, i + 1))
        i += 1
    return out, i


def parse_inventory(text: str) -> dict[str, Any]:
    """Parse the inventory YAML subset from a string.

    Raises InventoryParseError on unsupported constructs.
    """
    lines = text.splitlines()
    result, _ = _parse_mapping(lines, 0, 0)
    return result


def load_inventory(path: Path) -> dict[str, Any]:
    """Read and parse the inventory at ``path``."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise InventoryParseError(f"inventory not found: {path}") from e
    return parse_inventory(text)


def resolve_service_labels(inventory: dict[str, Any], slug: str) -> dict[str, Any]:
    """Substitute ``{slug}`` in each service label against the workspace slug.

    Amendment #6 (namespaced-labels-and-bootout). The first-run inventory
    declares service labels as templates because label identity is
    workspace-scoped; the helper resolves them at load time once the
    workspace slug is known. Returns a new inventory mapping with the
    resolved labels — the original is not mutated.

    Templates use Python ``str.format`` syntax; only the ``{slug}``
    placeholder is honoured. Other ``{...}`` tokens are surfaced as
    ``InventoryParseError`` rather than silently passed through, so a
    typo like ``{sulg}`` is named loudly.
    """
    services_in = inventory.get("services") or []
    services_out: list[dict[str, Any]] = []
    for svc in services_in:
        if not isinstance(svc, dict):
            services_out.append(svc)
            continue
        raw_label = svc.get("label")
        if not isinstance(raw_label, str):
            services_out.append(svc)
            continue
        try:
            resolved = raw_label.format(slug=slug)
        except (KeyError, IndexError) as e:
            raise InventoryParseError(
                f"unknown placeholder in service label {raw_label!r}: {e}"
            ) from e
        copied = dict(svc)
        copied["label"] = resolved
        services_out.append(copied)
    resolved_inventory = dict(inventory)
    resolved_inventory["services"] = services_out
    return resolved_inventory


# ---- schema validation ---------------------------------------------


def validate_inventory(data: dict[str, Any]) -> None:
    """Verify the parsed inventory has the required shape."""
    if not isinstance(data, dict):
        raise InventoryParseError("top-level inventory must be a mapping")
    if data.get("schema_version") != 1:
        raise InventoryParseError(
            f"unsupported schema_version: {data.get('schema_version')!r}"
        )
    shared = data.get("shared_venv")
    if not isinstance(shared, dict):
        raise InventoryParseError("shared_venv must be a mapping")
    if not isinstance(shared.get("path"), str):
        raise InventoryParseError("shared_venv.path must be a string")
    comps = shared.get("components")
    if not isinstance(comps, list) or not all(isinstance(c, str) for c in comps):
        raise InventoryParseError("shared_venv.components must be a list of strings")

    dedicated = data.get("dedicated_venvs") or []
    if not isinstance(dedicated, list):
        raise InventoryParseError("dedicated_venvs must be a list")
    for item in dedicated:
        if not isinstance(item, dict):
            raise InventoryParseError("dedicated_venvs entries must be mappings")
        for required_key in ("component", "venv_path", "requirements"):
            if not isinstance(item.get(required_key), str):
                raise InventoryParseError(
                    f"dedicated_venvs[*].{required_key} must be a string"
                )

    services = data.get("services") or []
    if not isinstance(services, list):
        raise InventoryParseError("services must be a list")
    for svc in services:
        if not isinstance(svc, dict):
            raise InventoryParseError("services entries must be mappings")
        if not isinstance(svc.get("label"), str):
            raise InventoryParseError("services[*].label must be a string")
        if not isinstance(svc.get("kind"), str):
            raise InventoryParseError("services[*].kind must be a string")
        health = svc.get("health")
        if not isinstance(health, dict):
            raise InventoryParseError("services[*].health must be a mapping")
