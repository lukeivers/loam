"""Wire Graphiti up with the prototype's chosen backends.

Single responsibility: construct a Graphiti instance with the configured
LLM (subscription-routed ``claude -p``), embedder (Ollama via
OpenAI-compat endpoint), and graph driver (embedded Kuzu). All other
concerns live elsewhere.

Amendment #8 (memory-system-subscription-routed-llm, 2026-04-22)
swapped the LLM backend from graphiti-core's ``AnthropicClient``
(which reads ``ANTHROPIC_API_KEY`` and routes through the billed API)
to ``ClaudePrintLLMClient`` (which subprocesses ``claude -p`` and
routes through the user's Claude Max subscription via OAuth). Fresh
first-run completes end-to-end without an ``ANTHROPIC_API_KEY``.

Amendment #11 audit-closure (§F1) deleted the residual
``make_anthropic_client()`` factory + ``AnthropicClient`` import — no
caller remained in the tree, so the "kept for eval scripts" claim was
a §2.5 orphan surface.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.cross_encoder.bge_reranker_client import BGERerankerClient
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig

from .claude_print_client import ClaudePrintLLMClient


class LazyBGERerankerClient(BGERerankerClient):
    """Lazy-loading wrapper around graphiti-core's BGE reranker.

    Amendment #25 (bge-reranker-swap, 2026-04-22). The parent class's
    ``__init__`` calls ``CrossEncoder('BAAI/bge-reranker-v2-m3')``
    synchronously, which triggers a ~1 GB Hugging Face download on
    first run and several seconds of weight-load time even when warm.
    Paying that cost at factory-construction time is unacceptable:

    1. Every pytest run that imports ``make_graphiti`` would have to
       either load the real model or mock at the
       ``sentence_transformers`` boundary. The first is slow and
       network-dependent; the second spreads mock surface across
       every factory-adjacent test.
    2. Amendment #24's MCP service ``lifespan`` calls
       ``make_graphiti`` on every launchd KeepAlive restart. Startup
       would block on weight load even when the reranker is never
       exercised.

    Reranking is only touched when ``graphiti.search()`` runs with a
    reranker-enabled ``SearchConfig``. Deferring the model load until
    first ``rank()`` lines cost up with value: no-rerank paths cost
    zero; first rerank call pays the one-time load.

    The subclass deliberately skips ``super().__init__()`` — that
    method *is* the eager load. ``isinstance(x, BGERerankerClient)``
    remains true (AC25.1 assertion), and ``rank()`` delegates to the
    parent after ensuring the model is loaded.
    """

    def __init__(self) -> None:
        # Do NOT call super().__init__(); that's the eager model
        # load this wrapper exists to defer.
        self.model = None  # type: ignore[assignment]

    async def rank(
        self, query: str, passages: list[str]
    ) -> list[tuple[str, float]]:
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder("BAAI/bge-reranker-v2-m3")
        return await super().rank(query, passages)


# Embedding dimensions per supported model. Used to configure the
# embedder; mismatch with the underlying model produces silent breakage
# (vectors of the wrong size). Keep this in lock-step with the model
# manifest in Ollama.
EMBED_DIMS: dict[str, int] = {
    "nomic-embed-text": 768,
    "bge-large": 1024,
    "qwen3-embedding": 1024,
    # Add more as evaluated; default fallback is 1024.
}


def load_env(env_path: str | Path | None = None) -> None:
    """Load .env from the memory-system directory by default."""
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path, override=False)


async def make_claude_print_client(
    *, skip_auth_probe: bool = False
) -> ClaudePrintLLMClient:
    """Construct the subscription-routed LLM client (amendment #8 default).

    Fails closed at construction if the ``claude`` binary is missing
    (``ClaudeBinaryMissingError``, code -32110) or if OAuth is absent
    (``ClaudeUnauthenticatedError``, code -32111). No
    ``ANTHROPIC_API_KEY`` is read; the child subprocess runs with a
    scrubbed env so it cannot fall through to the billed API even when
    the parent has the key set.

    Amendment #11 audit-closure (§F2) made this helper ``async``. The
    probe that validates OAuth state is itself async; running it from
    sync ``__init__`` while the caller already has an event loop
    running (the common case — ``make_graphiti`` is async) required a
    sync-over-async bridge with no AC backing. The async form awaits
    the probe directly. Sync-context callers instantiate
    ``ClaudePrintLLMClient`` directly; they don't go through this
    factory.
    """
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
    small = os.environ.get("ANTHROPIC_SMALL_MODEL", "claude-haiku-4-5")
    config = LLMConfig(model=model, small_model=small)
    client = ClaudePrintLLMClient(config=config, skip_auth_probe=True)
    if not skip_auth_probe:
        await client.probe_authenticated()
    return client


def make_ollama_embedder(model: str | None = None) -> OpenAIEmbedder:
    """Construct an Ollama-backed embedder via the OpenAI-compat endpoint.

    Ollama exposes /v1/embeddings on the same port as its native API;
    this is what the proposal calls the 'vendor-free on merit' path.
    """
    model = model or os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    api_key = os.environ.get("OLLAMA_API_KEY", "ollama")
    dim = EMBED_DIMS.get(model, 1024)
    config = OpenAIEmbedderConfig(
        api_key=api_key,
        embedding_model=model,
        embedding_dim=dim,
        base_url=base_url,
    )
    return OpenAIEmbedder(config=config)


def make_kuzu_driver(db_path: str | Path | None = None) -> KuzuDriver:
    """Construct the embedded Kuzu graph driver.

    Default path is the project's data/kuzu_db directory; pass an
    absolute path or `:memory:` for ephemeral test runs.

    Workaround for graphiti-core 0.28.2 (two bugs in KuzuDriver):

    1) `_database` attribute is declared on the GraphDriver base class
       but never initialised by KuzuDriver, while `Graphiti.add_episode`
       reads `self.driver._database` to decide whether to clone the
       driver per-group_id. Initialise the attribute here so passing
       a non-default `group_id` doesn't AttributeError. Single-file
       Kuzu doesn't actually do per-DB isolation; the attribute is
       just a marker for the clone-on-group-id-change branch.

    2) `KuzuDriver.build_indices_and_constraints` is a `pass` no-op
       with a comment claiming Kuzu doesn't support dynamic indices,
       but `KuzuGraphMaintenanceOperations.build_indices_and_constraints`
       actually does need to be invoked to create the FTS indices the
       search code depends on (`node_name_and_summary`, etc.). Without
       these indices, `graphiti.search()` raises a Kuzu Binder exception.
       Patch the driver to delegate to its own `_graph_ops`.
    """
    if db_path is None:
        db_path = os.environ.get("KUZU_DB_PATH", "./data/kuzu_db")
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    driver = KuzuDriver(db=str(db_path))
    driver._database = ""  # Match get_default_group_id(KUZU) so the
    # add_episode branch never tries to .clone() the driver.

    # Bug 2 workaround: route build_indices_and_constraints through the
    # graph_ops object that actually knows how to create FTS indices.
    # Make it idempotent: Kuzu raises a Binder exception when an index
    # already exists, but graphiti-core's gathered execution treats any
    # one failure as fatal. Catch and swallow "already exists" errors so
    # restart is safe.
    async def _build_indices_via_graph_ops(delete_existing: bool = False):
        from graphiti_core.graph_queries import (
            get_fulltext_indices,
            get_range_indices,
        )
        from graphiti_core.graph_queries import GraphProvider

        if delete_existing:
            await driver._graph_ops.delete_all_indexes(executor=driver)

        index_queries = (
            get_range_indices(GraphProvider.KUZU)
            + get_fulltext_indices(GraphProvider.KUZU)
        )
        for query in index_queries:
            try:
                await driver.execute_query(query)
            except RuntimeError as exc:
                if "already exists" in str(exc):
                    continue
                raise

    driver.build_indices_and_constraints = _build_indices_via_graph_ops  # type: ignore[method-assign]
    return driver


async def make_graphiti(
    *,
    embedder_model: str | None = None,
    db_path: str | Path | None = None,
) -> Graphiti:
    """Build a fully-wired Graphiti instance.

    After amendment #8 the LLM backend is ``ClaudePrintLLMClient`` —
    every graphiti LLM call (entity extraction, deduplication,
    summarisation, edge extraction, attribute extraction) subprocesses
    ``claude -p`` and routes through the user's Claude Max subscription
    via OAuth. No ``ANTHROPIC_API_KEY`` is required or consulted; the
    factory fails closed if the ``claude`` binary is missing or OAuth
    state is absent.

    The caller is responsible for `await graphiti.build_indices_and_constraints()`
    on first use (it's idempotent but does a round-trip per call).

    Token-usage observation: the LLMClient base class auto-instantiates
    a TokenUsageTracker; D4 reads `graphiti.llm_client.token_tracker`
    after ingest to break down cost by prompt name. Amendment #8 adds a
    parallel ``cost_tracker`` attribute on ``ClaudePrintLLMClient``
    that records ``total_cost_usd`` from the ``claude -p`` JSON
    envelope (typically 0.0 on Max, but Anthropic still reports an
    equivalent-cost estimate useful for subscription-usage budgeting).

    Full-build addition: after indices are built, ensure the Episodic
    table carries the D10 `retention_class` column. We do it lazily at
    first add_episode in MemoryAPI rather than here, to avoid a Kuzu
    connection before build_indices_and_constraints runs.

    Amendment #25 (bge-reranker-swap) passes an explicit
    ``cross_encoder=LazyBGERerankerClient()`` argument. Without it,
    ``graphiti_core.Graphiti.__init__`` defaults unset
    ``cross_encoder`` to ``OpenAIRerankerClient()`` — a billed-API
    reranker that fails with ``openai.AuthenticationError`` on first
    rerank when ``OPENAI_API_KEY`` is unset (which it is on our
    fresh-first-run target; amendment #8 removed billed-API coupling
    from the LLM path and this closes the parallel hole on the
    reranker path).
    """
    llm_client = await make_claude_print_client()
    embedder = make_ollama_embedder(embedder_model)
    driver = make_kuzu_driver(db_path)
    graphiti = Graphiti(
        llm_client=llm_client,
        embedder=embedder,
        graph_driver=driver,
        cross_encoder=LazyBGERerankerClient(),
    )
    return graphiti


async def prepare_graphiti(graphiti: Graphiti) -> None:
    """Run the idempotent graph init steps a MemoryAPI expects.

    - build_indices_and_constraints (FTS, range, vector indices)
    - ALTER TABLE Episodic ADD retention_class (D10)

    Call this once after make_graphiti() for each session where
    MemoryAPI is going to ingest. Safe to call multiple times.
    """
    from .retention import ensure_retention_column

    await graphiti.build_indices_and_constraints()
    await ensure_retention_column(graphiti.driver)
