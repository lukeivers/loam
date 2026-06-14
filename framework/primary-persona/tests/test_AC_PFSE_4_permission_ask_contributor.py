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

"""AC.PFSE.4 — an outbound reply containing a permission-asking pattern
on authorized work is caught (warned/flagged for rewrite) by a Stop-hook
contributor.

Verification surface (plan §5): the contributor, given a turn whose
reply says "want me to X?" on authorized work, emits the rewrite/flag; a
clean reply emits nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.stop_contributors_builtin import (
    permission_ask_contributor,
)
from loam.primary_persona.stop_contributor import (
    StopContributorRegistry,
    build_default_registry,
    run_stop_contributors,
)


_CTX = {"workspace_root": Path("."), "session_id": "s1"}


# ----- the contributor flags a closing-line permission-ask -----


@pytest.mark.parametrize(
    "reply",
    [
        "Did the work.\n\nWant me to dispatch the next slice?",
        "Built it.\n\nShall I proceed?",
        "Done.\n\nShould I go ahead and run the seal?",
        "Finished.\n\nConfirm and I'll dispatch the next cycle.",
        "Ready.\n\nWould you like me to start the build?",
        "Complete.\n\nDo you want me to continue?",
    ],
)
def test_AC_PFSE_4_permission_ask_flagged(reply: str) -> None:
    advisory = permission_ask_contributor(
        outbound_reply=reply, context=_CTX
    )
    assert advisory is not None
    assert advisory.name == "permission-ask"
    assert "permission-ask" in advisory.message.lower()


# ----- a clean reply (decision stated) emits nothing -----


@pytest.mark.parametrize(
    "reply",
    [
        "Dispatching the next slice now.",
        "Slice A sealed. Proceeding to Slice B.",
        "Built and sealed; moving on.",
        "",
        "   ",
    ],
)
def test_AC_PFSE_4_clean_reply_emits_nothing(reply: str) -> None:
    advisory = permission_ask_contributor(
        outbound_reply=reply, context=_CTX
    )
    assert advisory is None


# ----- a mid-reply clarifying question is NOT flagged (closing-only) ---


def test_AC_PFSE_4_midreply_question_not_flagged() -> None:
    """A genuine clarifying question mid-reply (not a closing-line ask)
    is legitimate and must not trip the contributor."""
    reply = (
        "Want me to use approach A or B? Here is the analysis...\n\n"
        "I went with approach A and shipped it. The build is green.\n"
        "Slice complete; moving to the next one.\n"
        "Tests pass. Sidecar advanced. Seal landed.\n"
        "No further action needed.\n"
        "All done."
    )
    advisory = permission_ask_contributor(
        outbound_reply=reply, context=_CTX
    )
    assert advisory is None


# ----- through the framework's compose path -----


def test_AC_PFSE_4_via_run_stop_contributors() -> None:
    out = run_stop_contributors(
        outbound_reply="Work done.\n\nWant me to proceed?",
        workspace_root=Path("."),
    )
    assert out is not None
    assert "systemMessage" in out
    assert "permission-ask" in out["systemMessage"].lower()


def test_AC_PFSE_4_clean_via_run_stop_contributors() -> None:
    out = run_stop_contributors(
        outbound_reply="Dispatching now.",
        workspace_root=Path("."),
    )
    assert out is None


# ----- registry registers the contributor -----


def test_AC_PFSE_4_registered_in_default_registry() -> None:
    registry = build_default_registry()
    assert "permission-ask" in registry.names()


# ----- the framework is fail-soft on a raising contributor -----


def test_AC_PFSE_4_registry_fail_soft_on_raising_contributor() -> None:
    def _boom(*, outbound_reply, context):
        raise RuntimeError("synthetic")

    registry = StopContributorRegistry()
    registry.register("boom", _boom)
    registry.register("permission-ask", permission_ask_contributor)
    advisories = registry.compose(
        outbound_reply="Done.\n\nWant me to proceed?",
        context=_CTX,
    )
    # The raising contributor is skipped; the working one still fires.
    names = {a.name for a in advisories}
    assert names == {"permission-ask"}


def test_AC_PFSE_4_registry_rejects_duplicate_name() -> None:
    registry = StopContributorRegistry()
    registry.register("x", permission_ask_contributor)
    with pytest.raises(ValueError):
        registry.register("x", permission_ask_contributor)
