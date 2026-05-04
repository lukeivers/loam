"""class-validator decorator recognizer.

Per AC.JSTS.2 + Surface #5 — detects class-validator decorators on
class fields:

- ``@IsString()``, ``@IsEmail()``, ``@IsNotEmpty()``,
  ``@MinLength(N)``, ``@MaxLength(N)``, ``@IsOptional()``,
  ``@IsBoolean()``, ``@IsNumber()``, ``@IsArray()``, ``@IsDate()``,
  ``@IsUUID()``, ``@IsUrl()``, ``@Length(min, max)``,
  ``@Matches(regex)``.

Each decorated field emits one PLAUSIBLE-band :class:`BandedAC` per
decorator (field can have multiple decorators; each gets its own AC
with the decorator-name in the AC ID for cross-decorator
deduplication).

Class-validator is NestJS-adjacent and a TS-only ecosystem; this
recognizer is invoked on TS/TSX trees only (decorators in JS exist
but the class-validator pattern is TS-canonical).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    class_field_decorators,
    class_name,
    file_slug,
    find_class_declarations,
    slugify,
)
from ..parser import node_line

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


# Regex to extract the decorator name from `@DecoratorName(...)`.
# class-validator decorators are CamelCase identifier-callable.
_DECORATOR_RE = re.compile(r"@(\w+)")

# Recognized class-validator decorator names; pass-1 list. Per
# Surface #5 — class-validator + Zod cover Eric's first project.
_CLASS_VALIDATOR_DECORATORS = frozenset(
    {
        "IsString", "IsNumber", "IsBoolean", "IsArray", "IsDate",
        "IsEmail", "IsUUID", "IsUrl", "IsOptional", "IsNotEmpty",
        "IsDefined", "IsEmpty", "IsIn", "IsNotIn", "IsEnum",
        "IsObject", "IsInt", "IsPositive", "IsNegative",
        "MinLength", "MaxLength", "Length",
        "Min", "Max", "MinDate", "MaxDate",
        "Matches", "Contains", "NotContains",
        "Equals", "NotEquals",
        "Allow", "ArrayContains", "ArrayNotContains",
        "ArrayMinSize", "ArrayMaxSize",
        "ValidateNested", "ValidateIf",
    }
)


def recognize_class_validator(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for every class-validator-
    decorated field.

    Returns ``[]`` for JS files (decorators are TS-mostly).
    """
    if file_path.suffix.lower() not in (".ts", ".tsx"):
        return []

    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for class_node in find_class_declarations(tree.root_node):
        cname = class_name(class_node, source)
        if cname is None:
            continue

        for field_name, dec_text, dec_node in class_field_decorators(
            class_node, source
        ):
            m = _DECORATOR_RE.match(dec_text)
            if not m:
                continue
            dec_name = m.group(1)
            if dec_name not in _CLASS_VALIDATOR_DECORATORS:
                continue

            line = node_line(dec_node)
            ac_id = (
                f"AC.JSTS.class_validator.{slugify(cname)}."
                f"{slugify(field_name)}.{slugify(dec_name)}.{fslug}"
            )
            out.append(
                BandedAC(
                    ac_id=ac_id,
                    text=(
                        f"{cname}.{field_name} validated by "
                        f"@{dec_name}()"
                    ),
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
