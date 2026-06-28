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

"""P1 — the LOCAL deploy tier of the dev->build->deploy spine.

An opt-in capability that composes ON the sealed deploy-safety floor and the
secure-build baseline. The floor stays idle at LOCAL (nothing irreversible
exists there); this tier adds the LOCAL-specific surface:

* ``acceptance`` — a P0-shape Acceptance record produced by a LOCAL build and
  judged by an independent check (AC.LOCAL.1).
* ``command_set`` — the enabled LOCAL verb set (no irreversible/prod action)
  + a destructive-SQL guard that WARNS, never blocks, against a disposable
  local target (AC.LOCAL.2).
* ``local_config`` — the additive ``role`` / ``backing_services`` fields the
  floor ignores and this tier reads (AC.LOCAL.2/.3 inputs).
* ``parity`` — the plain-language backing-service parity-gap surface against a
  downstream environment (AC.LOCAL.3).
* ``secrets`` — a LOCAL secret store backed by the OS keychain, never a
  repo-committed file (AC.LOCAL.4).
* ``build`` — ``build_local``, the real LOCAL build entry-point (AC.LOCAL.C
  outcome-altitude).
"""

from __future__ import annotations
