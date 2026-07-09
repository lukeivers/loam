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

"""loam fleet page static render (WS-A3).

Regenerates one static HTML page — live agents, recent outcomes, this
week's token-cost proxy, and the "needs a human" decision queue — from
the WS-A2 fleet JSON, the observability-aggregator cost API, and the
per-project-pm decision queue.  No server; a launchd/cron job (NOT a
``.claude/settings.json`` hook) regenerates it.  Degrades per-source.

Source readers (``sources``) import their upstream packages lazily, so
this top-level import succeeds with none of them installed.
"""

from __future__ import annotations

from .generate import generate_page
from .render import render_page
from .schedule import install_launchd_job, render_cron_line, render_plist

__all__ = [
    "generate_page",
    "render_page",
    "install_launchd_job",
    "render_plist",
    "render_cron_line",
]
