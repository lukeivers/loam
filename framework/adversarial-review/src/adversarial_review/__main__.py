# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""Package entry point: ``python -m adversarial_review <artifact> --objective ...``

Delegates to the manual on-demand review CLI. Using a package-level
__main__ (rather than ``-m adversarial_review.manual``) avoids the
double-import RuntimeWarning and gives a clean owner-facing incantation.

The ``insession`` first-arg routes to the in-session handshake CLI
(insession.py) — the path an in-session agent uses so the critic legs are
FRESH Task subagents instead of a nested ``claude -p`` subprocess (which
hangs when driven from an interactive session). Everything else is the
normal manual/subprocess-backed review.
"""
from __future__ import annotations

import sys

from .insession import insession_main
from .manual import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "insession":
        sys.exit(insession_main(sys.argv[2:]))
    sys.exit(main())
