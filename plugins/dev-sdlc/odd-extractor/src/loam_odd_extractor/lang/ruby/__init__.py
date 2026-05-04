"""Ruby/Rails first-class adapter (v0.1.8 Cycle 3).

Per AC.RAILS.1 — :class:`RubyAdapter` implements the
:class:`~loam_odd_extractor.registry.LanguageAdapter` Protocol.

Public API:

- :class:`RubyAdapter` — the adapter class.
- :func:`extract_rails_acs` — convenience function that runs the
  full extraction against a single repo path.

Per :doc:`AC.RAILS.6 </docs/rebuild/plans/v0-1-8-cycle-3-ruby-rails-adapter>`,
the adapter emits :class:`~loam_odd_extractor.bands.BandedAC` instances
with confidence per Rails idiom:

- VERIFIED — passing RSpec / Minitest test (per AC.RAILS.3).
- PLAUSIBLE — ActiveRecord / migrations / callbacks / concerns /
  polymorphic / jobs / routes (per AC.RAILS.2).
- HYPOTHESISED — heuristic-derived domain inference (per Surface #4).
"""

from __future__ import annotations

from .adapter import RubyAdapter, extract_rails_acs

__all__ = ["RubyAdapter", "extract_rails_acs"]
