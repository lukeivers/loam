"""ActiveJob + Sidekiq recognizer.

Per AC.RAILS.2 — detects:

- **ActiveJob** classes — ``class X < ApplicationJob`` (or
  ``ActiveJob::Base``) plus optional ``queue_as :name``.
- **Sidekiq** workers — ``include Sidekiq::Worker`` /
  ``include Sidekiq::Job`` inside any class plus optional
  ``sidekiq_options queue: :name``.

Each job class emits one PLAUSIBLE BandedAC; each ``queue_as`` or
``sidekiq_options queue:`` emits an additional PLAUSIBLE BandedAC.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ....bands import BandedAC, ConfidenceBand, Evidence
from .._ast_utils import (
    call_first_arg,
    call_keyword_arg_value,
    call_method_name,
    class_name,
    file_slug,
    find_calls,
    find_classes,
    superclass_name,
)
from ..parser import node_line, node_text

if TYPE_CHECKING:  # pragma: no cover
    import tree_sitter


_ACTIVE_JOB_SUPERCLASSES = ("ApplicationJob", "ActiveJob::Base")
_SIDEKIQ_INCLUDES = ("Sidekiq::Worker", "Sidekiq::Job")


def _has_sidekiq_include(
    class_node: "tree_sitter.Node", source: bytes
) -> bool:
    """Return True if the class body has ``include Sidekiq::*``."""
    for call_node in find_calls(class_node):
        method = call_method_name(call_node, source)
        if method != "include":
            continue
        for child in call_node.children:
            if child.type != "argument_list":
                continue
            for arg in child.children:
                if arg.type in ("scope_resolution", "constant"):
                    txt = node_text(arg, source)
                    if txt in _SIDEKIQ_INCLUDES:
                        return True
    return False


def recognize_jobs(
    tree: "tree_sitter.Tree",
    source: bytes,
    file_path: Path,
    repo_root: Path,
    repo_sha: str | None,
) -> list[BandedAC]:
    """Return PLAUSIBLE BandedACs for ActiveJob + Sidekiq workers."""
    out: list[BandedAC] = []
    fslug = file_slug(file_path, repo_root)
    try:
        file_rel = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        file_rel = str(file_path)

    for class_node in find_classes(tree.root_node):
        cname = class_name(class_node, source)
        if cname is None:
            continue
        sup = superclass_name(class_node, source)
        is_active_job = sup in _ACTIVE_JOB_SUPERCLASSES
        is_sidekiq = _has_sidekiq_include(class_node, source)
        if not (is_active_job or is_sidekiq):
            continue

        framework = "ActiveJob" if is_active_job else "Sidekiq"
        cline = node_line(class_node)
        out.append(
            BandedAC(
                ac_id=(
                    f"AC.RAILS.jobs.{cname.lower()}.{fslug}"
                ),
                text=(
                    f"{cname} is a {framework} job"
                ),
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=[f"{file_rel}:{cline}"],
                    repo_sha=repo_sha,
                ),
                backing_files=[file_rel],
            )
        )

        # queue_as :name for ActiveJob.
        for call_node in find_calls(class_node):
            method = call_method_name(call_node, source)
            if method == "queue_as":
                qname = call_first_arg(call_node, source) or "?"
                qline = node_line(call_node)
                out.append(
                    BandedAC(
                        ac_id=(
                            f"AC.RAILS.jobs.{cname.lower()}.queue_as."
                            f"{qname.strip(':')}.{fslug}"
                        ),
                        text=(
                            f"{cname} runs on queue {qname} "
                            f"(queue_as)"
                        ),
                        confidence=ConfidenceBand.PLAUSIBLE,
                        evidence=Evidence(
                            kind="source",
                            citations=[f"{file_rel}:{qline}"],
                            repo_sha=repo_sha,
                        ),
                        backing_files=[file_rel],
                    )
                )
            elif method == "sidekiq_options":
                qval = call_keyword_arg_value(
                    call_node, source, "queue"
                ) or "?"
                qline = node_line(call_node)
                out.append(
                    BandedAC(
                        ac_id=(
                            f"AC.RAILS.jobs.{cname.lower()}."
                            f"sidekiq_queue.{qval.strip(':')}.{fslug}"
                        ),
                        text=(
                            f"{cname} runs on Sidekiq queue {qval}"
                        ),
                        confidence=ConfidenceBand.PLAUSIBLE,
                        evidence=Evidence(
                            kind="source",
                            citations=[f"{file_rel}:{qline}"],
                            repo_sha=repo_sha,
                        ),
                        backing_files=[file_rel],
                    )
                )

    return out
