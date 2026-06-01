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

"""loam-acceptance-smoke — the loam 1.0 acceptance smoke.

The non-tech-user end-to-end gate (design: docs/plans/loam-1.0-acceptance-smoke.md).
Drives the REAL production `loam init` + first-run intake through three
fully role-played non-technical white-collar users, then judges the resulting
end-state against the prime-objective promise (VALUE_PROPOSITION) on named
orthogonal dimensions.

Every `claude -p` (the role-played user side AND every judge probe) spawns
ONLY through `loam_spawn_isolation.spawn_isolated_claude` (--strict-mcp-config
+ empty mcpServers + token/API-key-scrubbed env) so it cannot steal the
operator's single-consumer Telegram bot slot. No Anthropic API key —
subscription-only.

AC ladder (design §5): SMOKE.1 outcome-altitude / SMOKE.2 cross-variant
materially-different seeds / SMOKE.3 deep-research only-in-C within budget /
SMOKE.4 every rubric dimension scored with cited evidence / SMOKE.5
re-runnable + self-cleaning throwaway workspace.
"""

from __future__ import annotations

__all__ = [
    "VARIANTS",
    "VariantSpec",
    "run_variant",
    "VariantRun",
    "run_smoke",
    "SmokeReport",
]

from .variants import VARIANTS, VariantSpec
from .runner import run_variant, VariantRun
from .judge import run_smoke, SmokeReport
