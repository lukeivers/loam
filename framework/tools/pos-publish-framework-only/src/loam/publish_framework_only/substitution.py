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
# Entries 1-4 (M9-locked): master plan §13 D-Q.OSS.6.
# Entries 5-7 (D-Q.ABC.4): C2-prime amendment (sub-plan
# `oss-v0-1-0-publish-public-docs-classes-abc-prime.md` §11
# D-Q.ABC.4 carry-forward). Internal authority/spec docs → public
# counterparts.
# Entries 8-12 (D-Q.ABC-prime.2): C2-prime amendment §11 D-Q.ABC-
# prime.2 (5 entries; collapse plugin-relative ODD refs + plan/state
# refs to public counterparts). Order-sensitive: trailing-slash
# entry 12 (``docs/rebuild/plans/`` → ``docs/components/``) precedes
# any future no-slash partner.
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
    # Entry 5 (D-Q.ABC.4) — internal value-prop authority doc → public
    # positioning doc. Used by files 1, 5, 18, 24, 25 (CLAUDE.md +
    # corpus_inline_session_start + session_start_gate + first_run_
    # scaffold + tracker_seed) per C2-prime §5.4.
    (
        "docs/rebuild/VALUE_PROPOSITION.md",
        "docs/positioning.md",
    ),
    # Entry 6 (D-Q.ABC.4) — internal spec doc → public architecture
    # doc (closest public analogue). Used by file 25 (tracker_seed.py
    # SPEC_DOC_RELPATH constant) per C2-prime §5.4.
    (
        "docs/rebuild/spec/loam-objectives-spec.md",
        "docs/architecture.md",
    ),
    # Entry 7 (D-Q.ABC.4) — root-level ODD methodology ref → public
    # ODD doc. Used by files 4, 5, 18, 24 (gate-helpers + corpus_
    # inline + session_start_gate + first_run_scaffold).
    (
        "docs/odd-methodology.md",
        "docs/design/odd.md",
    ),
    # Entry 8 (D-Q.ABC-prime.2) — root-level ODD-in-loam ref → public
    # ODD doc. Mirrors entry 7. Used by files 4, 5, 18.
    (
        "docs/odd-in-loam.md",
        "docs/design/odd.md",
    ),
    # Entry 9 (D-Q.ABC-prime.2) — plugin-relative ODD methodology ref
    # → public ODD doc. Used by file 5 (corpus_inline_session_start).
    (
        "plugins/dev-sdlc/docs/odd-methodology.md",
        "docs/design/odd.md",
    ),
    # Entry 10 (D-Q.ABC-prime.2) — plugin-relative ODD-in-loam ref
    # → public ODD doc. Used by file 5.
    (
        "plugins/dev-sdlc/docs/odd-in-loam.md",
        "docs/design/odd.md",
    ),
    # Entry 11 (D-Q.ABC-prime.2) — internal STATE.md ref → public
    # getting-started doc. Used by files 5, 18.
    (
        "docs/rebuild/STATE.md",
        "docs/getting-started.md",
    ),
    # Entry 12 (D-Q.ABC-prime.2) — internal plans/ trailing-slash
    # path → public components/ doc-tree. Used by file 18 docstring
    # prose (the path-construction logic in
    # ``enumerate_amendments_in_flight`` uses individual ``Path /
    # "docs" / "rebuild" / "plans"`` segments which are NOT touched
    # by the textual SUB; the function returns ``[]`` in synth
    # workspaces because no ``docs/rebuild/plans/`` directory
    # exists publicly — that's the correct first-run-stranger
    # behaviour). Trailing-slash entry; precedes any future no-
    # slash partner.
    (
        "docs/rebuild/plans/",
        "docs/components/",
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
