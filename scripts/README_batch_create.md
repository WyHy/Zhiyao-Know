# 批量创建部门和用户 - 使用说明

## 📝 脚本说明

`scripts/batch_create_departments_users.py` 是一个批量创建测试数据的脚本，用于快速搭建演示环境。

## 🎯 创建的数据

### 部门结构（4个顶层部门，共27个部门）

```
集团总部
├─ 总经理办公室
├─ 人力资源部
│  ├─ 招聘组
│  ├─ 培训组
│  └─ 薪酬组
└─ 财务部
   ├─ 会计组
   ├─ 出纳组
   └─ 税务组

技术中心
├─ 研发部
│  ├─ 前端组
│  ├─ 后端组
│  └─ 算法组
├─ 测试部
│  ├─ 功能测试组
│  └─ 性能测试组
└─ 运维部

市场营销中心
├─ 市场部
│  ├─ 品牌组
│  └─ 推广组
└─ 销售部
   ├─ 华北区
   ├─ 华东区
   └─ 华南区

产品中心
├─ 产品规划部
├─ UI/UX设计部
└─ 产品运营部
```

### 用户（23个用户）

| 姓名 | 登录ID    | 密码     | 角色  | 所属部门             |
| ---- | --------- | -------- | ----- | -------------------- |
| 张伟 | zhangwei  | Pass1234 | admin | 总经理办公室         |
| 李娜 | lina      | Pass1234 | user  | 人力资源部, 招聘组   |
| 王强 | wangqiang | Pass1234 | user  | 人力资源部, 培训组   |
| 刘洋 | liuyang   | Pass1234 | user  | 财务部, 会计组       |
| 陈静 | chenjing  | Pass1234 | user  | 财务部, 出纳组       |
| 赵敏 | zhaomin   | Pass1234 | admin | 技术中心, 研发部     |
| 孙浩 | sunhao    | Pass1234 | user  | 研发部, 前端组       |
| 周婷 | zhouting  | Pass1234 | user  | 研发部, 前端组       |
| 吴磊 | wulei     | Pass1234 | user  | 研发部, 后端组       |
| 郑芳 | zhengfang | Pass1234 | user  | 研发部, 后端组       |
| 钱勇 | qianyong  | Pass1234 | user  | 研发部, 算法组       |
| 冯丽 | fengli    | Pass1234 | user  | 测试部, 功能测试组   |
| 许杰 | xujie     | Pass1234 | user  | 测试部, 性能测试组   |
| 何涛 | hetao     | Pass1234 | user  | 运维部               |
| 曹雪 | caoxue    | Pass1234 | admin | 市场营销中心         |
| 夏明 | xiaming   | Pass1234 | user  | 市场部, 品牌组       |
| 姜伟 | jiangwei  | Pass1234 | user  | 市场部, 推广组       |
| 尹静 | yinjing   | Pass1234 | user  | 销售部, 华北区       |
| 秦浩 | qinhao    | Pass1234 | user  | 销售部, 华东区       |
| 苏婷 | suting    | Pass1234 | user  | 销售部, 华南区       |
| 袁凯 | yuankai   | Pass1234 | user  | 产品中心, 产品规划部 |
| 潘丽 | panli     | Pass1234 | user  | UI/UX设计部          |
| 汤勇 | tangyong  | Pass1234 | user  | 产品运营部           |

## 🚀 使用方法

### 方式一：在 Docker 容器中运行

```bash
cd /Users/wangying/developments/tools/Yuxi-Know
docker compose exec api python scripts/batch_create_departments_users.py
```

### 方式二：直接运行（需要本地 Python 环境）

```bash
cd /Users/wangying/developments/tools/Yuxi-Know
python scripts/batch_create_departments_users.py
```

## ⚠️ 注意事项

1. **重复运行**：脚本不会删除已存在的数据，重复运行会报"名称重复"错误，但不影响新用户创建
2. **管理员账号**：需要使用管理员账号（admin / 1234hbnj）
3. **API 服务**：确保 API 服务正在运行（http://localhost:5050）
4. **数据清理**：如需清空数据重新创建，请手动删除数据库或使用数据库管理工具

## 🧪 测试账号

创建完成后，可以使用以下账号登录测试：

### 超级管理员
- 用户名：`admin`
- 密码：`1234hbnj`

### 部门管理员
- 张伟（总经理办）：`zhangwei` / `Pass1234`
- 赵敏（技术中心）：`zhaomin` / `Pass1234`
- 曹雪（市场营销）：`caoxue` / `Pass1234`

### 普通用户
- 孙浩（前端开发）：`sunhao` / `Pass1234`
- 吴磊（后端开发）：`wulei` / `Pass1234`
- 夏明（品牌推广）：`xiaming` / `Pass1234`

## 📊 验证创建结果

### 查看部门树

```bash
curl http://localhost:5050/api/departments/tree | jq
```

### 查看用户部门关系

```bash
# 需要先登录获取 token
TOKEN="YOUR_TOKEN_HERE"

# 查看指定用户的部门
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5050/api/departments/10/departments | jq
```

### 访问 API 文档

在浏览器打开：http://localhost:5050/docs

## 🔧 自定义数据

如需自定义部门和用户数据，请编辑脚本中的以下变量：

- `DEPARTMENTS_DATA`：部门结构（树形）
- `USERS_DATA`：用户列表及其所属部门

## 📝 脚本特性

✅ 自动创建多层级部门树
✅ 自动为用户分配部门
✅ 支持用户属于多个部门
✅ 自动设置主部门（第一个部门）
✅ 详细的执行日志
✅ 错误提示和统计信息

## 🎉 创建完成后

系统将包含：
- **27个部门**（4个顶层，多个子部门）
- **23个用户**（含3个部门管理员）
- **用户-部门关联关系**（支持多部门）

现在可以：
1. 使用不同账号登录测试权限
2. 为知识库添加部门标签
3. 测试多部门文件检索功能
4. 配置知识库访问控制

---

**祝使用愉快！** 🚀
