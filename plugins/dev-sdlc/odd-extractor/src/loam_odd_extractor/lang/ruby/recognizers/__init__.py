"""Rails-idiom recognizers (v0.1.8 Cycle 3).

Per AC.RAILS.2 — six idioms recognised; each lives in its own
module under this package. Per AC.RAILS.3 — RSpec + Minitest
recognizers emit VERIFIED-band ACs; the rest emit PLAUSIBLE.

Public API:

- ``ALL_RECOGNIZERS`` — list of (name, callable) pairs the adapter
  iterates. Each callable matches the
  :class:`Recognizer` Protocol.
- The seven idiom recognizers as named submodules.

Per Surface #1 — per-Rails-idiom file split. Each recognizer has a
matching test file at
``tests/lang/ruby/test_AC_RAILS_<n>_<slug>.py``.
"""

from __future__ import annotations

from .active_record import recognize_active_record_models
from .callbacks import recognize_callbacks
from .concerns import recognize_concerns
from .jobs import recognize_jobs
from .migrations import recognize_migrations
from .minitest_tests import recognize_minitest_tests
from .polymorphic import recognize_polymorphic_associations
from .routes import recognize_routes
from .rspec_tests import recognize_rspec_tests

__all__ = [
    "recognize_active_record_models",
    "recognize_callbacks",
    "recognize_concerns",
    "recognize_jobs",
    "recognize_migrations",
    "recognize_minitest_tests",
    "recognize_polymorphic_associations",
    "recognize_routes",
    "recognize_rspec_tests",
]
