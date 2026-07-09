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

"""Single import site for the shared artifact-probe liveness reader.

WS-B1 reaps dead-holder leases using the SAME liveness reader the fleet
collector (WS-A2) reads: ``probe_liveness()`` in
``handsoff_loop/convergence.py``.  The registry must NOT hand-roll a
second liveness reader (dispatch constraint).  This module is the one
place the shared reader is imported; ``registry`` imports it from here.
"""

from __future__ import annotations

import sys
from pathlib import Path

# framework/file-lease-registry/src/loam/file_lease_registry/_liveness.py
#   parents[4] == framework/
_HANDSOFF_SRC = (
    Path(__file__).resolve().parents[4]
    / "tools"
    / "handsoff-loop"
    / "src"
)
if _HANDSOFF_SRC.is_dir() and str(_HANDSOFF_SRC) not in sys.path:
    sys.path.insert(0, str(_HANDSOFF_SRC))

from handsoff_loop.convergence import probe_liveness  # noqa: E402

__all__ = ["probe_liveness"]
