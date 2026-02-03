# 测试数据目录

本目录包含用于测试的数据文件。

## ⚠️ 重要说明

**大文件和敏感数据不应提交到 git 仓库！**

本目录中的大多数文件已被 `.gitignore` 忽略，只有少量示例文件被追踪。

## 📂 目录结构

```
test/data/
├── 文件汇总/           # 企业文档测试数据（已忽略，1.4GB+）
├── ocr_test/           # OCR 测试图片
├── *.txt               # 文本测试数据（已忽略）
├── *.jsonl             # JSONL 测试数据（已忽略）
├── *.csv               # CSV 测试数据
├── *.docx              # Word 测试文档
├── *.xlsx              # Excel 测试表格
└── *.pptx              # PPT 测试演示
```

## ✅ 被 Git 追踪的文件

只有以下小文件被追踪：

- `lightrag_kb_test_tiny.txt` (69B) - 最小测试样本
- `A_Dream_of_Red_Mansions_tiny.jsonl` (241B) - 小样本数据
- `complex_graph_test.jsonl` (911B) - 复杂图谱测试
- `test_csv_file.csv` - CSV 格式示例
- `测试文档.docx` - Word 文档示例
- `测试表格.xlsx` - Excel 表格示例
- `测试演示.pptx` - PPT 演示示例
- `ocr_test/PixPin_2025-06-19_23-42-17.png` - OCR 测试图

## 🚫 被 Git 忽略的文件

以下文件类型/目录已在 `.gitignore` 中配置忽略：

- `test/data/文件汇总/` - 1.4GB 企业文档
- `test/data/*.txt` - 大文本文件（除了 tiny 示例）
- `test/data/*.jsonl` - 大 JSONL 文件（除了示例）

## 📥 如何获取完整测试数据

完整的测试数据应该：

1. **从内部存储/网盘下载**（如果是企业内部数据）
2. **或者使用脚本生成**（如果是可生成的测试数据）

示例：

```bash
# 方案1: 从内部网盘下载
# wget http://internal-storage/test-data.zip
# unzip test-data.zip -d test/data/

# 方案2: 使用脚本生成
# python scripts/generate_test_data.py
```

## 🧹 清理已追踪的大文件

如果不小心将大文件添加到了 git，运行清理脚本：

```bash
# 从 git 索引中移除大文件
bash scripts/cleanup_git_large_files.sh
```

## 📝 最佳实践

1. **永远不要将敏感数据提交到 git**
2. **大于 1MB 的文件应考虑是否需要追踪**
3. **测试数据优先使用小样本**
4. **完整数据集应使用外部存储（MinIO/S3/网盘）**
5. **提交前检查 `git status` 和 `.gitignore`**

## 🔍 检查仓库大小

```bash
# 查看 git 仓库大小
du -sh .git

# 查看哪些文件占用空间最大
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort --numeric-sort --key=2 | \
  tail -20
```
