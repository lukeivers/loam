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

"""loam protection-matrix — the protection pillar made a living, machine-
checkable catalogue + the ``loam guards`` coverage-check verb.

The catalogue (``data/failure-mode-guard-matrix.yaml``) is the single source
of truth: each known way an AI betrays a user by default × loam's actual
guard × default-on? × floor-vs-proportional × how we verify it fires. The
``loam guards`` verb derives the live guard set from ground truth, reconciles
it against the catalogue, and NAMES the gaps (the actionable output).
"""

from __future__ import annotations

__version__ = "0.1.0"

from .catalogue import (
    GuardRow,
    Catalogue,
    SchemaError,
    load_catalogue,
    default_catalogue_path,
)
from .derive import resolve_guard_ref, GuardRefResolution
from .check import (
    RowVerdict,
    CoverageReport,
    run_coverage_check,
    render_report,
    render_companion_doc,
)

__all__ = [
    "__version__",
    "GuardRow",
    "Catalogue",
    "SchemaError",
    "load_catalogue",
    "default_catalogue_path",
    "resolve_guard_ref",
    "GuardRefResolution",
    "RowVerdict",
    "CoverageReport",
    "run_coverage_check",
    "render_report",
    "render_companion_doc",
]
