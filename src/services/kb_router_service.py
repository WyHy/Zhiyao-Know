from __future__ import annotations

import asyncio
import re
from typing import Any

from src import knowledge_base
from src.services.kb_profile_service import get_profiles
from src.utils import logger

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_]{2,24}")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_PATTERN.findall(text or "") if t]


def _jaccard_score(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    return len(inter) / max(1, len(union))


def _profile_match_score(query_tokens: list[str], db_info: dict[str, Any], profile: dict[str, Any] | None) -> float:
    name = db_info.get("name", "")
    desc = db_info.get("description", "")
    fields = [name, desc]
    if profile:
        fields.extend(
            [
                profile.get("summary_text", ""),
                " ".join(profile.get("domain_tags", []) or []),
                " ".join(profile.get("topic_keywords", []) or []),
                " ".join(profile.get("entities", []) or []),
            ]
        )
    target_tokens = _tokenize(" ".join([x for x in fields if isinstance(x, str)]))
    return _jaccard_score(query_tokens, target_tokens)


async def _quick_recall_score(query_text: str, db_id: str, top_k: int = 5) -> float:
    try:
        result = await knowledge_base.aquery(query_text, db_id, top_k=top_k, chunk_top_k=top_k, agent_call=True)
    except Exception as e:
        logger.warning(f"Quick recall failed for db={db_id}: {e}")
        return 0.0

    if not result:
        return 0.0

    if isinstance(result, dict):
        chunks = result.get("chunks", [])
    elif isinstance(result, list):
        chunks = result
    else:
        chunks = []

    if not chunks:
        return 0.2

    scores: list[float] = []
    for c in chunks:
        if isinstance(c, dict):
            raw = c.get("score", c.get("rerank_score"))
            if isinstance(raw, (int, float)):
                scores.append(float(raw))

    if scores:
        best = max(scores)
        if best > 1:
            best = min(1.0, best / 100.0)
        return max(0.0, min(1.0, best))

    return min(1.0, 0.35 + 0.05 * len(chunks))


async def route_candidate_kbs(query_text: str, user: dict, top_n: int = 4) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query_text)
    databases = (await knowledge_base.get_databases_by_user(user)).get("databases", [])
    if not databases:
        return []

    db_ids = [db.get("db_id") for db in databases if db.get("db_id")]
    profiles = await get_profiles(db_ids)

    # 在线只做轻量初筛：先按名称/描述/已有画像的文本相关性筛一轮
    lexical_scored: list[dict[str, Any]] = []
    for db_info in databases:
        db_id = db_info.get("db_id")
        if not db_id:
            continue
        profile = profiles.get(db_id)
        profile_score = _profile_match_score(query_tokens, db_info, profile)
        lexical_scored.append(
            {
                "db_id": db_id,
                "name": db_info.get("name", ""),
                "description": db_info.get("description", ""),
                "profile_score": round(profile_score, 6),
            }
        )

    lexical_scored.sort(key=lambda x: x["profile_score"], reverse=True)
    top_probe = max(top_n * 2, 4)
    candidates = lexical_scored[:top_probe]
    sem = asyncio.Semaphore(3)

    async def _score_one(candidate: dict[str, Any]) -> dict[str, Any]:
        db_id = candidate["db_id"]
        profile_score = float(candidate.get("profile_score", 0.0))
        async with sem:
            quick_score = await _quick_recall_score(query_text, db_id, top_k=5)

        freshness_boost = 0.0
        score = 0.4 * profile_score + 0.5 * quick_score + 0.1 * freshness_boost
        return {
            "db_id": db_id,
            "name": candidate.get("name", ""),
            "description": candidate.get("description", ""),
            "score": round(score, 6),
            "profile_score": round(profile_score, 6),
            "quick_recall_score": round(quick_score, 6),
        }

    scored = await asyncio.gather(*[_score_one(c) for c in candidates])
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[: max(1, top_n)]


async def quick_verify_candidates(query_text: str, candidates: list[dict[str, Any]], per_kb_top_k: int = 5) -> list[dict[str, Any]]:
    if not candidates:
        return []

    verified: list[dict[str, Any]] = []
    for c in candidates:
        db_id = c.get("db_id")
        if not db_id:
            continue
        score = await _quick_recall_score(query_text, db_id, top_k=per_kb_top_k)
        item = dict(c)
        item["verify_score"] = round(score, 6)
        item["score"] = round(0.7 * float(c.get("score", 0.0)) + 0.3 * score, 6)
        verified.append(item)

    verified.sort(key=lambda x: x["score"], reverse=True)
    return verified


def score_candidate(profile: dict, quick_recall_score: float, freshness_boost: float) -> float:
    profile_text = " ".join(
        [
            " ".join(profile.get("domain_tags", []) or []),
            " ".join(profile.get("topic_keywords", []) or []),
            " ".join(profile.get("entities", []) or []),
        ]
    )
    profile_density = min(1.0, len(_tokenize(profile_text)) / 40.0)
    return 0.4 * profile_density + 0.4 * quick_recall_score + 0.2 * freshness_boost
