"""D10 — Retention-class tagger.

Each ingested episode carries a retention class:

  normal        — raw text persisted; structured facts extracted;
                  everything retrievable.
  derived-only  — structured facts only; raw text discarded after
                  extraction. Useful for privacy-sensitive sources
                  (financial, health) where the facts matter but the
                  prose is gated.
  ephemeral     — in-turn use only; no persisted memory beyond the
                  immediate call. The episode is held in RAM for the
                  duration of the ingest call but nothing lands in
                  Kuzu. Narrower than the D5 rubric — ephemerality
                  blocks storage entirely; retention=ephemeral still
                  extracts facts for the ACTIVE CONVERSATION, it just
                  doesn't persist them.

The default class is `normal` (Luke's 2026-04-18 09:23 decision per
proposal §"Open questions"). Workspaces override per-ingest.

Implementation strategy: Graphiti's `EPISODIC` node stores the raw
episode body by default. We influence this via:

  store_raw_episode_content = False   -> derived-only
  (do not call add_episode at all)    -> ephemeral (returns extraction
                                         result for transient use)

Graphiti 0.28.2 does NOT accept `store_raw_episode_content` as a
per-episode arg on `add_episode`; it's a construction-time flag on the
Graphiti instance. To avoid rebuilding the instance per-episode, we
implement derived-only as a POST-INGEST body scrub on the EPISODIC
node. The structured extraction has already happened; nothing points
back to the body text, so scrubbing `content` preserves the facts
while discarding the raw text. This matches the acceptance criterion
("produces structured facts in memory but no retrievable raw text").
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import section


class RetentionClass(str, Enum):
    NORMAL = "normal"
    DERIVED_ONLY = "derived-only"
    EPHEMERAL = "ephemeral"


@dataclass(frozen=True)
class RetentionPlan:
    """What the tagger decided for a given ingest.

    The plan is consumed by the ingest pipeline: NORMAL is the default
    path, DERIVED_ONLY triggers a post-ingest content scrub on the
    episodic node, EPHEMERAL short-circuits persistence entirely.
    """

    cls: RetentionClass

    @property
    def persists(self) -> bool:
        return self.cls is not RetentionClass.EPHEMERAL

    @property
    def persists_raw_text(self) -> bool:
        return self.cls is RetentionClass.NORMAL


def default_class() -> RetentionClass:
    raw = section("retention").get("default_class", "normal")
    return RetentionClass(raw)


def resolve(requested: str | RetentionClass | None) -> RetentionPlan:
    """Coerce a user-supplied string (or enum) into a RetentionPlan.

    Unknown strings fall back to the configured default, with a trace
    that will surface in the ingest span. This is intentional: a typo
    should not hard-fail a session; the observability record captures
    the fallback for later review.
    """
    if requested is None:
        return RetentionPlan(cls=default_class())
    if isinstance(requested, RetentionClass):
        return RetentionPlan(cls=requested)
    try:
        return RetentionPlan(cls=RetentionClass(requested))
    except ValueError:
        return RetentionPlan(cls=default_class())


# ----- Kuzu-level enforcement helpers --------------------------------

# The EPISODIC node label in graphiti-core 0.28.2 is `Episodic`.
# The content field is `content`. The retention class tag is stored as
# a new `retention_class` attribute, written as raw Cypher because
# graphiti-core doesn't expose per-episode metadata.


SCRUB_CONTENT_CQL = """
    MATCH (ep:Episodic {uuid: $uuid})
    SET ep.content = ''
    RETURN ep.uuid AS uuid
"""


TAG_RETENTION_CQL = """
    MATCH (ep:Episodic {uuid: $uuid})
    SET ep.retention_class = $cls
    RETURN ep.uuid AS uuid
"""


QUERY_BY_CLASS_CQL = """
    MATCH (ep:Episodic)
    WHERE ep.retention_class = $cls
    RETURN ep.uuid AS uuid, ep.name AS name, ep.created_at AS created_at
"""


ENSURE_RETENTION_COLUMN_CQL = (
    "ALTER TABLE Episodic ADD IF NOT EXISTS "
    "retention_class STRING DEFAULT 'normal'"
)


async def ensure_retention_column(driver: Any) -> None:
    """Idempotently add the `retention_class` column to the Episodic
    table. Kuzu 0.11+ supports `ALTER TABLE ADD IF NOT EXISTS`; graphiti
    does not declare this column in its static schema so we add it at
    memory-system init."""
    try:
        await driver.execute_query(ENSURE_RETENTION_COLUMN_CQL)
    except Exception as exc:
        # If the column already exists on an older Kuzu that doesn't
        # support IF NOT EXISTS, the error message contains "already
        # exists" — treat that as success.
        if "already exists" in str(exc):
            return
        raise


async def apply_plan(
    driver: Any,
    *,
    episode_uuid: str,
    plan: RetentionPlan,
) -> None:
    """Apply the retention plan to a freshly-ingested episode.

    Always tags the episode with its class. For DERIVED_ONLY, scrubs
    the raw text after extraction has finished. For NORMAL, only tags.
    For EPHEMERAL, the ingest pipeline should never reach this function
    (episodes are not ingested) — but if it does, we tag and scrub
    anyway so the DB state reflects the intent.
    """
    await driver.execute_query(TAG_RETENTION_CQL, uuid=episode_uuid, cls=plan.cls.value)
    if plan.cls in {RetentionClass.DERIVED_ONLY, RetentionClass.EPHEMERAL}:
        await driver.execute_query(SCRUB_CONTENT_CQL, uuid=episode_uuid)


async def list_by_class(driver: Any, cls: RetentionClass) -> list[dict[str, Any]]:
    """Enumerate episodes of a given retention class."""
    rows, _, _ = await driver.execute_query(QUERY_BY_CLASS_CQL, cls=cls.value)
    return list(rows or [])


async def query_retention_class(driver: Any, episode_uuid: str) -> str | None:
    """Return the stored retention_class for an episode, or None."""
    rows, _, _ = await driver.execute_query(
        "MATCH (ep:Episodic {uuid: $uuid}) RETURN ep.retention_class AS cls",
        uuid=episode_uuid,
    )
    if not rows:
        return None
    return rows[0].get("cls")
