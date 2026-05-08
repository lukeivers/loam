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

"""Amendment #26 — teardown observability retrofit (telegram-interface).

Verifies AvailabilityProbe.stop_background() surfaces a broad-Exception
background-task failure via logger.debug per tightened CDC 2. Also
verifies the CancelledError split — cancelled tasks remain silent
(expected flow), only broad Exception triggers the emission.
"""

from __future__ import annotations

import asyncio
import logging

import pytest

from loam.telegram_interface.availability import AvailabilityProbe


async def _raising_background():
    raise RuntimeError("synthetic background-task failure — amendment #26")


async def _cancel_friendly_background():
    try:
        await asyncio.sleep(3600.0)
    except asyncio.CancelledError:
        raise


@pytest.mark.asyncio
async def test_s4_stop_background_surfaces_broad_exception(caplog):
    async def _noop_getme():
        from loam.telegram_interface.availability import (
            ProbeResult,
        )
        return ProbeResult(available=True)

    probe = AvailabilityProbe(getme_probe=_noop_getme)
    # Install a background task that raises something OTHER than
    # CancelledError when awaited post-cancel.
    probe._background_task = asyncio.create_task(_raising_background())
    # Let it finish raising so the cancel() call is a no-op and the
    # await surfaces the RuntimeError.
    await asyncio.sleep(0)

    with caplog.at_level(
        logging.DEBUG, logger="loam.telegram_interface.availability"
    ):
        await probe.stop_background()

    matching = [
        r for r in caplog.records
        if r.name == "loam.telegram_interface.availability"
        and r.message == "availability_stop_background_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None
    assert matching[0].levelno == logging.DEBUG


@pytest.mark.asyncio
async def test_s4_stop_background_silent_on_cancelled_error(caplog):
    """CancelledError remains expected-flow per tightened CDC 2 — no
    logger emission on cancel."""
    async def _noop_getme():
        from loam.telegram_interface.availability import ProbeResult
        return ProbeResult(available=True)

    probe = AvailabilityProbe(getme_probe=_noop_getme)
    probe._background_task = asyncio.create_task(
        _cancel_friendly_background()
    )
    # Yield so the task starts.
    await asyncio.sleep(0)

    with caplog.at_level(
        logging.DEBUG, logger="loam.telegram_interface.availability"
    ):
        await probe.stop_background()

    matching = [
        r for r in caplog.records
        if r.name == "loam.telegram_interface.availability"
        and r.message == "availability_stop_background_failed"
    ]
    assert matching == [], (
        "CancelledError must remain silent per tightened CDC 2"
    )
