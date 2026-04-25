"""loam-mode — pos-v2 dev-mode auto-load partition selector + audit.

Sub-plan F (two-modes-and-multi-workspace programme) — partition
data + selector + audit. Sub-plan B (amendment #45 + dev-discipline
companion) — SessionStart emitter that consumes the partition.
"""

from loam_mode.manifest import (
    Manifest,
    ManifestEntry,
    load_manifest,
    expand_entry,
)
from loam_mode.selector import select_corpus
from loam_mode.audit import (
    AuditReport,
    audit_partition,
    scan_cross_mode_references,
)
from loam_mode.session_start import (
    DEFAULT_DEV_EXTENSION_FILENAME,
    build_loam_mode_inner_hook,
    compute_session_mode,
    emit_session_start_context,
    read_dev_intent_safe,
)

__all__ = [
    "Manifest",
    "ManifestEntry",
    "load_manifest",
    "expand_entry",
    "select_corpus",
    "AuditReport",
    "audit_partition",
    "scan_cross_mode_references",
    "DEFAULT_DEV_EXTENSION_FILENAME",
    "build_loam_mode_inner_hook",
    "compute_session_mode",
    "emit_session_start_context",
    "read_dev_intent_safe",
]
