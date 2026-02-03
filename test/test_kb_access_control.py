#!/usr/bin/env python3
"""
测试知识库访问控制（黑名单机制）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import text
from src.services.kb_access_control_service import KBAccessControlService
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def test_kb_access_control():
    logger.info("=" * 60)
    logger.info("知识库访问控制测试（黑名单机制）")
    logger.info("=" * 60)
    
    base_url = "http://localhost:5050"
    
    # 1. 普通用户默认可以访问所有知识库
    logger.info("1️⃣  测试：普通用户默认可以访问所有知识库")
    client = httpx.AsyncClient(base_url=base_url, timeout=30)
    resp = await client.post("/api/auth/token", data={"username": "lina", "password": "Pass1234"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    resp = await client.get("/api/knowledge/databases")
    databases = resp.json().get("databases", [])
    logger.info(f"   ✅ 李娜可以访问 {len(databases)} 个知识库")
    
    if not databases:
        logger.info("   ⚠️  没有知识库，跳过后续测试")
        await client.aclose()
        return
    
    kb_id_1 = databases[0]["db_id"]
    kb_name_1 = databases[0].get("name", "未命名")
    logger.info(f"   第一个知识库: {kb_name_1} (ID: {kb_id_1})")
    await client.aclose()
    
    # 2. 管理员禁止用户访问某个知识库
    logger.info("\n2️⃣  测试：管理员禁止李娜访问第一个知识库")
    access_control = KBAccessControlService()
    
    # 获取李娜的ID
    db = PostgresManager()
    db.initialize()
    async with db.get_async_session_context() as session:
        result = await session.execute(
            text("SELECT id FROM users WHERE user_id = :user_id"),
            {"user_id": "lina"}
        )
        lina_id = result.fetchone()[0]
    
    # 禁止访问
    await access_control.deny_user_access(
        kb_id=kb_id_1,
        user_ids=[lina_id],
        reason="测试黑名单功能",
        operator_id=1
    )
    logger.info(f"   ✅ 已禁止李娜(ID:{lina_id})访问知识库 {kb_name_1}")
    
    # 3. 验证用户现在无法访问该知识库
    logger.info("\n3️⃣  测试：验证李娜现在看不到被禁止的知识库")
    client = httpx.AsyncClient(base_url=base_url, timeout=30)
    resp = await client.post("/api/auth/token", data={"username": "lina", "password": "Pass1234"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    resp = await client.get("/api/knowledge/databases")
    new_databases = resp.json().get("databases", [])
    new_kb_ids = [db["db_id"] for db in new_databases]
    
    logger.info(f"   现在李娜可以访问 {len(new_databases)} 个知识库（减少了 {len(databases) - len(new_databases)} 个）")
    if kb_id_1 not in new_kb_ids:
        logger.info(f"   ✅ 被禁止的知识库已不在列表中")
    else:
        logger.error(f"   ❌ 被禁止的知识库仍在列表中（有问题！）")
    await client.aclose()
    
    # 4. 验证其他用户仍可以访问
    logger.info("\n4️⃣  测试：验证其他用户（王强）仍可以访问该知识库")
    client = httpx.AsyncClient(base_url=base_url, timeout=30)
    resp = await client.post("/api/auth/token", data={"username": "wangqiang", "password": "Pass1234"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    resp = await client.get("/api/knowledge/databases")
    wq_databases = resp.json().get("databases", [])
    wq_kb_ids = [db["db_id"] for db in wq_databases]
    
    logger.info(f"   王强可以访问 {len(wq_databases)} 个知识库")
    if kb_id_1 in wq_kb_ids:
        logger.info(f"   ✅ 王强可以访问知识库 {kb_name_1}（黑名单只针对李娜）")
    else:
        logger.error(f"   ❌ 王强也无法访问该知识库（不应该！）")
    await client.aclose()
    
    # 5. 恢复访问权限
    logger.info("\n5️⃣  测试：管理员恢复李娜的访问权限")
    await access_control.allow_user_access(kb_id=kb_id_1, user_ids=[lina_id])
    logger.info(f"   ✅ 已恢复李娜对知识库 {kb_name_1} 的访问权限")
    
    # 6. 验证用户可以再次访问
    logger.info("\n6️⃣  测试：验证李娜现在可以再次看到该知识库")
    client = httpx.AsyncClient(base_url=base_url, timeout=30)
    resp = await client.post("/api/auth/token", data={"username": "lina", "password": "Pass1234"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    resp = await client.get("/api/knowledge/databases")
    final_databases = resp.json().get("databases", [])
    final_kb_ids = [db["db_id"] for db in final_databases]
    
    logger.info(f"   现在李娜可以访问 {len(final_databases)} 个知识库（恢复了 {len(final_databases) - len(new_databases)} 个）")
    if kb_id_1 in final_kb_ids:
        logger.info(f"   ✅ 知识库已恢复在列表中")
    else:
        logger.error(f"   ❌ 知识库仍不在列表中（有问题！）")
    await client.aclose()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成！")
    logger.info("=" * 60)


async def main():
    try:
        await test_kb_access_control()
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
