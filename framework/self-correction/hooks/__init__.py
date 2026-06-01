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

"""Self-correction hooks — inbound-path entry-points that feed the
self-correction engine.

Currently:
  - ``distress_detector`` — the deterministic distress-signal detector
    (AC.SR-DISTRESS.1). The hook is the *detector* that, by the 2nd
    qualifying signal, trips the existing self-correction ``user_reported``
    correction path; it does NOT build a parallel correction engine.
"""
