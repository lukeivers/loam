"""R22: all OTel emissions route through whatever TracerProvider is
globally installed. The primitive must not construct its own.
"""

from __future__ import annotations

import sys


def test_R22_no_tracerprovider_constructed() -> None:
    """Grep the source — no TracerProvider/TracerProvider() instantiation
    inside the primitive."""
    import reversibility_primitive as rp

    # Scan every source file listed under the package.
    import pathlib

    pkg_dir = pathlib.Path(rp.__file__).parent
    offenders: list[str] = []
    for py in pkg_dir.rglob("*.py"):
        text = py.read_text()
        # We allow the word in comments/docstrings. Scan for an
        # actual call expression.
        if "TracerProvider(" in text:
            offenders.append(str(py))
    assert offenders == [], (
        f"Primitive constructs its own TracerProvider in: {offenders}"
    )


def test_R22_uses_get_tracer() -> None:
    """Sanity — the emitter uses opentelemetry.trace.get_tracer, which
    reads whatever provider the observability-aggregator installs."""
    from reversibility_primitive import observability as obs

    import inspect

    src = inspect.getsource(obs)
    assert "trace.get_tracer(" in src
