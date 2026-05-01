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

"""pOS self-upgrade framework.

External CLI that coordinates every sealed component's existing
upgrade-fidelity surfaces into a single atomic operation enforcing the
seven-clause acceptance (a–g) from v1.1 R1 of the pOS objectives spec.

Entry point: :func:`self_upgrade.cli.main` (`pos upgrade <tag>`).

Rollback is whole-upgrade atomic; partial acceptance is rejected on
first-principles grounds (the sealed components are coupled — half-
upgraded state is undefined).
"""

from .manifest import (
    BreakingChange,
    ChangeKind,
    ComponentSchema,
    FileEntry,
    Manifest,
    Migration,
    load_manifest,
    save_manifest,
)
from .conflict_report import (
    ConflictEntry,
    ConflictReport,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)

__all__ = [
    "BreakingChange",
    "ChangeKind",
    "ComponentSchema",
    "ConflictEntry",
    "ConflictReport",
    "FileEntry",
    "Manifest",
    "Migration",
    "Resolution",
    "load_conflict_report",
    "load_manifest",
    "save_conflict_report",
    "save_manifest",
]
