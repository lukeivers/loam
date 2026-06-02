# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pre-review secret auto-redaction (AC.BR.3) — composes the safety floor.

Every candidate item's bytes are scanned against the safety-layer's
14-pattern secret floor (``CONTENT_PATTERNS``) DURING assembly, and any match
is redacted BEFORE the user ever sees the review surface. The user is never
shown — and can never accidentally ship — a secret loam caught (Lens 1:
compose ``framework/safety-layer/hooks/_secret_patterns.py``, do not
re-implement a scanner).

The floor lives in a hook-script dir (not an installed package), so we source
it from its canonical file location in the loam tree — the SAME single source
of truth the safety hook itself loads. If the floor cannot be located (a
broken tree), this FAILS CLOSED: it raises rather than silently shipping
unredacted bytes, because a privacy floor that silently degrades is the
failure mode this whole layer exists to prevent.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

#: The plain-language placeholder a redacted secret is replaced with. Carries
#: zero internal vocabulary (it appears in the user-facing review surface).
SECRET_PLACEHOLDER = "[a password or secret loam removed for your safety]"


class SecretFloorUnavailable(RuntimeError):
    """The safety-layer secret floor could not be located — fail closed.

    Raised instead of returning unredacted bytes: silently skipping
    redaction would defeat AC.BR.3. The caller must treat this as a hard
    failure (no bundle is shown to the user without the floor having run).
    """


def _find_repo_root(start: Path | None = None) -> Path | None:
    """Walk up to the loam repo root (a dir with framework/ + docs/)."""
    cur = (start or Path(__file__).resolve()).parent
    for cand in (cur, *cur.parents):
        if (cand / "framework").is_dir() and (cand / "docs").is_dir():
            return cand
    return None


def _load_content_patterns() -> tuple[tuple[str, "re.Pattern[str]"], ...]:
    """Load (name, compiled-regex) pairs from the canonical secret floor.

    Sources ``framework/safety-layer/hooks/_secret_patterns.py`` by file path
    (the hook dir is not an installed package) and reads its public
    ``CONTENT_PATTERNS`` tuple. This is consumption of the sealed safety
    floor through its canonical file, NOT a re-implementation.
    """
    root = _find_repo_root()
    if root is None:
        raise SecretFloorUnavailable(
            "could not locate the loam repo root to source the secret floor"
        )
    floor_path = (
        root / "framework" / "safety-layer" / "hooks" / "_secret_patterns.py"
    )
    if not floor_path.is_file():
        raise SecretFloorUnavailable(
            f"secret floor not found at {floor_path}"
        )
    mod_name = "loam_egress_consent._secret_floor"
    spec = importlib.util.spec_from_file_location(mod_name, floor_path)
    if spec is None or spec.loader is None:
        raise SecretFloorUnavailable(
            f"could not load the secret floor module at {floor_path}"
        )
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the floor module uses @dataclass, which resolves
    # its own __module__ via sys.modules at class-creation time.
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    patterns = getattr(module, "CONTENT_PATTERNS", None)
    if not patterns:
        raise SecretFloorUnavailable(
            "secret floor module exposes no CONTENT_PATTERNS"
        )
    return tuple((p.name, p.regex) for p in patterns)


def redact_secrets(data: bytes) -> tuple[bytes, tuple[str, ...]]:
    """Redact every secret-floor match in *data* before review.

    Returns ``(redacted_bytes, matched_pattern_names)``. Decodes UTF-8
    leniently (errors replaced) for the regex scan — the floor patterns are
    ASCII credential shapes — and re-encodes the redacted text. If the floor
    cannot be sourced, raises ``SecretFloorUnavailable`` (fail-closed): a
    bundle is never shown to the user without the floor having run.

    The replacement is a plain-language placeholder (``SECRET_PLACEHOLDER``),
    so a redacted item's exact-bytes expansion shows the placeholder — the
    secret itself is gone from the bundle entirely, not merely hidden.
    """
    patterns = _load_content_patterns()
    text = data.decode("utf-8", errors="replace")
    matched: list[str] = []
    for name, rx in patterns:
        if rx.search(text):
            matched.append(name)
            text = rx.sub(SECRET_PLACEHOLDER, text)
    return text.encode("utf-8"), tuple(matched)
