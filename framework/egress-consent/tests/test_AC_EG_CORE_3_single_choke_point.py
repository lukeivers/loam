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

"""AC.EG-CORE.3 — single choke point.

No user-content off-machine send exists except through the gate. Verified by
(1) a tree-grep over the component source: no raw network-egress call site
outside ``gate.py``; and (2) the send transport is invoked ONLY from
``EgressReleaseGate.release`` — there is no gate-bypass path that reaches a
transport.
"""

from __future__ import annotations

import re
from pathlib import Path

import loam.egress_consent as egress_consent

SRC_DIR = Path(egress_consent.__file__).resolve().parent

# Network-egress primitives that would constitute a raw off-machine send.
# The component must NOT call these anywhere — egress goes through the
# injected transport, which the gate alone invokes.
_RAW_EGRESS_PATTERNS = (
    r"\burllib\.request\b",
    r"\burlopen\b",
    r"\brequests\.(?:get|post|put|patch|delete)\b",
    r"\bhttp\.client\b",
    r"\bsocket\.socket\b",
    r"\bsmtplib\b",
    r"\bhttpx\b",
)


def _component_py_files() -> list[Path]:
    return [p for p in SRC_DIR.glob("*.py")]


def test_no_raw_egress_call_sites_in_component() -> None:
    """No source file performs a raw network send — egress is transport-only."""
    offending: list[str] = []
    for path in _component_py_files():
        text = path.read_text(encoding="utf-8")
        for pat in _RAW_EGRESS_PATTERNS:
            if re.search(pat, text):
                offending.append(f"{path.name}: {pat}")
    assert offending == [], (
        "raw network-egress call site(s) found outside the gate's injected "
        f"transport: {offending}"
    )


def test_transport_invoked_only_from_gate_release() -> None:
    """The ``self._transport(`` call appears ONLY in gate.py's release path.

    A grep-level structural check that the single choke point holds: the
    transport is invoked from exactly one place.
    """
    transport_call = re.compile(r"self\._transport\(")
    callers: list[str] = []
    for path in _component_py_files():
        text = path.read_text(encoding="utf-8")
        if transport_call.search(text):
            callers.append(path.name)
    assert callers == ["gate.py"], (
        f"transport invoked outside gate.py: {callers}"
    )


def test_gate_has_no_bypass_send_method() -> None:
    """The gate exposes no public send-without-check method.

    Every public method that could emit goes through ``check`` first. We
    assert the only send-bearing public surface is ``release`` (which calls
    ``check`` as its first statement).
    """
    from loam.egress_consent.gate import EgressReleaseGate

    public = [
        name
        for name in dir(EgressReleaseGate)
        if not name.startswith("_")
    ]
    # The send-capable surface is exactly {check, release}; check is pure.
    assert set(public) == {"check", "release"}, (
        f"unexpected public gate surface (possible bypass): {public}"
    )

    # release() must call check() before touching the transport.
    import inspect

    src = inspect.getsource(EgressReleaseGate.release)
    check_idx = src.index("self.check(")
    transport_idx = src.index("self._transport(")
    assert check_idx < transport_idx, (
        "release() invokes the transport before checking — bypass risk"
    )
