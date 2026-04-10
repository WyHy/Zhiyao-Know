"""
测试文件检索接口 - 验证普通用户能否正常获取文件列表

使用说明：
1. 确保 API 服务正在运行
2. 测试多个用户的文件检索权限
3. 对比本地和生产环境的差异

运行：docker compose exec api python scripts/test_file_search.py
或指定环境：docker compose exec api python scripts/test_file_search.py --env production
"""

import asyncio
import os
import sys
from pathlib import Path
import argparse
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


class FileSearchTester:
    """文件检索测试器"""
    
    def __init__(self, base_url: str = "http://localhost:5050/api"):
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30)
        self.token = None
        self.current_user = None
    
    async def login(self, username: str, password: str):
        """登录并获取 token"""
        print(f"\n🔐 登录用户: {username}")
        
        try:
            response = await self.client.post(
                "/auth/token",
                data={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                
                # 获取用户信息
                user_response = await self.client.get("/auth/me")
                if user_response.status_code == 200:
                    self.current_user = user_response.json()
                    print(f"   ✅ 登录成功")
                    print(f"   用户ID: {self.current_user.get('user_id')}")
                    print(f"   用户名: {self.current_user.get('username')}")
                    print(f"   角色: {self.current_user.get('role')}")
                    print(f"   部门: {self.current_user.get('department_name', '无')}")
                    return True
            else:
                print(f"   ❌ 登录失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 登录异常: {e}")
            return False
    
    async def get_departments(self):
        """获取部门列表"""
        print(f"\n📂 获取部门列表")
        
        try:
            response = await self.client.get("/departments")
            
            if response.status_code == 200:
                data = response.json()
                departments = data.get("data", [])
                print(f"   ✅ 成功获取部门树，顶层部门: {len(departments)} 个")
                return departments
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return []
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return []
    
    async def get_knowledge_bases(self):
        """获取知识库列表"""
        print(f"\n📚 获取知识库列表")
        
        try:
            response = await self.client.get("/knowledge/databases")
            
            if response.status_code == 200:
                data = response.json()
                databases = data.get("databases", [])
                print(f"   ✅ 可访问的知识库: {len(databases)} 个")
                
                if databases:
                    print(f"\n   前5个知识库:")
                    for db in databases[:5]:
                        print(f"   - {db.get('name', 'N/A')} (ID: {db.get('db_id', 'N/A')[:20]}...)")
                
                return databases
            else:
                print(f"   ❌ 获取失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return []
                
        except Exception as e:
            print(f"   ❌ 获取异常: {e}")
            return []
    
    async def search_files(self, params: dict):
        """搜索文件"""
        print(f"\n🔍 搜索文件")
        print(f"   参数: {json.dumps(params, ensure_ascii=False, indent=6)}")
        
        try:
            response = await self.client.post("/files/search", json=params)
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("data", {})
                total = result.get("total", 0)
                files = result.get("files", [])
                dept_stats = result.get("department_stats", {})
                
                print(f"   ✅ 搜索成功")
                print(f"   总文件数: {total}")
                print(f"   当前页文件数: {len(files)}")
                print(f"   部门统计: {dept_stats}")
                
                if files:
                    print(f"\n   前3个文件:")
                    for i, f in enumerate(files[:3], 1):
                        print(f"   {i}. {f.get('filename', 'N/A')}")
                        print(f"      类型: {f.get('file_type', 'N/A')}")
                        print(f"      大小: {f.get('file_size', 0)} bytes")
                        print(f"      知识库: {f.get('kb_name', 'N/A')}")
                else:
                    print(f"   ⚠️  未找到任何文件")
                
                return result
            else:
                print(f"   ❌ 搜索失败: {response.status_code}")
                print(f"   响应: {response.text[:500]}")
                return None
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")
            return None
    
    async def test_user(self, username: str, password: str):
        """测试单个用户的文件检索"""
        print(f"\n{'='*60}")
        print(f"  测试用户: {username}")
        print(f"{'='*60}")
        
        # 登录
        if not await self.login(username, password):
            return False
        
        # 获取部门列表
        departments = await self.get_departments()
        
        # 获取知识库列表
        kbs = await self.get_knowledge_bases()
        
        # 测试场景1: 空条件搜索（应该返回用户可访问的所有文件）
        print(f"\n📋 测试场景1: 空条件搜索")
        await self.search_files({
            "keyword": "",
            "department_ids": [],
            "include_subdepts": True,
            "file_types": [],
            "sort_by": "created_at",
            "order": "desc",
            "page": 1,
            "page_size": 20
        })
        
        # 测试场景2: 指定部门搜索（如果有部门）
        if departments:
            first_dept_id = self._get_first_dept_id(departments)
            if first_dept_id:
                print(f"\n📋 测试场景2: 指定部门搜索 (部门ID: {first_dept_id})")
                await self.search_files({
                    "keyword": "",
                    "department_ids": [first_dept_id],
                    "include_subdepts": True,
                    "file_types": [],
                    "sort_by": "created_at",
                    "order": "desc",
                    "page": 1,
                    "page_size": 20
                })
        
        # 测试场景3: 关键词搜索
        print(f"\n📋 测试场景3: 关键词搜索")
        await self.search_files({
            "keyword": "测试",
            "department_ids": [],
            "include_subdepts": True,
            "file_types": [],
            "sort_by": "created_at",
            "order": "desc",
            "page": 1,
            "page_size": 20
        })
        
        return True
    
    def _get_first_dept_id(self, departments):
        """获取第一个部门ID（递归）"""
        if not departments:
            return None
        
        for dept in departments:
            if dept.get("id"):
                return dept["id"]
            if dept.get("children"):
                child_id = self._get_first_dept_id(dept["children"])
                if child_id:
                    return child_id
        
        return None
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试文件检索接口")
    parser.add_argument("--env", choices=["local", "production"], default="local", help="测试环境")
    parser.add_argument("--user", help="指定测试用户（格式: username:password）")
    args = parser.parse_args()
    
    default_password = (
        os.getenv("YUXI_TEST_PASSWORD")
        or os.getenv("YUXI_SUPER_ADMIN_PASSWORD")
        or "sgcc@0716!Jz"
    )

    # 根据环境选择配置
    if args.env == "production":
        base_url = "http://47.122.119.66:5050/api"
        test_users = [
            (os.getenv("YUXI_TEST_PROD_USERNAME", "zhangwei"), default_password),  # 生产环境账号
        ]
    else:
        base_url = "http://localhost:5050/api"
        test_users = [
            (os.getenv("YUXI_TEST_USER1_USERNAME", "lina"), default_password),       # 普通用户
            (os.getenv("YUXI_TEST_USER2_USERNAME", "wangqiang"), default_password),  # 普通用户
            (os.getenv("YUXI_TEST_ADMIN_USERNAME", "zhangwei"), default_password),   # 管理员
        ]
    
    # 如果指定了用户，只测试该用户
    if args.user:
        username, password = args.user.split(":", 1)
        test_users = [(username, password)]
    
    print("\n" + "="*60)
    print(f"  文件检索接口测试 - {args.env.upper()} 环境")
    print("="*60)
    
    # 测试每个用户
    for username, password in test_users:
        tester = FileSearchTester(base_url)
        try:
            await tester.test_user(username, password)
        except Exception as e:
            print(f"\n❌ 测试用户 {username} 时出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await tester.close()
        
        # 用户之间稍作延迟
        if len(test_users) > 1:
            await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print("  测试完成")
    print("="*60 + "\n")
    
    print("💡 建议:")
    print("   - 如果普通用户返回空，检查 kb_department_relations 表")
    print("   - 如果管理员也返回空，检查知识库数据是否存在")
    print("   - 对比本地和生产环境的输出差异")
    print()


if __name__ == "__main__":
    asyncio.run(main())
