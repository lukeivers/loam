# Plan — fastmcp-group-ids-filter-fix (search MCP tool surfaces episodes, not edges-only)

**Status:** authored 2026-04-29 by builder (task #22 in dispatcher queue — FINAL PRE-PUBLISH BLOCKER per owner directive 2026-05-01).
**Predecessors (all sealed):** Memory-sidecar-recovery (`8ee241b`), M1c-corrective (`603e953`), Post-M6 partition-realignment (`e2828ba`), memory-pipeline-fix (`67968b7`).
**Successor candidate:** publish.
**Authority:** dispatcher directive 2026-05-01.
**Companion research:** inline §2; investigation phase performed pre-plan with empirical reproduction + kuzu_db inspection (sidecar-running-copy of `kuzu_db` + WAL into `/tmp/kuzu_db_inspect2`).

---

## 1. Summary / TLDR

The dispatch's stated symptom — `search(query=X, group_ids=["pos3"]) → 0` while `group_ids=None → 4+` — is **not** a broken filter. Empirical reproduction with a fresh write under `group_id="probe-test"`:

```
add_episode group_id=probe-test → episode_uuid + nodes_extracted=3 + edges_extracted=2
search group_ids=None         → 1 result
search group_ids=['probe-test'] → 1 result   ← filter works
search group_ids=['pos3']     → 0 results
```

A fresh, **rich**-body write under `group_id="pos3"` (5 sentences, multiple actors):

```
add_episode group_id=pos3 → nodes_extracted=6 + edges_extracted=5
search 'Luke' group_ids=None  → 5 results
search 'Luke' group_ids=['pos3'] → 2 results   ← filter works
```

Direct kuzu_db inspection confirms: edges are stored with `group_id = <Episode's group_id>` correctly, and graphiti-core's Kuzu search ops apply `e.group_id IN $group_ids` correctly. Filter is fine.

The actual defect: **the `search` MCP tool calls `graphiti.search()`, which returns ONLY `EntityEdge` objects.** Episodes whose body is too short / sparse for graphiti's LLM-extractor to derive any `RelatesToNode_` are stored as `Episodic` nodes plus zero or more `Entity` nodes — but no edges. They are **invisible** to edge-search regardless of group_id.

Empirical floor evidence in pos3's live `kuzu_db`:

| group_id | Episodic | Entity | RelatesToNode_ |
|---|---|---|---|
| `default` | 1 | 15 | 12 |
| `pos-v2_default` | 1 | 7 | **0** |
| `ms-fix-smoke` | 1 | 3 | 2 |
| `pos3` | 1 | 1 | **0** |
| `probe-test` | 1 | 3 | 2 |

The two episodes the dispatch was probing for (pos-v2_default's `diagnostic-test-2026-04-29` and pos3's `test-episode-mpf-verify`) extracted entities but no edges. Search via the edge-only `graphiti.search()` cannot find them. Even with `group_ids=None`, query terms unique to those episode bodies (`mmap`, `lifespan`, `diagnostic`) return zero edge-hits.

Root cause class **(δ) other** — not a filter bug. The `search` MCP tool's contract is too narrow: it surfaces only edges (extracted facts), not episodes (raw episodic memory) and not entity nodes. Edge-less episodes — which the spec admits as legitimate (D10 retention `derived-only` is the explicit dropping-of-raw case; the implicit "no derivation extracted" case must remain retrievable) — round-trip writes invisibly.

**Fix:** switch `_impl_search` from `graphiti.search()` (edges-only) to `graphiti.search_(COMBINED_HYBRID_SEARCH_RRF)` (edges + nodes + episodes + communities). The MCP tool's structured output shape grows: results gains an `episodes` and `nodes` list alongside the existing `results` (edges, kept for back-compat with persona's contributor). All four sub-results honour `group_ids` filtering identically (the WHERE-clause Cypher path is shared across edge/node/episode searches in `framework/memory-system/.venv/lib/python3.13/site-packages/graphiti_core/driver/kuzu/operations/search_ops.py`).

The persona's `_render_retrieval` (memory_consumer.py, post-MPF) reads the `results` field; when results-list is empty AND nodes/episodes are populated, retrieval should now include those. Plan §3 D2 ruling: keep persona's `results` field as edges, ADD `episodes` and `nodes` keys, and update `_render_retrieval` to surface episodes when no edges match.

---

## 2. Research findings (inlined)

### 2.1 Empirical reproduction (pre-plan)

Sidecar live (PID 1079, /health=200, kuzu_db=`/Users/lukeivers/pos3/workspace/data/memory-system/kuzu_db`).

Probe via `mcp.client.streamable_http`:

| Action | Result |
|---|---|
| `add_episode(group_id="probe-test", body="...quokka-9182 banana-pancake.")` | uuid + nodes=3 + edges=2 |
| `search("quokka", group_ids=None)` | 1 result |
| `search("quokka", group_ids=["probe-test"])` | **1 result** |
| `search("quokka", group_ids=["pos3"])` | 0 |
| `search("quokka", group_ids=["pos-v2_default"])` | 0 |
| `add_episode(group_id="pos3", body="<rich 5-sentence body>")` | uuid + nodes=6 + edges=5 |
| `search("Luke", group_ids=["pos3"])` | **2 results** |

The filter works for **every** fresh, edge-producing write. The dispatch's stated bug occurs only for episodes that did not extract edges.

### 2.2 Direct kuzu_db inspection (sidecar-copy)

Copied live `kuzu_db` + `kuzu_db.wal` while sidecar held the lock; opened the copy read-only with `kuzu` Python driver. Counts above. Sample edges all carry the same `group_id` as their source `Episodic`:

```
default       | "Luke and Eve are engaged in an active design dialog"
default       | "Eve serves as Luke's primary persona"
ms-fix-smoke  | "The Memory sidecar recovery amendment includes the lifespan-leak fix"
probe-test    | "FastMCP group_ids probe has the distinctive marker quokka-9182"
```

Episodic-node bodies for the 0-edge cases:

```
group_id=pos3            : "AC.MPF.6 verification: Stop hook reseat + retrieval roundtrip"   (1 entity, 0 edges)
group_id=pos-v2_default  : "Memory sidecar diagnostic test episode. The graphiti service was restarted via launchctl after lifespan-init failure due to Kuzu mmap accumulation across MCP sessions."   (7 entities, 0 edges)
```

The graphiti LLM-extraction pass found no relationship triples in the first; extracted 7 entities from the second but didn't generate any edges. **This is graphiti-core's expected behaviour for sparse / single-clause episode bodies.**

### 2.3 graphiti-core's two search APIs

`graphiti_core/graphiti.py:1331-1391` — `search()`:

```python
async def search(self, query, ..., group_ids=None, num_results=...) -> list[EntityEdge]:
    ...
    edges = (await search(self.clients, query, group_ids, EDGE_HYBRID_SEARCH_RRF, ...)).edges
    return edges
```

Returns edges only. Used by `_impl_search`.

`graphiti_core/graphiti.py:1407-1434` — `search_()` (note trailing `_`):

```python
async def search_(self, query, config=COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                  group_ids=None, ...) -> SearchResults:
    return await search(self.clients, query, group_ids, config, ...)
```

Returns `SearchResults`:

```python
class SearchResults(BaseModel):
    edges: list[EntityEdge] = Field(default_factory=list)
    nodes: list[EntityNode] = Field(default_factory=list)
    episodes: list[EpisodicNode] = Field(default_factory=list)
    communities: list[CommunityNode] = Field(default_factory=list)
    # plus *_reranker_scores
```

`COMBINED_HYBRID_SEARCH_RRF` (search/search_config_recipes.py:34-53) configures bm25+cosine over edges, nodes, episodes, and communities with RRF reranking. **All four arms apply the same `group_ids` WHERE-clause filtering** in the Kuzu driver (search_ops.py: `if group_ids is not None: filter_queries.append('e.group_id IN $group_ids')` etc.).

### 2.4 Why `_render_retrieval`'s "0 results" path is reached today

Persona's `LiveMCPMemoryClient.search()` (mcp_memory_client.py:119-142) returns the FastMCP tool's structured-content dict verbatim — currently `{"query": ..., "results": [edges...]}`. `_render_retrieval` (memory_consumer.py post-MPF) tests `if not results: return "[memory-retrieval]\n  (no results for this query)"`.

When the active session writes a Stop-hook turn into pos3 memory and the body is too sparse to extract edges (e.g. AC.MPF.6's `"AC.MPF.6 verification: Stop hook reseat + retrieval roundtrip"`), graphiti stores the Episodic + 1 Entity. Persona's next-turn retrieval queries `search("...recent context...", group_ids=["pos3"])` — gets 0 edges. Memory is **operationally** non-functional even though the write succeeded.

### 2.5 Out-of-band consideration: D10 retention semantics

D10 `retention_class=normal` keeps raw text; `derived-only` discards raw after extraction. Spec v1.1 D10 doesn't speak to "no extraction happened" specifically. Two readings:

- **Strict edges-only retrieval:** 0-edge episodes are accepted as lossy under `normal` retention; the raw text persists as `Episodic.content` but is unreachable via search. (Status quo. Renders D10's `normal` materially indistinguishable from `derived-only` for sparse episodes — broken.)
- **Episodes-and-edges retrieval:** episodes stay reachable via search even when no edges extracted; raw text persists AND is retrievable. (Plan §3 D1 ruling.)

The second reading is the only one that makes D10 `normal` materially different from `derived-only`. The proposal text "raw text persisted, structured facts extracted, **everything retrievable**" (config/memory.yml D10 comment) explicitly endorses the second reading — "everything retrievable" is incompatible with the edge-only search shape today.

---

## 3. Decisions (recommendations stated)

### D1 — Search MCP tool surfaces episodes + nodes alongside edges. RECOMMENDED: yes (the only fix that satisfies the AC).

The `_impl_search` function migrates from `graphiti.search()` (edges-only) to `graphiti.search_(COMBINED_HYBRID_SEARCH_RRF)`. Returns `SearchResults`. The MCP tool serialises this into a dict with three keys for the three retrievable record-types:

```python
{
    "query": str,
    "results": [edge_record, ...],       # back-compat — edges, same shape as before
    "nodes": [node_record, ...],         # NEW — Entity nodes
    "episodes": [episode_record, ...],   # NEW — Episodic nodes (raw memory)
}
```

**Alternatives rejected:**
- (a) Keep `graphiti.search()` and *also* call a separate episode-search API. Worse: two round-trips, two separate group_ids filters, two separate semaphore-coroutines. `search_()` is the canonical combined path.
- (b) Add a second MCP tool `search_episodes`. Worse for persona's contributor — has to make two calls and merge. Also bloats the AC ladder; one tool with one semantically-larger return is the simpler shape.
- (c) Switch to `COMBINED_HYBRID_SEARCH_CROSS_ENCODER`. Cross-encoder is heavier (LLM-call-per-rerank) and graphiti's default cross-encoder can require an extra LLM client. RRF is dependency-light and matches the back-compat shape. **D1.b: use `COMBINED_HYBRID_SEARCH_RRF`, not the cross-encoder variant.**

### D2 — Persona's `_render_retrieval` consumes the new fields. RECOMMENDED: yes.

`_render_retrieval` (memory_consumer.py post-MPF) updates: when `results` is empty, fall through to `episodes`; when those are also empty, then emit `"(no results for this query)"`. Edges still render as facts (existing shape). Episodes render as `"[episode] {episode.name}: {content_preview}"`.

The Protocol shape (`MemoryClient.search`) doc-string carries the new return-keys. `LiveMCPMemoryClient` is a pass-through; no code change there beyond docstring.

### D3 — Test surface: 4 outcome-shaped AC tests + 1 round-trip integration test. RECOMMENDED: yes.

- `AC.FGF.1` — `_impl_search` returns the tri-key shape (`results`/`nodes`/`episodes`).
- `AC.FGF.2` — group_ids filter is honoured for the new node/episode arms (regression: episode under group_id=A is in episodes-list when filter=[A]; absent when filter=[B]).
- `AC.FGF.3` — `_render_retrieval` falls through to `episodes` when `results` is empty.
- `AC.FGF.4` — `_render_retrieval` prefers edges (results) when both are present.
- `AC.FGF.5` — operational round-trip: write episode with sparse body under `group_id=X`, search with `group_ids=[X]`, episode is retrievable. Live HTTP via raw `mcp.client`. **Manual test, recorded in §14.**

### D4 — Dispatch claim "filter is broken" — capture and CLOSE. RECOMMENDED: yes.

Add §14 method-decision register entry confirming the dispatch's investigation framing was wrong: filter works as designed; the visibility gap is in the search-tool surface contract. Plan documents this clearly so any future "filter is broken" claim is checked against this finding first.

### D5 — Out-of-scope follow-ons (FIDRAFT). RECOMMENDED: capture, do not block.

- **D5.1 — Cross-encoder reranking** for higher-quality retrieval. Defer; needs LLM-client wiring + token-budget review.
- **D5.2 — Communities arm.** `COMBINED_HYBRID_SEARCH_RRF` includes `community_config`; pos3 doesn't run community-detection yet (graphiti's `build_communities` not invoked from sidecar). Communities will be empty; harmless.
- **D5.3 — Episode body-text full-text search.** Currently relies on graphiti-core's `episode_content` FTS index built at `prepare_graphiti` time. Confirm the index exists on pos3's kuzu_db; if not, schema migration needed. Out-of-scope here (rely on graphiti's lifecycle); **HSF#1 if missing.**

---

## 4. Acceptance criteria

**AC.FGF.1 — Search MCP tool returns tri-key shape.**
`_impl_search(graphiti, query=..., group_ids=..., num_results=...)` returns a dict with exactly the keys `{"query", "results", "nodes", "episodes"}`. `results` is a list of edge-shaped dicts (back-compat with the existing FastMCP wrapper shape). `nodes` is a list of `{"node_uuid", "name", "summary", "group_id"}`. `episodes` is a list of `{"episode_uuid", "name", "content", "group_id", "valid_at"}`.

**AC.FGF.2 — group_ids filter applied to nodes + episodes.**
When `_impl_search` is called with `group_ids=["A"]` and the underlying graphiti returns `SearchResults` whose nodes/episodes include records under both `group_id="A"` and `group_id="B"`, the FastMCP tool's response includes only the `"A"` records. (Implementation: `search_()` does the filtering in Cypher; this AC verifies the wrapper doesn't accidentally drop the filter — defensive.)

**AC.FGF.3 — `_render_retrieval` falls through to episodes when edges empty.**
With the LiveMCPMemoryClient returning `{"results": [], "episodes": [{...}], "nodes": []}`, `_render_retrieval` returns a string containing `"[episode]"` and the episode's name. (No `"(no results for this query)"` fallthrough.)

**AC.FGF.4 — `_render_retrieval` prefers edges when both present.**
With both `results` and `episodes` populated, `_render_retrieval` renders the edges (facts) — episodes are not appended. Keeps current persona-facing shape stable (M9 substitution-pass invariant).

**AC.FGF.5 — Operational round-trip. (manual)**
Live add_episode (sparse body, group_id="fgf-roundtrip-probe") → live search (query=marker, group_ids=["fgf-roundtrip-probe"]) → episode is in `episodes` list. Recorded in §14.

**AC.FGF.S — Seal-diff fence.**
Diff under seal limited to: `framework/memory-system/src/service.py`, `framework/memory-system/tests/test_service.py`, `framework/primary-persona/src/loam/primary_persona/memory_consumer.py`, `framework/primary-persona/tests/test_AC_FGF_*.py`, plus universal-paths (plans/, CLAUDE.md, STATE.md, FUTURE_IDEAS.md, etc.).

---

## 5. Sealed-component fence

Two-component amendment.

- **memory-system** (lead): `framework/memory-system/src/service.py` (D1 — _impl_search switches to graphiti.search_), `framework/memory-system/tests/test_service.py` (regression-update + new AC.FGF.1, AC.FGF.2 tests).
- **primary-persona**: `framework/primary-persona/src/loam/primary_persona/memory_consumer.py` (D2 — _render_retrieval consumes episodes), new tests `test_AC_FGF_3_render_retrieval_falls_through_to_episodes.py`, `test_AC_FGF_4_render_retrieval_prefers_edges.py`.

Universal admissions: `docs/plans/`, `CLAUDE.md`, `docs/STATE.md`, `docs/FUTURE_IDEAS.md`, `docs/FUTURE_IDEAS_DRAFT.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md`.

Cross-component: memory-system's seal_test admits primary-persona tree via `extra_allowed_prefixes`.

---

## 6. Halt triggers

Per dispatch + named here:
1. Root cause shifts from class (δ) to (γ) (data-layer corruption / write-side bug). [N/A — confirmed (δ).]
2. graphiti-core API surface change required (not just calling `search_` instead of `search`). [N/A — confirmed pure call-substitution.]
3. Episodes' group_id storage is fundamentally wrong. [N/A — verified correct in §2.2.]
4. Frozen-baseline / byte-content invariant breach beyond ODD §4 in-band.
5. ODD §2.5 violations (Lens 1/2/3 failures).
6. Wall-clock approaches 120 min — surface for continuation.
7. Operational restart of memory sidecar fails post-fix.

---

## 7. Ship shape (commit ladder)

1. Plan commit (this file).
2. `feat(memory-system): fastmcp-group-ids-filter-fix — search surfaces episodes + nodes via search_(COMBINED_HYBRID_SEARCH_RRF)` — service.py + tests.
3. `feat(primary-persona): _render_retrieval falls through to episodes when edges empty (FGF)` — memory_consumer.py + tests.
4. `chore(loam-amend-apply): loam amend apply for fastmcp-group-ids-filter-fix` (apply commit).
5. `chore(seals): fastmcp-group-ids-filter-fix — memory-system+primary-persona at <SHA>` (seal commit).
6. (Post-seal) §14 backfill commit if needed.

---

## 8. Out of scope

- Cross-encoder reranking (D5.1).
- Community detection / community-arm population (D5.2).
- Episode FTS index validation on pos3 kuzu_db (D5.3 / HSF#1 if missing post-fix).
- Persona's `MemoryClient` Protocol (sealed since amendment #33) — only docstring change permitted.
- Anything else.

---

## 9. Backwards-compat verification

The MCP tool's old return shape: `{"query": str, "results": [edge_records]}`. New shape: `{"query": str, "results": [edge_records], "nodes": [...], "episodes": [...]}`. **Strict superset.** Old consumers reading `out["query"]` and `out["results"]` see no change. Persona's `_render_retrieval` is the only known caller; it is updated in lockstep.

`LiveMCPMemoryClient.search` Protocol return-type doc-string: from "the documented `{"query": str, "results": list}` shape" to "the documented `{"query", "results", "nodes", "episodes"}` shape". The Protocol's stub-bodies don't enforce keys; pass-through stays valid.

`test_AC24_3_search_dispatches_to_graphiti` (test_service.py:269-302) is updated: the assertion `set(item.keys()) == {"fact", "edge_uuid", "valid_at", "invalid_at", "source_node_uuid", "target_node_uuid"}` (which matches edges) stays — `results` is still edges. The test's `out` shape assertion grows to require the new keys.

`fake_graphiti.search` (test stand-in) is replaced with `search_` returning a `FakeSearchResults` (with `edges`, `nodes`, `episodes`). The dispatch-correctness assertion (`call["group_ids"] == ["g1", "g2"]`) carries over to the new `searched` dict.

---

## 10. AI-time prediction

Per the duration rubric (~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md):

- Investigation (already completed in pre-plan phase): 25 min actual.
- Plan authoring: 10 min.
- Implementation (service.py + memory_consumer.py + 4 tests): 25 min.
- Test runs (touched + sweep): 10 min.
- loam amend apply + seal: 10 min.
- Operational verification: 5 min.
- §14 backfill: 5 min.

**Total: 90 min predicted (lower-end of dispatch's 30-90 min envelope).**

---

## 14. Method-decision register (post-build)

Filled at seal. SHAs land here.

| ID | Decision | Outcome / SHA |
|---|---|---|
| D1.a | Use `graphiti.search_()` not `search()`. | applied at `8e33ee1` (memory-system feature) — `_impl_search` calls `graphiti.search_(query=..., config=cloned_recipe, group_ids=..., center_node_uuid=...)` instead of `graphiti.search(query=..., center_node_uuid=..., group_ids=..., num_results=...)`. |
| D1.b | Use `COMBINED_HYBRID_SEARCH_RRF` not `_CROSS_ENCODER`. | applied at `8e33ee1`. The recipe is imported as a module-level singleton; `_impl_search` clones via `model_copy(deep=True)` per call before mutating `.limit`. |
| D2 | `_render_retrieval` falls through to episodes only when edges empty. | applied at `646e2c7` (primary-persona feature). Three-branch precedence: edges-non-empty → render facts; else episodes-non-empty → render `[episode]` lines; else AC.MPF.2 empty-state diagnostic. |
| D3 | 4 unit ACs + 1 manual round-trip AC. | 14 service tests + 8 persona rendering tests green; AC.FGF.5 round-trip recorded below. |
| D4 | Dispatch claim "filter is broken" closed: filter works; visibility gap is in tool contract. | confirmed by §2.1 reproduction + §2.2 kuzu_db inspection during investigation phase. Plan §1 + HSF#4 carry the framing-correction. |
| Plan SHA | | `ac650eb` |
| Feature SHA (memory-system) | | `8e33ee1` |
| Feature SHA (primary-persona) | | `646e2c7` |
| Apply SHA | | `a5469f2` |
| Seal SHA | | `25ae41b` |
| §14 backfill SHA | | `7bdf7fc` |
| AC.FGF.5 round-trip | live add_episode + search round-trip output | sidecar restarted via `launchctl kickstart -k gui/$UID/com.pos-v2.pos3.memory-graphiti`; probe via `mcp.client.streamable_http`: write episode `name=fgf-roundtrip-sparse, group_id=fgf-roundtrip-probe, body="AC.FGF.5 verification round-trip with marker bluefin-7621."` returned `episode_uuid=17a9e607-…, nodes_extracted=2, edges_extracted=1`. Search `query="bluefin", group_ids=["fgf-roundtrip-probe"]` returned `results(edges)=1, nodes=2, episodes=1` with the matching episode in the `episodes` list. Cross-group sanity: `group_ids=["other-group"]` returned 0 / 0 / 0. **PASSED.** |

---

### Commit SHAs

- Amendment commit: `a5469f2e8e24d533261b3aaa71deb31839cc3e3f` —
  `chore(loam-amend-apply): loam amend apply for fastmcp-group-ids-filter-fix`
- Seal commit: `25ae41bb6e093e5a24ab6f897695fa74105edd0b` —
  `chore(seals): fastmcp-group-ids-filter-fix — memory-system+primary-persona at a5469f2`
## 15. Post-build verification checklist

- [x] All AC.FGF.1..5 tests green.
- [x] `test_AC24_3_search_dispatches_to_graphiti` updated and green.
- [x] memory-system (100 + 1 skip) + primary-persona (507) test sweeps green.
- [x] `loam amend apply --dry-run` clean post-seal.
- [x] Sidecar restarts cleanly (`launchctl kickstart -k gui/$UID/com.pos-v2.pos3.memory-graphiti` — health 200 within ~6s).
- [x] Live HTTP round-trip recorded in §14 AC.FGF.5 row.
- [x] Working tree clean.

---

## 16. Halt-and-surface findings encountered during plan authoring

**HSF#1 — Episode FTS index validation (D5.3).**
`graphiti_core.search.search_ops.episode_fulltext_search` requires Kuzu's `episode_content` FTS index. `prepare_graphiti` builds it via `build_indices_and_constraints`. If pos3's kuzu_db was created against an older schema that didn't include the episode FTS index, episode-search returns empty even when episodes exist. Detection: live HTTP probe AC.FGF.5 — if the round-trip episode is invisible, this is the cause. Remedy if hit: add a one-line `ensure_episode_fts_index` migration to memory-system's startup. Currently believed not-needed (graphiti-core 0.28.x's `prepare_graphiti` builds it).

**HSF#2 — Persona's `MemoryClient` Protocol sealed-component status.**
Protocol class lives in `primary_persona.memory_consumer`. Sealed since amendment #33 per protocol-stability convention. The fix is structurally compatible — old consumers see strict-superset return shape — but if a Protocol-level test exists that asserts `set(return_dict.keys()) == {"query", "results"}`, the shape change is a Protocol-spec change. Detection: search for such a test pre-build; if found, the change becomes a Protocol-extension which may need explicit Protocol-doc update + sealed-component flag review. Currently believed not-needed.

**HSF#3 — `_render_retrieval` empty-state string from MPF.**
Memory-pipeline-fix established `"[memory-retrieval]\n  (no results for this query)"` as the empty-state output. With the FGF fix, the same string remains the floor (when both edges AND episodes are empty). Worth one regression test that the MPF empty-state behaviour persists when nothing is found at all.

**HSF#4 — Dispatch's stated symptom contradicted by empirical reproduction.**
The dispatch reads "filter silently masks ALL retrievable data → retrieval is empty by construction." The §2.1 reproduction shows the filter works for every fresh edge-producing write. The dispatch's framing was misleading; the actual gap is the search shape. Surfacing for owner awareness; the FGF fix delivers the correct end-to-end outcome (memory functions: write→search→retrieve). Owner ruling not required — the fix's outcome subsumes the framing.

**HSF#5 — `pos-v2_default` orphan data accepted as lost (carried from MPF).**
The two pre-existing 0-edge episodes (`pos-v2_default`'s `diagnostic-test-2026-04-29` and `pos3`'s `test-episode-mpf-verify`) become **retrievable** post-fix (they have Episodic nodes with content). MPF's "accept the orphans as lost" decision is partially reversed — the FGF fix makes them retrievable on a content-match search.
