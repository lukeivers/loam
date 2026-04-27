#!/bin/sh
# hands-off-lifecycle/hooks/first-run.sh
#
# pos-v2 first-run SessionStart hook. POSIX shell (no bash-isms).
#
# Invoked as a Claude Code SessionStart hook on a fresh clone.
#
# 2026-04-22 session-start-detachment amendment rewrite:
#
# This hook is now a **thin status-report-and-handoff**. It completes
# in under 5 seconds — Claude Code's SessionStart hook is the wrong
# container for the 3-8 minute cold-cache first-run flow, and prior
# attempts to run the heavy lifting inside the hook were killed by the
# hook's 120 s timeout, leaving ~/.pos/ and .venv/ partially populated
# and silent on the user's screen. Luke hit this himself on his
# /tmp/pos3 clone; the four failure classes are documented in the
# amendment commit message and this hook's fixtures.
#
# Responsibilities of THIS file:
#   1. Read the state sentinel at ~/.pos/first-run.state.
#   2. Decide: fresh-start, still-running, failed-respawn, already-done.
#   3. Emit a plain-language additionalContext message naming the
#      progress file and expected wait window.
#   4. For fresh-start or failed-respawn: detect Python 3.13, spawn the
#      Python worker **detached** (new session group, redirected stdio,
#      no parent PID lineage), and return immediately.
#
# Responsibilities the hook NO LONGER owns:
#   - Creating the shared venv (moved into the detached worker).
#   - pip install of per-component requirements (already detached work,
#     but formerly invoked synchronously from here).
#   - Running Amendment 4's scaffold, plist substitution, service
#     bootstrap, health polling — all moved.
#   - Self-retiring this script — the worker handles it on success.
#
# Exit codes from the hook perspective: always 0. Status semantics are
# carried in the stdout payload (additionalContext for Claude Code) and
# the state file (authoritative state for future hook firings).

set -u

# ---- POSIX-baseline PATH and file locations -----------------------
#
# If the invoker stripped PATH we still need cat, printf, rm, etc.
# Prepending rather than replacing preserves any caller-specified tools
# (POS_V2_PYTHON escape hatch, e.g.).
PATH="${PATH:-}:/usr/bin:/bin"
export PATH

# Resolve the pos-v2 workspace root. CLAUDE_PROJECT_DIR is set by Claude
# Code at hook fire time; fall back to script-relative resolution when
# the hook is invoked outside Claude Code (test harness, manual run).
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
    POS_V2_ROOT="$CLAUDE_PROJECT_DIR"
else
    SCRIPT_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd -P) || {
        printf 'pos v2 first-run: cannot resolve script directory.\n'
        exit 0
    }
    # Post-D.1: this script lives at framework/hands-off-lifecycle/hooks/;
    # workspace root is three levels up.
    POS_V2_ROOT=$(cd "$SCRIPT_DIR/../../.." 2>/dev/null && pwd -P) || {
        printf 'pos v2 first-run: cannot resolve workspace root.\n'
        exit 0
    }
fi

HELPER="$POS_V2_ROOT/framework/hands-off-lifecycle/hooks/first_run_helper.py"
DISPATCH="$POS_V2_ROOT/framework/hands-off-lifecycle/hooks/first_run_dispatch.py"

# ~/.pos is the per-host config dir. Overridable for tests via the
# POS_V2_POS_ROOT env var (same spelling the Python side respects).
POS_ROOT="${POS_V2_POS_ROOT:-$HOME/.pos}"

# ---- Python 3.13 detection ---------------------------------------
#
# We need a 3.13+ interpreter to run first_run_dispatch.py, which
# decides what state we are in and whether to spawn the worker. The
# dispatch script is stdlib-only — no venv required.
#
# Detection order matches the pre-amendment script so the UX is
# consistent across detached and inline modes:
#   1. $POS_V2_PYTHON (CI / dev escape hatch)
#   2. python3.13 on PATH
#   3. /opt/homebrew/bin/python3.13 (Homebrew ARM)
#   4. /usr/local/bin/python3.13 (Homebrew Intel / some Linux)
#   5. python3 on PATH (verify 3.13+)

_verify_version_ge_313() {
    "$1" -c '
import sys
v = sys.version_info
if (v.major, v.minor) < (3, 13):
    sys.exit(1)
print(f"{v.major}.{v.minor}.{v.micro}")
' 2>/dev/null
}

_try_candidate() {
    candidate="$1"
    if [ -z "$candidate" ]; then
        return 1
    fi
    if ! command -v "$candidate" >/dev/null 2>&1 && [ ! -x "$candidate" ]; then
        return 1
    fi
    ver=$(_verify_version_ge_313 "$candidate" 2>/dev/null) || return 1
    [ -n "$ver" ] || return 1
    DETECTED_PYTHON="$candidate"
    DETECTED_VERSION="$ver"
    return 0
}

DETECTED_PYTHON=""
DETECTED_VERSION=""

if [ -n "${POS_V2_PYTHON:-}" ]; then
    _try_candidate "$POS_V2_PYTHON" || true
else
    if [ -z "$DETECTED_PYTHON" ]; then
        _try_candidate "python3.13" || true
    fi
    if [ -z "$DETECTED_PYTHON" ]; then
        _try_candidate "/opt/homebrew/bin/python3.13" || true
    fi
    if [ -z "$DETECTED_PYTHON" ]; then
        _try_candidate "/usr/local/bin/python3.13" || true
    fi
    if [ -z "$DETECTED_PYTHON" ]; then
        _try_candidate "python3" || true
    fi
fi

if [ -z "$DETECTED_PYTHON" ]; then
    # No compatible Python. This is the one case the shell has to
    # handle itself — the dispatch script requires 3.13 to run.
    # The "Detected: none" + error-code line are preserved from the
    # pre-amendment diagnostic for the T5/T6 acceptance tests, which
    # assert against both markers.
    cat <<EOF_DIAG
Your pos-v2 workspace cannot finish installing — Python 3.13 was not
found on this machine.

Error code: -32091 platform-unsupported:no-compatible-python-found
Required:   Python 3.13 or newer
Detected:   none

Install Python 3.13 (expected time: 2-5 minutes), then reopen claude.

  macOS (Homebrew):
    1. Install Homebrew if you do not have it: https://brew.sh
    2. brew install python@3.13
    3. Reopen this workspace in Claude Code.
EOF_DIAG
    exit 0
fi

# ---- Hand off to the Python dispatch script -----------------------
#
# first_run_dispatch.py is stdlib-only and completes in under a second
# on any real machine. It reads the state file, decides what to do, and
# emits the additionalContext text the user sees. When a new worker
# needs to be spawned the dispatch does it via os.posix_spawn with
# start_new_session so the worker survives the hook process's exit.

exec "$DETECTED_PYTHON" "$DISPATCH" \
    --pos-v2-root "$POS_V2_ROOT" \
    --pos-root "$POS_ROOT" \
    --helper "$HELPER" \
    --python "$DETECTED_PYTHON" \
    --python-version "$DETECTED_VERSION"
