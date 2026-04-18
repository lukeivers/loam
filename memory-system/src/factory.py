"""Wire Graphiti up with the prototype's chosen backends.

Single responsibility: construct a Graphiti instance with the configured
LLM (Anthropic Claude), embedder (Ollama via OpenAI-compat endpoint),
and graph driver (embedded Kuzu). All other concerns live elsewhere.

The brief constrains: Anthropic Max for all LLM work; local Ollama for
embeddings; no other vendors. Embedder is the one outside-Max component
(no Anthropic embedding API as of 2026-04-17).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from graphiti_core import Graphiti
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.anthropic_client import AnthropicClient
from graphiti_core.llm_client.config import LLMConfig


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


def make_anthropic_client(small: bool = False) -> AnthropicClient:
    """Construct the Anthropic LLM client used by Graphiti.

    `small` selects the small-model field, used by Graphiti for cheaper
    sub-prompts (entity dedupe, classification). The brief constraint
    is Anthropic-only — no fallback to other vendors.
    """
    model = os.environ.get(
        "ANTHROPIC_SMALL_MODEL" if small else "ANTHROPIC_MODEL",
        "claude-haiku-4-5",
    )
    config = LLMConfig(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model=model,
        small_model=os.environ.get("ANTHROPIC_SMALL_MODEL", "claude-haiku-4-5"),
    )
    return AnthropicClient(config=config)


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

    The caller is responsible for `await graphiti.build_indices_and_constraints()`
    on first use (it's idempotent but does a round-trip per call).

    Token-usage observation: the LLMClient base class auto-instantiates
    a TokenUsageTracker; D4 reads `graphiti.llm_client.token_tracker`
    after ingest to break down cost by prompt name.

    Full-build addition: after indices are built, ensure the Episodic
    table carries the D10 `retention_class` column. We do it lazily at
    first add_episode in MemoryAPI rather than here, to avoid a Kuzu
    connection before build_indices_and_constraints runs.
    """
    llm_client = make_anthropic_client()
    embedder = make_ollama_embedder(embedder_model)
    driver = make_kuzu_driver(db_path)
    graphiti = Graphiti(
        llm_client=llm_client,
        embedder=embedder,
        graph_driver=driver,
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
