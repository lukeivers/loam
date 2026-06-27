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

"""Secure-build baseline (Tilth ``F-SECURE-BUILD-BASELINE``, Sub-cycle C).

The always-on build floor for the artifact loam PRODUCES (a distinct
surface from securing loam itself). Three guarantees, on for every build
by default:

* **secrets-never-committed** (AC.SBB.1) — enforced in the safety-layer's
  ``secret_pattern_guard`` staged-diff extension; this package carries the
  non-tunable-floor declaration that names it (``strictness``).
* **dependency-hygiene audit** (AC.SBB.2) — ``dependency_audit`` shells out
  to the ecosystem audit (``npm audit`` / ``pip-audit``; Lens 1 compose,
  not a re-implemented vuln DB) and gates on a configured severity floor.
* **artifact-cleanliness** (AC.SBB.3) — ``gitignore_template`` (the floor
  ``.gitignore`` for harness runtime state + secrets) + ``artifact_sweep``
  (a pre-commit sweep that keeps those paths out even under ``git add -A``).

Strictness (block vs surface) is the only tunable; the secret floor is not
among the tunables (AC.SBB.4 — ``strictness``).
"""

from __future__ import annotations
