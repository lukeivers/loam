"""AC25 — memory-system factory: explicit BGE reranker wiring.

Amendment #25 (bge-reranker-swap, 2026-04-22) swaps graphiti-core's
silent default reranker (``OpenAIRerankerClient`` — requires
``OPENAI_API_KEY``) for an explicit local BGE cross-encoder. The
factory introduces a ``LazyBGERerankerClient`` wrapper that defers
the ``CrossEncoder('BAAI/bge-reranker-v2-m3')`` model load from
``__init__`` to first ``rank()`` call, so:

1. ``make_graphiti()`` stays cheap at construction time (no ~1 GB
   HF download, no weight load). Amendment #24's MCP service
   lifespan, which calls ``make_graphiti`` at every launchd
   KeepAlive restart, is unaffected.
2. pytest runs don't need to mock the ``sentence_transformers``
   boundary — ``isinstance`` checks pass on the wrapper without
   loading the real model.

Tests asserted here:

- AC25.1 — ``make_graphiti()`` returns a Graphiti whose
  ``cross_encoder`` is a ``BGERerankerClient`` instance
  (subclass match via ``LazyBGERerankerClient``).
- AC25.2 — Instantiating ``LazyBGERerankerClient()`` directly does
  not load the model (``.model is None`` sentinel).
- AC25.3 — ``memory-system/requirements.txt`` pins
  ``sentence-transformers`` with a ``>=`` specifier.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from graphiti_core.cross_encoder.bge_reranker_client import BGERerankerClient
from graphiti_core.driver.driver import GraphDriver
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client.client import LLMClient

from src import factory
from src.factory import LazyBGERerankerClient, make_graphiti


# --- Stubs -----------------------------------------------------------------
# Graphiti.__init__ builds a ``GraphitiClients`` pydantic model that
# validates its fields with ``isinstance`` checks against the
# ``LLMClient`` / ``EmbedderClient`` / ``GraphDriver`` base ABCs.
# Subclassing the ABCs and providing no-op implementations of the
# abstract methods we don't exercise is enough to pass validation.


class _StubLLMClient(LLMClient):
    """Minimal LLMClient subclass. None of its methods are called by
    ``Graphiti.__init__`` — only ``set_tracer`` (inherited from
    ``LLMClient``). AC25.1 asserts cross_encoder shape, not LLM
    behaviour.
    """

    def __init__(self) -> None:  # noqa: D401
        # Skip parent __init__ — it reads env vars for API clients
        # we never need.
        self.model = "stub-model"
        self.small_model = "stub-small-model"
        self.tracer = None

    async def _generate_response(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def get_num_tokens(self, text: str) -> int:  # pragma: no cover
        return 0


class _StubEmbedderConfig:
    embedding_dim = 768


class _StubEmbedder(EmbedderClient):
    config = _StubEmbedderConfig()

    async def create(self, input_data):  # pragma: no cover
        return [0.0] * self.config.embedding_dim

    async def create_batch(self, input_data_list):  # pragma: no cover
        return [[0.0] * self.config.embedding_dim for _ in input_data_list]


from graphiti_core.graph_queries import GraphProvider


class _StubDriver(GraphDriver):
    """Minimal GraphDriver subclass. AC25.1 never touches the driver;
    the stub only needs to satisfy the pydantic ``isinstance`` check
    and expose the attributes Graphiti reads at ``__init__`` time.
    """

    provider = GraphProvider.KUZU

    def __init__(self) -> None:  # noqa: D401
        # Skip parent __init__; we're not connecting to anything.
        self._database = ""

    # Abstract surface — all no-op; never invoked by AC25.1.
    def execute_query(self, cypher_query_, **kwargs):  # pragma: no cover
        raise NotImplementedError

    async def execute_write(self, func, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def session(self, database=None):  # pragma: no cover
        raise NotImplementedError

    def close(self):  # pragma: no cover
        return None

    def delete_all_indexes(self):  # pragma: no cover
        raise NotImplementedError

    async def build_indices_and_constraints(
        self, delete_existing: bool = False
    ):  # pragma: no cover
        return None


async def _fake_make_claude_print_client(*, skip_auth_probe: bool = False):
    return _StubLLMClient()


def _fake_make_ollama_embedder(model=None):
    return _StubEmbedder()


def _fake_make_kuzu_driver(db_path=None):
    return _StubDriver()


# --- AC25.1 ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_AC25_1_make_graphiti_uses_bge_reranker_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``make_graphiti()`` wires a BGE reranker, not OpenAI.

    Without the amendment, ``graphiti_core.Graphiti.__init__`` would
    silently default ``cross_encoder`` to ``OpenAIRerankerClient()``
    (billed API, needs ``OPENAI_API_KEY``). This test asserts the
    explicit BGE wiring landed.
    """
    monkeypatch.setattr(
        factory, "make_claude_print_client", _fake_make_claude_print_client
    )
    monkeypatch.setattr(factory, "make_ollama_embedder", _fake_make_ollama_embedder)
    monkeypatch.setattr(factory, "make_kuzu_driver", _fake_make_kuzu_driver)

    graphiti = await make_graphiti()

    assert isinstance(graphiti.cross_encoder, BGERerankerClient), (
        f"cross_encoder must be a BGERerankerClient (or subclass); "
        f"got {type(graphiti.cross_encoder).__name__}. Without the "
        f"amendment-#25 explicit wiring, graphiti-core defaults to "
        f"OpenAIRerankerClient which requires OPENAI_API_KEY we do "
        f"not configure."
    )
    # And specifically the lazy subclass — not the eager parent.
    assert isinstance(graphiti.cross_encoder, LazyBGERerankerClient), (
        "cross_encoder must be the lazy wrapper so service startup "
        "does not pay the BGE model-load cost."
    )


# --- AC25.2 ----------------------------------------------------------------


def test_AC25_2_lazy_wrapper_defers_model_load() -> None:
    """``LazyBGERerankerClient()`` does NOT load the BGE model at
    construction time.

    Parent ``BGERerankerClient.__init__`` calls ``CrossEncoder(
    'BAAI/bge-reranker-v2-m3')`` eagerly — a ~1 GB HF download on
    first run. The wrapper's ``__init__`` must skip that and leave
    ``.model`` as a ``None`` sentinel.
    """
    client = LazyBGERerankerClient()
    assert client.model is None, (
        "LazyBGERerankerClient must defer the CrossEncoder load; "
        ".model should be None until first rank() call."
    )


# --- AC25.3 ----------------------------------------------------------------


def test_AC25_3_requirements_pins_sentence_transformers() -> None:
    """``memory-system/requirements.txt`` pins sentence-transformers.

    ``BGERerankerClient`` imports ``sentence_transformers.CrossEncoder``
    at module-load time (guarded by an ImportError-with-hint). The
    amendment adds the dep at the memory-system level so fresh
    venvs pick it up without needing ``graphiti-core[
    sentence-transformers]`` extras.
    """
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    text = req_path.read_text()
    # Match 'sentence-transformers>=X.Y.Z' (optionally with trailing
    # whitespace / comments). The floor doesn't need to be asserted
    # exactly — presence of a >= pin is the invariant.
    assert re.search(r"(?m)^sentence-transformers\s*>=", text), (
        "requirements.txt must pin sentence-transformers with a >= "
        "specifier (amendment #25). Found lines:\n" + text
    )
