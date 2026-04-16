from __future__ import annotations

import asyncio
import re
from typing import Any

from src import knowledge_base
from src.utils import logger

_SENTENCE_SPLIT_PATTERN = re.compile(r"[。！？!?\n]+")
_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_]{2,24}")


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_PATTERN.findall(text or "") if t}


def _estimate_tokens(text: str) -> int:
    # 中文场景下粗略估算：约 2 字符 ~ 1 token
    return max(1, len(text or "") // 2)


def _normalize_chunk(item: Any, db_id: str) -> dict[str, Any] | None:
    if isinstance(item, dict):
        content = item.get("content") or item.get("text") or item.get("chunk") or ""
        if not content:
            return None
        score_raw = item.get("score", item.get("rerank_score", 0.0))
        score = float(score_raw) if isinstance(score_raw, (int, float)) else 0.0
        if score > 1:
            score = min(1.0, score / 100.0)
        return {
            "kb_id": db_id,
            "doc_id": item.get("file_id") or item.get("doc_id"),
            "file_name": item.get("file_name") or item.get("filename") or item.get("source"),
            "chunk_id": item.get("id") or item.get("chunk_id"),
            "content": str(content),
            "score": max(0.0, min(1.0, score)),
            "source": item,
        }

    if isinstance(item, str) and item.strip():
        return {
            "kb_id": db_id,
            "doc_id": None,
            "file_name": None,
            "chunk_id": None,
            "content": item.strip(),
            "score": 0.3,
            "source": {"raw": item.strip()},
        }
    return None


async def federated_retrieve(
    query_text: str,
    candidate_db_ids: list[str],
    per_kb_top_k: int = 12,
    **kwargs,
) -> list[dict[str, Any]]:
    if not candidate_db_ids:
        return []

    sem = asyncio.Semaphore(8)

    async def _retrieve_one(db_id: str) -> list[dict[str, Any]]:
        async with sem:
            try:
                result = await knowledge_base.aquery(
                    query_text,
                    db_id,
                    agent_call=True,
                    top_k=per_kb_top_k,
                    chunk_top_k=per_kb_top_k,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"federated retrieve failed: db={db_id}, err={e}")
                return []

        chunks_raw: list[Any]
        if isinstance(result, dict):
            chunks_raw = result.get("chunks", [])
        elif isinstance(result, list):
            chunks_raw = result
        else:
            chunks_raw = []

        normalized: list[dict[str, Any]] = []
        for item in chunks_raw:
            chunk = _normalize_chunk(item, db_id)
            if chunk:
                normalized.append(chunk)
        return normalized

    parts = await asyncio.gather(*[_retrieve_one(db_id) for db_id in candidate_db_ids])
    merged: list[dict[str, Any]] = []
    for p in parts:
        merged.extend(p)
    return merged


def global_rerank(query_text: str, chunks: list[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
    if not chunks:
        return []

    q_tokens = _tokenize(query_text)

    scored: list[dict[str, Any]] = []
    for c in chunks:
        content = c.get("content", "")
        c_tokens = _tokenize(content)
        lexical = 0.0 if not c_tokens else len(q_tokens & c_tokens) / max(1, len(q_tokens | c_tokens))
        base = float(c.get("score", 0.0) or 0.0)
        final_score = 0.7 * base + 0.3 * lexical
        item = dict(c)
        item["rerank_score"] = round(final_score, 6)
        scored.append(item)

    scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return scored[: max(1, top_k)]


def context_budget_guard(chunks: list[dict[str, Any]], max_tokens: int = 18000) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not chunks:
        return [], {
            "truncated": False,
            "original_count": 0,
            "kept_count": 0,
            "estimated_tokens": 0,
            "max_tokens": max_tokens,
        }

    # L1: 最高置信前 4 条；L2: 其余可压缩条目；L3: 背景尾部条目
    sorted_chunks = list(chunks)
    sorted_chunks.sort(key=lambda x: x.get("rerank_score", x.get("score", 0.0)), reverse=True)

    l1 = sorted_chunks[:4]
    rest = sorted_chunks[4:]
    l2 = rest[:8]
    l3 = rest[8:]

    def _clip_content(content: str, max_chars: int) -> str:
        return content if len(content) <= max_chars else f"{content[:max_chars]}..."

    kept: list[dict[str, Any]] = []

    # L1 保留原文优先
    for c in l1:
        kept.append(dict(c))

    # L2 做句级压缩
    for c in l2:
        item = dict(c)
        item["content"] = _clip_content(item.get("content", ""), 500)
        item["compression_level"] = "L2"
        kept.append(item)

    # L3 背景摘要化
    for c in l3:
        item = dict(c)
        item["content"] = _clip_content(item.get("content", ""), 220)
        item["compression_level"] = "L3"
        kept.append(item)

    # 预算裁剪
    trimmed: list[dict[str, Any]] = []
    token_sum = 0
    for c in kept:
        estimate = _estimate_tokens(c.get("content", ""))
        if token_sum + estimate > max_tokens:
            break
        token_sum += estimate
        trimmed.append(c)

    # 如果连 L1 都放不下，至少保留 1 条最高证据
    if not trimmed and kept:
        first = dict(kept[0])
        first["content"] = first.get("content", "")[: max(120, max_tokens * 2)]
        trimmed = [first]
        token_sum = _estimate_tokens(first["content"])

    meta = {
        "truncated": len(trimmed) < len(kept),
        "original_count": len(chunks),
        "kept_count": len(trimmed),
        "estimated_tokens": token_sum,
        "max_tokens": max_tokens,
    }
    return trimmed, meta


def build_citations(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for c in chunks:
        citations.append(
            {
                "kb_id": c.get("kb_id"),
                "doc_id": c.get("doc_id"),
                "file_name": c.get("file_name"),
                "chunk_id": c.get("chunk_id"),
                "score": c.get("rerank_score", c.get("score")),
                "snippet": (c.get("content") or "")[:200],
            }
        )
    return citations


def claim_check(answer: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(answer or "") if s.strip()]
    if not sentences:
        return {"grounded": False, "support_ratio": 0.0, "unsupported_sentences": []}

    evidence_text = "\n".join([c.get("content", "") for c in chunks])
    evidence_tokens = _tokenize(evidence_text)

    supported = 0
    unsupported: list[str] = []
    for s in sentences:
        s_tokens = _tokenize(s)
        if not s_tokens:
            continue
        overlap = len(s_tokens & evidence_tokens) / max(1, len(s_tokens))
        if overlap >= 0.35:
            supported += 1
        else:
            unsupported.append(s)

    ratio = supported / max(1, len(sentences))
    return {
        "grounded": ratio >= 0.7,
        "support_ratio": round(ratio, 4),
        "unsupported_sentences": unsupported,
    }
