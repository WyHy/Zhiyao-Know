"""
批量创建部门和用户的测试脚本

使用说明：
1. 确保 API 服务正在运行（http://localhost:5050）
2. 使用管理员账号运行此脚本
3. 脚本会自动创建部门树和用户，并分配关系

运行：docker compose exec api python scripts/batch_create_departments_users.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.utils import logger

# API 配置
API_BASE_URL = "http://47.122.119.66:5050/api"
ADMIN_USERNAME = os.getenv("YUXI_SUPER_ADMIN_NAME", "whzykj")
ADMIN_PASSWORD = (
    os.getenv("YUXI_SUPER_ADMIN_PASSWORD")
    or os.getenv("YUXI_TEST_PASSWORD")
    or "sgcc@0716!Jz"
)
USER_DEFAULT_PASSWORD = (
    os.getenv("YUXI_TEST_PASSWORD")
    or os.getenv("YUXI_SUPER_ADMIN_PASSWORD")
    or "sgcc@0716!Jz"
)


# 部门数据结构（树形）
DEPARTMENTS_DATA = [
    {
        "name": "集团总部",
        "description": "集团公司总部",
        "sort_order": 1,
        "children": [
            {
                "name": "总经理办公室",
                "description": "负责集团整体战略规划和决策",
                "sort_order": 1,
            },
            {
                "name": "人力资源部",
                "description": "负责人力资源管理和招聘",
                "sort_order": 2,
                "children": [
                    {"name": "招聘组", "description": "负责人才招聘", "sort_order": 1},
                    {"name": "培训组", "description": "负责员工培训", "sort_order": 2},
                    {"name": "薪酬组", "description": "负责薪酬福利管理", "sort_order": 3},
                ]
            },
            {
                "name": "财务部",
                "description": "负责财务管理和预算控制",
                "sort_order": 3,
                "children": [
                    {"name": "会计组", "description": "负责会计核算", "sort_order": 1},
                    {"name": "出纳组", "description": "负责资金管理", "sort_order": 2},
                    {"name": "税务组", "description": "负责税务筹划", "sort_order": 3},
                ]
            },
        ]
    },
    {
        "name": "技术中心",
        "description": "负责技术研发和创新",
        "sort_order": 2,
        "children": [
            {
                "name": "研发部",
                "description": "产品研发部门",
                "sort_order": 1,
                "children": [
                    {"name": "前端组", "description": "前端开发团队", "sort_order": 1},
                    {"name": "后端组", "description": "后端开发团队", "sort_order": 2},
                    {"name": "算法组", "description": "AI算法研发", "sort_order": 3},
                ]
            },
            {
                "name": "测试部",
                "description": "产品测试与质量保证",
                "sort_order": 2,
                "children": [
                    {"name": "功能测试组", "description": "功能测试", "sort_order": 1},
                    {"name": "性能测试组", "description": "性能测试", "sort_order": 2},
                ]
            },
            {
                "name": "运维部",
                "description": "系统运维和支持",
                "sort_order": 3,
            },
        ]
    },
    {
        "name": "市场营销中心",
        "description": "负责市场推广和销售",
        "sort_order": 3,
        "children": [
            {
                "name": "市场部",
                "description": "市场调研和品牌推广",
                "sort_order": 1,
                "children": [
                    {"name": "品牌组", "description": "品牌建设", "sort_order": 1},
                    {"name": "推广组", "description": "市场推广", "sort_order": 2},
                ]
            },
            {
                "name": "销售部",
                "description": "产品销售和客户服务",
                "sort_order": 2,
                "children": [
                    {"name": "华北区", "description": "华北区域销售", "sort_order": 1},
                    {"name": "华东区", "description": "华东区域销售", "sort_order": 2},
                    {"name": "华南区", "description": "华南区域销售", "sort_order": 3},
                ]
            },
        ]
    },
    {
        "name": "产品中心",
        "description": "产品规划和设计",
        "sort_order": 4,
        "children": [
            {"name": "产品规划部", "description": "产品战略规划", "sort_order": 1},
            {"name": "UI/UX设计部", "description": "用户体验设计", "sort_order": 2},
            {"name": "产品运营部", "description": "产品运营和数据分析", "sort_order": 3},
        ]
    },
]


# 用户数据（将分配到不同部门）
USERS_DATA = [
    # 总部
    {"username": "张伟", "user_id": "zhangwei", "password": "", "role": "admin", "phone": "13800000001", "departments": ["总经理办公室"]},
    {"username": "李娜", "user_id": "lina", "password": "", "role": "user", "phone": "13800000002", "departments": ["人力资源部", "招聘组"]},
    {"username": "王强", "user_id": "wangqiang", "password": "", "role": "user", "phone": "13800000003", "departments": ["人力资源部", "培训组"]},
    {"username": "刘洋", "user_id": "liuyang", "password": "", "role": "user", "phone": "13800000004", "departments": ["财务部", "会计组"]},
    {"username": "陈静", "user_id": "chenjing", "password": "", "role": "user", "phone": "13800000005", "departments": ["财务部", "出纳组"]},
    
    # 技术中心
    {"username": "赵敏", "user_id": "zhaomin", "password": "", "role": "admin", "phone": "13800000006", "departments": ["技术中心", "研发部"]},
    {"username": "孙浩", "user_id": "sunhao", "password": "", "role": "user", "phone": "13800000007", "departments": ["研发部", "前端组"]},
    {"username": "周婷", "user_id": "zhouting", "password": "", "role": "user", "phone": "13800000008", "departments": ["研发部", "前端组"]},
    {"username": "吴磊", "user_id": "wulei", "password": "", "role": "user", "phone": "13800000009", "departments": ["研发部", "后端组"]},
    {"username": "郑芳", "user_id": "zhengfang", "password": "", "role": "user", "phone": "13800000010", "departments": ["研发部", "后端组"]},
    {"username": "钱勇", "user_id": "qianyong", "password": "", "role": "user", "phone": "13800000011", "departments": ["研发部", "算法组"]},
    {"username": "冯丽", "user_id": "fengli", "password": "", "role": "user", "phone": "13800000012", "departments": ["测试部", "功能测试组"]},
    {"username": "许杰", "user_id": "xujie", "password": "", "role": "user", "phone": "13800000013", "departments": ["测试部", "性能测试组"]},
    {"username": "何涛", "user_id": "hetao", "password": "", "role": "user", "phone": "13800000014", "departments": ["运维部"]},
    
    # 市场营销中心
    {"username": "曹雪", "user_id": "caoxue", "password": "", "role": "admin", "phone": "13800000015", "departments": ["市场营销中心"]},
    {"username": "夏明", "user_id": "xiaming", "password": "", "role": "user", "phone": "13800000016", "departments": ["市场部", "品牌组"]},
    {"username": "姜伟", "user_id": "jiangwei", "password": "", "role": "user", "phone": "13800000017", "departments": ["市场部", "推广组"]},
    {"username": "尹静", "user_id": "yinjing", "password": "", "role": "user", "phone": "13800000018", "departments": ["销售部", "华北区"]},
    {"username": "秦浩", "user_id": "qinhao", "password": "", "role": "user", "phone": "13800000019", "departments": ["销售部", "华东区"]},
    {"username": "苏婷", "user_id": "suting", "password": "", "role": "user", "phone": "13800000020", "departments": ["销售部", "华南区"]},
    
    # 产品中心
    {"username": "袁凯", "user_id": "yuankai", "password": "", "role": "user", "phone": "13800000021", "departments": ["产品中心", "产品规划部"]},
    {"username": "潘丽", "user_id": "panli", "password": "", "role": "user", "phone": "13800000022", "departments": ["UI/UX设计部"]},
    {"username": "汤勇", "user_id": "tangyong", "password": "", "role": "user", "phone": "13800000023", "departments": ["产品运营部"]},
]

for user in USERS_DATA:
    user["password"] = USER_DEFAULT_PASSWORD


class BatchCreator:
    """批量创建助手"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)
        self.token = None
        self.dept_id_map = {}  # 部门名称 -> ID 映射
    
    async def login(self):
        """管理员登录"""
        print(f"🔐 正在登录管理员账号: {ADMIN_USERNAME}")
        
        response = await self.client.post(
            "/auth/token",
            data={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"登录失败: {response.text}")
        
        data = response.json()
        self.token = data["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        
        print(f"✅ 登录成功! Token: {self.token[:20]}...\n")
    
    async def load_existing_departments(self):
        """加载已存在的部门ID映射"""
        print("📋 加载现有部门...")
        
        response = await self.client.get("/departments")
        
        if response.status_code == 200:
            result = response.json()
            departments = result.get("data", [])
            
            # 递归处理部门树
            def process_dept(dept):
                self.dept_id_map[dept["name"]] = dept["id"]
                for child in dept.get("children", []):
                    process_dept(child)
            
            for dept in departments:
                process_dept(dept)
            
            print(f"✅ 加载了 {len(self.dept_id_map)} 个部门\n")
        else:
            print(f"⚠️  加载部门失败: {response.text}\n")
    
    async def create_department_tree(self, dept_data, parent_id=None, level=1):
        """递归创建部门树"""
        indent = "  " * (level - 1)
        
        # 创建当前部门
        create_data = {
            "name": dept_data["name"],
            "description": dept_data.get("description"),
            "parent_id": parent_id,
            "sort_order": dept_data.get("sort_order", 0),
        }
        
        print(f"{indent}📁 创建部门: {dept_data['name']}")
        
        response = await self.client.post("/departments", json=create_data)
        
        if response.status_code not in [200, 201]:
            print(f"{indent}❌ 创建失败: {response.text}")
            return None
        
        result = response.json()
        dept_id = result["data"]["id"]
        self.dept_id_map[dept_data["name"]] = dept_id
        
        print(f"{indent}✅ 创建成功! ID: {dept_id}")
        
        # 递归创建子部门
        if "children" in dept_data:
            for child in dept_data["children"]:
                await self.create_department_tree(child, dept_id, level + 1)
        
        return dept_id
    
    async def create_all_departments(self):
        """创建所有部门"""
        print("=" * 60)
        print("📋 开始创建部门树\n")
        
        for dept in DEPARTMENTS_DATA:
            await self.create_department_tree(dept)
            print()  # 空行分隔
        
        print(f"✅ 部门创建完成! 共创建 {len(self.dept_id_map)} 个部门\n")
    
    async def create_user(self, user_data):
        """创建单个用户或为已存在用户分配部门"""
        # 创建用户
        create_data = {
            "username": user_data["username"],
            "user_id": user_data["user_id"],
            "password": user_data["password"],
            "role": user_data.get("role", "user"),
            "phone_number": user_data.get("phone"),
        }
        
        print(f"👤 处理用户: {user_data['username']} ({user_data['user_id']})")
        
        response = await self.client.post("/auth/users", json=create_data)
        user_id = None
        user_exists = False
        
        if response.status_code in [200, 201]:
            result = response.json()
            user_id = result["id"]
            print(f"   ✅ 用户创建成功! ID: {user_id}")
        elif "已存在" in response.text or "exists" in response.text.lower():
            # 用户已存在，获取用户ID
            user_exists = True
            print(f"   ℹ️  用户已存在，正在获取用户信息...")
            
            # 获取用户列表查找该用户
            list_response = await self.client.get("/auth/users")
            if list_response.status_code == 200:
                users = list_response.json()
                for user in users:
                    if user.get("user_id") == user_data["user_id"]:
                        user_id = user["id"]
                        print(f"   ✅ 找到用户! ID: {user_id}")
                        break
            
            if not user_id:
                print(f"   ❌ 无法获取用户ID，跳过部门分配")
                return None, False
        else:
            print(f"   ❌ 创建失败: {response.text}")
            return None, False
        
        # 分配部门
        dept_names = user_data.get("departments", [])
        if dept_names:
            dept_ids = [self.dept_id_map[name] for name in dept_names if name in self.dept_id_map]
            
            if dept_ids:
                primary_id = dept_ids[0]  # 第一个为主部门
                
                assign_data = {
                    "department_ids": dept_ids,
                    "primary_id": primary_id,
                }
                
                dept_names_str = ", ".join(dept_names)
                action = "更新" if user_exists else "分配"
                print(f"   📋 {action}部门: {dept_names_str}")
                
                response = await self.client.post(
                    f"/departments/{user_id}/departments",
                    json=assign_data
                )
                
                if response.status_code == 200:
                    print(f"   ✅ {action}部门成功")
                else:
                    print(f"   ⚠️  {action}部门失败: {response.text}")
            else:
                print(f"   ⚠️  未找到部门映射: {dept_names}")
        else:
            print(f"   ℹ️  无需分配部门")
        
        return user_id, user_exists
    
    async def create_all_users(self):
        """创建所有用户"""
        print("=" * 60)
        print("👥 开始创建/更新用户\n")
        
        created_count = 0
        updated_count = 0
        failed_count = 0
        
        for user_data in USERS_DATA:
            result = await self.create_user(user_data)
            if result[0]:  # user_id 存在
                if result[1]:  # user_exists
                    updated_count += 1
                else:
                    created_count += 1
            else:
                failed_count += 1
            print()  # 空行分隔
        
        print(f"✅ 用户处理完成!")
        print(f"   新创建: {created_count} 个")
        print(f"   已更新: {updated_count} 个")
        if failed_count > 0:
            print(f"   失败: {failed_count} 个")
        print()
    
    async def show_summary(self):
        """显示汇总信息"""
        print("=" * 60)
        print("📊 创建汇总\n")
        
        # 获取部门树
        response = await self.client.get("/departments/tree")
        if response.status_code == 200:
            tree = response.json()["data"]
            print(f"📁 部门总数: {len(self.dept_id_map)}")
            print(f"👥 用户总数: {len(USERS_DATA)}")
            print(f"\n部门结构:")
            self._print_tree(tree)
        
        print("\n" + "=" * 60)
        print("🎉 批量创建完成！")
        print("\n可以使用以下账号登录测试:")
        print(f"  管理员: {ADMIN_USERNAME} / {USER_DEFAULT_PASSWORD}")
        print(f"  普通用户: zhangwei / {USER_DEFAULT_PASSWORD}")
        print(f"  技术部门: sunhao / {USER_DEFAULT_PASSWORD}")
        print("=" * 60)
    
    def _print_tree(self, nodes, level=0):
        """打印树形结构"""
        for node in nodes:
            indent = "  " * level
            print(f"{indent}├─ {node['name']} (ID: {node['id']})")
            if node.get("children"):
                self._print_tree(node["children"], level + 1)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主函数"""
    creator = BatchCreator()
    
    try:
        # 1. 登录
        await creator.login()
        
        # 2. 加载已有部门（重要！）
        await creator.load_existing_departments()
        
        # 3. 创建部门（如果不存在）
        await creator.create_all_departments()
        
        # 4. 创建/更新用户
        await creator.create_all_users()
        
        # 5. 显示汇总
        await creator.show_summary()
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await creator.close()


if __name__ == "__main__":
    asyncio.run(main())
