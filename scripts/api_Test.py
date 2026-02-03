import asyncio
import httpx

async def test():
    print('=== 测试 /api/departments 接口权限 ===\n')
    
    # 1. 未登录
    print('1️⃣  未登录访问')
    client = httpx.AsyncClient(base_url='http://47.122.119.66:5050', timeout=5)
    resp = await client.get('/api/departments')
    print(f'   状态码: {resp.status_code}')
    if resp.status_code == 401:
        print('   ✅ 正确返回401')
    await client.aclose()
    
    # 2. 普通用户
    print('\n2️⃣  普通用户（李娜）')
    client = httpx.AsyncClient(base_url='http://47.122.119.66:5050', timeout=5)
    resp = await client.post('/api/auth/token', data={
        'username': 'lina',
        'password': 'Pass1234'
    })
    
    if resp.status_code == 200:
        token = resp.json()['access_token']
        print('   ✅ 登录成功')
        client.headers.update({'Authorization': f'Bearer {token}'})
        
        resp = await client.get('/api/departments')
        print(f'   /api/departments 状态码: {resp.status_code}')
        
        if resp.status_code == 200:
            tree = resp.json().get('data', [])
            print(f'   ✅ 成功获取部门树，顶层部门: {len(tree)} 个')
        elif resp.status_code == 403:
            print(f'   ❌ 返回403权限不足')
        else:
            print(f'   ❌ 错误 {resp.status_code}')
    else:
        print(f'   ❌ 登录失败: {resp.status_code}')
    
    await client.aclose()
    
    # 3. 管理员
    print('\n3️⃣  管理员（张伟）')
    client = httpx.AsyncClient(base_url='http://47.122.119.66:5050', timeout=5)
    resp = await client.post('/api/auth/token', data={
        'username': 'zhangwei',
        'password': 'Pass1234'
    })
    
    if resp.status_code == 200:
        token = resp.json()['access_token']
        print('   ✅ 登录成功')
        client.headers.update({'Authorization': f'Bearer {token}'})
        
        resp = await client.get('/api/departments')
        print(f'   /api/departments 状态码: {resp.status_code}')
        
        if resp.status_code == 200:
            tree = resp.json().get('data', [])
            print(f'   ✅ 成功获取部门树，顶层部门: {len(tree)} 个')
    else:
        print(f'   ❌ 登录失败: {resp.status_code}')
    
    await client.aclose()
    print('\n=== 测试完成 ===')

asyncio.run(test())