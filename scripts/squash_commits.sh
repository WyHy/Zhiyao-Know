#!/bin/bash
# 合并最近的 "update" 提交
# 这个脚本会将 b323b5a 之后的所有提交合并成一个有意义的提交

set -e

cd /Users/wangying/developments/tools/Yuxi-Know

echo "=========================================="
echo "  合并最近的 Git 提交"
echo "=========================================="
echo ""
echo "当前提交历史："
git log --oneline -15
echo ""
echo "将要合并的提交："
git log --oneline b323b5a..HEAD
echo ""
read -p "确认合并这些提交？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

# 获取要保留的基准提交
BASE_COMMIT="b323b5a"

# 使用 reset --soft 重置到基准提交（保留所有更改）
echo ""
echo "🔄 重置到基准提交 $BASE_COMMIT..."
git reset --soft $BASE_COMMIT

# 查看暂存的更改
echo ""
echo "📋 已暂存的更改："
git diff --cached --stat | head -20

# 创建新的提交
echo ""
echo "💾 创建合并后的提交..."
git commit -m "feat: 完善部门管理和文件检索功能

主要更新：
- 实现部门树形结构管理（CRUD）
- 实现用户-部门多对多关联
- 实现知识库-部门关联和访问控制
- 实现多部门文件检索功能
- 完善前端部门管理和文件检索页面
- 优化 .gitignore，移除大型测试数据
- 添加数据库自动初始化支持
- 添加部署文档和清理脚本
- 修复部门选择和显示问题
- 支持层级部门查询（包含子部门）"

echo ""
echo "✅ 提交合并完成！"
echo ""
echo "📊 新的提交历史："
git log --oneline -10
echo ""
echo "⚠️ 下一步："
echo "如果需要推送到远程（会重写历史）："
echo "   git push --force-with-lease origin main"
echo ""
echo "如果想撤销合并："
echo "   git reset --hard ORIG_HEAD"
echo ""
