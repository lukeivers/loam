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

"""keep-pace hook chain (keep-pace-with-user MVP).

Cycle 1 (KP0) ships the chain substrate: a fail-open-whole-chain runner
with a per-turn total-latency budget and per-hook latency observability,
plus the UserPromptSubmit + PreToolUse CLI entry points wired into the
hook surface. Later cycles (KP1 retrieval, KP9 draft-gate) register
contributors onto this chain; KP0 itself ships a no-op-safe chain so the
wiring can be proven fail-open before any memory logic exists.

Stdlib-only by design — these run inside the live Claude Code session
and must never import a heavy dependency or break the turn.
"""
