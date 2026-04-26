"""pOS v2 workspace-sync — canonical-to-workspace git-shaped sync.

Architecture B (per-workspace embedded framework, locked 2026-04-26):
this component pulls canonical changes into a downstream workspace
clone (e.g. pos3) under the three-class workspace-data envelope
(A=preserve / B=operator-preference / C=LLM-resolved).

The companion sealed component `self-upgrade/` is the canonical-only
A-mode mechanism (in-place symlink swap on the canonical maintainer's
machine). Both components share design DNA but no runtime coupling
(per ruling A5 + Hard Constraint #11 of the workspace-sync plan).

Operator-visible CLI verbs:

    pos-sync --canonical <path> [--ref <commit-or-tag>] \\
             [--workspace <path>] [--dry-run] [--auto-accept]

    pos-workspace-sync ...   # alias
"""

__version__ = "0.1.0"
