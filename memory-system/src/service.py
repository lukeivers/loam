"""FastAPI wrapper around Graphiti — the 'managed local service' shape.

Why a service rather than library-only? D1's acceptance criterion calls
for 'a test Python call reaches Graphiti, submits an episode, retrieves
it via query — round-trip succeeds. Service auto-starts and survives a
restart.' A long-lived process holding the Kuzu connection (a) makes
auto-start meaningful (launchd KeepAlive), (b) gives the survives-a-
restart property a concrete test (kill, relaunch, query the prior
episode), and (c) matches the proposal's adaptation #4 (Graphiti MCP
hosting) shape without yet building the MCP layer itself.

The minimal endpoints intentionally mirror what the full-build adapter
will expose: health, ingest, search. No auth, no rate-limiting, no
persona context — those are full-build concerns.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from graphiti_core.nodes import EpisodeType
from pydantic import BaseModel, Field

from .factory import load_env, make_graphiti


# Module-level Graphiti instance, lazily built in lifespan.
_graphiti = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build Graphiti once at process start; close on shutdown."""
    global _graphiti
    load_env()
    _graphiti = await make_graphiti()
    await _graphiti.build_indices_and_constraints()
    try:
        yield
    finally:
        if _graphiti is not None:
            await _graphiti.close()


app = FastAPI(
    title="pOS v2 memory-system prototype",
    version="0.1.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    status: str
    llm_model: str | None = None
    embedder_dim: int | None = None
    db_path: str | None = None


class IngestRequest(BaseModel):
    name: str
    body: str
    source_description: str = "synthetic episode"
    reference_time: datetime | None = None
    source: str = Field(default="text", description="message | text | json")
    group_id: str = "default"


class IngestResponse(BaseModel):
    episode_uuid: str
    nodes_extracted: int
    edges_extracted: int


class SearchRequest(BaseModel):
    query: str
    group_ids: list[str] | None = None
    num_results: int = 10
    center_node_uuid: str | None = None


class SearchResultItem(BaseModel):
    fact: str
    edge_uuid: str
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    source_node_uuid: str
    target_node_uuid: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    if _graphiti is None:
        raise HTTPException(503, detail="graphiti not initialised")
    return HealthResponse(
        status="ok",
        llm_model=_graphiti.llm_client.model,
        embedder_dim=_graphiti.embedder.config.embedding_dim,
        db_path=os.environ.get("KUZU_DB_PATH", "./data/kuzu_db"),
    )


_EPISODE_TYPES = {t.value: t for t in EpisodeType}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest) -> IngestResponse:
    if _graphiti is None:
        raise HTTPException(503, detail="graphiti not initialised")
    source = _EPISODE_TYPES.get(req.source, EpisodeType.text)
    ref_time = req.reference_time or datetime.now(timezone.utc)
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)
    result = await _graphiti.add_episode(
        name=req.name,
        episode_body=req.body,
        source_description=req.source_description,
        reference_time=ref_time,
        source=source,
        group_id=req.group_id,
    )
    return IngestResponse(
        episode_uuid=result.episode.uuid,
        nodes_extracted=len(result.nodes),
        edges_extracted=len(result.edges),
    )


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    if _graphiti is None:
        raise HTTPException(503, detail="graphiti not initialised")
    edges = await _graphiti.search(
        query=req.query,
        center_node_uuid=req.center_node_uuid,
        group_ids=req.group_ids,
        num_results=req.num_results,
    )
    items = [
        SearchResultItem(
            fact=edge.fact,
            edge_uuid=edge.uuid,
            valid_at=edge.valid_at,
            invalid_at=edge.invalid_at,
            source_node_uuid=edge.source_node_uuid,
            target_node_uuid=edge.target_node_uuid,
        )
        for edge in edges
    ]
    return SearchResponse(query=req.query, results=items)


@app.get("/token-usage")
async def token_usage() -> dict[str, Any]:
    if _graphiti is None:
        raise HTTPException(503, detail="graphiti not initialised")
    by_prompt = _graphiti.llm_client.token_tracker.get_usage()
    total = _graphiti.llm_client.token_tracker.get_total_usage()
    return {
        "by_prompt": {
            name: {
                "input_tokens": u.total_input_tokens,
                "output_tokens": u.total_output_tokens,
                "call_count": u.call_count,
            }
            for name, u in by_prompt.items()
        },
        "total": {
            "input_tokens": total.input_tokens,
            "output_tokens": total.output_tokens,
        },
    }


def run() -> None:
    """Entry point for `python -m src.service`."""
    import uvicorn

    load_env()
    host = os.environ.get("GRAPHITI_SERVICE_HOST", "127.0.0.1")
    port = int(os.environ.get("GRAPHITI_SERVICE_PORT", "8765"))
    uvicorn.run(
        "src.service:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run()
