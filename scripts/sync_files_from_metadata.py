"""
从元数据文件直接同步文件到 kb_files 表（更简单的方法）

运行：docker compose exec api python scripts/sync_files_from_metadata.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.knowledge_file_repository import KnowledgeFileRepository
from src.storage.db.models import KBFile
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def sync_from_metadata():
    """从元数据 JSON 文件同步"""
    logger.info("=" * 70)
    logger.info("从元数据文件同步文件到 kb_files 表")
    logger.info("=" * 70)
    
    # 初始化
    pg_manager = PostgresManager()
    pg_manager.initialize()
    kb_file_repo = KnowledgeFileRepository()
    
    # 读取 Milvus 元数据
    metadata_file = Path("saves/knowledge_base_data/milvus_data/metadata_milvus.json")
    if not metadata_file.exists():
        logger.warning("元数据文件不存在，跳过")
        return
    
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    files_meta = metadata.get("files", {})
    logger.info(f"\n📄 元数据中找到 {len(files_meta)} 个文件")
    
    total_synced = 0
    total_skipped = 0
    total_errors = 0
    
    for file_id, file_meta in files_meta.items():
        try:
            kb_id = file_meta.get("database_id") or file_meta.get("db_id")
            if not kb_id:
                logger.warning(f"  ⚠️  {file_meta.get('filename', file_id)}: 缺少 database_id")
                total_errors += 1
                continue
            
            # 检查是否已存在
            existing = await kb_file_repo.get_by_file_id(file_id)
            
            if existing:
                total_skipped += 1
                continue
            
            # 使用 upsert 创建或更新（不传时间戳，让数据库自动生成）
            data = {
                "db_id": kb_id,
                "filename": file_meta.get("filename", ""),
                "path": file_meta.get("path", ""),
                "file_size": file_meta.get("size", 0),
                "file_type": file_meta.get("file_type", ""),
                "status": file_meta.get("status", "indexed"),
            }
            
            await kb_file_repo.upsert(file_id, data)
            logger.info(f"  ✅ {file_meta.get('filename', file_id)} -> {kb_id}")
            total_synced += 1
            
        except Exception as e:
            logger.error(f"  ❌ {file_meta.get('filename', file_id)}: {e}")
            total_errors += 1
    
    # 统计
    logger.info(f"\n" + "=" * 70)
    logger.info(f"同步完成！")
    logger.info(f"  ✅ 新增: {total_synced} 个文件")
    logger.info(f"  ⏭️  跳过: {total_skipped} 个文件（已存在）")
    logger.info(f"  ❌ 错误: {total_errors} 个")
    logger.info("=" * 70)


async def main():
    try:
        await sync_from_metadata()
    except Exception as e:
        logger.error(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
