"""
数据库表结构升级脚本
- 将部门表改为树形结构
- 将用户-部门关系改为多对多
- 添加知识库-部门关联表
- 添加知识库访问控制表
- 添加文件表
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.postgres.manager import PostgresManager
from src.utils import logger


async def upgrade_database():
    """升级数据库表结构"""
    
    db = PostgresManager()
    db.initialize()
    
    print("🔄 开始升级数据库表结构...\n")
    
    async with db.get_async_session_context() as session:
        try:
            # ============================================
            # 1. 备份现有用户的部门关系
            # ============================================
            print("1️⃣ 备份现有用户-部门关系...")
            result = await session.execute(
                text("SELECT id, department_id FROM users WHERE department_id IS NOT NULL")
            )
            user_dept_backup = [(row[0], row[1]) for row in result]
            print(f"   ✅ 备份了 {len(user_dept_backup)} 个用户的部门关系\n")
            
            # ============================================
            # 2. 更新部门表结构
            # ============================================
            print("2️⃣ 升级部门表...")
            
            # 检查列是否存在
            check_column = await session.execute(
                text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='departments' AND column_name='parent_id'
                """)
            )
            has_parent_id = check_column.fetchone() is not None
            
            if not has_parent_id:
                await session.execute(text("ALTER TABLE departments DROP CONSTRAINT IF EXISTS departments_name_key"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES departments(id) ON DELETE CASCADE"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS level INTEGER NOT NULL DEFAULT 1"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS path VARCHAR(500)"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS is_active INTEGER NOT NULL DEFAULT 1"))
                await session.execute(text("ALTER TABLE departments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()"))
                
                # 创建索引
                await session.execute(text("CREATE INDEX IF NOT EXISTS idx_departments_parent_id ON departments(parent_id)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS idx_departments_level ON departments(level)"))
                await session.execute(text("CREATE INDEX IF NOT EXISTS idx_departments_path ON departments(path)"))
                
                # 更新现有部门的 level=1, path=id
                await session.execute(text("UPDATE departments SET level = 1, path = CAST(id AS VARCHAR) WHERE parent_id IS NULL"))
                
                print("   ✅ 部门表升级完成\n")
            else:
                print("   ⏭️  部门表已经是新结构，跳过\n")
            
            # ============================================
            # 3. 创建用户-部门关联表
            # ============================================
            print("3️⃣ 创建用户-部门关联表...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_department_relations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
                    is_primary INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, department_id)
                )
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_dept_user_id ON user_department_relations(user_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_dept_dept_id ON user_department_relations(department_id)"))
            print("   ✅ 用户-部门关联表创建完成\n")
            
            # ============================================
            # 4. 迁移用户的部门关系
            # ============================================
            print("4️⃣ 迁移用户部门关系到新表...")
            migrated_count = 0
            for user_id, dept_id in user_dept_backup:
                await session.execute(
                    text("""
                        INSERT INTO user_department_relations (user_id, department_id, is_primary)
                        VALUES (:user_id, :dept_id, 1)
                        ON CONFLICT (user_id, department_id) DO NOTHING
                    """),
                    {"user_id": user_id, "dept_id": dept_id}
                )
                migrated_count += 1
            print(f"   ✅ 迁移了 {migrated_count} 条用户-部门关系\n")
            
            # ============================================
            # 5. 创建知识库-部门关联表
            # ============================================
            print("5️⃣ 创建知识库-部门关联表...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS kb_department_relations (
                    id SERIAL PRIMARY KEY,
                    kb_id VARCHAR(100) NOT NULL,
                    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(kb_id, department_id)
                )
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_dept_kb_id ON kb_department_relations(kb_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_dept_dept_id ON kb_department_relations(department_id)"))
            print("   ✅ 知识库-部门关联表创建完成\n")
            
            # ============================================
            # 6. 创建知识库访问控制表
            # ============================================
            print("6️⃣ 创建知识库访问控制表...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS kb_access_control (
                    id SERIAL PRIMARY KEY,
                    kb_id VARCHAR(100) NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    access_type VARCHAR(20) NOT NULL DEFAULT 'deny',
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    created_by INTEGER REFERENCES users(id),
                    UNIQUE(kb_id, user_id)
                )
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_access_kb_id ON kb_access_control(kb_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_access_user_id ON kb_access_control(user_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_access_kb_user ON kb_access_control(kb_id, user_id)"))
            print("   ✅ 知识库访问控制表创建完成\n")
            
            # ============================================
            # 7. 创建文件表
            # ============================================
            print("7️⃣ 创建知识库文件表...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS kb_files (
                    id SERIAL PRIMARY KEY,
                    file_id VARCHAR(100) UNIQUE NOT NULL,
                    kb_id VARCHAR(100) NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    file_type VARCHAR(50),
                    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
                    title TEXT,
                    summary TEXT,
                    tags JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    created_by INTEGER REFERENCES users(id)
                )
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_files_file_id ON kb_files(file_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_files_kb_id ON kb_files(kb_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_files_filename ON kb_files(filename)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_files_status ON kb_files(status)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_files_created_at ON kb_files(created_at)"))
            
            # 创建全文检索索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_kb_files_search ON kb_files 
                USING gin(to_tsvector('simple', 
                    COALESCE(filename, '') || ' ' || 
                    COALESCE(title, '') || ' ' || 
                    COALESCE(summary, '')
                ))
            """))
            print("   ✅ 知识库文件表创建完成\n")
            
            await session.commit()
            
            print("=" * 50)
            print("🎉 数据库升级完成！")
            print("=" * 50)
            print("\n新增的表：")
            print("  ✅ user_department_relations (用户-部门多对多)")
            print("  ✅ kb_department_relations (知识库-部门多对多)")
            print("  ✅ kb_access_control (知识库访问控制)")
            print("  ✅ kb_files (文件检索)")
            print("\n已迁移的数据：")
            print(f"  ✅ {migrated_count} 条用户-部门关系")
            
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库升级失败: {e}")
            import traceback
            print(f"\n❌ 升级失败: {e}")
            print(traceback.format_exc())
            return False


if __name__ == "__main__":
    success = asyncio.run(upgrade_database())
    sys.exit(0 if success else 1)
