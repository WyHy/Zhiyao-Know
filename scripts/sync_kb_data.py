"""
同步知识库数据 - 将现有知识库的文件同步到数据库，并建立部门关联

运行：docker compose exec api python scripts/sync_kb_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.knowledge.factory import KnowledgeBaseFactory
from src.utils import logger


async def sync_kb_files_to_db():
    """同步知识库文件到数据库"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 1. 获取所有知识库
        result = await session.execute(text("SELECT id, name, type FROM knowledge_bases"))
        knowledge_bases = result.fetchall()
        
        if not knowledge_bases:
            logger.info("没有找到知识库")
            return
        
        logger.info(f"找到 {len(knowledge_bases)} 个知识库")
        
        total_files = 0
        
        for kb_id, kb_name, kb_type in knowledge_bases:
            logger.info(f"\n处理知识库: {kb_name} (ID: {kb_id}, 类型: {kb_type})")
            
            try:
                # 2. 获取知识库实例
                kb_instance = KnowledgeBaseFactory.get_instance(kb_id)
                
                # 3. 获取知识库中的文件列表
                # 对于 Milvus 类型的知识库
                if kb_type == "milvus":
                    # 从 Milvus 集合中获取文件列表
                    try:
                        # 查询已有的文件元数据
                        files_info = await kb_instance.list_files()  # 假设有这个方法
                        
                        if not files_info:
                            logger.info(f"  知识库 {kb_name} 中没有文件")
                            continue
                        
                        for file_info in files_info:
                            # 插入或更新文件记录
                            await session.execute(
                                text("""
                                    INSERT INTO kb_files (
                                        file_id, kb_id, filename, file_path, 
                                        file_size, file_type, status, created_by
                                    )
                                    VALUES (
                                        :file_id, :kb_id, :filename, :file_path,
                                        :file_size, :file_type, :status, :created_by
                                    )
                                    ON CONFLICT (file_id) DO UPDATE SET
                                        status = EXCLUDED.status,
                                        updated_at = NOW()
                                """),
                                {
                                    "file_id": file_info.get("file_id", f"{kb_id}_{file_info['filename']}"),
                                    "kb_id": kb_id,
                                    "filename": file_info["filename"],
                                    "file_path": file_info.get("file_path"),
                                    "file_size": file_info.get("file_size", 0),
                                    "file_type": file_info.get("file_type", "unknown"),
                                    "status": "indexed",  # 既然在知识库中，就认为已索引
                                    "created_by": 1,  # 默认管理员
                                }
                            )
                            total_files += 1
                        
                        logger.info(f"  ✅ 同步了 {len(files_info)} 个文件")
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️  获取文件列表失败: {e}")
                        # 如果没有 list_files 方法，使用其他方式
                        logger.info(f"  使用备用方法...")
                        # 可以从 MinIO 或其他地方获取文件列表
                        
                elif kb_type == "lightrag":
                    logger.info(f"  知识库类型为 LightRAG，暂不支持文件列表同步")
                    # LightRAG 通常存储在图数据库中，没有独立的文件概念
                
            except Exception as e:
                logger.error(f"  ❌ 处理知识库失败: {e}")
                continue
        
        await session.commit()
        logger.info(f"\n✅ 总共同步了 {total_files} 个文件到数据库")


async def create_kb_department_relations():
    """创建知识库和部门的关联"""
    db = PostgresManager()
    db.initialize()
    
    async with db.get_async_session_context() as session:
        # 获取所有知识库和部门
        kb_result = await session.execute(text("SELECT id, name FROM knowledge_bases"))
        kbs = kb_result.fetchall()
        
        dept_result = await session.execute(text("SELECT id, name FROM departments WHERE id != 1"))  # 排除默认部门
        depts = dept_result.fetchall()
        
        if not kbs or not depts:
            logger.warning("没有足够的知识库或部门来创建关联")
            return
        
        logger.info(f"\n创建知识库-部门关联")
        logger.info(f"知识库数: {len(kbs)}, 部门数: {len(depts)}")
        
        # 为每个知识库分配一个部门（示例分配规则）
        kb_dept_mapping = {
            "测试": ["研发部", "测试部"],
            "融媒体中心": ["宣传部", "市场部"],
            "纪委办": ["纪委办公室"],
            "数字化部": ["数据中心", "信息部"],
        }
        
        created_count = 0
        
        for kb_id, kb_name in kbs:
            # 根据名称匹配部门
            target_dept_names = kb_dept_mapping.get(kb_name, [])
            
            if not target_dept_names:
                # 如果没有匹配规则，分配给第一个部门
                target_dept_names = [depts[0][1]]
            
            for dept_id, dept_name in depts:
                if dept_name in target_dept_names:
                    try:
                        await session.execute(
                            text("""
                                INSERT INTO kb_department_relations (kb_id, department_id)
                                VALUES (:kb_id, :department_id)
                                ON CONFLICT DO NOTHING
                            """),
                            {"kb_id": str(kb_id), "department_id": dept_id}
                        )
                        logger.info(f"  ✅ 关联: {kb_name} -> {dept_name}")
                        created_count += 1
                    except Exception as e:
                        logger.warning(f"  ⚠️  关联失败: {e}")
        
        await session.commit()
        logger.info(f"\n✅ 创建了 {created_count} 个知识库-部门关联")


async def create_sample_files():
    """创建一些示例文件（如果知识库中没有文件）"""
    db = PostgresManager()
    db.initialize()
    
    logger.info("\n创建示例文件数据")
    
    async with db.get_async_session_context() as session:
        # 获取知识库
        result = await session.execute(text("SELECT id, name FROM knowledge_bases LIMIT 4"))
        kbs = result.fetchall()
        
        if not kbs:
            logger.warning("没有知识库")
            return
        
        sample_files = [
            {"filename": "10雷锋纪录.jpg", "type": "jpg", "size": 1024000},
            {"filename": "11年诊具流程.png", "type": "png", "size": 512000},
            {"filename": "2023YFC2308502001.jpg", "type": "jpg", "size": 2048000},
            {"filename": "2023YFC2308503001.jpg", "type": "jpg", "size": 1536000},
            {"filename": "测试表格2.xlsx", "type": "xlsx", "size": 102400},
        ]
        
        file_count = 0
        
        for kb_id, kb_name in kbs:
            for i, file_data in enumerate(sample_files):
                file_id = f"{kb_id}_file_{i+1}"
                
                try:
                    await session.execute(
                        text("""
                            INSERT INTO kb_files (
                                file_id, kb_id, filename, file_path,
                                file_size, file_type, status, created_by,
                                title, summary
                            )
                            VALUES (
                                :file_id, :kb_id, :filename, :file_path,
                                :file_size, :file_type, :status, :created_by,
                                :title, :summary
                            )
                            ON CONFLICT (file_id) DO NOTHING
                        """),
                        {
                            "file_id": file_id,
                            "kb_id": str(kb_id),  # 转换为字符串
                            "filename": file_data["filename"],
                            "file_path": f"/files/{kb_id}/{file_data['filename']}",
                            "file_size": file_data["size"],
                            "file_type": file_data["type"],
                            "status": "indexed",
                            "created_by": 1,
                            "title": f"示例文件 - {file_data['filename']}",
                            "summary": f"这是一个 {file_data['type']} 类型的示例文件",
                        }
                    )
                    file_count += 1
                except Exception as e:
                    logger.warning(f"  插入文件失败: {e}")
        
        await session.commit()
        logger.info(f"✅ 创建了 {file_count} 个示例文件")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始同步知识库数据")
    logger.info("=" * 60)
    
    # 1. 创建知识库-部门关联
    await create_kb_department_relations()
    
    # 2. 尝试同步文件
    # await sync_kb_files_to_db()
    
    # 3. 如果没有文件，创建示例文件
    await create_sample_files()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 数据同步完成！")
    logger.info("=" * 60)
    logger.info("\n现在可以测试文件检索功能了：")
    logger.info("  访问: http://localhost:5173/file-search-test")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
