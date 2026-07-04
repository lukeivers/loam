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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Domain review-methodology corpus — checked before every pull, KEPT (P6).

D7 / AC.AR.9: before reviewing a deeply-technical artifact, the stage
checks a canonical methodology corpus for a review-methodology doc
covering the artifact's domain. Present -> reuse it (review N+1 is
cheaper + sharper than review N — the standing capability's memory).
Missing/stale -> run ONE cited research pull (claim-or-cite), KEEP the
result in the indexed corpus, then apply it. The two methodology docs
shipped with this capability seed the corpus as its domain-agnostic
layer.

This module owns the KEEP + CHECK-BEFORE-PULL + INDEX + REUSE contract —
the part the brief pins. The automated WebSearch/WebFetch pull for a
brand-new domain is a documented SEAM (:func:`record_pull` accepts a
pulled doc + citations and keeps it); wiring a live auto-pull is staged
(it belongs with activation).

Per ODD §2.5: :func:`resolve` -> AC.AR.9 (check-before-pull + reuse);
:func:`record_pull` -> AC.AR.9 (KEEP + index + citations);
:func:`domain_agnostic_methodology` -> AC.AR.9 (seed docs present).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml  # type: ignore[import-untyped]

    _YAML = True
except Exception:  # noqa: BLE001 — degrade to a tiny built-in reader
    _YAML = False

# The corpus lives beside the package (a filesystem corpus with a YAML
# index — the mechanism is the builder's call per D7). Overridable for
# tests via CorpusStore(root=...).
_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "corpus"

# Staleness: age (days) beyond which a kept doc is flagged for refresh.
# A single default; a per-domain velocity multiplier is a staged knob.
DEFAULT_STALENESS_DAYS = 365


@dataclass
class MethodologyDoc:
    """A kept domain review-methodology doc (AC.AR.9).

    ``text`` is the failure taxonomy + named techniques + defect
    checklist the critic seeds with. ``citations`` is the claim-or-cite
    evidence (real sources) that KEPT research must carry (P6). ``kept``
    is the ISO date it was kept; ``stale`` marks it for refresh.
    """

    domain: str
    text: str
    citations: list[str] = field(default_factory=list)
    kept: str = ""
    path: str = ""
    stale: bool = False


class CorpusStore:
    """The indexed methodology corpus (AC.AR.9).

    Backed by ``<root>/index.yaml`` (domain -> {path, citations, kept})
    plus the doc files. :meth:`resolve` is the CHECK-BEFORE-PULL entry;
    :meth:`record_pull` is the KEEP entry.
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root else _DEFAULT_ROOT
        self.index_path = self.root / "index.yaml"

    # -- read -----------------------------------------------------------
    def _load_index(self) -> dict:
        if not self.index_path.exists():
            return {"domains": {}, "domain_agnostic": []}
        raw = self.index_path.read_text(encoding="utf-8")
        if _YAML:
            data = yaml.safe_load(raw) or {}
        else:
            data = _mini_yaml(raw)
        data.setdefault("domains", {})
        data.setdefault("domain_agnostic", [])
        return data

    def _is_stale(self, kept: str) -> bool:
        if not kept:
            return True
        try:
            kept_date = _dt.date.fromisoformat(kept)
        except ValueError:
            return True
        age = (_dt.date.today() - kept_date).days
        return age > DEFAULT_STALENESS_DAYS

    def resolve(self, domain: str) -> Optional[MethodologyDoc]:
        """CHECK the corpus for a domain's methodology BEFORE pulling (AC.AR.9).

        Returns the kept doc (marking it ``stale`` when past the staleness
        window) or ``None`` when the domain is uncovered — the signal to
        run a pull. Never pulls here; the check is the whole point.
        """
        index = self._load_index()
        entry = index["domains"].get(domain)
        if not entry:
            return None
        path = self.root / entry["path"]
        if not path.exists():
            return None
        kept = entry.get("kept", "")
        return MethodologyDoc(
            domain=domain,
            text=path.read_text(encoding="utf-8"),
            citations=list(entry.get("citations", [])),
            kept=kept,
            path=str(path),
            stale=self._is_stale(kept),
        )

    # The compact checklist seeded into the critic prompt (the Fagan
    # defect-checklist — the highest-yield inspection tool). Distilled from
    # the full kept docs, which stay in the corpus for citations/provenance.
    SEED_CHECKLIST = "domain-agnostic/AR-review-checklist.md"

    def seed_methodology(self) -> str:
        """The COMPACT methodology seeded into the critic prompt (P6 / D7).

        Returns the distilled failure-taxonomy checklist — small enough to
        seed on every call and more effective input than 28KB of research
        prose (Fagan: the checklist is the highest-yield tool). Falls back
        to the full domain-agnostic concatenation only if the checklist is
        absent, so the critic always has a real taxonomy, never none.
        """
        p = self.root / self.SEED_CHECKLIST
        if p.exists():
            return p.read_text(encoding="utf-8")
        return self.domain_agnostic_methodology()

    def domain_agnostic_methodology(self) -> str:
        """The always-available domain-agnostic methodology (AC.AR.9).

        Concatenates the seed docs (the general adversarial-review
        methodology + the AI-critic failure-modes doc). This is the
        floor every review seeds with when no domain-specific doc exists,
        so even an uncovered domain reviews against a real failure
        taxonomy, never against "good work" in the abstract (AI §F3).
        """
        index = self._load_index()
        names = index.get("domain_agnostic", [])
        texts: list[str] = []
        for name in names:
            p = self.root / name
            if p.exists():
                texts.append(p.read_text(encoding="utf-8"))
        return "\n\n".join(texts)

    # -- write (KEEP) ---------------------------------------------------
    def record_pull(
        self,
        domain: str,
        text: str,
        citations: list[str],
        *,
        kept: Optional[str] = None,
    ) -> MethodologyDoc:
        """KEEP a pulled methodology doc in the indexed corpus (AC.AR.9 / P6).

        The claim-or-cite discipline is enforced: a pull with no real
        citations is rejected — ephemeral, uncited research that
        evaporates per-review is exactly what P6 forbids. Writes the doc
        file + updates the index so review N+1 in this domain REUSES it.
        """
        if not citations or not any(c.strip() for c in citations):
            raise ValueError(
                "kept methodology requires real citations (claim-or-cite, "
                "P6): an uncited pull cannot be kept."
            )
        self.root.mkdir(parents=True, exist_ok=True)
        slug = "".join(c if c.isalnum() else "-" for c in domain.lower())
        rel = f"domain/{slug}.md"
        doc_path = self.root / rel
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(text, encoding="utf-8")
        kept = kept or _dt.date.today().isoformat()

        index = self._load_index()
        index["domains"][domain] = {
            "path": rel,
            "citations": citations,
            "kept": kept,
        }
        self._write_index(index)
        return MethodologyDoc(
            domain=domain,
            text=text,
            citations=citations,
            kept=kept,
            path=str(doc_path),
            stale=False,
        )

    def _write_index(self, index: dict) -> None:
        if _YAML:
            self.index_path.write_text(
                yaml.safe_dump(index, sort_keys=True), encoding="utf-8"
            )
        else:
            self.index_path.write_text(_dump_mini_yaml(index), encoding="utf-8")


# ---------------------------------------------------------------------
# Tiny YAML fallback (stdlib-only), used only when PyYAML is absent.
# Handles the flat index shape this module writes; not a general parser.
# ---------------------------------------------------------------------


def _mini_yaml(raw: str) -> dict:
    data: dict = {"domains": {}, "domain_agnostic": []}
    section = None
    current_domain = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            continue
        if section == "domain_agnostic" and stripped.startswith("- "):
            data["domain_agnostic"].append(stripped[2:].strip())
            continue
        if section == "domains":
            if indent == 2 and stripped.endswith(":"):
                current_domain = stripped[:-1].strip().strip('"')
                data["domains"][current_domain] = {"citations": []}
            elif current_domain and ":" in stripped:
                k, _, v = stripped.partition(":")
                k = k.strip()
                v = v.strip().strip('"')
                if stripped.startswith("- "):
                    data["domains"][current_domain].setdefault(
                        "citations", []
                    ).append(stripped[2:].strip())
                else:
                    data["domains"][current_domain][k] = v
    return data


def _dump_mini_yaml(index: dict) -> str:
    lines = ["domain_agnostic:"]
    for name in index.get("domain_agnostic", []):
        lines.append(f"  - {name}")
    lines.append("domains:")
    for domain, entry in index.get("domains", {}).items():
        lines.append(f'  "{domain}":')
        lines.append(f"    path: {entry.get('path', '')}")
        lines.append(f"    kept: {entry.get('kept', '')}")
        lines.append("    citations:")
        for c in entry.get("citations", []):
            lines.append(f"      - {c}")
    return "\n".join(lines) + "\n"
