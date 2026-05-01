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

"""Foundational-adapter bundle — one adapter per sealed component.

Twelve adapters total. The asymmetry (declaration-only, sidecar
launcher, CLI probe, escape-hatch loader) is intentional: the
extension protocol absorbs it because `contribute(host)` means
"do whatever this component needs at boot."

Registration order for the three gate wraps matches the sealed
integration test `cost-governance/tests/test_ipc_wrap_composition.py`:

    Registration: cost → reversibility → safety
    Dispatch:     safety → reversibility → cost → orig_activate

(Proposal §3.2's `after` table inverted this; verified against the
sealed integration test. The DISPATCH objective in proposal §3.2 is
correct; only the registration-order `after=` declarations needed
inversion. See the build agent's return summary.)
"""
