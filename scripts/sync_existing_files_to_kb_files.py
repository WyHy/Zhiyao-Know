"""
同步已存在的文件到 kb_files 表

问题：之前上传的文件只存在于知识库元数据中，没有写入 kb_files 表
解决：从各个知识库的元数据中读取文件信息，同步到 kb_files 表

运行：docker compose exec api python scripts/sync_existing_files_to_kb_files.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import knowledge_base
from src.repositories.knowledge_file_repository import KnowledgeFileRepository
from src.storage.db.models import KBFile
from src.utils import logger


async def sync_files():
    """同步所有知识库的文件到 kb_files 表"""
    logger.info("=" * 70)
    logger.info("开始同步知识库文件到 kb_files 表")
    logger.info("=" * 70)
    
    # 初始化 PostgreSQL
    from src.storage.postgres.manager import PostgresManager
    pg_manager = PostgresManager()
    pg_manager.initialize()
    
    kb_file_repo = KnowledgeFileRepository()
    
    # 直接从数据库获取所有知识库
    from sqlalchemy import text
    async with pg_manager.get_async_session_context() as session:
        result = await session.execute(text("""
            SELECT db_id, name, kb_type
            FROM knowledge_bases
            ORDER BY created_at
        """))
        all_databases = [{"db_id": row[0], "name": row[1], "kb_type": row[2]} for row in result.fetchall()]
    
    logger.info(f"\n📚 找到 {len(all_databases)} 个知识库")
    
    total_synced = 0
    total_skipped = 0
    total_errors = 0
    
    for db in all_databases:
        db_id = db.get("db_id")
        db_name = db.get("name", "未知")
        kb_type = db.get("kb_type", "milvus")
        
        logger.info(f"\n处理知识库: {db_name} ({db_id})")
        
        try:
            # 根据类型获取知识库实例
            if kb_type == "lightrag":
                from src.knowledge.implementations.lightrag import LightRAGKB
                kb_instance = LightRAGKB(work_dir="saves/knowledge_base_data/lightrag_data")
            else:  # milvus
                from src.knowledge.implementations.milvus import MilvusKB
                kb_instance = MilvusKB(work_dir="saves/knowledge_base_data/milvus_data")
            
            # 从元数据文件中获取文件列表
            if not hasattr(kb_instance, 'files_meta'):
                logger.warning(f"  ⚠️  无法访问 files_meta，跳过")
                continue
            
            # 筛选该知识库的文件
            db_files = {
                fid: fmeta for fid, fmeta in kb_instance.files_meta.items()
                if fmeta.get("db_id") == db_id
            }
            
            if not db_files:
                logger.info(f"  ℹ️  没有文件")
                continue
            
            logger.info(f"  📄 找到 {len(db_files)} 个文件")
            
            for file_id, file_meta in db_files.items():
                try:
                    # 检查是否已存在
                    existing = await kb_file_repo.get_by_id(file_id)
                    
                    if existing:
                        logger.debug(f"    - {file_meta.get('filename', 'unknown')} (已存在，跳过)")
                        total_skipped += 1
                        continue
                    
                    # 创建新记录
                    kb_file = KBFile(
                        file_id=file_id,
                        kb_id=db_id,
                        filename=file_meta.get("filename", ""),
                        file_path=file_meta.get("path", ""),
                        file_size=file_meta.get("size", 0),
                        file_type=file_meta.get("type", ""),
                        status=file_meta.get("status", "indexed"),
                        title=file_meta.get("title"),
                        summary=file_meta.get("summary"),
                        tags=file_meta.get("tags", []),
                        created_at=file_meta.get("created_at"),
                        updated_at=file_meta.get("updated_at"),
                        created_by=file_meta.get("created_by"),
                    )
                    
                    await kb_file_repo.create(kb_file)
                    logger.info(f"    ✅ {file_meta.get('filename', 'unknown')}")
                    total_synced += 1
                    
                except Exception as e:
                    logger.error(f"    ❌ {file_meta.get('filename', 'unknown')}: {e}")
                    total_errors += 1
                    
        except Exception as e:
            logger.error(f"  ❌ 处理知识库失败: {e}")
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
        await sync_files()
    except Exception as e:
        logger.error(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
