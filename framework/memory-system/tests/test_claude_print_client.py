"""Acceptance tests for amendment #8 —
memory-system-subscription-routed-llm (ClaudePrintLLMClient).

Each AC (1-8) maps 1:1 to a test function per the proposal §3. AC7
(error-code-block discipline) introspects the
``ClaudePrintClientError`` hierarchy for the new -32110..-32119
memory-system runtime block. AC8 (reranker does not invoke billed
OpenAI at ingest) pins the subscription-routing invariant while
the full reranker replacement is deferred to a follow-up amendment.
AC9 (seal diff discipline) is exercised in
``tests/test_no_sealed_amendments.py`` — the memory-system half of the
multi-component seal.

Every test mocks the subprocess layer (``asyncio.create_subprocess_exec``)
and ``shutil.which`` — no real subprocess spawns during the suite.
Fixtures build synthetic ``claude -p --output-format json`` envelopes
that mirror the empirical shape verified 2026-04-22:

    {"type":"result", "result":"<text>", "total_cost_usd":<float>,
     "is_error":<bool>, ...}
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from pydantic import BaseModel, Field


# ---- fixtures -------------------------------------------------------


class _SmallResponse(BaseModel):
    """Tiny response_model used by AC3 parsing tests."""

    kind: str = Field(description="what kind of thing")
    count: int = Field(description="how many")


def _envelope(result_text: str, *, is_error: bool = False, cost: float = 0.0) -> str:
    """Build a fake claude -p --output-format json envelope."""
    return json.dumps(
        {
            "type": "result",
            "result": result_text,
            "total_cost_usd": cost,
            "is_error": is_error,
        }
    )


class _FakeProc:
    """Test double for the asyncio subprocess returned from create_subprocess_exec."""

    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self._stdout = stdout.encode("utf-8")
        self._stderr = stderr.encode("utf-8")
        self.returncode = 0

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def _make_exec_mock(stdout: str, stderr: str = "") -> MagicMock:
    """Build an AsyncMock for ``asyncio.create_subprocess_exec``.

    Records the argv + env kwarg each call via ``call_args_list`` so
    tests can assert on argv shape and env scrubbing (AC2).
    """

    async def _factory(*args: str, **kwargs: object) -> _FakeProc:
        return _FakeProc(stdout=stdout, stderr=stderr)

    return AsyncMock(side_effect=_factory)


# ---- AC1 — factory requires no ANTHROPIC_API_KEY -------------------


def test_AC1_make_graphiti_succeeds_without_anthropic_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Unset ANTHROPIC_API_KEY, patch subprocess + which to simulate an
    authenticated claude, and verify make_graphiti() returns a Graphiti
    instance without raising."""
    from src import factory

    # The proposal's AC1 is specifically about ANTHROPIC_API_KEY
    # absence — the Ollama embedder + graphiti's OpenAI reranker still
    # need OPENAI_API_KEY (used against the local Ollama endpoint), so
    # we only delete ANTHROPIC_API_KEY here. A placeholder Ollama-style
    # OPENAI_API_KEY is set to cover the embedder / reranker seams.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    with patch("src.claude_print_client.shutil.which", return_value="/usr/local/bin/claude"):
        # probe subprocess returns an authenticated envelope
        exec_mock = _make_exec_mock(_envelope("ready"))
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            graphiti = asyncio.run(
                factory.make_graphiti(db_path=str(tmp_path / "kuzu_db"))
            )

    assert graphiti is not None
    # The llm_client is the subscription-routed one, not AnthropicClient.
    from src.claude_print_client import ClaudePrintLLMClient

    assert isinstance(graphiti.llm_client, ClaudePrintLLMClient)


# ---- AC2 — argv + scrubbed env -------------------------------------


def test_AC2_subprocess_argv_and_env_scrubbed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Client spawns ``claude -p --no-session-persistence --output-format
    json --model <model> "<prompt>"``; env kwarg excludes
    ANTHROPIC_API_KEY / OPENAI_API_KEY even when parent has them set.

    Amendment #30 extension (AC-i,
    docs/plans/amendment-30-memory-system-env-scrubber-user.md):
    positive-assert that USER is preserved from the parent env into the
    scrubbed child env. Closes the USER-missing defect that shipped
    through amendments #8 and #11 — the pre-amendment AC2 test asserted
    API-key absence and PATH presence but never positive-presence of
    USER, so the silent drop of USER from the allowlist was invisible
    to this test by construction.
    """
    from src.claude_print_client import ClaudePrintLLMClient

    # Seed the parent env with keys that MUST NOT leak into the child.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-parent-should-never-reach-child")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-another-leak-candidate")
    # Amendment #30 AC-i: USER must survive the scrubbing pass. Use a
    # deliberately distinctive controlled-value so the assertion proves
    # the exact parent→child propagation, not a coincidental match with
    # whatever the CI runner's real USER happens to be.
    monkeypatch.setenv("USER", "amendment30-login-user")

    exec_mock = _make_exec_mock(_envelope('{"kind":"x","count":1}'))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            # skip_auth_probe=True because we're asserting on the live
            # _generate_response call, not the probe.
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            messages = [
                Message(role="system", content="sys"),
                Message(role="user", content="hi"),
            ]
            asyncio.run(
                client._generate_response(messages, response_model=_SmallResponse)
            )

    assert exec_mock.await_count == 1
    call = exec_mock.await_args
    argv = call.args
    env = call.kwargs["env"]

    assert argv[0] == "/bin/claude"
    # v0.2.5 corrective C5 — the MCP-isolation flag triple now precedes `-p`.
    # AC2's invariant is the print-mode SHAPE (the flags are present + ordered
    # correctly), not a literal index of `-p`. Use index-of so the assertion
    # composes with C5's prepend.
    assert "-p" in argv
    p_idx = argv.index("-p")
    # MCP-isolation flags must precede `-p` (Claude CLI requirement; per
    # AC.WSα.8 + AC.V025-C5.1).
    assert "--strict-mcp-config" in argv
    assert argv.index("--strict-mcp-config") < p_idx
    assert "--mcp-config" in argv
    assert argv.index("--mcp-config") < p_idx
    assert "--no-session-persistence" in argv
    assert "--output-format" in argv
    assert argv[argv.index("--output-format") + 1] == "json"
    assert "--model" in argv
    assert "--bare" not in argv  # AC2 hard-requirement: --bare never

    # Env scrub — API keys dropped, PATH preserved.
    assert "ANTHROPIC_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "PATH" in env  # child needs this to resolve claude-adjacent tools
    # Amendment #30 AC-i: USER preserved with the parent-env value.
    assert env["USER"] == "amendment30-login-user"


# ---- AC-ii (amendment #30) — pre-spawn structural check on child env -


def test_AC30_child_env_contains_login_user_at_spawn_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Amendment #30 AC-ii (pre-spawn structural check,
    docs/plans/amendment-30-memory-system-env-scrubber-user.md).

    At the moment memory-system is about to spawn a ``claude -p``
    subprocess, the dict that will be handed to the OS as the child's
    env contains ``USER`` bound to the login user's value — determined
    at construction time from the parent process's env.

    The scrubbed child-env dict is captured directly from the
    constructed ``ClaudePrintLLMClient._child_env`` attribute; no real
    subprocess ever executes. The invariant is structural on the
    scrubber's output, not a behavioural observation of a real
    ``claude`` process. Future regression of the USER-missing defect
    surfaces as a failing deterministic dict-invariant assertion, not
    as a runtime "Not logged in · Please run /login" message in
    production.
    """
    from src.claude_print_client import ClaudePrintLLMClient

    # Controlled login-user value the parent env carries at construction
    # time. The scrubber must propagate it verbatim into the child env.
    monkeypatch.setenv("USER", "amendment30-login-user-spawn-check")

    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=_make_exec_mock(_envelope("ready")),
        ):
            # skip_auth_probe=True so the test's pre-spawn inspection
            # runs against the ``_child_env`` dict populated in
            # ``__init__`` without depending on probe-subprocess
            # completion semantics.
            client = ClaudePrintLLMClient(skip_auth_probe=True)

    # Pre-spawn structural inspection: the dict that ``_generate_response``
    # will pass as ``env=self._child_env`` already exists on the client
    # after construction. No subprocess is ever actually executed —
    # AC-ii's invariant is on the scrubber's output dict.
    assert "USER" in client._child_env, (
        "pre-spawn child env is missing USER; amendment #30 AC-ii: the "
        "scrubber must preserve USER from the parent env so the "
        "claude CLI's OAuth keychain lookup succeeds"
    )
    assert client._child_env["USER"] == "amendment30-login-user-spawn-check"


# ---- AC3 — JSON parsing into expected dict -------------------------


def test_AC3_parses_claude_print_envelope_into_response_model_dict() -> None:
    """Given a synthetic envelope whose ``result`` field is a JSON blob
    matching a Pydantic response_model, the client returns the parsed
    dict."""
    from src.claude_print_client import ClaudePrintLLMClient

    result_blob = json.dumps({"kind": "fruit", "count": 7})
    exec_mock = _make_exec_mock(_envelope(result_blob, cost=0.01))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            messages = [
                Message(role="system", content="s"),
                Message(role="user", content="u"),
            ]
            resp = asyncio.run(
                client._generate_response(
                    messages, response_model=_SmallResponse
                )
            )

    assert resp == {"kind": "fruit", "count": 7}
    # total_cost_usd surfaced (§5 #4 observability ruling).
    assert client.cost_tracker.total_usd == pytest.approx(0.01)
    assert client.cost_tracker.call_count == 1


def test_AC3_malformed_result_json_raises_typed_parse_error() -> None:
    """Result text that isn't valid JSON raises ClaudePrintResponseError,
    not a bare JSONDecodeError that would leak through graphiti's retry."""
    from src.claude_print_client import (
        ClaudePrintLLMClient,
        ClaudePrintResponseError,
    )

    exec_mock = _make_exec_mock(_envelope("not-json {nope"))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            with pytest.raises(ClaudePrintResponseError):
                asyncio.run(
                    client._generate_response(
                        [Message(role="user", content="q")],
                        response_model=_SmallResponse,
                    )
                )


# ---- AC4 — claude binary missing -----------------------------------


def test_AC4_factory_fails_closed_when_claude_binary_missing() -> None:
    """shutil.which returns None → ClaudeBinaryMissingError; no
    subprocess spawn; remediation text names Claude Code."""
    from src.claude_print_client import (
        ClaudeBinaryMissingError,
        ClaudePrintLLMClient,
    )

    exec_mock = _make_exec_mock(_envelope("unused"))
    with patch("src.claude_print_client.shutil.which", return_value=None):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            with pytest.raises(ClaudeBinaryMissingError) as excinfo:
                ClaudePrintLLMClient()

    assert excinfo.value.code == -32110
    assert excinfo.value.kind == "claude-binary-missing"
    assert "Claude Code" in str(excinfo.value)
    assert exec_mock.await_count == 0, (
        "Structural refusal must halt before any subprocess spawn"
    )


# ---- AC5 — unauthenticated claude ----------------------------------


def test_AC5_factory_fails_closed_when_claude_not_logged_in() -> None:
    """Probe subprocess emits the 'Not logged in · Please run /login'
    signal → ClaudeUnauthenticatedError distinguishable from AC4's
    via the ``kind:`` label."""
    from src.claude_print_client import (
        ClaudeUnauthenticatedError,
        ClaudePrintLLMClient,
    )

    # This is the exact string the CLI produces when OAuth is absent —
    # per the empirical note in the task spec.
    probe_stdout = "Not logged in · Please run /login"
    exec_mock = _make_exec_mock(probe_stdout)
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            with pytest.raises(ClaudeUnauthenticatedError) as excinfo:
                ClaudePrintLLMClient()

    assert excinfo.value.code == -32111
    assert excinfo.value.kind == "claude-unauthenticated"
    # Distinguishable from AC4: different kind label on the payload.
    assert excinfo.value.kind != "claude-binary-missing"
    assert "claude /login" in str(excinfo.value) or "/login" in str(excinfo.value)


def test_AC5_envelope_wrapped_not_logged_in_also_halts() -> None:
    """If the CLI wraps the Not-logged-in signal inside its JSON
    envelope ({"result":"Not logged in..."}) the factory still halts."""
    from src.claude_print_client import (
        ClaudeUnauthenticatedError,
        ClaudePrintLLMClient,
    )

    wrapped = _envelope("Not logged in · Please run /login", is_error=True)
    exec_mock = _make_exec_mock(wrapped)
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            with pytest.raises(ClaudeUnauthenticatedError):
                ClaudePrintLLMClient()


# ---- AC6 — rate-limit translates to graphiti RateLimitError --------


def test_AC6_rate_limit_response_raises_graphiti_RateLimitError() -> None:
    """is_error=true + rate-limit marker → RateLimitError from graphiti
    so the existing retry-with-backoff machinery kicks in."""
    from src.claude_print_client import ClaudePrintLLMClient

    payload = _envelope(
        "Claude usage limit reached — rate limit exceeded; retry later",
        is_error=True,
    )
    exec_mock = _make_exec_mock(payload)
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            with pytest.raises(RateLimitError):
                asyncio.run(
                    client._generate_response(
                        [Message(role="user", content="q")],
                        response_model=_SmallResponse,
                    )
                )


def test_AC6_non_rate_limit_error_does_not_raise_RateLimitError() -> None:
    """Regression: a generic is_error=true response that is NOT a
    rate-limit must NOT be misrouted through RateLimitError (which
    graphiti's retry would hammer uselessly). Separate error class."""
    from src.claude_print_client import (
        ClaudePrintLLMClient,
        ClaudePrintResponseError,
    )

    payload = _envelope("model returned an unrelated error", is_error=True)
    exec_mock = _make_exec_mock(payload)
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            with pytest.raises(ClaudePrintResponseError):
                asyncio.run(
                    client._generate_response(
                        [Message(role="user", content="q")],
                        response_model=_SmallResponse,
                    )
                )


# ---- AC7 — error-code-block discipline -----------------------------


def test_AC7_error_classes_occupy_32110_through_32119_block() -> None:
    """Every ``ClaudePrintClientError`` (base + subclasses) defined by
    amendment #8 carries a ``.code`` inside the -32110..-32119
    memory-system runtime block. No class collides with sibling
    components' claimed codes.

    Amendment #11 audit-closure §F13: the base-class sentinel moved
    from -32099 (which collided with
    ``hands_off_lifecycle_internal`` per hands-off-lifecycle's README)
    to -32119, the last slot of memory-system's own runtime block. The
    assertion now includes the base class so future audits cannot
    re-introduce the collision.
    """
    import src.claude_print_client as mod
    from src.claude_print_client import ClaudePrintClientError

    # Find every ClaudePrintClientError (base + subclasses) defined in
    # the amendment's module. Introspection over module attributes is
    # the structural check the proposal names — every error class
    # including the base must sit inside the runtime block.
    error_classes: list[type[ClaudePrintClientError]] = []
    for name in dir(mod):
        obj = getattr(mod, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, ClaudePrintClientError)
        ):
            error_classes.append(obj)

    # Sanity — base class plus the three concrete ones.
    assert ClaudePrintClientError in error_classes
    assert len(error_classes) >= 4, (
        "expected at least base + 3 concrete subclasses in the hierarchy"
    )

    # Each class's .code is inside -32119 <= code <= -32110.
    forbidden_collisions = {
        -32095,  # staging-overflow (memory-system staging)
        -32096,  # drain-poison (memory-system drain)
        -32099,  # hands_off_lifecycle_internal (hands-off-lifecycle README)
    }
    for cls in error_classes:
        code = cls.code
        assert -32119 <= code <= -32110, (
            f"{cls.__name__}.code={code} is outside the memory-system "
            "runtime block -32110..-32119 claimed by amendment #8"
        )
        assert code not in forbidden_collisions, (
            f"{cls.__name__}.code={code} collides with a sibling "
            "component's claimed code (staging -32095, drain -32096, "
            "or hands_off_lifecycle_internal -32099)"
        )

    # Distinct-code invariant across the concrete subclasses (base may
    # equal one — but here it sits on -32119 and no concrete subclass
    # uses that slot, so all classes must have distinct codes).
    codes = [cls.code for cls in error_classes]
    assert len(codes) == len(set(codes)), (
        f"duplicate .code values across ClaudePrintClientError classes: {codes}"
    )

    # Explicit pin on the base-class sentinel — amendment #11 §F13
    # fix. If a future refactor moves it back into a sibling-owned
    # code, this line fires before the implicit collision-check above.
    assert ClaudePrintClientError.code == -32119


# ---- AC8 — reranker does not invoke billed OpenAI at ingest --------


class _StubEmbedder:
    """Fully-mocked embedder (amendment #11 §F10).

    Returns zero-vectors. No network call. Used in the AC8 ingest test
    so the memory-system factory's ingest path can run under fully
    mocked I/O (subprocess + embedder + graph driver) without any
    outbound HTTP.
    """

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim
        self.call_count = 0

    async def create(self, input_data):  # type: ignore[no-untyped-def]
        self.call_count += 1
        return [0.0] * self.dim

    async def create_batch(self, input_data_list):  # type: ignore[no-untyped-def]
        self.call_count += len(input_data_list)
        return [[0.0] * self.dim for _ in input_data_list]


def _ingest_subprocess_envelope() -> str:
    """Envelope returned for every LLM call during an AC8 ingest.

    The ``.result`` field holds JSON that validates against graphiti's
    extract-nodes and extract-edges response models simultaneously:
    ``extracted_entities`` + ``edges`` are both empty lists, which
    short-circuits the ingest pipeline — no entities means no
    dedupe-search, no embeddings, no reranker activity. With the
    extraction result empty, the only outbound work is the episode
    write through the (also mocked) graph driver.
    """
    return _envelope(
        json.dumps(
            {
                "extracted_entities": [],
                "edges": [],
                "summaries": [],
                "attributes": {},
                "name": "",
                "summary": "",
            }
        )
    )


def test_AC8_ingest_path_issues_no_openai_api_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """AC8 — memory-system's ingest path (``graphiti.add_episode``)
    must not issue any outbound OpenAI API request.

    Amendment #11 audit-closure §F10 rewrite: the original test stopped
    at factory construction, but AC8's text names *"memory-system's
    default ingest surface"* — the test must actually exercise
    ``add_episode`` behind fully-mocked subprocess + embedder + graph
    driver, then assert zero OpenAI calls *across that ingest*.

    Construction:
      - subprocess: patched ``asyncio.create_subprocess_exec`` returns
        a ``_ingest_subprocess_envelope`` for every call. Graphiti's
        extract-nodes / extract-edges prompts all receive the same
        empty-result JSON — no entities → no dedupe search → no
        embeddings → no reranker activity.
      - embedder: ``_StubEmbedder`` substituted onto ``graphiti.embedder``
        + ``graphiti.clients.embedder`` right after factory construction.
        No network calls to Ollama or OpenAI-compat endpoints.
      - graph driver: Kuzu driver pointed at ``:memory:`` via the
        factory. Kuzu is embedded; no network. ``build_indices_and_constraints``
        is invoked so writes succeed.

    Ingest:
      - ``MemoryAPI.ingest(body, name=..., source="text")`` runs the
        full memory-system ingest surface (D5 ephemerality → D6 scope
        → D8/D10 retention plan → ``graphiti.add_episode``).

    Assertion:
      - The ``openai`` HTTP boundary count is 0 *after* ingest, not
        only after construction.
    """
    from src import factory, memory as memory_mod

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Proposal AC8: OPENAI_API_KEY=ollama lets the auto-instantiated
    # OpenAIRerankerClient construct without error. Any actual call
    # issued against OpenAI would bypass this placeholder; this test
    # asserts the call is never issued at all.
    monkeypatch.setenv("OPENAI_API_KEY", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    # Intercept OpenAI at both the async- and sync- HTTP client
    # boundaries. The reranker composes an ``AsyncOpenAI`` under the
    # hood; any call surfaces through ``.post``.
    openai_call_count = {"n": 0}

    async def _never_call(*args: object, **kwargs: object) -> None:
        openai_call_count["n"] += 1
        raise AssertionError(
            "ingest path issued an outbound OpenAI request; amendment #8 "
            "requires zero billed-API calls from graphiti's default path"
        )

    import openai

    monkeypatch.setattr(openai.AsyncOpenAI, "post", _never_call, raising=False)
    monkeypatch.setattr(openai.OpenAI, "post", _never_call, raising=False)

    async def _drive_ingest() -> None:
        # Construct via the factory so the subscription-routed LLM
        # client + scrubbed env + probe path all exercise.
        with patch(
            "src.claude_print_client.shutil.which",
            return_value="/bin/claude",
        ):
            with patch(
                "src.claude_print_client.asyncio.create_subprocess_exec",
                new=_make_exec_mock(_ingest_subprocess_envelope()),
            ):
                # `:memory:` Kuzu so writes are in-memory and fast.
                graphiti = await factory.make_graphiti(db_path=":memory:")
                # Replace the embedder with a stub so no Ollama call
                # leaks. Graphiti's ``clients`` dataclass also carries
                # the embedder reference; both slots get stubbed.
                stub_embedder = _StubEmbedder()
                graphiti.embedder = stub_embedder
                graphiti.clients.embedder = stub_embedder
                # prepare_graphiti runs build_indices_and_constraints
                # + the D10 retention-class column add, so the full
                # MemoryAPI.ingest flow (including retention.apply_plan)
                # resolves.
                await factory.prepare_graphiti(graphiti)

                # AC8 invariant: OpenAI must stay untouched across the
                # ingest, not only construction.
                assert openai.AsyncOpenAI.post is _never_call, (
                    "OpenAI async client intercept was replaced before ingest"
                )

                # Isolated emitter so the test doesn't scribble into
                # the shared ``data/observability/`` runtime spool.
                from src.observability import Emitter

                emitter = Emitter(sink_dir=tmp_path / "obs")
                api = memory_mod.MemoryAPI(graphiti, emitter=emitter)
                result = await api.ingest(
                    body="memory-system AC8 ingest smoke",
                    name="ac8-smoke",
                    source="text",
                )
                # Ingest ran to completion: we got an episode uuid.
                assert result.episode_uuid is not None

    asyncio.run(_drive_ingest())

    # Zero OpenAI calls across factory construction AND the ingest.
    assert openai_call_count["n"] == 0, (
        f"ingest made {openai_call_count['n']} OpenAI calls; expected 0"
    )


# ---- amendment #11 §F3 — span attribute wiring --------------------


def test_memory_ingest_emits_claude_equivalent_cost_usd_span_attr(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Amendment #11 audit-closure §F3 — the landed implementation of
    proposal §5 #4 observability ruling.

    ``MemoryAPI.ingest`` snapshots ``cost_tracker.total_usd`` before
    and after each ingest and emits the delta as a
    ``claude.equivalent_cost_usd`` span attribute. Max-subscription
    calls typically report 0.0 here, but the mock envelope sets a
    non-zero cost to exercise the attribute-emission path.
    """
    from src import factory, memory as memory_mod
    from src.observability import Emitter

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "ollama")

    async def _drive() -> Emitter:
        # Envelope with a non-zero total_cost_usd so the delta is
        # observable on the span. The extraction result is still empty
        # (ingest short-circuits).
        cost_envelope = _envelope(
            json.dumps(
                {
                    "extracted_entities": [],
                    "edges": [],
                    "summaries": [],
                    "attributes": {},
                    "name": "",
                    "summary": "",
                }
            ),
            cost=0.0125,
        )
        with patch(
            "src.claude_print_client.shutil.which",
            return_value="/bin/claude",
        ):
            with patch(
                "src.claude_print_client.asyncio.create_subprocess_exec",
                new=_make_exec_mock(cost_envelope),
            ):
                graphiti = await factory.make_graphiti(db_path=":memory:")
                stub_embedder = _StubEmbedder()
                graphiti.embedder = stub_embedder
                graphiti.clients.embedder = stub_embedder
                await factory.prepare_graphiti(graphiti)

                # Isolated emitter writing under tmp_path so the test's
                # spans don't mix with any shared default sink.
                emitter = Emitter(sink_dir=tmp_path / "obs")
                api = memory_mod.MemoryAPI(graphiti, emitter=emitter)
                await api.ingest(
                    body="span-attr smoke",
                    name="ac11.5-smoke",
                    source="text",
                )
                return emitter

    emitter = asyncio.run(_drive())
    spans = emitter.read_spans()
    ingest_spans = [s for s in spans if s["name"] == "memory.ingest"]
    assert len(ingest_spans) == 1, f"expected one memory.ingest span, got {ingest_spans}"
    attrs = ingest_spans[0]["attributes"]
    assert "claude.equivalent_cost_usd" in attrs, (
        f"ingest span missing claude.equivalent_cost_usd attribute: {attrs}"
    )
    # The delta across the ingest is at least one call's cost
    # (extract_nodes always fires once). With a 0.0125-per-call mock,
    # the delta is some positive multiple of 0.0125.
    cost = attrs["claude.equivalent_cost_usd"]
    assert cost >= 0.0125 - 1e-9, (
        f"expected at least one call's worth of cost, got {cost}"
    )


# ---- argv shape regression -----------------------------------------


def test_argv_does_not_include_bare_flag() -> None:
    """Explicit regression: --bare bypasses OAuth and requires
    ANTHROPIC_API_KEY; its presence would defeat the whole amendment."""
    from src.claude_print_client import ClaudePrintLLMClient

    exec_mock = _make_exec_mock(_envelope('{"kind":"x","count":0}'))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            asyncio.run(
                client._generate_response(
                    [Message(role="user", content="q")],
                    response_model=_SmallResponse,
                )
            )

    argv = exec_mock.await_args.args
    assert "--bare" not in argv
