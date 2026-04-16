#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import sys
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


async def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill kb profiles for old knowledge bases")
    parser.add_argument("--db-id", action="append", default=[], help="specific db_id, can be passed multiple times")
    parser.add_argument("--limit", type=int, default=0, help="limit total kb count")
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
    db_ids = [r.db_id for r in rows]

    if args.db_id:
        wanted = set(args.db_id)
        db_ids = [x for x in db_ids if x in wanted]

    if args.limit and args.limit > 0:
        db_ids = db_ids[: args.limit]

    print("=" * 68)
    print("知识库画像回填")
    print("=" * 68)
    print(f"目标知识库数量: {len(db_ids)}")
    print(f"批次大小: {args.batch_size}")
    print(f"模式: {'DRY-RUN' if args.dry_run else 'EXECUTE'}")

    if args.dry_run:
        for db_id in db_ids:
            print(f"[DRY-RUN] would build profile for {db_id}")
        return

    summary = await build_profiles_batch(db_ids, batch_size=args.batch_size)
    print("\n执行结果:")
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
