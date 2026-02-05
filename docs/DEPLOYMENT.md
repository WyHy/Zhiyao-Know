# 新服务器部署指南

本指南说明如何在全新服务器上部署 Yuxi-Know，确保数据库自动初始化。

## ✅ 数据库自动初始化机制

**好消息：项目已具备完整的数据库自动初始化功能！**

### 🔄 自动化流程

当你在新服务器上部署时，系统会自动完成以下操作：

1. **应用启动时**（`lifespan.py`）：
   - ✅ 初始化 PostgreSQL 连接
   - ✅ 自动创建所有业务数据表
   - ✅ 确保知识库 schema 完整
   - ✅ 初始化知识库管理器

2. **表结构自动创建**：
   - ✅ `departments` - 部门表（树形结构）
   - ✅ `users` - 用户表（通过 department_id 关联部门）
   - ✅ `kb_department_relations` - 知识库-部门关联表
   - ✅ `kb_access_control` - 知识库访问控制表（黑名单）
   - ✅ `knowledge_files` - 知识库文件表
   - ✅ `conversations` - 对话表
   - ✅ `messages` - 消息表
   - ✅ `knowledge_bases` - 知识库表
   - ✅ 以及其他所有业务表

### 📋 涉及的关键文件

```
server/utils/lifespan.py              # 应用启动时初始化
src/storage/postgres/manager.py      # 数据库管理器
src/storage/db/models.py              # 数据库模型定义
src/storage/postgres/models_business.py  # 业务模型
src/storage/postgres/models_knowledge.py # 知识库模型
scripts/init_database.py              # 手动初始化脚本（可选）
```

## 🚀 部署步骤

### 1. 准备环境

确保服务器已安装：
- Docker
- Docker Compose

### 2. 克隆代码

```bash
git clone <your-repository-url>
cd Yuxi-Know
```

### 3. 配置环境变量

复制环境变量模板：

```bash
cp .env.template .env
```

编辑 `.env` 文件，配置必要的环境变量：

```bash
# PostgreSQL 配置（必需）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=yuxi_know

# 超级管理员账号（首次启动时创建）
YUXI_SUPER_ADMIN_NAME=admin
YUXI_SUPER_ADMIN_PASSWORD=your_admin_password

# LLM 配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# 其他配置...
```

### 4. 启动服务

```bash
# 启动所有服务（包括 PostgreSQL）
docker compose up -d

# 查看日志（确认初始化成功）
docker compose logs -f api-dev
```

**预期日志输出**：

```
PostgreSQL manager initialized for knowledge base: postgresql+asyncpg://***
PostgreSQL business tables created/checked
PostgreSQL schema ensured
Knowledge base manager initialized
```

### 5. 验证部署（可选）

运行验证脚本，确认数据库结构正确：

```bash
# 查看数据库表
docker compose exec api python -c "
import asyncio
from src.storage.postgres.manager import PostgresManager
from sqlalchemy import text

async def check():
    db = PostgresManager()
    db.initialize()
    async with db.get_async_session_context() as session:
        result = await session.execute(text('''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        '''))
        tables = [row[0] for row in result.fetchall()]
        print(f'已创建 {len(tables)} 个表:')
        for table in tables:
            print(f'  - {table}')

asyncio.run(check())
"
```

预期输出包括：
- `departments`
- `users`
- `kb_department_relations`
- `kb_access_control`
- `knowledge_files`
- `knowledge_bases`
- 等等...

### 6. 创建测试数据（可选）

如果需要测试数据：

```bash
# 运行批量创建脚本
docker compose exec api python scripts/batch_create_departments_users.py
```

这会创建：
- 测试部门（树形结构）
- 测试用户（分配到不同部门）

### 7. 访问应用

打开浏览器访问：
- 前端：`http://<your-server-ip>:5173`
- API 文档：`http://<your-server-ip>:5050/docs`

使用超级管理员账号登录：
- 用户名：`.env` 中配置的 `YUXI_SUPER_ADMIN_NAME`
- 密码：`.env` 中配置的 `YUXI_SUPER_ADMIN_PASSWORD`

## 🔧 手动初始化（如果自动初始化失败）

如果应用启动时自动初始化失败，可以手动运行：

```bash
# 手动初始化数据库
docker compose exec api python scripts/init_database.py
```

这个脚本会：
1. 创建所有表
2. 添加必要的约束（如 `is_active` 默认值）
3. 创建默认部门
4. 验证初始化结果

## 📊 数据库结构说明

### 核心表

#### departments（部门表）
```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES departments(id),
    level INTEGER NOT NULL DEFAULT 1,
    path VARCHAR(500),  -- 如 "1/5/12"
    sort_order INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(255),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### kb_department_relations（知识库-部门关联）
```sql
CREATE TABLE kb_department_relations (
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    created_at TIMESTAMP
);
```

#### kb_access_control（知识库访问控制-黑名单）
```sql
CREATE TABLE kb_access_control (
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    access_type VARCHAR(20) NOT NULL DEFAULT 'deny',
    reason TEXT,
    created_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);
```

## ⚠️ 注意事项

### 1. 环境变量

**必须配置的环境变量**：
- `POSTGRES_URL` - PostgreSQL 连接字符串（如果不使用 docker-compose 的默认配置）
- `YUXI_SUPER_ADMIN_NAME` - 超级管理员用户名
- `YUXI_SUPER_ADMIN_PASSWORD` - 超级管理员密码

### 2. 数据持久化

Docker Compose 配置已包含数据卷持久化：
```yaml
volumes:
  postgres-data:  # PostgreSQL 数据
  minio-data:     # MinIO 对象存储
```

确保不要删除这些卷，否则会丢失数据。

### 3. 迁移现有数据

如果从旧版本升级，需要运行迁移脚本：

```bash
# 迁移用户部门字段（单选 -> 多选）
docker compose exec api python scripts/sync_department_field.py

# 迁移知识库-部门关联
docker compose exec api python scripts/migrate_kb_department_relations.py

# 清理重复部门数据
docker compose exec api python scripts/cleanup_duplicate_departments.py
```

### 4. 数据库备份

建议定期备份 PostgreSQL：

```bash
# 备份
docker compose exec postgres pg_dump -U postgres yuxi_know > backup.sql

# 恢复
docker compose exec -T postgres psql -U postgres yuxi_know < backup.sql
```

## 🐛 故障排查

### 问题 1：表未自动创建

**症状**：应用启动但数据库表不存在

**解决**：
```bash
# 1. 检查环境变量
docker compose exec api env | grep POSTGRES_URL

# 2. 查看日志
docker compose logs api-dev | grep -i "postgres\|database\|error"

# 3. 手动初始化
docker compose exec api python scripts/init_database.py
```

### 问题 2：`departments.is_active` 为 NULL

**症状**：创建部门时报错 `null value in column "is_active"`

**解决**：
```bash
# 运行初始化脚本，添加默认值约束
docker compose exec api python scripts/init_database.py

# 或手动添加
docker compose exec postgres psql -U postgres yuxi_know -c "
ALTER TABLE departments ALTER COLUMN is_active SET DEFAULT 1;
ALTER TABLE departments ALTER COLUMN is_active SET NOT NULL;
"
```

### 问题 3：连接数据库失败

**症状**：`Failed to initialize PostgreSQL manager`

**解决**：
```bash
# 1. 检查 PostgreSQL 是否运行
docker compose ps postgres

# 2. 检查连接字符串
echo $POSTGRES_URL

# 3. 测试连接
docker compose exec postgres psql -U postgres -d yuxi_know -c "SELECT 1;"

# 4. 重启服务
docker compose restart api-dev
```

## 📚 相关文档

- [批量创建部门和用户](../scripts/README_batch_create.md)
- [数据库模型定义](../src/storage/db/models.py)
- [PostgreSQL 管理器](../src/storage/postgres/manager.py)

## ✅ 验证清单

部署完成后，检查以下项目：

- [ ] Docker 容器全部运行（`docker compose ps`）
- [ ] PostgreSQL 可连接（`docker compose exec postgres psql -U postgres`）
- [ ] 数据库表已创建（查看日志或运行验证脚本）
- [ ] 超级管理员可以登录
- [ ] 可以创建部门
- [ ] 可以创建用户并分配部门
- [ ] 可以创建知识库
- [ ] 文件检索功能正常

## 🎉 总结

**是的，项目支持自动初始化数据库！**

只需要：
1. 配置环境变量
2. 运行 `docker compose up -d`
3. 系统自动创建所有表结构

无需手动创建表或运行迁移脚本（除非从旧版本升级）。
