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

"""D6 — Safe-mode narrative + deterministic fallback.

Acceptance (brief):
- Rate-limited / Garbage / Latency-sustained / partial-Overloaded
  produce Claude-authored narrative via the adapter.
- Down / fully-Overloaded / Auth-broken use the deterministic template
  (no Claude call attempted).
- Template covers what's paused, which mode, recommended action,
  resume conditions.
- Model is workspace-tunable; default claude-haiku-4-5.
- Template wording is workspace-tunable via YAML.
"""

from __future__ import annotations


from loam.dormancy import ClaudeClient, DegradationConfig, DegradationMode
from loam.dormancy.config import load_config
from loam.dormancy.notification import NarrativeRenderer

from .fakes import FakeInvoker


async def test_narrative_uses_claude_for_rate_limited() -> None:
    cfg = DegradationConfig()
    invoker = FakeInvoker(["Rate-limited: pausing LLM scopes, retry soon."])
    client = ClaudeClient(invoke=invoker)
    renderer = NarrativeRenderer(cfg=cfg, client=client)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.rate_limited,
        signal="rate_limited",
        policy="pause_llm_only",
        paused_scope_count=2,
    )
    assert "Rate-limited: pausing LLM scopes" in text
    # degradation-narrative prompt attribution recorded
    assert invoker.call_log[0]["prompt_name"] == "degradation-narrative"


async def test_narrative_uses_template_for_down_no_claude_call() -> None:
    cfg = DegradationConfig()
    invoker = FakeInvoker([])  # must NOT be invoked
    client = ClaudeClient(invoke=invoker)
    renderer = NarrativeRenderer(cfg=cfg, client=client)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.down,
        signal="connection_error",
        policy="pause_all",
        paused_scope_count=1,
    )
    assert len(invoker.call_log) == 0  # Claude NOT called
    assert "connection_error" in text
    assert "pause_all" in text


async def test_narrative_uses_template_for_auth_broken() -> None:
    cfg = DegradationConfig()
    invoker = FakeInvoker([])
    client = ClaudeClient(invoke=invoker)
    renderer = NarrativeRenderer(cfg=cfg, client=client)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.auth_broken,
        signal="auth_broken",
        policy="request_user_decision",
        paused_scope_count=0,
    )
    assert len(invoker.call_log) == 0
    assert "auth_broken" in text
    assert "ANTHROPIC_API_KEY" in text  # recommendation included


async def test_narrative_falls_back_to_template_on_claude_error() -> None:
    cfg = DegradationConfig()
    invoker = FakeInvoker([ConnectionError("unreachable")])
    client = ClaudeClient(invoke=invoker)
    renderer = NarrativeRenderer(cfg=cfg, client=client)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.rate_limited,
        signal="rate_limited",
        policy="pause_llm_only",
        paused_scope_count=1,
    )
    # Fallback template text
    assert "rate_limited" in text
    assert "pause_llm_only" in text


async def test_narrative_model_is_workspace_tunable_via_yaml() -> None:
    text = """
narrative:
  model: claude-opus-4-6
  timeout_seconds: 5
  fallback_template: "CUSTOM {mode}"
  recovery_template: "CUSTOM RECOVER {resumed_count}"
"""
    cfg = load_config(text=text)
    assert cfg.narrative.model == "claude-opus-4-6"
    renderer = NarrativeRenderer(cfg=cfg, client=None)
    text_alert = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.down,
        signal="x",
        policy="p",
        paused_scope_count=0,
    )
    assert text_alert == "CUSTOM down"
    text_rec = renderer.render_recovery(
        episode_id="ep", resumed_count=5, duration_seconds=1.0
    )
    assert text_rec == "CUSTOM RECOVER 5"


async def test_narrative_default_model_is_claude_haiku_45() -> None:
    cfg = DegradationConfig()
    assert cfg.narrative.model == "claude-haiku-4-5"


async def test_narrative_template_covers_four_required_fields() -> None:
    """Fallback template must cover: what's paused, which mode,
    recommended user action, resume conditions."""
    cfg = DegradationConfig()
    renderer = NarrativeRenderer(cfg=cfg, client=None)
    text = await renderer.render_alert(
        episode_id="ep",
        mode=DegradationMode.rate_limited,
        signal="rate_limited",
        policy="pause_llm_only",
        paused_scope_count=3,
    )
    # what's paused
    assert "3 scope" in text
    # which mode
    assert "rate_limited" in text
    # recommended action
    assert "Wait" in text or "clear" in text.lower()
    # resume conditions
    assert "probe" in text.lower() or "retry-after" in text.lower()
