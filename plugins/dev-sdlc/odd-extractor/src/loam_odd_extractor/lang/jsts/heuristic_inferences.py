"""Heuristic-shaped HYPOTHESISED-band inference for JS/TS.

Per AC.JSTS.5 + Surface #7 — Cycle 4a produces HYPOTHESISED ACs
from heuristic-shaped inferences over already-extracted PLAUSIBLE
ACs. Mirror of Cycle 3 ``lang/ruby/heuristic_inferences.py``.

Per AC.DRY.3 (v0.1.8 Cycle 4b) — the per-heuristic
``BandedAC(... confidence=HYPOTHESISED, evidence=Evidence(
kind="inference", ...))`` boilerplate is delegated to
:func:`make_inferred_banded_ac` from
``loam_odd_extractor.lang._common.heuristic_helpers``. This module
retains the per-language regex tables + heuristic firing logic.

Heuristic patterns (5; extensible — Cycle 4b/5+ extends this list):

- Zod ``email: z.string().email()`` (or chained ``.email()``)
  → "<Schema> requires a valid email" (HYPOTHESISED — runtime
  usage may be conditional).
- Zod ``<field>: z.string().min(N)`` → "<Schema>.<field> has
  minimum length N" (HYPOTHESISED).
- class-validator ``@IsEmail()`` on field → "<Class>.<field> must
  be a valid email" (HYPOTHESISED).
- Express middleware chain naming auth-like middleware
  (``requireAuth``, ``authenticate``, ``isLoggedIn``, ``withAuth``,
  ``requireUser``) → "Route <method> <path> requires authentication"
  (HYPOTHESISED).
- Playwright page-object method named ``login*``/``signIn*``/
  ``signUp*`` → "Page object <X> exposes an authentication entry
  point" (HYPOTHESISED).
"""

from __future__ import annotations

import re

from ...bands import BandedAC, ConfidenceBand
from .._common.heuristic_helpers import make_inferred_banded_ac


# Regexes to extract structure from PLAUSIBLE AC text (from the
# JS/TS recognizers).
_ZOD_EMAIL_RE = re.compile(
    r"^Zod (\w+)\.(\w+):.*\.email\(\)"
)
_ZOD_MIN_LEN_RE = re.compile(
    r"^Zod (\w+)\.(\w+):.*\.min\((\d+)\)"
)
_CV_IS_EMAIL_RE = re.compile(
    r"^(\w+)\.(\w+) validated by @IsEmail\(\)"
)
_EXPRESS_AUTH_MW_RE = re.compile(
    r"^Express route (\w+) (\S+) with middleware \[([^\]]+)\]"
)
_PAGE_AUTH_METHOD_RE = re.compile(
    r"^(\w+)#(login\w*|signIn\w*|signUp\w*): page-interaction method"
)

_AUTH_MW_TOKENS = (
    "requireauth", "authenticate", "isloggedin", "withauth",
    "requireuser", "ensureauth", "needsauth", "checkauth",
    "verifyauth", "loginrequired",
)


def _has_auth_middleware(middleware_csv: str) -> tuple[bool, str | None]:
    """Return ``(matched, matching_token)`` if the middleware list
    contains an auth-named middleware.
    """
    for raw in middleware_csv.split(","):
        token = raw.strip().lower()
        for needle in _AUTH_MW_TOKENS:
            if needle in token:
                return True, raw.strip()
    return False, None


def infer_domain_rules(
    banded_acs: list[BandedAC],
) -> list[BandedAC]:
    """Produce HYPOTHESISED BandedACs from already-extracted
    PLAUSIBLE ACs.

    Each heuristic that fires emits one HYPOTHESISED BandedAC with
    ``evidence.kind="inference"`` and a non-empty ``rationale``
    field naming the source heuristic + the source AC's ac_id.
    """
    out: list[BandedAC] = []

    for ac in banded_acs:
        if ac.confidence is not ConfidenceBand.PLAUSIBLE:
            continue
        text = ac.text
        ac_id = ac.ac_id

        # Heuristic 1: Zod `.email()` validator → "<Schema> requires
        # a valid <field>".
        m = _ZOD_EMAIL_RE.match(text)
        if m:
            schema, field = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.JSTS.inferred.zod_email_required."
                        f"{schema.lower()}.{field.lower()}"
                    ),
                    text=(
                        f"Inferred: {schema} requires a valid "
                        f"{field}"
                    ),
                    rationale=(
                        f"heuristic: Zod schema {schema} has "
                        f"a `{field}: z.string().email()` "
                        f"chain → infers email-format requirement. "
                        f"Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 2: Zod `.min(N)` validator → "<Schema>.<field>
        # has minimum length N".
        m = _ZOD_MIN_LEN_RE.match(text)
        if m:
            schema, field, n = m.group(1), m.group(2), m.group(3)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.JSTS.inferred.zod_min_length."
                        f"{schema.lower()}.{field.lower()}"
                    ),
                    text=(
                        f"Inferred: {schema}.{field} has minimum "
                        f"length {n}"
                    ),
                    rationale=(
                        f"heuristic: Zod schema {schema} has "
                        f"a `{field}: ...min({n})` chain → "
                        f"infers minimum-length constraint. "
                        f"Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 3: class-validator @IsEmail → "<Class>.<field>
        # must be a valid email".
        m = _CV_IS_EMAIL_RE.match(text)
        if m:
            cls, field = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.JSTS.inferred.cv_is_email."
                        f"{cls.lower()}.{field.lower()}"
                    ),
                    text=(
                        f"Inferred: {cls}.{field} must be a valid "
                        f"email address"
                    ),
                    rationale=(
                        f"heuristic: class-validator @IsEmail() "
                        f"on {cls}.{field} → infers email-format "
                        f"requirement. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )
            continue

        # Heuristic 4: Express auth middleware → "Route X requires
        # authentication".
        m = _EXPRESS_AUTH_MW_RE.match(text)
        if m:
            verb, path, mw_csv = m.group(1), m.group(2), m.group(3)
            matched, mw_name = _has_auth_middleware(mw_csv)
            if matched:
                out.append(
                    make_inferred_banded_ac(
                        ac_id=(
                            f"AC.JSTS.inferred.route_requires_auth."
                            f"{verb.lower()}."
                            f"{re.sub(r'[^a-z0-9]+', '_', path.lower()).strip('_') or 'root'}"
                        ),
                        text=(
                            f"Inferred: Route {verb} {path} requires "
                            f"authentication (middleware: {mw_name})"
                        ),
                        rationale=(
                            f"heuristic: Express route {verb} "
                            f"{path} chains middleware "
                            f"`{mw_name}` whose name matches the "
                            f"auth-token list → infers auth gate. "
                            f"Source AC: {ac_id}"
                        ),
                        source_ac=ac,
                    )
                )
                continue

        # Heuristic 5: Playwright page-object auth method → "Page
        # object <X> exposes an authentication entry point".
        m = _PAGE_AUTH_METHOD_RE.match(text)
        if m:
            page, method = m.group(1), m.group(2)
            out.append(
                make_inferred_banded_ac(
                    ac_id=(
                        f"AC.JSTS.inferred.page_auth_entry."
                        f"{page.lower()}.{method.lower()}"
                    ),
                    text=(
                        f"Inferred: page object {page} exposes an "
                        f"authentication entry point via "
                        f"{page}#{method}"
                    ),
                    rationale=(
                        f"heuristic: Playwright page object "
                        f"{page} has method {method} whose name "
                        f"matches the auth-method-prefix list "
                        f"(login*/signIn*/signUp*) → infers "
                        f"auth entry point. Source AC: {ac_id}"
                    ),
                    source_ac=ac,
                )
            )

    return out
