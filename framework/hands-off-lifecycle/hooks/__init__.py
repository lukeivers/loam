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

"""hands-off-lifecycle hook surfaces.

Phase-5-second-component: ``true-first-run`` installs here because
first-run is hands-off-lifecycle's mechanical prerequisite — the
supervisor the hook fragment describes only becomes invokable once
first-run has built the venv it needs.

Modules:
    first_run_inventory — stdlib-only YAML-subset parser for
        ``first-run-inventory.yaml``.
    first_run_settings  — .claude/settings.json stanza-specific merge.
    first_run_helper    — entry point invoked by ``first-run.sh``.
"""
