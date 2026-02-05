#!/usr/bin/env python3
"""
测试导入 API 的脚本

运行方式：
    docker compose exec api uv run python scripts/test_import_api.py
"""

import asyncio
import httpx

API_BASE_URL = "http://localhost:5050"
USERNAME = "admin"
PASSWORD = "1234hbnj"


async def test_apis():
    token = None
    
    # 1. 登录
    print("\n" + "="*60)
    print("1. 测试登录")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/auth/token",
            data={"username": USERNAME, "password": PASSWORD}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print(f"   ✅ Token 获取成功")
    
    if not token:
        print("❌ 登录失败，终止测试")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 创建部门
    print("\n" + "="*60)
    print("2. 测试创建部门")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # 创建一级部门
        response = await client.post(
            f"{API_BASE_URL}/api/departments",
            headers=headers,
            json={
                "name": "测试一级部门",
                "parent_id": None,
                "description": "测试用"
            }
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
        
        dept1_id = None
        if response.status_code == 200:
            data = response.json()
            print(f"   响应类型: {type(data)}")
            print(f"   响应键: {data.keys() if isinstance(data, dict) else 'N/A'}")
            
            # 尝试不同的解析方式
            if isinstance(data, dict):
                if "data" in data and isinstance(data["data"], dict):
                    dept1_id = data["data"].get("id")
                    print(f"   ✅ 从 data.data.id 获取: {dept1_id}")
                elif "id" in data:
                    dept1_id = data.get("id")
                    print(f"   ✅ 从 data.id 获取: {dept1_id}")
    
    if not dept1_id:
        print("   ⚠️ 一级部门创建可能失败，尝试查询")
        # 查询部门树
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/departments/tree",
                headers=headers
            )
            print(f"   部门树状态码: {response.status_code}")
            print(f"   部门树响应: {response.text[:1000]}")
            
            if response.status_code == 200:
                tree_data = response.json()
                print(f"   部门树键: {tree_data.keys() if isinstance(tree_data, dict) else 'N/A'}")
    
    # 3. 创建二级部门
    if dept1_id:
        print("\n" + "="*60)
        print("3. 测试创建二级部门")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/departments",
                headers=headers,
                json={
                    "name": "测试二级部门",
                    "parent_id": dept1_id,
                    "description": "测试用"
                }
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
            
            dept2_id = None
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    dept2_id = data["data"].get("id")
                    print(f"   ✅ 二级部门 ID: {dept2_id}")
    else:
        dept2_id = None
    
    # 4. 创建知识库
    print("\n" + "="*60)
    print("4. 测试创建知识库")
    print("="*60)
    
    test_dept_id = dept2_id or dept1_id or 1  # 使用测试部门或默认部门
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{API_BASE_URL}/api/knowledge/databases",
            headers=headers,
            json={
                "database_name": "测试知识库",
                "description": "API测试用",
                "embed_model_name": "siliconflow/BAAI/bge-m3",
                "kb_type": "milvus",
                "additional_params": {},
                "share_config": {
                    "is_shared": True,
                    "accessible_departments": [test_dept_id]
                }
            }
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:1000]}")
        
        kb_id = None
        if response.status_code == 200:
            data = response.json()
            print(f"   响应键: {data.keys() if isinstance(data, dict) else 'N/A'}")
            
            # 尝试不同的解析方式
            if isinstance(data, dict):
                if "db_id" in data:
                    kb_id = data.get("db_id")
                    print(f"   ✅ 从 data.db_id 获取: {kb_id}")
                elif "data" in data and isinstance(data["data"], dict):
                    kb_id = data["data"].get("db_id")
                    print(f"   ✅ 从 data.data.db_id 获取: {kb_id}")
    
    # 5. 清理测试数据
    print("\n" + "="*60)
    print("5. 清理测试数据")
    print("="*60)
    
    if kb_id:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/knowledge/databases/{kb_id}",
                headers=headers
            )
            print(f"   删除知识库: {response.status_code}")
    
    if dept2_id:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/departments/{dept2_id}",
                headers=headers
            )
            print(f"   删除二级部门: {response.status_code}")
    
    if dept1_id:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/departments/{dept1_id}",
                headers=headers
            )
            print(f"   删除一级部门: {response.status_code}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_apis())
