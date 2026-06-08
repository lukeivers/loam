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

"""loam frame-kernel — the resident microkernel (TCB) + the
SubagentStart auto-context handoff.

The keystone of the loam-realignment: extends loam governance from the
human->persona boundary down to the persona->subagent boundary by
lifting the SubagentStart primitive. The composition logic lives in
:mod:`loam.frame_kernel.bundle`; the hook entry-point at
``framework/frame-kernel/hooks/subagent_start_context.py`` reads a
SubagentStart envelope and emits the bundle as
``hookSpecificOutput.additionalContext``.
"""

from .bundle import (
    MISSING_KERNEL_MARKER,
    MICROKERNEL_PRIME_MARKER,
    compose_bundle,
    render_envelope,
)

__all__ = [
    "MISSING_KERNEL_MARKER",
    "MICROKERNEL_PRIME_MARKER",
    "compose_bundle",
    "render_envelope",
]
