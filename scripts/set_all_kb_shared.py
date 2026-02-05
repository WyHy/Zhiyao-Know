"""
将所有知识库设置为全员共享的脚本
"""

import asyncio
import sys
from pathlib import Path
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager


async def set_all_kb_shared():
    """将所有知识库设置为全员共享"""
    
    print("📚 开始设置所有知识库为全员共享...")
    print("=" * 60)
    
    # 初始化数据库
    db = PostgresManager()
    db.initialize()
    
    try:
        async with db.get_async_session_context() as session:
            # 1. 获取所有知识库
            result = await session.execute(text("""
                SELECT db_id, name, share_config
                FROM knowledge_bases
                ORDER BY created_at DESC
            """))
            kbs = result.fetchall()
            
            if not kbs:
                print("✅ 没有知识库需要设置")
                return
            
            print(f"\n找到 {len(kbs)} 个知识库:\n")
            
            # 2. 统计需要更新的知识库
            need_update = []
            already_shared = []
            
            for db_id, name, share_config in kbs:
                share_config = share_config or {}
                is_shared = share_config.get('is_shared', False)
                accessible_departments = share_config.get('accessible_departments', [])
                
                if is_shared and not accessible_departments:
                    already_shared.append(name)
                    print(f"  ✅ {name} - 已经是全员共享")
                else:
                    need_update.append((db_id, name))
                    status = "部分共享" if is_shared else "不共享"
                    if accessible_departments:
                        status += f" (限定部门: {accessible_departments})"
                    print(f"  ⚠️  {name} - {status}")
            
            # 3. 批量更新
            if need_update:
                print(f"\n\n🔄 开始更新 {len(need_update)} 个知识库...")
                
                shared_config = json.dumps({
                    'is_shared': True,
                    'accessible_departments': []
                })
                
                for db_id, name in need_update:
                    await session.execute(text("""
                        UPDATE knowledge_bases
                        SET share_config = :config
                        WHERE db_id = :db_id
                    """), {'config': shared_config, 'db_id': db_id})
                    
                    print(f"  ✅ 已更新: {name}")
                
                await session.commit()
                
                print("\n" + "=" * 60)
                print(f"✅ 成功！{len(need_update)} 个知识库已设置为全员共享")
                if already_shared:
                    print(f"   {len(already_shared)} 个知识库本来就是全员共享")
            else:
                print("\n" + "=" * 60)
                print(f"✅ 所有 {len(already_shared)} 个知识库都已经是全员共享状态")
            
    except Exception as e:
        print(f"\n❌ 设置失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(set_all_kb_shared())
