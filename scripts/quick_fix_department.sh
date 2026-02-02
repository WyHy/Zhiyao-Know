#!/bin/bash
# 快速修复部门创建错误

echo "🔧 开始修复部门创建错误..."
echo ""

# 1. 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录下运行此脚本"
    exit 1
fi

# 2. 重启 API 服务（应用代码修复）
echo "📦 重启 API 服务..."
docker compose restart api
sleep 3

# 3. 运行数据库迁移
echo ""
echo "🗄️  运行数据库迁移..."
docker compose exec -T api python scripts/fix_department_is_active.py

# 4. 验证修复
echo ""
echo "✅ 验证修复..."
docker compose exec -T api python -c "
import asyncio
from src.services.department_service import DepartmentService

async def test():
    try:
        service = DepartmentService()
        dept = await service.create_department(
            name='测试部门_$(date +%s)',
            description='验证修复是否成功'
        )
        print('✅ 部门创建成功！修复生效！')
        print(f'   部门ID: {dept[\"id\"]}')
        print(f'   部门名: {dept[\"name\"]}')
        print(f'   is_active: {dept[\"is_active\"]}')
        
        # 删除测试部门
        await service.delete_department(dept['id'])
        print('   （测试部门已删除）')
        return True
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        return False

result = asyncio.run(test())
exit(0 if result else 1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=" 60
    echo "🎉 修复完成！现在可以运行批量创建脚本了："
    echo "   docker compose exec api python scripts/batch_create_departments_users.py"
    echo "=" 60
else
    echo ""
    echo "❌ 修复验证失败，请检查日志"
    exit 1
fi
