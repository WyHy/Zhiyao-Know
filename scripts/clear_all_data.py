#!/usr/bin/env python3
"""
清空所有数据的脚本（保留超级管理员和默认部门）

警告：此操作不可逆！

将删除：
- 所有非超级管理员用户
- 所有非默认部门
- 所有知识库数据（数据库、文件、向量库）

保留：
- 超级管理员账户
- 默认部门

运行方式：
    docker compose exec api uv run python scripts/clear_all_data.py [--dry-run]
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.config.app import config
from src.storage.postgres.manager import PostgresManager


async def clear_all_data(dry_run: bool = False):
    """清空所有数据"""
    
    print("=" * 60)
    if dry_run:
        print("🔍 预览模式 - 不会实际删除数据")
    else:
        print("⚠️  警告：此操作将删除所有数据！")
        print("    保留：超级管理员 + 默认部门")
    print("=" * 60)
    
    db = PostgresManager()
    db.initialize()
    
    # 获取默认部门 ID
    default_dept_id = None
    async with db.get_async_session_context() as session:
        result = await session.execute(
            text("SELECT id FROM departments WHERE name = '默认部门' LIMIT 1")
        )
        row = result.fetchone()
        if row:
            default_dept_id = row[0]
    
    if not default_dept_id:
        print("\n❌ 错误：未找到默认部门，请先初始化系统")
        return
    
    print(f"\n🏢 默认部门 ID: {default_dept_id} (将保留)")
    
    # 显示统计
    async with db.get_async_session_context() as session:
        # 超级管理员
        result = await session.execute(
            text("SELECT username FROM users WHERE role = 'superadmin'")
        )
        superadmins = [r[0] for r in result.fetchall()]
        print(f"🛡️  超级管理员: {', '.join(superadmins)} (将保留)")
        
        # 非超级管理员用户
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE role != 'superadmin'")
        )
        user_count = result.fetchone()[0]
        print(f"\n👤 非超级管理员用户: {user_count} 个 (将删除)")
        
        # 非默认部门
        result = await session.execute(
            text("SELECT COUNT(*) FROM departments WHERE id != :default_id"),
            {"default_id": default_dept_id}
        )
        dept_count = result.fetchone()[0]
        print(f"🏢 非默认部门: {dept_count} 个 (将删除)")
        
        # 知识库
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_bases"))
        kb_count = result.fetchone()[0]
        print(f"📚 知识库: {kb_count} 个 (将删除)")
    
    if dry_run:
        print("\n" + "=" * 60)
        print("🔍 预览完成 - 使用不带 --dry-run 参数执行实际删除")
        print("=" * 60)
        return
    
    # 实际删除
    print("\n" + "-" * 40)
    print("开始删除...")
    print("-" * 40)
    
    # 清理顺序（考虑外键依赖）
    operations = [
        # 1. 清理操作日志（引用 users）
        ("operation_logs", "DELETE FROM operation_logs"),
        
        # 2. 知识库相关
        ("kb_files", "DELETE FROM kb_files"),
        ("knowledge_files", "DELETE FROM knowledge_files"),
        ("kb_department_relations", "DELETE FROM kb_department_relations"),
        ("kb_access_control", "DELETE FROM kb_access_control"),
        ("knowledge_bases", "DELETE FROM knowledge_bases"),
        
        # 3. agent_configs - 删除非默认部门的配置（有唯一约束，不能更新）
        ("agent_configs (删除非默认部门)", 
         f"DELETE FROM agent_configs WHERE department_id != {default_dept_id}"),
        
        # 4. users - 非超管清除部门关联，超管设为默认部门
        ("users (非超管清除部门关联)", f"UPDATE users SET department_id = NULL WHERE role != 'superadmin'"),
        ("users (超管设为默认部门)", f"UPDATE users SET department_id = {default_dept_id} WHERE role = 'superadmin'"),
        
        # 5. 删除非超级管理员用户
        ("users (非超管)", "DELETE FROM users WHERE role != 'superadmin'"),
    ]
    
    for name, sql in operations:
        try:
            async with db.get_async_session_context() as session:
                result = await session.execute(text(sql))
                await session.commit()
                print(f"   ✅ {name}: {result.rowcount} 条")
        except Exception as e:
            err_msg = str(e)
            if "does not exist" in err_msg:
                print(f"   ⚠️  {name}: 表不存在，跳过")
            else:
                print(f"   ⚠️  {name}: {err_msg[:80]}")
    
    # 按层级删除部门（从最深层开始，避免外键冲突）
    print("   🏢 按层级删除部门...")
    total_deleted = 0
    for _ in range(10):  # 最多10层
        try:
            async with db.get_async_session_context() as session:
                # 删除没有子部门的非默认部门
                result = await session.execute(text(f"""
                    DELETE FROM departments 
                    WHERE id != {default_dept_id}
                    AND id NOT IN (
                        SELECT DISTINCT parent_id FROM departments 
                        WHERE parent_id IS NOT NULL
                    )
                """))
                await session.commit()
                if result.rowcount == 0:
                    break
                total_deleted += result.rowcount
                print(f"      - 删除 {result.rowcount} 个叶子部门")
        except Exception as e:
            print(f"      ⚠️  删除失败: {str(e)[:60]}")
            break
    print(f"   ✅ departments: 共删除 {total_deleted} 个")
    
    # 清理文件存储
    print("\n📁 清理本地文件存储...")
    kb_data_dir = os.path.join(config.save_dir, "knowledge_base_data")
    if os.path.exists(kb_data_dir):
        file_count = sum(len(files) for _, _, files in os.walk(kb_data_dir))
        for item in os.listdir(kb_data_dir):
            item_path = os.path.join(kb_data_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"   ⚠️  删除失败 {item}: {e}")
        print(f"   ✅ 已清理 {file_count} 个文件")
    else:
        print(f"   ⚠️  目录不存在")
    
    # 清理 MinIO 存储
    print("\n📦 清理 MinIO 存储...")
    try:
        from minio import Minio
        from minio.error import S3Error
        
        minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        minio_secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        
        # 获取所有以 ref-kb- 开头的存储桶（知识库文件存储桶）
        buckets = client.list_buckets()
        kb_buckets = [b.name for b in buckets if b.name.startswith("ref-kb-")]
        
        print(f"   找到 {len(kb_buckets)} 个知识库存储桶")
        
        deleted_buckets = 0
        deleted_files = 0
        for bucket_name in kb_buckets:
            try:
                # 删除桶中所有对象
                objects = client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    client.remove_object(bucket_name, obj.object_name)
                    deleted_files += 1
                
                # 删除存储桶
                client.remove_bucket(bucket_name)
                deleted_buckets += 1
            except S3Error as e:
                print(f"   ⚠️  删除存储桶 {bucket_name} 失败: {e}")
        
        print(f"   ✅ 已删除 {deleted_buckets} 个存储桶，{deleted_files} 个文件")
    except ImportError:
        print("   ⚠️  minio 库未安装，跳过")
    except Exception as e:
        print(f"   ⚠️  MinIO 清理失败: {e}")
    
    # 清理 Milvus
    print("\n🔷 清理 Milvus...")
    try:
        from pymilvus import connections, utility
        
        milvus_uri = os.getenv("MILVUS_URI", "http://milvus:19530")
        milvus_db = os.getenv("MILVUS_DB_NAME", "default")
        
        connections.connect(alias="clear_script", uri=milvus_uri, db_name=milvus_db)
        collections = utility.list_collections(using="clear_script")
        
        deleted = 0
        for coll_name in collections:
            try:
                utility.drop_collection(coll_name, using="clear_script")
                deleted += 1
            except Exception:
                pass
        
        connections.disconnect("clear_script")
        print(f"   ✅ 已删除 {deleted} 个 collections")
    except ImportError:
        print("   ⚠️  pymilvus 未安装，跳过")
    except Exception as e:
        print(f"   ⚠️  连接失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 清理完成！")
    print(f"   保留：超级管理员 ({', '.join(superadmins)}) + 默认部门")
    print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="清空所有数据（保留超级管理员和默认部门）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际删除")
    args = parser.parse_args()
    
    await clear_all_data(args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
