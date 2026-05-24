"""AC.TOKEN.3 — The settings-merge mechanism preserves existing user
keys in ``~/.claude/settings.json`` when writing recommended values;
never silently overwrites.

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.3
+ AC.PO.1 ladder (sovereignty preservation IS translation-burden
absorption — user doesn't need to know what's safe to write).

The test uses a tmpfs fixture for the settings file (no touch of
the real ``~/.claude/settings.json``) and exercises the production
``merge.apply`` entry-point. Verifies:

1. A pre-existing non-loam user key (e.g., ``theme: "dark"``) is
   preserved byte-for-byte after the merge.
2. Recommended keys are added when absent (NEW classification).
3. COLLISION on a recommended key (user has set it to a different
   value) is SURFACED in the structured diagnostic AND preserved by
   default (no overwrite without explicit ``--overwrite``).
4. The atomic-write contract holds: the temp file is cleaned up
   and the final settings.json is valid JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MERGE_DIR = (
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "cost-optimised-defaults"
)


def _import_merge():
    """Import the merge module per the per-test sys.path convention
    (pytest-launch-independent; mirrors AC.COMPACT.S pattern)."""
    if str(MERGE_DIR) not in sys.path:
        sys.path.insert(0, str(MERGE_DIR))
    import merge  # type: ignore[import-not-found]
    return merge


def test_existing_user_key_preserved_after_merge(tmp_path: Path) -> None:
    """A non-loam user key is preserved byte-for-byte after merge."""
    merge = _import_merge()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"theme": "dark", "voice": {"enabled": True}}),
        encoding="utf-8",
    )

    result = merge.apply(settings_path)

    post = json.loads(settings_path.read_text(encoding="utf-8"))
    assert post["theme"] == "dark", (
        "AC.TOKEN.3: pre-existing non-loam user key `theme` must be "
        f"preserved after merge; got {post.get('theme')!r}."
    )
    assert post["voice"] == {"enabled": True}, (
        "AC.TOKEN.3: pre-existing nested non-loam user key `voice` "
        f"must be preserved after merge; got {post.get('voice')!r}."
    )
    # Sanity: recommended keys were written.
    assert "model" in post, (
        "AC.TOKEN.3 sanity: recommended `model` key must be present "
        "after merge."
    )
    assert post["model"] == "sonnet", (
        f"AC.TOKEN.3 sanity: `model` should be `sonnet`; got "
        f"{post['model']!r}."
    )
    assert "env" in post and isinstance(post["env"], dict), (
        "AC.TOKEN.3 sanity: recommended `env` block must be present "
        "after merge."
    )
    assert post["env"].get("MAX_THINKING_TOKENS") == "10000", (
        f"AC.TOKEN.3 sanity: `env.MAX_THINKING_TOKENS` should be "
        f"`10000`; got {post['env'].get('MAX_THINKING_TOKENS')!r}."
    )
    # Sanity: diagnostic reports the writes.
    assert "model" in result.keys_written
    assert "env.MAX_THINKING_TOKENS" in result.keys_written


def test_collision_preserved_by_default_and_surfaced_in_diagnostic(
    tmp_path: Path,
) -> None:
    """A COLLISION (user has set a recommended key to a different
    value) is preserved by default AND surfaced in the diagnostic."""
    merge = _import_merge()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "model": "opus",
                "env": {"MAX_THINKING_TOKENS": "20000"},
            }
        ),
        encoding="utf-8",
    )

    # Apply WITHOUT --overwrite for the collision keys; default = keep.
    result = merge.apply(settings_path)

    post = json.loads(settings_path.read_text(encoding="utf-8"))
    # Collision keys preserved.
    assert post["model"] == "opus", (
        f"AC.TOKEN.3: COLLISION key `model` (user had `opus`) must "
        f"be preserved on default apply (no --overwrite); got "
        f"{post['model']!r}."
    )
    assert post["env"]["MAX_THINKING_TOKENS"] == "20000", (
        f"AC.TOKEN.3: COLLISION key `env.MAX_THINKING_TOKENS` (user "
        f"had `20000`) must be preserved on default apply; got "
        f"{post['env']['MAX_THINKING_TOKENS']!r}."
    )
    # Diagnostic surfaces both collisions.
    assert "model" in result.keys_preserved_due_to_conflict, (
        "AC.TOKEN.3: structured diagnostic must surface `model` in "
        f"keys_preserved_due_to_conflict; got "
        f"{result.keys_preserved_due_to_conflict!r}."
    )
    assert (
        "env.MAX_THINKING_TOKENS"
        in result.keys_preserved_due_to_conflict
    ), (
        "AC.TOKEN.3: structured diagnostic must surface "
        "`env.MAX_THINKING_TOKENS` in keys_preserved_due_to_conflict; "
        f"got {result.keys_preserved_due_to_conflict!r}."
    )
    # Non-collision recommended key (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE)
    # is NEW and gets written.
    assert (
        post["env"]["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] == "50"
    ), (
        f"AC.TOKEN.3 sanity: NEW key "
        f"`env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` should be written "
        f"to recommended `50`; got "
        f"{post['env'].get('CLAUDE_AUTOCOMPACT_PCT_OVERRIDE')!r}."
    )


def test_collision_can_be_explicitly_overwritten_per_key(
    tmp_path: Path,
) -> None:
    """A user can explicitly opt-in to overwriting a COLLISION key by
    passing it in overwrite_keys."""
    merge = _import_merge()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "model": "opus",
                "env": {"MAX_THINKING_TOKENS": "20000"},
            }
        ),
        encoding="utf-8",
    )

    result = merge.apply(
        settings_path, overwrite_keys=("model",)
    )

    post = json.loads(settings_path.read_text(encoding="utf-8"))
    # `model` overwritten per user's explicit choice.
    assert post["model"] == "sonnet", (
        f"AC.TOKEN.3: explicit --overwrite model should write the "
        f"recommended value; got {post['model']!r}."
    )
    assert "model" in result.keys_written
    # `env.MAX_THINKING_TOKENS` still preserved (not in overwrite_keys).
    assert post["env"]["MAX_THINKING_TOKENS"] == "20000", (
        "AC.TOKEN.3: --overwrite is per-key; a non-overwritten "
        f"collision key should still be preserved; got "
        f"{post['env']['MAX_THINKING_TOKENS']!r}."
    )
    assert (
        "env.MAX_THINKING_TOKENS"
        in result.keys_preserved_due_to_conflict
    )


def test_missing_settings_file_creates_one_with_recommended_keys(
    tmp_path: Path,
) -> None:
    """If ~/.claude/settings.json is absent, apply creates a fresh
    one with the recommended keys."""
    merge = _import_merge()
    settings_path = tmp_path / "subdir" / "settings.json"  # parent absent

    result = merge.apply(settings_path)

    assert settings_path.exists(), (
        "AC.TOKEN.3: apply must create the settings file (incl. parent "
        "directories) when absent; not found."
    )
    post = json.loads(settings_path.read_text(encoding="utf-8"))
    assert post == {
        "model": "sonnet",
        "env": {
            "MAX_THINKING_TOKENS": "10000",
            "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50",
        },
    }, (
        f"AC.TOKEN.3: fresh settings file must contain exactly the 3 "
        f"recommended keys (model + 2 env entries); got {post!r}."
    )
    assert set(result.keys_written) == {
        "model",
        "env.MAX_THINKING_TOKENS",
        "env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE",
    }


def test_atomic_write_leaves_valid_json(tmp_path: Path) -> None:
    """Post-apply settings file is valid JSON (atomic-write contract:
    no partial-write corruption visible)."""
    merge = _import_merge()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"existing": "value"}), encoding="utf-8"
    )

    merge.apply(settings_path)

    raw = settings_path.read_text(encoding="utf-8")
    parsed = json.loads(raw)  # raises JSONDecodeError on partial write
    assert isinstance(parsed, dict), (
        "AC.TOKEN.3: post-apply settings file must be a valid JSON "
        f"object; got {type(parsed).__name__}."
    )
    # No leftover temp files in the parent dir.
    temp_files = [
        p for p in settings_path.parent.iterdir()
        if p.name.startswith(settings_path.name + ".")
        and p.name.endswith(".tmp")
    ]
    assert not temp_files, (
        "AC.TOKEN.3: atomic write must clean up its temp files; "
        f"found leftover temp files: {temp_files}."
    )
