from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any

from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
from src.repositories.knowledge_file_repository import KnowledgeFileRepository
from src.utils import logger

_STOPWORDS = {
    "的",
    "了",
    "和",
    "与",
    "及",
    "是",
    "在",
    "对",
    "按",
    "及其",
    "相关",
    "管理",
    "办法",
    "制度",
    "规定",
    "方案",
    "通知",
    "工作",
    "文件",
    "资料",
}

_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_]{2,24}")


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens = [t.strip().lower() for t in _TOKEN_PATTERN.findall(text)]
    return [t for t in tokens if t and t not in _STOPWORDS]


def _extract_keywords(texts: list[str], top_k: int = 24) -> list[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        counter.update(_tokenize(text))
    return [w for w, _ in counter.most_common(top_k)]


def _extract_entities(filenames: list[str], top_k: int = 20) -> list[str]:
    candidates: list[str] = []
    for name in filenames:
        base = name.rsplit(".", 1)[0]
        candidates.extend(_tokenize(base))
    return [w for w, _ in Counter(candidates).most_common(top_k)]


def _infer_doc_types(filenames: list[str]) -> list[str]:
    exts: Counter[str] = Counter()
    for name in filenames:
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else "unknown"
        exts.update([ext])
    return [f"{k}:{v}" for k, v in exts.most_common(10)]


def _infer_time_range(records: list[Any]) -> dict[str, str | None]:
    created_at_values: list[datetime] = []
    for r in records:
        ts = getattr(r, "created_at", None)
        if isinstance(ts, datetime):
            created_at_values.append(ts)
    if not created_at_values:
        return {"start": None, "end": None}
    created_at_values.sort()
    return {
        "start": created_at_values[0].isoformat(),
        "end": created_at_values[-1].isoformat(),
    }


def _build_summary(name: str, description: str, keywords: list[str], doc_types: list[str], file_count: int) -> str:
    kw_preview = "、".join(keywords[:10]) if keywords else "暂无"
    type_preview = "、".join(doc_types[:5]) if doc_types else "暂无"
    base_desc = description or "暂无描述"
    return (
        f"知识库“{name}”当前包含 {file_count} 份文件。"
        f"已有描述：{base_desc}。"
        f"主题关键词：{kw_preview}。"
        f"文档类型分布：{type_preview}。"
    )


async def build_profile(db_id: str, force: bool = False) -> dict[str, Any]:
    kb_repo = KnowledgeBaseRepository()
    file_repo = KnowledgeFileRepository()

    kb = await kb_repo.get_by_id(db_id)
    if kb is None:
        raise ValueError(f"Knowledge base not found: {db_id}")

    additional_params = dict(kb.additional_params or {})
    old_profile = additional_params.get("kb_profile")
    if old_profile and not force:
        return old_profile

    records = await file_repo.list_by_db_id(db_id)
    filenames = [getattr(r, "filename", "") or "" for r in records if not getattr(r, "is_folder", False)]

    source_texts = [kb.name or "", kb.description or "", *filenames]
    keywords = _extract_keywords(source_texts, top_k=24)
    entities = _extract_entities(filenames, top_k=20)
    doc_types = _infer_doc_types(filenames)
    time_range = _infer_time_range(records)

    profile = {
        "profile_version": 1,
        "last_profiled_at": datetime.utcnow().isoformat(),
        "db_id": kb.db_id,
        "display_name": kb.name,
        "domain_tags": keywords[:8],
        "topic_keywords": keywords,
        "entities": entities,
        "doc_types": doc_types,
        "time_range": time_range,
        "applicable_questions": [],
        "non_applicable_questions": [],
        "quality_score": 0.6 if filenames else 0.2,
        "summary_text": _build_summary(kb.name, kb.description or "", keywords, doc_types, len(filenames)),
    }

    additional_params["kb_profile"] = profile
    await kb_repo.update(db_id, {"additional_params": additional_params})
    logger.info(f"Built kb profile for {db_id}: files={len(filenames)}, keywords={len(keywords)}")
    return profile


async def refresh_profile_incremental(db_id: str, file_ids: list[str] | None = None) -> dict[str, Any]:
    del file_ids  # 首版统一走全量重建，避免引入额外复杂度
    return await build_profile(db_id, force=True)


async def build_profiles_batch(db_ids: list[str], batch_size: int = 20) -> dict[str, Any]:
    summary = {
        "total": len(db_ids),
        "success": 0,
        "failed": 0,
        "errors": [],
    }

    for i in range(0, len(db_ids), max(1, batch_size)):
        batch = db_ids[i : i + batch_size]
        for db_id in batch:
            try:
                await build_profile(db_id, force=True)
                summary["success"] += 1
            except Exception as e:
                summary["failed"] += 1
                summary["errors"].append({"db_id": db_id, "error": str(e)})
                logger.error(f"Build profile failed for {db_id}: {e}")

    return summary


async def get_profile(db_id: str) -> dict[str, Any] | None:
    kb_repo = KnowledgeBaseRepository()
    kb = await kb_repo.get_by_id(db_id)
    if kb is None:
        return None
    return (kb.additional_params or {}).get("kb_profile")


async def get_profiles(db_ids: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    kb_repo = KnowledgeBaseRepository()
    for db_id in db_ids:
        kb = await kb_repo.get_by_id(db_id)
        if kb is None:
            continue
        profile = (kb.additional_params or {}).get("kb_profile")
        if profile:
            result[db_id] = profile
    return result
