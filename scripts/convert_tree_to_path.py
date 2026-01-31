"""
将树形关系的知识图谱 JSONL 文件转换为路径格式

使用方法：
    python scripts/convert_tree_to_path.py input.jsonl output.jsonl
    
或者在代码中调用：
    from scripts.convert_tree_to_path import convert_to_path_format
    convert_to_path_format('input.jsonl', 'output.jsonl')
"""

import json
import sys
from pathlib import Path


def convert_to_path_format(input_file, output_file):
    """
    将树形关系转换为路径格式
    
    Args:
        input_file: 输入的 JSONL 文件路径
        output_file: 输出的 JSONL 文件路径
        
    输入格式（h 是子节点，t 是父节点）：
        {"h": "子节点", "t": "父节点", "r": "关系"}
        
    输出格式：
        {"h": "根/父节点", "t": "根/父节点/子节点", "r": "关系"}
    """
    print(f"开始转换: {input_file} -> {output_file}")
    
    # 第一遍：读取所有数据并构建父子关系
    parent_map = {}  # child -> parent (注意：h 是子节点，t 是父节点)
    lines = []
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    lines.append(data)
                    
                    # 记录父子关系（h 是子节点，t 是父节点）
                    h = data.get("h")  # 子节点
                    t = data.get("t")  # 父节点
                    r = data.get("r")
                    
                    if not h or not t or not r:
                        print(f"  警告：第 {line_num} 行数据不完整，跳过: {line}")
                        continue
                    
                    parent_map[h] = t  # child -> parent
                    
                except json.JSONDecodeError as e:
                    print(f"  错误：第 {line_num} 行 JSON 解析失败: {e}")
                    continue
        
        print(f"✓ 成功读取 {len(lines)} 条记录")
        
    except FileNotFoundError:
        print(f"✗ 错误：找不到文件 {input_file}")
        return False
    except Exception as e:
        print(f"✗ 读取文件时发生错误: {e}")
        return False
    
    # 递归构建完整路径
    def get_path(node, visited=None):
        """
        递归构建节点的完整路径
        
        Args:
            node: 节点名称
            visited: 已访问的节点集合（用于检测循环引用）
            
        Returns:
            完整路径字符串
        """
        if visited is None:
            visited = set()
        
        # 检测循环引用
        if node in visited:
            print(f"  警告：检测到循环引用，节点: {node}")
            return node
        
        visited.add(node)
        
        # 如果没有父节点，说明是根节点
        if node not in parent_map:
            return node
        
        # 递归构建父节点路径
        parent_path = get_path(parent_map[node], visited.copy())
        return f"{parent_path}/{node}"
    
    # 第二遍：生成带路径的新数据
    converted_lines = []
    for i, data in enumerate(lines, 1):
        try:
            h = data.get("h")  # 子节点
            t = data.get("t")  # 父节点
            r = data.get("r")
            
            if not h or not t or not r:
                continue
            
            # 生成路径（保持原有的父子关系）
            new_data = {
                "h": get_path(h),  # 子节点的完整路径
                "t": get_path(t),  # 父节点的完整路径
                "r": r,
            }
            converted_lines.append(new_data)
            
        except Exception as e:
            print(f"  错误：第 {i} 条记录转换失败: {e}")
            continue
    
    # 写入输出文件
    try:
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for data in converted_lines:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        print(f"✓ 转换完成！已生成 {len(converted_lines)} 条记录")
        
        # 显示示例输出
        print("\n示例输出（前 5 条）：")
        for i, data in enumerate(converted_lines[:5], 1):
            print(f"  {i}. h: {data['h']}")
            print(f"     t: {data['t']}")
            print(f"     r: {data['r']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ 写入文件时发生错误: {e}")
        return False


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("使用方法: python convert_tree_to_path.py <输入文件> <输出文件>")
        print("\n示例:")
        print("  python scripts/convert_tree_to_path.py test/data/file_structure_kg.jsonl test/data/file_structure_kg_path.jsonl")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = convert_to_path_format(input_file, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
