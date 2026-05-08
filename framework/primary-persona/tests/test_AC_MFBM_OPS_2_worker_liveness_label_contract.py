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

"""AC.MFBM-OPS.2 — Worker-liveness Label-contract regression-pin.

Plan ref: ``docs/plans/m-fbm-operational-health.md`` §4
AC.MFBM-OPS.2.

Diagnosis trigger (2026-05-04): the dispatch's hypothesised failure
mode was a generic ``com.loam.ws.memory-write-worker`` Label being
hijackable across workspaces. Empirical finding (Surface #2 of the
plan): the ``service_label`` function in workspace-bootstrap already
namespaces the Label by workspace slug per amendment #6. This test
pins the function-level contract so a future regression that
re-introduces a generic Label or breaks slug derivation surfaces
immediately rather than silently.

The companion launchctl-side test lives at
``framework/workspace-bootstrap/tests/test_AC_MFBM_OPS_5_plist_label_workspace_slug.py``
— same regression surface, tested at the scaffold-output level.

Per ODD §2.5 every assertion below maps to AC.MFBM-OPS.2.
"""

from __future__ import annotations

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import service_label


def test_AC_MFBM_OPS_2_label_for_pos3_slug_is_workspace_namespaced() -> None:
    """``service_label("memory-write-worker", "pos3")`` returns the
    namespaced reverse-DNS Label launchd uses for the live workspace
    on Luke's machine (``com.loam.pos3.memory-write-worker``)."""
    label = service_label("memory-write-worker", "pos3")
    assert label == "com.loam.pos3.memory-write-worker"
    # Negative regression-pin: the generic legacy shape MUST NOT
    # appear in the returned Label.
    assert "com.loam.ws.memory-write-worker" not in label


def test_AC_MFBM_OPS_2_label_for_alpha_ws_slug_is_workspace_namespaced() -> None:
    """Mirror the AC.J.5 ``alpha-ws`` fixture: distinct workspaces
    get distinct Labels."""
    label = service_label("memory-write-worker", "alpha-ws")
    assert label == "com.loam.alpha-ws.memory-write-worker"


def test_AC_MFBM_OPS_2_label_for_canonical_pos_v2_slug_is_namespaced() -> None:
    """A long-form realistic slug also produces the namespaced
    Label — guards against a hypothetical bug that only handles
    short slugs."""
    label = service_label(
        "memory-write-worker", "ivers-corp-pos-v2"
    )
    assert label == "com.loam.ivers-corp-pos-v2.memory-write-worker"


def test_AC_MFBM_OPS_2_distinct_slugs_yield_distinct_labels() -> None:
    """The Label namespacing is a function of the slug — distinct
    slugs MUST yield distinct Labels (the property the diagnosis's
    hypothesised collision would have violated)."""
    label_a = service_label("memory-write-worker", "alpha-ws")
    label_b = service_label("memory-write-worker", "beta-ws")
    label_c = service_label("memory-write-worker", "pos3")
    assert label_a != label_b != label_c
    assert label_a != label_c


def test_AC_MFBM_OPS_2_unknown_kind_raises() -> None:
    """``service_label`` MUST raise ``ValueError`` for any kind not
    in the registered service-kinds — a defensive regression-pin
    against a change that removes the kind tuple's gate."""
    with pytest.raises(ValueError):
        service_label("not-a-real-kind", "pos3")
