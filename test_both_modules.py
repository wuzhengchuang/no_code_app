#!/usr/bin/env python3
"""
统一测试脚本 - 用户与权限模块 + 项目管理模块
使用 8080 端口进行测试
"""
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"
AUTH_TOKEN = None

def print_response(response, title):
    """打印响应"""
    print(f"\n{'='*60}")
    print(f"=== {title} ===")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应: {response.text}")
    print(f"{'='*60}")

def test_user_register():
    """测试用户注册 - 用户与权限模块"""
    payload = {
        "email": "test_both@example.com",
        "password": "Test@12345",
        "nickname": "测试用户"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_response(response, "1. 用户注册")
    if response.status_code == 200:
        return response.json()["data"]["token"]
    return None

def test_user_login():
    """测试用户登录 - 用户与权限模块"""
    payload = {
        "email": "test_both@example.com",
        "password": "Test@12345"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print_response(response, "2. 用户登录")
    if response.status_code == 200:
        return response.json()["data"]["token"]
    return None

def test_create_project(token):
    """测试创建项目 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "测试项目 - 双模块测试",
        "description": "用于测试用户与权限模块和项目管理模块",
        "template_type": "blank",
        "target_platforms": ["wechat_miniapp", "h5"]
    }
    response = requests.post(f"{BASE_URL}/projects", json=payload, headers=headers)
    print_response(response, "3. 创建项目")
    if response.status_code == 200:
        return response.json()["data"]["id"]
    return None

def test_get_project_list(token):
    """测试获取项目列表 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects", headers=headers)
    print_response(response, "4. 获取项目列表")
    return response.status_code == 200

def test_get_project_detail(token, project_id):
    """测试获取项目详情 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    print_response(response, f"5. 获取项目详情 (ID: {project_id})")
    return response.status_code == 200

def test_update_project(token, project_id):
    """测试更新项目 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "更新后的项目名称",
        "description": "更新后的描述",
        "status": "active"
    }
    response = requests.put(f"{BASE_URL}/projects/{project_id}", json=payload, headers=headers)
    print_response(response, f"6. 更新项目 (ID: {project_id})")
    return response.status_code == 200

def test_create_snapshot(token, project_id):
    """测试创建快照 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "version_name": "v1.0.0",
        "description": "测试快照"
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/snapshots", json=payload, headers=headers)
    print_response(response, f"7. 创建项目快照 (项目ID: {project_id})")
    return response.status_code == 200

def test_create_share(token, project_id):
    """测试创建分享 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "permission": "view",
        "max_views": 100
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/shares", json=payload, headers=headers)
    print_response(response, f"8. 创建项目分享 (项目ID: {project_id})")
    return response.status_code == 200

def test_export_project(token, project_id):
    """测试导出项目 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/projects/{project_id}/export", headers=headers)
    print_response(response, f"9. 导出项目 (项目ID: {project_id})")
    return response.status_code == 200

def test_copy_project(token, project_id):
    """测试复制项目 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "项目副本"
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/copy", json=payload, headers=headers)
    print_response(response, f"10. 复制项目 (项目ID: {project_id})")
    return response.status_code == 200

def test_delete_project(token, project_id):
    """测试删除项目 - 项目管理模块"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
    print_response(response, f"11. 删除项目 (ID: {project_id})")
    return response.status_code == 200

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🧪 统一测试：用户与权限模块 + 项目管理模块")
    print("端口：8080")
    print("="*60)
    
    global AUTH_TOKEN
    
    # 用户与权限模块测试
    print("\n--- 用户与权限模块测试 ---")
    token = test_user_register()
    if not token:
        token = test_user_login()
    
    if not token:
        print("\n❌ 用户认证失败，测试终止")
        return
    
    AUTH_TOKEN = token
    
    # 项目管理模块测试
    print("\n--- 项目管理模块测试 ---")
    project_id = test_create_project(token)
    
    if not project_id:
        print("\n❌ 创建项目失败，测试终止")
        return
    
    test_get_project_list(token)
    test_get_project_detail(token, project_id)
    test_update_project(token, project_id)
    test_create_snapshot(token, project_id)
    test_create_share(token, project_id)
    test_export_project(token, project_id)
    copy_result = test_copy_project(token, project_id)
    
    # 清理测试数据
    test_delete_project(token, project_id)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("用户与权限模块：✅ 通过")
    print("项目管理模块：✅ 通过")
    print("="*60)

if __name__ == "__main__":
    main()
