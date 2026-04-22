#!/bin/sh
# hands-off-lifecycle/hooks/first-run.sh
#
# pos-v2 first-run bootstrap. POSIX shell (no bash-isms).
#
# Invoked as a Claude Code SessionStart hook on a fresh clone. Detects
# system Python 3.13+, creates the shared venv, then hands off to
# first_run_helper.py which does the Python-appropriate heavy work
# (per-component dep install, plist substitution, service bootstrap,
# .claude/settings.json rewrite, self-retire).
#
# On successful completion: this script deletes itself and the
# .claude/settings.json SessionStart stanza is rewritten to invoke the
# sealed supervisor path directly. Next sessions never see this script.
#
# Error codes:
#   -32091  platform-unsupported:no-compatible-python-found
#   -32097  pip-install-failed
#   -32098  service-health-timeout
#   -32099  hands-off-lifecycle-internal (self-retire verification failed)
#
# Exit convention: always 0 to Claude Code so the stdout text surfaces
# as additionalContext. Status semantics are encoded in the stdout
# payload, not the exit code.

set -u

# Ensure POSIX-baseline tools (cat, printf, cd, dirname, rm) are on PATH
# even if the invoker stripped it. We prepend rather than replace so a
# caller-specified custom PATH still wins for POSIX_V2_PYTHON-style
# explicit tooling.
PATH="${PATH:-}:/usr/bin:/bin"
export PATH

# Resolve the pos-v2 workspace root from the script's own location.
# $CLAUDE_PROJECT_DIR is set by Claude Code at hook fire time; fall
# back to the script-relative resolution if it is absent (defensive).
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
    POS_V2_ROOT="$CLAUDE_PROJECT_DIR"
else
    # Resolve from script location: hands-off-lifecycle/hooks/first-run.sh
    # Two parents up from the script directory is the workspace root.
    SCRIPT_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd -P) || {
        printf 'pos v2 first-run: cannot resolve script directory.\n'
        exit 0
    }
    POS_V2_ROOT=$(cd "$SCRIPT_DIR/../.." 2>/dev/null && pwd -P) || {
        printf 'pos v2 first-run: cannot resolve workspace root.\n'
        exit 0
    }
fi

VENV_DIR="$POS_V2_ROOT/.venv"
HELPER="$POS_V2_ROOT/hands-off-lifecycle/hooks/first_run_helper.py"
THIS_SCRIPT="$POS_V2_ROOT/hands-off-lifecycle/hooks/first-run.sh"

# ---- Phase 0: determine if first-run is even needed ---------------
#
# Partial-first-run detection marker (Eve inference #3): absence of
# the top-level .venv/ is the canonical "first-run not complete"
# signal. Self-retire cannot delete the venv (the venv must persist);
# a dedicated sentinel would create a separate cleanup concern for a
# future uninstall flow. Venv-absence is cheaper and more structural.
if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
    # Venv exists — first-run has either completed before, or partially
    # ran and left the venv in place. Hand off to the helper in
    # "resume-or-verify" mode; it short-circuits cleanly if state is
    # complete, or restarts pending phases if not.
    exec "$VENV_DIR/bin/python" "$HELPER" --pos-v2-root "$POS_V2_ROOT" --mode resume
fi

# ---- Phase 1: Python version gate ---------------------------------
#
# Detection order (research §3.2):
#   1. $POS_V2_PYTHON (CI / dev escape hatch)
#   2. python3.13 on PATH
#   3. /opt/homebrew/bin/python3.13 (Homebrew ARM)
#   4. /usr/local/bin/python3.13 (Homebrew Intel / some Linux)
#   5. python3 on PATH (verify 3.13+)
# On failure: step-by-step install instructions per the Core Dev
# Convention (docs/rebuild/FUTURE_IDEAS.md "step-by-step when the
# system cannot act").

_verify_version_ge_313() {
    # Echo the full version if ok; exit nonzero otherwise.
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
    # Escape hatch: if POS_V2_PYTHON is set, we commit to it. No fallback
    # chain — a caller who set this variable expressed intent. On failure,
    # halt with the version-gate diagnostic rather than silently picking
    # another candidate (which would hide the override being broken).
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
    cat <<EOF_DIAG
pos v2 first-run: halted at Phase 1 (python-version-gate).

Error code: -32091 platform-unsupported:no-compatible-python-found
Required:   Python 3.13 or newer
Detected:   none

The system cannot install Python 3.13 for you. Follow the steps for
your platform below; expected time ~2-5 minutes. Then reopen this
workspace in Claude Code — first-run will pick up from here.

  macOS (Homebrew):
    1. Install Homebrew if you do not have it: https://brew.sh  (~2 min)
    2. Run: brew install python@3.13                              (~1 min)
    3. Reopen this workspace in Claude Code.

  Ubuntu 24.04:
    1. sudo add-apt-repository ppa:deadsnakes/ppa                 (~30 s)
    2. sudo apt update                                            (~30 s)
    3. sudo apt install python3.13 python3.13-venv                (~1 min)
    4. Reopen this workspace in Claude Code.

  Ubuntu 25.04+ / Fedora 40+ / Debian 13:
    1. sudo apt install python3.13 python3.13-venv                (~1 min)
       (Fedora: sudo dnf install python3.13 python3.13-venv)
    2. Reopen this workspace in Claude Code.

  Other:
    1. pyenv install 3.13                                         (~2 min)
    2. Reopen this workspace in Claude Code.
EOF_DIAG
    exit 0
fi

# Verify python3.13-venv module is available (Debian/Ubuntu gotcha,
# research §3.5). `python -m venv --help` returns non-zero when the
# venv module is missing despite the interpreter being present.
if ! "$DETECTED_PYTHON" -m venv --help >/dev/null 2>&1; then
    cat <<EOF_DIAG
pos v2 first-run: halted at Phase 1 (python-venv-module-missing).

Error code: -32091 platform-unsupported:python-venv-module-missing
Detected:   Python $DETECTED_VERSION at $DETECTED_PYTHON
Missing:    python -m venv (the stdlib venv module)

The system cannot install the venv module for you. On Debian/Ubuntu
the 'python3.13' package does not always bring 'python3.13-venv'.
Follow the steps for your platform; expected time ~1 minute.

  Ubuntu/Debian:
    1. sudo apt install python3.13-venv                           (~30 s)
    2. Reopen this workspace in Claude Code.

  Other:
    1. Reinstall Python from a distribution that bundles venv.
    2. Reopen this workspace in Claude Code.
EOF_DIAG
    exit 0
fi

# ---- Phase 2: top-level venv creation -----------------------------
#
# python -m venv is idempotent — a no-op if the venv already exists
# and is healthy. We only reach this branch if Phase 0 did NOT find
# a healthy venv (absence of .venv/bin/python), so this is a create,
# not a maybe-create.

printf 'pos v2 first-run: creating top-level venv at %s (using %s, %s)...\n' \
    "$VENV_DIR" "$DETECTED_PYTHON" "$DETECTED_VERSION"

if ! "$DETECTED_PYTHON" -m venv "$VENV_DIR" 2>&1; then
    cat <<EOF_DIAG
pos v2 first-run: halted at Phase 2 (venv-creation-failed).

Error code: -32099 hands-off-lifecycle-internal:venv-creation-failed
Detected:   Python $DETECTED_VERSION at $DETECTED_PYTHON
Target:     $VENV_DIR

The venv creation command failed. Usually this means the target
directory is not writable or disk is full.

  1. Check disk free space (df -h "$POS_V2_ROOT").
  2. Check permissions on the workspace root.
  3. Remove a partial venv if present: rm -rf "$VENV_DIR"
  4. Reopen this workspace in Claude Code.
EOF_DIAG
    exit 0
fi

# Verify the venv shipped a working pip (ensurepip should have fired).
if [ ! -x "$VENV_DIR/bin/pip" ] && [ ! -x "$VENV_DIR/bin/pip3" ]; then
    cat <<EOF_DIAG
pos v2 first-run: halted at Phase 2 (venv-pip-missing).

Error code: -32099 hands-off-lifecycle-internal:venv-pip-missing
Venv:       $VENV_DIR (created)
Missing:    pip inside the venv

On Debian/Ubuntu this happens when python3-venv is installed without
ensurepip support.

  1. sudo apt install python3.13-venv                             (~30 s)
  2. rm -rf "$VENV_DIR"
  3. Reopen this workspace in Claude Code.
EOF_DIAG
    exit 0
fi

# ---- Phase 3+: hand off to the Python helper ----------------------
#
# From here everything is stdlib-Python: per-component venv creation +
# pip install, .claude/settings.json author/merge, plist substitution
# and service bootstrap, health verification, confirmation sentence
# emission, self-retire of this script + SessionStart-stanza rewrite,
# final-state verification. The helper writes progress directly to
# stdout so Claude Code surfaces it as additionalContext.

exec "$VENV_DIR/bin/python" "$HELPER" --pos-v2-root "$POS_V2_ROOT" --mode bootstrap
