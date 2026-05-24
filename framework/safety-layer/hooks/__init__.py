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

"""PreToolUse safety hooks shipped with framework/safety-layer/.

Three hooks compose alongside the existing SafetyController:

* ``secret_pattern_guard.py`` — content + file-path secret detection
  (the 14-pattern ECC floor for content; the file-path patterns
  migrated from plugins/dev-sdlc/hooks/bash_guard.py per
  D-SECHK.OVERLAP partial-absorb).
* ``dangerous_flag_guard.py`` — git push --no-verify, git commit
  --no-verify, git push --force on protected branches.
* ``config_write_guard.py`` — Edit/Write/MultiEdit blocks against
  .eslintrc / biome.json / .pre-commit-config.yaml / .git/config.

All three fail-open (allow + structured-log on internal exception)
per D-SECHK.FAIL-OPEN. Toggle-off via
``LOAM_SAFETY_HOOKS=off`` (all) or
``LOAM_SAFETY_HOOKS_{SECRET,DANGEROUS_FLAG,CONFIG_WRITE}=off``
(individual).
"""
