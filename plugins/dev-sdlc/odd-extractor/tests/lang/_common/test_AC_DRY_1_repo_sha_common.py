"""AC.DRY.1 (v0.1.8 Cycle 4b) — ``_common/repo_sha.py`` exposes
the canonical ``resolve_repo_sha`` helper.

Pre-4b ``resolve_repo_sha`` was duplicated byte-equivalent at
``lang/ruby/repo_sha.py`` and ``lang/jsts/repo_sha.py``; Cycle 4b
factored both copies into ``lang/_common/repo_sha.py``. This test
verifies (a) the canonical home is importable, (b) it returns the
expected SHA for a tmp git repo, (c) per-language ``repo_sha.py``
files are GONE.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_common_repo_sha_module_importable() -> None:
    """``loam_odd_extractor.lang._common.repo_sha.resolve_repo_sha``
    is importable.
    """
    from loam_odd_extractor.lang._common.repo_sha import resolve_repo_sha

    assert callable(resolve_repo_sha)


def test_common_repo_sha_resolves_for_tmp_git_repo(tmp_path: Path) -> None:
    """The canonical helper returns the HEAD SHA for a tmp git repo."""
    from loam_odd_extractor.lang._common.repo_sha import resolve_repo_sha

    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "f.txt").write_text("hello")
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
         "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
         "commit", "--quiet", "-m", "init"],
        cwd=tmp_path,
        check=True,
    )

    sha = resolve_repo_sha(tmp_path)
    assert sha is not None
    assert len(sha) == 40
    assert all(c in "0123456789abcdef" for c in sha.lower())


def test_common_repo_sha_returns_none_for_non_git_repo(
    tmp_path: Path,
) -> None:
    """Returns ``None`` for non-git directories."""
    from loam_odd_extractor.lang._common.repo_sha import resolve_repo_sha

    assert resolve_repo_sha(tmp_path) is None


def test_per_adapter_repo_sha_files_are_deleted() -> None:
    """The pre-4b ``lang/ruby/repo_sha.py`` and
    ``lang/jsts/repo_sha.py`` files are DELETED — the canonical home
    is the only source.
    """
    import loam_odd_extractor

    pkg_root = Path(loam_odd_extractor.__file__).parent
    ruby_path = pkg_root / "lang" / "ruby" / "repo_sha.py"
    jsts_path = pkg_root / "lang" / "jsts" / "repo_sha.py"

    assert not ruby_path.exists(), (
        f"lang/ruby/repo_sha.py still exists at {ruby_path}; "
        f"should be deleted per AC.DRY.1"
    )
    assert not jsts_path.exists(), (
        f"lang/jsts/repo_sha.py still exists at {jsts_path}; "
        f"should be deleted per AC.DRY.1"
    )


def test_adapters_import_from_common() -> None:
    """Both ``lang/ruby/adapter.py`` and ``lang/jsts/adapter.py``
    import ``resolve_repo_sha`` from ``.._common.repo_sha`` (the
    canonical path).
    """
    import loam_odd_extractor

    pkg_root = Path(loam_odd_extractor.__file__).parent
    for adapter_rel in ("lang/ruby/adapter.py", "lang/jsts/adapter.py"):
        text = (pkg_root / adapter_rel).read_text()
        assert (
            "from .._common.repo_sha import resolve_repo_sha" in text
        ), (
            f"{adapter_rel} does not import resolve_repo_sha from "
            f".._common.repo_sha (canonical path per AC.DRY.1)"
        )
