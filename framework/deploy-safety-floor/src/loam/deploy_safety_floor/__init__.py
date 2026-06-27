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

"""loam deploy-safety FLOOR — framework-native gate primitives.

The always-on safety floor for loam's productionizing capability: a
per-environment config abstraction, a destructive-action classifier whose
gate strength is ``max(declared, resolved-target)``, an attestation-record
contract with a refuse-all-destructive default posture, and the PreToolUse
gate that reads them. Every higher (opt-in) deploy tier composes ON this
floor; no marketplace toggle casually turns it off.

Scope boundary (plan §3 HALT-2): this component ships the framework-side
SCAFFOLD + DEFAULT POSTURE only. The live provider probes that POPULATE an
attestation record (deletion-protection reads, Object-Lock, IAM scoping,
``prevent_destroy``) are deploy-tier and are NOT implemented here.
"""

from __future__ import annotations
