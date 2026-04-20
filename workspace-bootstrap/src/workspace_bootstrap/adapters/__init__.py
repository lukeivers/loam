"""Foundational-adapter bundle — one adapter per sealed component.

Twelve adapters total. The asymmetry (declaration-only, sidecar
launcher, CLI probe, escape-hatch loader) is intentional: the
extension protocol absorbs it because `contribute(host)` means
"do whatever this component needs at boot."

Registration order for the three gate wraps matches the sealed
integration test `cost-governance/tests/test_ipc_wrap_composition.py`:

    Registration: cost → reversibility → safety
    Dispatch:     safety → reversibility → cost → orig_activate

(Proposal §3.2's `after` table inverted this; verified against the
sealed integration test. The DISPATCH objective in proposal §3.2 is
correct; only the registration-order `after=` declarations needed
inversion. See the build agent's return summary.)
"""
