"""D2 idempotency variant — 5 gate runs against the same diff produce
identical decisions (modulo timestamps).

Per master plan §3 Cycle 1 dispatch: "D2 idempotency variant: 5+
gate runs on same diff are byte-identical." Cycle 1 verifies the
decision payload (excluding timestamps) is identical; the audit-log
filename + timestamp differs by design (each invocation writes a
new entry).
"""

from __future__ import annotations

import argparse
import json


def test_d2_idempotent_decision_5_runs(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """5 gate invocations against the same regression diff produce
    identical action / requires_ratification / touched_ac_ids /
    novel_count.
    """
    from loam_pr_safety.cli import build_pr_safety_subcommand

    workspace_root, repo_id = workspace_with_contract

    # Build a regression diff (touches AC.SYNTH.1 line 50).
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add 60-line auth.py",
    )
    modified_lines = "\n".join(
        f"# changed at {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: tweak line 50",
    )

    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_pr_safety_subcommand(sub)

    decisions = []
    for _ in range(5):
        args = parser.parse_args(
            [
                "pr-safety",
                "gate",
                str(tmp_git_repo),
                "--workspace-root",
                str(workspace_root),
                "--repo-id",
                repo_id,
                "--diff",
                "HEAD~1..HEAD",
                "--json",
            ]
        )
        args.func(args)
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        # Strip transient fields (none in payload — payload is shape-only).
        decisions.append(payload)

    # All 5 decisions are byte-identical.
    for d in decisions[1:]:
        assert d == decisions[0]
