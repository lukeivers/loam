"""Synth-time path / personal-info substitution pass.

Applied by ``loam.publish_framework_only.synth`` AFTER the partition
filter (see ``synth._build_synthetic_tree``). For every leaf classified
``PUBLIC_ONLY`` or ``DEV_AND_PUBLIC``, the substitution pass reads the
blob's content, applies a fixed-table textual rewrite, and IFF the
substitution changed the content, writes a new blob via
``git hash-object -w``. The new blob's SHA replaces the source blob's
SHA in the synthetic tree.

The substitution is purely textual ``s/X/Y/g`` per AC.OSS-M9.1; the
table is owner-locked at master plan §13 D-Q.OSS.6:

    /Users/lukeivers/ivers-corp-pos-v2/  →  <workspace>/loam/
    /Users/lukeivers/ivers-corp-pos-v2   →  <workspace>/loam
    lukeivers/pos-v2                     →  lukeivers/loam
    Luke Ivers                           →  Alice Anderson

Determinism + idempotence (AC.OSS-M9.3): the table contains no entry
where the replacement is itself a substitution source (e.g.
``<workspace>/loam`` doesn't appear as a key), so re-running on a
synthesised tree finds zero tokens to substitute and produces an
identical tree-SHA.

Binary-blob safety (AC.OSS-M9.4): the substitution attempts UTF-8
decode; on ``UnicodeDecodeError`` the original blob bytes are
preserved verbatim (the caller uses the source blob SHA unchanged).
"""

from __future__ import annotations

from dataclasses import dataclass


# The substitution table. Order matters: the no-trailing-slash entry
# would also match inside a path that DOES carry a trailing slash, so
# the trailing-slash entry must apply first to avoid double-rewrite
# (e.g. ``/Users/lukeivers/ivers-corp-pos-v2/file.py`` would otherwise
# become ``<workspace>/loam/file.py`` via the no-slash rule, but the
# trailing-slash rule produces the same result). The order is captured
# explicitly via tuple-of-tuples so the iteration order is stable
# across Python versions.
#
# Per master plan §13 D-Q.OSS.6 (locked): four entries.
SUBSTITUTION_TABLE: tuple[tuple[str, str], ...] = (
    (
        "/Users/lukeivers/ivers-corp-pos-v2/",
        "<workspace>/loam/",
    ),
    (
        "/Users/lukeivers/ivers-corp-pos-v2",
        "<workspace>/loam",
    ),
    (
        "lukeivers/pos-v2",
        "lukeivers/loam",
    ),
    (
        "Luke Ivers",
        "Alice Anderson",
    ),
)


@dataclass(frozen=True)
class SubstitutionResult:
    """Outcome of applying ``SUBSTITUTION_TABLE`` to a single blob.

    ``content`` is the post-substitution bytes (== input when ``changed``
    is False). ``changed`` is True iff at least one token was replaced.
    ``binary`` is True when the input bytes failed UTF-8 decode (and
    so the substitution was skipped — ``content == input`` and
    ``changed == False``).
    """

    content: bytes
    changed: bool
    binary: bool


def apply_substitutions(
    blob_content: bytes,
    table: tuple[tuple[str, str], ...] = SUBSTITUTION_TABLE,
) -> SubstitutionResult:
    """Apply the substitution table to a single blob's content.

    Parameters
    ----------
    blob_content:
        Raw bytes from the source blob (e.g. ``git cat-file blob <sha>``).
    table:
        Tuple of ``(source, replacement)`` substitution pairs. Defaults
        to ``SUBSTITUTION_TABLE`` (the M9-locked four-entry table).
        Tests pass a custom table to exercise edge cases.

    Returns
    -------
    SubstitutionResult
        Carries the post-substitution bytes, a ``changed`` flag, and
        a ``binary`` flag.

    Behaviour
    ---------
    1. If the bytes do not UTF-8-decode (binary blob — PNG, etc.),
       returns the input unchanged with ``binary=True`` per
       AC.OSS-M9.4.
    2. Otherwise, decodes to text, applies each ``(source, replacement)``
       pair via ``str.replace`` in table order, and re-encodes UTF-8.
    3. ``changed`` is True iff the resulting bytes differ from the
       input.
    """
    try:
        text = blob_content.decode("utf-8")
    except UnicodeDecodeError:
        return SubstitutionResult(
            content=blob_content,
            changed=False,
            binary=True,
        )
    rewritten = text
    for source, replacement in table:
        rewritten = rewritten.replace(source, replacement)
    if rewritten == text:
        return SubstitutionResult(
            content=blob_content,
            changed=False,
            binary=False,
        )
    return SubstitutionResult(
        content=rewritten.encode("utf-8"),
        changed=True,
        binary=False,
    )
