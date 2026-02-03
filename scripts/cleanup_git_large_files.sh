#!/bin/bash
# 清理 git 仓库中的大文件和测试数据
# 注意：这个脚本会修改 git 历史，仅在必要时使用

set -e

echo "=========================================="
echo "Git 仓库大文件清理脚本"
echo "=========================================="
echo ""
echo "⚠️  警告：此操作会修改 git 历史！"
echo "⚠️  建议在执行前备份仓库！"
echo ""
read -p "是否继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "📋 Step 1: 从当前索引中移除大文件..."
git rm -r --cached test/data/文件汇总/ 2>/dev/null || true
git rm --cached test/data/*.txt 2>/dev/null || true
git rm --cached test/data/*.jsonl 2>/dev/null || true

echo ""
echo "📋 Step 2: 添加回小的示例文件..."
git add test/data/lightrag_kb_test_tiny.txt 2>/dev/null || true
git add test/data/A_Dream_of_Red_Mansions_tiny.jsonl 2>/dev/null || true
git add test/data/complex_graph_test.jsonl 2>/dev/null || true

echo ""
echo "✅ 完成！已从索引中移除大文件"
echo ""
echo "📝 下一步操作："
echo "1. 提交这些变更："
echo "   git commit -m 'chore: remove large test data files from git tracking'"
echo ""
echo "2. (可选) 如果要清理历史记录中的大文件，使用 git-filter-repo："
echo "   pip install git-filter-repo"
echo "   git filter-repo --path test/data/文件汇总 --invert-paths"
echo "   git filter-repo --path test/data/*.txt --invert-paths"
echo ""
echo "   注意：这会重写整个 git 历史！"
echo ""
echo "3. 强制推送（如果清理了历史）："
echo "   git push --force"
echo ""
