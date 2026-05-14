#!/usr/bin/env python3
"""项目管理子模块API测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"

def print_response(response):
    """打印响应"""
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"响应内容: {response.text}")
    print("-" * 50)

def test_user_register():
    """测试用户注册"""
    print("=== 1. 用户注册 ===")
    payload = {
        "email": "test@example.com",
        "password": "Test@123456",
        "nickname": "测试用户"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print_response(response)
    return response

def test_user_login():
    """测试用户登录"""
    print("=== 2. 用户登录 ===")
    payload = {
        "email": "test@example.com",
        "password": "Test@123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print_response(response)
    if response.status_code == 200:
        return response.json()["data"]["token"]
    return None

def test_create_project(token):
    """测试创建项目"""
    print("=== 3. 创建项目 ===")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "我的第一个项目",
        "description": "这是一个测试项目",
        "template_type": "blank",
        "target_platforms": ["wechat_miniapp", "h5"]
    }
    response = requests.post(f"{BASE_URL}/projects", json=payload, headers=headers)
    print_response(response)
    if response.status_code == 200:
        return response.json()["data"]["id"]
    return None

def test_get_projects(token):
    """测试获取项目列表"""
    print("=== 4. 获取项目列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects", headers=headers)
    print_response(response)

def test_get_project(token, project_id):
    """测试获取项目详情"""
    print(f"=== 5. 获取项目详情 (ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    print_response(response)

def test_update_project(token, project_id):
    """测试更新项目"""
    print(f"=== 6. 更新项目 (ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "更新后的项目名称",
        "description": "更新后的描述",
        "status": "active"
    }
    response = requests.put(f"{BASE_URL}/projects/{project_id}", json=payload, headers=headers)
    print_response(response)

def test_create_snapshot(token, project_id):
    """测试创建快照"""
    print(f"=== 7. 创建项目快照 (项目ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "version_name": "v1.0.0",
        "description": "第一个正式版本"
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/snapshots", json=payload, headers=headers)
    print_response(response)
    if response.status_code == 200:
        return response.json()["data"]["id"]
    return None

def test_create_share(token, project_id):
    """测试创建分享"""
    print(f"=== 8. 创建项目分享 (项目ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "permission": "copy",
        "max_views": 100,
        "max_copies": 10
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/shares", json=payload, headers=headers)
    print_response(response)

def test_export_project(token, project_id):
    """测试导出项目"""
    print(f"=== 9. 导出项目 (项目ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/projects/{project_id}/export", headers=headers)
    print_response(response)

def test_copy_project(token, project_id):
    """测试复制项目"""
    print(f"=== 10. 复制项目 (项目ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "项目副本"
    }
    response = requests.post(f"{BASE_URL}/projects/{project_id}/copy", json=payload, headers=headers)
    print_response(response)

def test_delete_project(token, project_id):
    """测试删除项目"""
    print(f"=== 11. 删除项目 (项目ID: {project_id}) ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
    print_response(response)

def main():
    """主测试流程"""
    print("=" * 60)
    print("项目管理子模块API测试")
    print("=" * 60)
    
    # 1. 用户注册
    test_user_register()
    
    # 2. 用户登录
    token = test_user_login()
    if not token:
        print("登录失败，测试终止")
        return
    
    # 3. 创建项目
    project_id = test_create_project(token)
    if not project_id:
        print("创建项目失败，测试终止")
        return
    
    # 4. 获取项目列表
    test_get_projects(token)
    
    # 5. 获取项目详情
    test_get_project(token, project_id)
    
    # 6. 更新项目
    test_update_project(token, project_id)
    
    # 7. 创建快照
    snapshot_id = test_create_snapshot(token, project_id)
    
    # 8. 创建分享
    test_create_share(token, project_id)
    
    # 9. 导出项目
    test_export_project(token, project_id)
    
    # 10. 复制项目
    test_copy_project(token, project_id)
    
    # 11. 删除项目
    # test_delete_project(token, project_id)
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
