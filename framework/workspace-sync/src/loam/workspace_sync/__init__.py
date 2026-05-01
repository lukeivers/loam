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

"""pOS v2 workspace-sync — git-merge-based canonical-to-workspace sync.

D-migration D.3 (amendment #64) — pos-sync becomes a thin wrapper
around `git fetch + git merge --ff-only` against
``<workspace>/framework/``. The pre-D.3 bespoke resolve→stage→apply
pipeline retired (~2400 LOC); the LLM-resolver primitives
(``merge_resolver.py`` + ``_resolver_client.py`` with
``--strict-mcp-config``) are preserved as the rare-conflict fallback
the new CLI invokes only when ``git merge`` produces unresolved
conflicts.

HC#6 of D-migration: the merge operates exclusively inside
``<workspace>/framework/``; files under ``<workspace>/workspace/``
are structurally untouchable.

Operator-visible CLI verbs:

    pos-sync [--canonical <path-or-url>] \\
             [--ref <commit-or-branch>] [--workspace <path>] \\
             [--auto-accept]

    pos-workspace-sync ...   # alias
"""

__version__ = "0.2.0"
