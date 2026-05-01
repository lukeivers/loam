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

"""ObjectiveFilter — Pydantic-shaped filter for `query_projection_view`.

Amendment #38 (objective-tracker schema widening) introduces this
module alongside the `lifted_from` provenance field. The filter is
the surface every Heavy-B downstream consumer composes against —
loam amend's `project` subcommand, primary-persona's tracker-context
contributor, future audit-coverage tools.

Field set is intentionally narrow: AC38.3 names exactly the keys
downstream Heavy-B consumers need (`authored_by` and
`lifted_from_source_doc`). Future filter expressiveness lands as new
optional `ObjectiveFilter` fields under §4 re-extension.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ObjectiveFilter(BaseModel):
    """Filter shape for `ObjectiveTracker.query_projection_view`.

    Empty filter (every field None) returns the full record set; any
    set field narrows the result to records matching ALL set fields
    (logical AND across declared keys). Records lacking the field a
    filter names (e.g. `lifted_from is None` when
    `lifted_from_source_doc` is set) are excluded — see AC38.3.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    authored_by: str | None = Field(default=None, min_length=1)
    """Match records whose `authored_by` equals this string. None
    means no constraint on `authored_by`."""

    lifted_from_source_doc: str | None = Field(default=None, min_length=1)
    """Match records whose `lifted_from.source_doc` equals this
    string. Records with `lifted_from is None` are excluded when this
    is set. None means no constraint on provenance."""

    def is_empty(self) -> bool:
        """True iff every filter field is unset (None)."""
        return self.authored_by is None and self.lifted_from_source_doc is None
