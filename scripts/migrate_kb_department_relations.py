"""
数据库迁移脚本：知识库-部门关联功能

此脚本用于服务器部署更新时，确保数据库表结构正确，并为现有知识库创建初始的部门关联。

运行方式：
  docker compose exec api python scripts/migrate_kb_department_relations.py

功能：
  1. 确保必要的表存在（kb_department_relations, kb_access_control）
  2. 为现有知识库创建默认的部门关联（可选）
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.utils import logger

# 导入基础模型以确保表定义存在
from src.storage.db.models import KBDepartmentRelation, KBAccessControl


async def check_and_create_tables():
    """检查并创建必要的表"""
    logger.info("=" * 70)
    logger.info("步骤 1: 检查并创建必要的数据库表")
    logger.info("=" * 70)
    
    pg_manager = PostgresManager()
    pg_manager.initialize()
    
    async with pg_manager.get_async_session_context() as session:
        # 检查 kb_department_relations 表是否存在
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'kb_department_relations'
            )
        """))
        kb_dept_table_exists = result.scalar()
        
        # 检查 kb_access_control 表是否存在
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'kb_access_control'
            )
        """))
        kb_access_table_exists = result.scalar()
        
        logger.info(f"kb_department_relations 表: {'✅ 已存在' if kb_dept_table_exists else '❌ 不存在'}")
        logger.info(f"kb_access_control 表: {'✅ 已存在' if kb_access_table_exists else '❌ 不存在'}")
        
        if not kb_dept_table_exists or not kb_access_table_exists:
            logger.info("\n正在创建缺失的表...")
            try:
                # 直接使用 PostgresManager 创建表
                from src.storage.db.models import Base
                from sqlalchemy import MetaData
                
                # 创建特定的表
                if not kb_dept_table_exists:
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS kb_department_relations (
                            id SERIAL PRIMARY KEY,
                            kb_id VARCHAR(100) NOT NULL,
                            department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT kb_department_relations_unique UNIQUE (kb_id, department_id)
                        )
                    """))
                    await session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_kb_dept_kb_id ON kb_department_relations(kb_id)
                    """))
                    await session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_kb_dept_dept_id ON kb_department_relations(department_id)
                    """))
                    logger.info("  ✅ kb_department_relations 表创建完成")
                
                if not kb_access_table_exists:
                    await session.execute(text("""
                        CREATE TABLE IF NOT EXISTS kb_access_control (
                            id SERIAL PRIMARY KEY,
                            kb_id VARCHAR(100) NOT NULL,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            access_type VARCHAR(20) NOT NULL DEFAULT 'deny',
                            reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT kb_access_control_unique UNIQUE (kb_id, user_id)
                        )
                    """))
                    await session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_kb_access_kb_id ON kb_access_control(kb_id)
                    """))
                    await session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_kb_access_user_id ON kb_access_control(user_id)
                    """))
                    logger.info("  ✅ kb_access_control 表创建完成")
                
                await session.commit()
                logger.info("✅ 表创建完成")
            except Exception as e:
                logger.error(f"❌ 创建表失败: {e}")
                raise
        else:
            logger.info("✅ 所有必要的表都已存在")
    
    return kb_dept_table_exists, kb_access_table_exists


async def check_existing_relations():
    """检查现有的知识库-部门关联"""
    logger.info("\n" + "=" * 70)
    logger.info("步骤 2: 检查现有的知识库-部门关联")
    logger.info("=" * 70)
    
    pg_manager = PostgresManager()
    pg_manager.initialize()
    
    async with pg_manager.get_async_session_context() as session:
        # 统计知识库数量
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_bases"))
        kb_count = result.scalar()
        
        # 统计关联数量
        result = await session.execute(text("SELECT COUNT(*) FROM kb_department_relations"))
        relation_count = result.scalar()
        
        # 统计部门数量（排除默认部门）
        result = await session.execute(text("SELECT COUNT(*) FROM departments WHERE id != 1"))
        dept_count = result.scalar()
        
        logger.info(f"知识库总数: {kb_count}")
        logger.info(f"部门总数: {dept_count} (不含默认部门)")
        logger.info(f"已有关联数: {relation_count}")
        
        if relation_count == 0 and kb_count > 0:
            logger.warning("\n⚠️  当前没有任何知识库-部门关联！")
            logger.warning("   建议：为知识库创建部门关联，否则用户无法通过部门搜索文件")
            return True  # 需要创建关联
        elif relation_count > 0:
            logger.info("\n✅ 已存在知识库-部门关联")
            
            # 显示现有关联
            result = await session.execute(text("""
                SELECT 
                    kdr.kb_id,
                    kb.name as kb_name,
                    kdr.department_id,
                    d.name as dept_name
                FROM kb_department_relations kdr
                LEFT JOIN knowledge_bases kb ON kdr.kb_id = kb.db_id
                LEFT JOIN departments d ON kdr.department_id = d.id
                LIMIT 10
            """))
            relations = result.fetchall()
            
            logger.info("\n前10个关联关系:")
            for rel in relations:
                kb_id_short = rel[0][:20] + "..." if len(rel[0]) > 20 else rel[0]
                logger.info(f"  [{kb_id_short}] {rel[1]} -> {rel[3]}")
            
            if relation_count > 10:
                logger.info(f"  ... 还有 {relation_count - 10} 个关联")
            
            return False  # 不需要创建关联
        
        return False


async def create_default_relations():
    """为没有关联的知识库创建默认的部门关联（可选）"""
    logger.info("\n" + "=" * 70)
    logger.info("步骤 3: 创建默认的知识库-部门关联（可选）")
    logger.info("=" * 70)
    
    pg_manager = PostgresManager()
    pg_manager.initialize()
    
    async with pg_manager.get_async_session_context() as session:
        # 获取所有知识库的 db_id
        result = await session.execute(text("SELECT db_id, name FROM knowledge_bases"))
        all_kbs = result.fetchall()
        
        if not all_kbs:
            logger.info("没有找到知识库，跳过")
            return
        
        # 获取已有关联的知识库
        result = await session.execute(text("SELECT DISTINCT kb_id FROM kb_department_relations"))
        linked_kb_ids = {row[0] for row in result.fetchall()}
        
        # 找出未关联的知识库
        unlinked_kbs = [kb for kb in all_kbs if kb[0] not in linked_kb_ids]
        
        if not unlinked_kbs:
            logger.info("✅ 所有知识库都已有部门关联")
            return
        
        logger.info(f"发现 {len(unlinked_kbs)} 个未关联的知识库")
        
        # 获取可用的部门（排除默认部门）
        result = await session.execute(text("""
            SELECT id, name 
            FROM departments 
            WHERE id != 1 
            ORDER BY level, sort_order
            LIMIT 1
        """))
        default_dept = result.fetchone()
        
        if not default_dept:
            logger.warning("⚠️  没有可用的部门（除默认部门外），无法创建关联")
            logger.warning("   建议：先创建部门，然后手动为知识库分配部门")
            return
        
        logger.info(f"\n将未关联的知识库关联到: {default_dept[1]} (ID: {default_dept[0]})")
        logger.info("(后续可通过前端界面修改知识库的部门归属)\n")
        
        created_count = 0
        for kb_id, kb_name in unlinked_kbs:
            try:
                await session.execute(
                    text("""
                        INSERT INTO kb_department_relations (kb_id, department_id)
                        VALUES (:kb_id, :department_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"kb_id": kb_id, "department_id": default_dept[0]}
                )
                logger.info(f"  ✅ {kb_name} -> {default_dept[1]}")
                created_count += 1
            except Exception as e:
                logger.error(f"  ❌ 关联失败 ({kb_name}): {e}")
        
        await session.commit()
        logger.info(f"\n✅ 创建了 {created_count} 个新关联")


async def verify_migration():
    """验证迁移结果"""
    logger.info("\n" + "=" * 70)
    logger.info("步骤 4: 验证迁移结果")
    logger.info("=" * 70)
    
    pg_manager = PostgresManager()
    pg_manager.initialize()
    
    async with pg_manager.get_async_session_context() as session:
        # 统计数据
        result = await session.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM knowledge_bases) as kb_count,
                (SELECT COUNT(*) FROM departments WHERE id != 1) as dept_count,
                (SELECT COUNT(*) FROM kb_department_relations) as relation_count,
                (SELECT COUNT(*) FROM kb_access_control) as access_control_count
        """))
        stats = result.fetchone()
        
        logger.info("数据库统计:")
        logger.info(f"  知识库数量: {stats[0]}")
        logger.info(f"  部门数量: {stats[1]}")
        logger.info(f"  知识库-部门关联: {stats[2]}")
        logger.info(f"  访问控制记录: {stats[3]}")
        
        # 检查是否有未关联的知识库
        result = await session.execute(text("""
            SELECT kb.db_id, kb.name
            FROM knowledge_bases kb
            LEFT JOIN kb_department_relations kdr ON kb.db_id = kdr.kb_id
            WHERE kdr.id IS NULL
        """))
        unlinked = result.fetchall()
        
        if unlinked:
            logger.warning(f"\n⚠️  仍有 {len(unlinked)} 个知识库未关联到部门:")
            for kb in unlinked[:5]:
                logger.warning(f"    - {kb[1]}")
            if len(unlinked) > 5:
                logger.warning(f"    ... 还有 {len(unlinked) - 5} 个")
            logger.warning("\n建议通过前端界面为这些知识库分配部门")
        else:
            logger.info("\n✅ 所有知识库都已关联到部门")


async def main():
    """主函数"""
    logger.info("\n" + "=" * 70)
    logger.info("知识库-部门关联功能 数据库迁移脚本")
    logger.info("=" * 70)
    
    try:
        # 1. 检查并创建表
        await check_and_create_tables()
        
        # 2. 检查现有关联
        need_create = await check_existing_relations()
        
        # 3. 如果需要，创建默认关联（可选）
        if need_create:
            logger.info("\n是否为未关联的知识库创建默认部门关联？")
            logger.info("(如果选择否，可以稍后通过前端界面手动分配)")
            # 自动创建
            await create_default_relations()
        
        # 4. 验证结果
        await verify_migration()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ 数据库迁移完成！")
        logger.info("=" * 70)
        logger.info("\n后续步骤:")
        logger.info("  1. 重启 API 服务: docker compose restart api")
        logger.info("  2. 访问前端测试页面: http://localhost:5173/file-search-test")
        logger.info("  3. 通过系统设置管理知识库与部门的关联关系")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ 迁移失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
