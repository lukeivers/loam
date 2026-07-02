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

"""AC.CRAC.3 ★ (outcome-altitude) — a truncated HTTP body read
(``http.client.IncompleteRead``) is routed to ``FetchError`` through the
production ``fetch_source`` entry-point, so the caller marks the entry
stale rather than silently retaining it as current (the AC.CLP-CUR.5
protection floor).

``http.client.IncompleteRead`` is an ``HTTPException`` — NOT an
``OSError`` — so without the explicit catch re-authored in
``fetch.py`` (stranded in the unreachable cloud commit) it would escape
the fetch handler uncaught. This test drives the real ``fetch_source``
with no pre-arranged state: a patched ``urlopen`` whose ``read()`` raises
``IncompleteRead``.
"""

from __future__ import annotations

import http.client

import pytest

from capability_refresh.fetch import FetchError, fetch_source


class _TruncatedResponse:
    """Stands in for the ``urlopen()`` context-manager response whose body
    read is truncated mid-stream."""

    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        raise http.client.IncompleteRead(b"half a body", 999)


def test_AC_CRAC_3_incomplete_read_raises_fetch_error(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "capability_refresh.fetch.urllib.request.urlopen",
        lambda req, timeout=None: _TruncatedResponse(),
    )
    with pytest.raises(FetchError):
        fetch_source("https://example.com/anything", tmp_path)


def test_AC_CRAC_3_incomplete_read_is_not_an_oserror():
    """Regression guard on WHY the explicit catch is load-bearing: if
    ``IncompleteRead`` were an ``OSError`` the pre-existing handler would
    already cover it and no fix would be needed. It is not."""
    assert not issubclass(http.client.IncompleteRead, OSError)
    assert issubclass(http.client.IncompleteRead, http.client.HTTPException)
