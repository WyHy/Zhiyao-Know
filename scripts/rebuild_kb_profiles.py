#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("YUXI_SKIP_APP_INIT", "1")
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env", override=False)

from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
from src.services.kb_profile_service import build_profiles_batch
from src.storage.postgres.manager import pg_manager


def _should_rebuild(additional_params: dict, since_hours: int) -> bool:
    if since_hours <= 0:
        return True
    profile = (additional_params or {}).get("kb_profile") or {}
    last_profiled_at = profile.get("last_profiled_at")
    if not last_profiled_at:
        return True
    try:
        dt = datetime.fromisoformat(last_profiled_at.replace("Z", "+00:00"))
    except Exception:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    threshold = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    return dt <= threshold


async def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild kb profiles")
    parser.add_argument("--since-hours", type=int, default=0, help="only rebuild profiles older than this")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not pg_manager._initialized:
        pg_manager.initialize()

    repo = KnowledgeBaseRepository()
    try:
        rows = await repo.get_all()
    except Exception as e:
        if args.dry_run:
            print(f"[DRY-RUN] 无法连接数据库，跳过实际扫描: {e}")
            return
        raise
    selected = [r for r in rows if _should_rebuild(r.additional_params or {}, args.since_hours)]
    db_ids = [r.db_id for r in selected]

    print("=" * 68)
    print("知识库画像重建")
    print("=" * 68)
    print(f"知识库总数: {len(rows)}")
    print(f"待重建数量: {len(db_ids)}")
    print(f"since_hours: {args.since_hours}")
    print(f"模式: {'DRY-RUN' if args.dry_run else 'EXECUTE'}")

    if args.dry_run:
        for db_id in db_ids[:200]:
            print(f"[DRY-RUN] would rebuild profile for {db_id}")
        return

    summary = await build_profiles_batch(db_ids, batch_size=args.batch_size)
    print("\n执行结果:")
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
