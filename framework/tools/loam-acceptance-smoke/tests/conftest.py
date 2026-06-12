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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""Suite-local src-path resolution for loam-acceptance-smoke.

Resolves this tool's own ``src/`` onto ``sys.path`` so the suite
collects from a fresh checkout with no package installation (the
handsoff-loop / capability-refresh conftest precedent;
broken-suite-family-fixes AC.SUITEFIX.2). Without it the test modules
fail collection with ``ModuleNotFoundError: loam_acceptance_smoke``
whenever the tool is not editable-installed in the running
interpreter.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
