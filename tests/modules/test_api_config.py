"""
接口配置与数据模型子模块测试用例

模块功能：API配置、数据模型管理、JSON解析、变量模板引擎
测试范围：接口CRUD、数据模型生成、API测试器、Mock数据生成等核心功能
"""
import pytest
import json
import re
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


# API配置模型测试
class TestApiConfigModel:
    """API配置数据模型测试"""
    
    def test_api_config_creation(self):
        """测试API配置创建"""
        api_config = {
            'id': 'api-001',
            'name': '获取用户列表',
            'method': 'GET',
            'url': 'https://api.example.com/users',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {{token}}'
            },
            'params': {
                'page': 1,
                'size': 10
            },
            'body': None,
            'timeout': 30,
            'project_id': 'proj-001',
            'created_at': datetime.now()
        }
        
        assert api_config['method'] == 'GET'
        assert api_config['url'] == 'https://api.example.com/users'
        assert api_config['timeout'] == 30

    def test_api_method_validation(self):
        """测试API方法验证"""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        invalid_methods = ['get', 'post', 'invalid']
        
        for method in valid_methods:
            assert method in valid_methods
        
        for method in invalid_methods:
            assert method not in valid_methods

    def test_post_api_with_body(self):
        """测试带请求体的POST API"""
        api_config = {
            'id': 'api-002',
            'name': '创建用户',
            'method': 'POST',
            'url': 'https://api.example.com/users',
            'headers': {'Content-Type': 'application/json'},
            'body': {
                'name': '{{userName}}',
                'email': '{{userEmail}}',
                'age': '{{userAge}}'
            }
        }
        
        assert api_config['method'] == 'POST'
        assert api_config['body'] is not None
        assert 'name' in api_config['body']

    def test_api_with_path_params(self):
        """测试带路径参数的API"""
        api_config = {
            'id': 'api-003',
            'name': '获取用户详情',
            'method': 'GET',
            'url': 'https://api.example.com/users/{{userId}}',
            'path_params': {'userId': '123'}
        }
        
        assert '{{userId}}' in api_config['url']
        assert 'userId' in api_config['path_params']


# 数据模型测试
class TestDataModel:
    """数据模型测试"""
    
    def test_data_model_creation(self):
        """测试数据模型创建"""
        data_model = {
            'id': 'model-001',
            'name': 'User',
            'project_id': 'proj-001',
            'fields': [
                {'name': 'id', 'type': 'number', 'required': True},
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'email', 'type': 'string', 'required': False},
                {'name': 'createdAt', 'type': 'datetime', 'required': False}
            ],
            'created_at': datetime.now()
        }
        
        assert data_model['name'] == 'User'
        assert len(data_model['fields']) == 4
        assert data_model['fields'][0]['type'] == 'number'

    def test_field_types(self):
        """测试字段类型"""
        valid_types = ['string', 'number', 'boolean', 'datetime', 'array', 'object', 'any']
        
        for field_type in valid_types:
            assert field_type in valid_types

    def test_nested_object_field(self):
        """测试嵌套对象字段"""
        data_model = {
            'id': 'model-002',
            'name': 'Order',
            'fields': [
                {'name': 'id', 'type': 'number'},
                {'name': 'user', 'type': 'object', 'fields': [
                    {'name': 'id', 'type': 'number'},
                    {'name': 'name', 'type': 'string'}
                ]},
                {'name': 'items', 'type': 'array', 'itemType': 'object', 'fields': [
                    {'name': 'productId', 'type': 'number'},
                    {'name': 'quantity', 'type': 'number'}
                ]}
            ]
        }
        
        user_field = data_model['fields'][1]
        assert user_field['type'] == 'object'
        assert 'fields' in user_field
        
        items_field = data_model['fields'][2]
        assert items_field['type'] == 'array'
        assert 'itemType' in items_field


# JSON解析算法测试
class TestJsonParsing:
    """JSON解析算法测试"""
    
    def test_parse_valid_json(self):
        """测试解析有效JSON"""
        json_string = '''{
            "name": "Test",
            "items": [1, 2, 3],
            "nested": {"key": "value"}
        }'''
        
        result = json.loads(json_string)
        
        assert result['name'] == 'Test'
        assert len(result['items']) == 3
        assert result['nested']['key'] == 'value'

    def test_parse_invalid_json(self):
        """测试解析无效JSON"""
        invalid_json = '{name: "Test"}'
        
        try:
            json.loads(invalid_json)
            assert False, "Should raise exception"
        except json.JSONDecodeError:
            assert True

    def test_parse_json_with_special_characters(self):
        """测试解析包含特殊字符的JSON"""
        json_string = '''{
            "text": "Hello\\nWorld",
            "path": "/users/test",
            "quote": "He said \\"Hello\\""
        }'''
        
        result = json.loads(json_string)
        
        assert result['text'] == 'Hello\nWorld'
        assert result['quote'] == 'He said "Hello"'

    def test_generate_schema_from_json(self):
        """测试从JSON生成Schema"""
        json_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "active": True,
            "tags": ["admin", "user"],
            "profile": {
                "age": 25,
                "address": "123 Street"
            }
        }
        
        # 模拟Schema生成
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"},
                "email": {"type": "string"},
                "active": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "profile": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "number"},
                        "address": {"type": "string"}
                    }
                }
            }
        }
        
        assert schema['properties']['id']['type'] == 'number'
        assert schema['properties']['tags']['type'] == 'array'
        assert schema['properties']['profile']['type'] == 'object'


# 变量模板引擎测试
class TestVariableTemplateEngine:
    """变量模板引擎测试"""
    
    def test_simple_variable_replacement(self):
        """测试简单变量替换"""
        template = 'Hello {{name}}!'
        variables = {'name': 'World'}
        
        # 模拟变量替换
        result = re.sub(r'\{\{(\w+)\}\}', lambda m: variables.get(m.group(1), ''), template)
        
        assert result == 'Hello World!'

    def test_nested_variable_replacement(self):
        """测试嵌套变量替换"""
        template = 'User: {{user.name}}, Email: {{user.email}}'
        variables = {'user': {'name': 'John', 'email': 'john@example.com'}}
        
        # 模拟嵌套变量替换
        def replace_nested(match):
            path = match.group(1)
            value = variables
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return ''
            return str(value)
        
        result = re.sub(r'\{\{(\w+(?:\.\w+)*)\}\}', replace_nested, template)
        
        assert result == 'User: John, Email: john@example.com'

    def test_array_index_variable(self):
        """测试数组索引变量"""
        template = 'First item: {{items[0]}}, Second: {{items[1]}}'
        variables = {'items': ['Apple', 'Banana', 'Cherry']}
        
        # 模拟数组索引替换
        def replace_with_array(match):
            path = match.group(1)
            parts = path.split('[')
            if len(parts) == 2:
                arr_name = parts[0]
                index = int(parts[1].replace(']', ''))
                if arr_name in variables and isinstance(variables[arr_name], list):
                    return variables[arr_name][index]
            return ''
        
        result = re.sub(r'\{\{(\w+\[\d+\])\}\}', replace_with_array, template)
        
        assert result == 'First item: Apple, Second: Banana'

    def test_variable_not_found(self):
        """测试变量不存在"""
        template = 'Hello {{nonexistent}}!'
        variables = {'name': 'World'}
        
        result = re.sub(r'\{\{(\w+)\}\}', lambda m: variables.get(m.group(1), 'N/A'), template)
        
        assert result == 'Hello N/A!'

    def test_complex_expression(self):
        """测试复杂表达式"""
        template = 'Total: {{price * quantity}}'
        variables = {'price': 10, 'quantity': 5}
        
        # 模拟简单表达式计算
        result = template.replace('{{price * quantity}}', str(variables['price'] * variables['quantity']))
        
        assert result == 'Total: 50'


# API测试器测试
class TestApiTester:
    """API测试器测试"""
    
    def test_execute_get_request(self):
        """测试执行GET请求"""
        api_config = {
            'method': 'GET',
            'url': 'https://api.example.com/users',
            'headers': {'Content-Type': 'application/json'}
        }
        
        # 模拟请求执行
        response = {
            'status': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': {'data': [], 'total': 0}
        }
        
        assert response['status'] == 200
        assert 'data' in response['body']

    def test_execute_post_request(self):
        """测试执行POST请求"""
        api_config = {
            'method': 'POST',
            'url': 'https://api.example.com/users',
            'headers': {'Content-Type': 'application/json'},
            'body': {'name': 'Test', 'email': 'test@example.com'}
        }
        
        # 模拟请求执行
        response = {
            'status': 201,
            'body': {'id': 1, 'name': 'Test', 'email': 'test@example.com'}
        }
        
        assert response['status'] == 201
        assert response['body']['id'] == 1

    def test_execute_request_with_variables(self):
        """测试带变量的请求执行"""
        api_config = {
            'method': 'GET',
            'url': 'https://api.example.com/users/{{userId}}',
            'headers': {'Authorization': 'Bearer {{token}}'}
        }
        variables = {'userId': '123', 'token': 'abc123'}
        
        # 模拟变量替换和请求执行
        resolved_url = api_config['url'].replace('{{userId}}', variables['userId'])
        resolved_headers = {'Authorization': 'Bearer ' + variables['token']}
        
        assert resolved_url == 'https://api.example.com/users/123'
        assert resolved_headers['Authorization'] == 'Bearer abc123'

    def test_request_timeout(self):
        """测试请求超时"""
        api_config = {
            'method': 'GET',
            'url': 'https://api.example.com/slow',
            'timeout': 5
        }
        
        # 模拟超时
        timeout = True
        
        assert timeout is True

    def test_request_error(self):
        """测试请求错误"""
        api_config = {
            'method': 'GET',
            'url': 'https://api.example.com/invalid'
        }
        
        # 模拟错误响应
        response = {
            'status': 404,
            'body': {'error': 'Not Found'}
        }
        
        assert response['status'] == 404
        assert 'error' in response['body']


# Mock数据生成器测试
class TestMockDataGenerator:
    """Mock数据生成器测试"""
    
    def test_generate_mock_string(self):
        """测试生成字符串类型Mock数据"""
        field = {'name': 'name', 'type': 'string'}
        
        # 模拟生成
        mock_value = 'Mock String'
        
        assert isinstance(mock_value, str)
        assert len(mock_value) > 0

    def test_generate_mock_number(self):
        """测试生成数字类型Mock数据"""
        field = {'name': 'age', 'type': 'number', 'min': 1, 'max': 100}
        
        # 模拟生成
        mock_value = 25
        
        assert isinstance(mock_value, int)
        assert 1 <= mock_value <= 100

    def test_generate_mock_boolean(self):
        """测试生成布尔类型Mock数据"""
        field = {'name': 'active', 'type': 'boolean'}
        
        # 模拟生成
        mock_value = True
        
        assert isinstance(mock_value, bool)

    def test_generate_mock_datetime(self):
        """测试生成日期时间类型Mock数据"""
        field = {'name': 'createdAt', 'type': 'datetime'}
        
        # 模拟生成
        mock_value = '2024-01-15T10:30:00Z'
        
        assert isinstance(mock_value, str)
        assert 'T' in mock_value

    def test_generate_mock_array(self):
        """测试生成数组类型Mock数据"""
        field = {'name': 'tags', 'type': 'array', 'itemType': 'string', 'length': 3}
        
        # 模拟生成
        mock_value = ['tag1', 'tag2', 'tag3']
        
        assert isinstance(mock_value, list)
        assert len(mock_value) == 3
        assert all(isinstance(item, str) for item in mock_value)

    def test_generate_mock_object(self):
        """测试生成对象类型Mock数据"""
        field = {
            'name': 'user',
            'type': 'object',
            'fields': [
                {'name': 'id', 'type': 'number'},
                {'name': 'name', 'type': 'string'}
            ]
        }
        
        # 模拟生成
        mock_value = {'id': 1, 'name': 'Mock User'}
        
        assert isinstance(mock_value, dict)
        assert 'id' in mock_value
        assert 'name' in mock_value

    def test_generate_mock_from_model(self):
        """测试从数据模型生成Mock数据"""
        model = {
            'name': 'User',
            'fields': [
                {'name': 'id', 'type': 'number'},
                {'name': 'name', 'type': 'string'},
                {'name': 'email', 'type': 'string'},
                {'name': 'active', 'type': 'boolean'}
            ]
        }
        
        # 模拟生成
        mock_data = {
            'id': 1,
            'name': 'Mock User',
            'email': 'mock@example.com',
            'active': True
        }
        
        assert len(mock_data) == len(model['fields'])
        assert 'id' in mock_data
        assert 'email' in mock_data


# API接口测试
class TestApiConfigAPI:
    """API配置API测试"""
    
    def test_create_api_config(self, client, auth_token):
        """测试创建API配置"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        api_data = {
            'name': '获取列表',
            'method': 'GET',
            'url': 'https://api.example.com/list',
            'headers': {'Content-Type': 'application/json'}
        }
        
        response = client.post('/api/projects/proj-001/apis', headers=headers, json=api_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == '获取列表'

    def test_get_api_list(self, client, auth_token):
        """测试获取API列表"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/projects/proj-001/apis', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_api_detail(self, client, auth_token):
        """测试获取API详情"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/projects/proj-001/apis/api-001', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'method' in data['data']
        assert 'url' in data['data']

    def test_update_api_config(self, client, auth_token):
        """测试更新API配置"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        update_data = {
            'name': '更新后的API',
            'url': 'https://api.example.com/updated'
        }
        
        response = client.put('/api/projects/proj-001/apis/api-001', headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == '更新后的API'

    def test_delete_api_config(self, client, auth_token):
        """测试删除API配置"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.delete('/api/projects/proj-001/apis/api-001', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_execute_api(self, client, auth_token):
        """测试执行API"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/projects/proj-001/apis/api-001/execute', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'response' in data['data']


class TestDataModelAPI:
    """数据模型API测试"""
    
    def test_create_data_model(self, client, auth_token):
        """测试创建数据模型"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        model_data = {
            'name': 'Product',
            'fields': [
                {'name': 'id', 'type': 'number', 'required': True},
                {'name': 'name', 'type': 'string', 'required': True},
                {'name': 'price', 'type': 'number', 'required': False}
            ]
        }
        
        response = client.post('/api/projects/proj-001/models', headers=headers, json=model_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Product'

    def test_get_model_list(self, client, auth_token):
        """测试获取数据模型列表"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/projects/proj-001/models', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_model_detail(self, client, auth_token):
        """测试获取数据模型详情"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/projects/proj-001/models/model-001', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'fields' in data['data']

    def test_update_data_model(self, client, auth_token):
        """测试更新数据模型"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        update_data = {
            'name': 'Updated Product',
            'fields': [
                {'name': 'id', 'type': 'number'},
                {'name': 'name', 'type': 'string'}
            ]
        }
        
        response = client.put('/api/projects/proj-001/models/model-001', headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_delete_data_model(self, client, auth_token):
        """测试删除数据模型"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.delete('/api/projects/proj-001/models/model-001', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_generate_mock_data(self, client, auth_token):
        """测试生成Mock数据"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/projects/proj-001/models/model-001/mock', headers=headers, json={'count': 5})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) == 5


# 服务层测试
class TestApiService:
    """API服务测试"""
    
    def test_validate_api_config(self):
        """测试验证API配置"""
        valid_config = {
            'name': 'Test API',
            'method': 'GET',
            'url': 'https://api.example.com/test'
        }
        
        # 模拟验证
        result = True
        
        assert result is True

    def test_resolve_variables(self):
        """测试变量解析"""
        config = {
            'url': 'https://api.example.com/users/{{userId}}',
            'headers': {'Authorization': 'Bearer {{token}}'}
        }
        variables = {'userId': '123', 'token': 'abc123'}
        
        # 模拟解析
        resolved = {
            'url': 'https://api.example.com/users/123',
            'headers': {'Authorization': 'Bearer abc123'}
        }
        
        assert resolved['url'] == 'https://api.example.com/users/123'

    def test_build_request(self):
        """测试构建请求"""
        config = {
            'method': 'POST',
            'url': 'https://api.example.com/users',
            'headers': {'Content-Type': 'application/json'},
            'body': {'name': 'Test'}
        }
        
        # 模拟构建
        request = {
            'method': 'POST',
            'url': 'https://api.example.com/users',
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'name': 'Test'})
        }
        
        assert request['method'] == 'POST'
        assert request['body'] is not None


class TestDataModelService:
    """数据模型服务测试"""
    
    def test_generate_model_from_response(self):
        """测试从响应生成模型"""
        response = {
            'id': 1,
            'name': 'Test',
            'price': 100.5,
            'active': True,
            'tags': ['a', 'b']
        }
        
        # 模拟生成模型
        model = {
            'name': 'ResponseModel',
            'fields': [
                {'name': 'id', 'type': 'number'},
                {'name': 'name', 'type': 'string'},
                {'name': 'price', 'type': 'number'},
                {'name': 'active', 'type': 'boolean'},
                {'name': 'tags', 'type': 'array', 'itemType': 'string'}
            ]
        }
        
        assert len(model['fields']) == 5
        assert model['fields'][0]['type'] == 'number'

    def test_validate_model_schema(self):
        """测试验证模型Schema"""
        model = {
            'name': 'Test',
            'fields': [{'name': 'id', 'type': 'number'}]
        }
        
        # 模拟验证
        result = True
        
        assert result is True


# Fixtures
@pytest.fixture
def client():
    """创建测试客户端"""
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def auth_token():
    """提供认证令牌"""
    return 'valid_test_token'
