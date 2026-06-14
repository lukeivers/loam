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

"""AC.CLP-PUSH-RENDER.4 ★ — outcome-altitude.

A production-CLI render against the LIVE corpus with NO pre-arranged
state produces a well-formed marketplace tree (.claude-plugin/
marketplace.json + plugins/<name>/ each with plugin.json + skills/<name>/
SKILL.md) that validates. This invokes the production entry-point
``knowledge_pack.cli.main`` exactly as the cadence binding does, against
the real ``docs/capability-corpus/`` — no fixture, no pre-seeded pack.

This is the ★ AC: production entry-point, no pre-arranged state
(feedback_test_outcome_altitude_required).
"""

from __future__ import annotations

from pathlib import Path

from knowledge_pack.cli import main
from knowledge_pack.validate import validate_pack

# The real repo root: this test file is at
# framework/tools/knowledge-pack/tests/<this>.
REPO_ROOT = Path(__file__).resolve().parents[4]
LIVE_CORPUS = REPO_ROOT / "docs" / "capability-corpus"


def test_AC_CLP_PUSH_RENDER_4_production_cli_live_corpus(tmp_path):
    """Production entry-point renders the LIVE corpus into a validating
    marketplace tree, with no pre-arranged state."""
    assert LIVE_CORPUS.is_dir(), "live corpus must exist for the ★ render"
    pack_root = tmp_path / "live-pack"  # fresh, empty — no pre-arranged state

    # Invoke the production CLI exactly as the cadence step does.
    rc = main([
        "render",
        "--corpus-root", str(LIVE_CORPUS),
        "--pack-root", str(pack_root),
    ])
    assert rc == 0, "production render must exit clean"

    # The emitted tree is a well-formed marketplace (the CLI already
    # validated; re-validate here at outcome altitude).
    plugin_names = validate_pack(pack_root)
    assert plugin_names, "render produced no plugins"

    # The live-verified marketplace shape is present.
    assert (pack_root / ".claude-plugin" / "marketplace.json").is_file()
    assert (pack_root / "pack-manifest.json").is_file()
    assert (pack_root / "gate-record.json").is_file()

    # At least the Class A claude-code plugin renders from the live corpus
    # (goal.md / loop.md / etc. are real entries).
    assert "loam-knowledge-claude-code" in plugin_names
    cc_skills = list(
        (pack_root / "plugins" / "loam-knowledge-claude-code" / "skills").glob("*/SKILL.md")
    )
    assert cc_skills, "no claude-code skills rendered from the live corpus"


def test_AC_CLP_PUSH_RENDER_4_freshly_rendered_pack_not_publish_eligible(tmp_path):
    """The ★ render's default gate verdict is PENDING — a freshly
    rendered live pack is NOT publish-eligible (the curation gate holds at
    outcome altitude too)."""
    from knowledge_pack.gate import is_publish_eligible

    pack_root = tmp_path / "live-pack"
    rc = main(["render", "--corpus-root", str(LIVE_CORPUS),
               "--pack-root", str(pack_root)])
    assert rc == 0
    assert not is_publish_eligible(pack_root)
