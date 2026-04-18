"""Tiny smoke-version of eval_embeddings.py — 3 episodes, 5 questions,
one model. Used to validate the harness shape before kicking off the
full eval (which costs real time and tokens).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.eval_embeddings import REPO, evaluate_model
from src.factory import load_env  # noqa: E402


async def main() -> int:
    load_env()
    episodes = json.loads((REPO / "data" / "episodes.json").read_text())
    test_set = json.loads((REPO / "data" / "test_set.json").read_text())
    # Canary: first 5 episodes (covers Halcyon arc), 5 questions across
    # modes that those episodes can answer.
    canary_episodes = episodes[:5]
    canary_question_ids = {"q01", "q02", "q05", "q26", "q29"}
    canary_questions = [q for q in test_set["questions"] if q["id"] in canary_question_ids]
    await evaluate_model("nomic-embed-text", canary_episodes, canary_questions)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
