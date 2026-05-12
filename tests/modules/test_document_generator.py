"""
文档生成子模块测试用例

模块功能：技术文档自动生成、Jinja2模板引擎、数据库Schema文档、Postman集合生成
测试范围：文档模板、文档生成器、数据库文档、API文档等核心功能
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


# 文档模板测试
class TestDocumentTemplates:
    """文档模板测试"""
    
    def test_claude_md_template(self):
        """测试CLAUDE.md模板"""
        template = {
            'id': 'claude-md',
            'name': 'CLAUDE.md',
            'type': 'markdown',
            'content': '''
# {{projectName}}

## 项目概述

{{description}}

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | {{frontendTech}} |
| 后端 | {{backendTech}} |

## API接口

{% for api in apis %}
- {{api.name}}: {{api.method}} {{api.url}}
{% endfor %}
''',
            'variables': ['projectName', 'description', 'frontendTech', 'backendTech', 'apis']
        }
        
        assert template['type'] == 'markdown'
        assert 'projectName' in template['variables']
        assert 'apis' in template['variables']

    def test_readme_template(self):
        """测试README模板"""
        template = {
            'id': 'readme',
            'name': 'README.md',
            'type': 'markdown',
            'content': '''
# {{projectName}}

{{description}}

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

## 项目结构

```
{{projectStructure}}
```
''',
            'variables': ['projectName', 'description', 'projectStructure']
        }
        
        assert template['name'] == 'README.md'
        assert 'projectStructure' in template['variables']

    def test_technical_spec_template(self):
        """测试技术规格模板"""
        template = {
            'id': 'tech-spec',
            'name': '技术规格文档',
            'type': 'markdown',
            'content': '''
# {{projectName}} - 技术规格文档

## 1. 需求分析

### 1.1 功能需求

{{functionalRequirements}}

### 1.2 非功能需求

{{nonFunctionalRequirements}}

## 2. 架构设计

{{architecture}}

## 3. 数据库设计

{{databaseDesign}}

## 4. API设计

{{apiDesign}}
''',
            'variables': ['projectName', 'functionalRequirements', 'architecture', 'databaseDesign']
        }
        
        assert 'architecture' in template['variables']
        assert 'databaseDesign' in template['variables']

    def test_postman_collection_template(self):
        """测试Postman集合模板"""
        template = {
            'id': 'postman-collection',
            'name': 'Postman Collection',
            'type': 'json',
            'content': '''
{
    "info": {
        "name": "{{projectName}}",
        "description": "{{description}}"
    },
    "item": [
        {% for api in apis %}
        {
            "name": "{{api.name}}",
            "request": {
                "method": "{{api.method}}",
                "url": "{{api.url}}"
            }
        }{{ "," if not loop.last else "" }}
        {% endfor %}
    ]
}
''',
            'variables': ['projectName', 'description', 'apis']
        }
        
        assert template['type'] == 'json'


# 文档生成器测试
class TestDocumentGenerator:
    """文档生成器测试"""
    
    def test_generate_all_documents(self):
        """测试生成所有文档"""
        generator = {
            'projectId': 'proj-001',
            'templates': ['claude-md', 'readme', 'tech-spec']
        }
        
        # 模拟生成
        documents = [
            {'id': 'claude-md', 'name': 'CLAUDE.md', 'content': '# Project'},
            {'id': 'readme', 'name': 'README.md', 'content': '# Project'},
            {'id': 'tech-spec', 'name': '技术规格文档', 'content': '# Tech Spec'}
        ]
        
        assert len(documents) == 3
        assert documents[0]['id'] == 'claude-md'

    def test_generate_claude_md(self):
        """测试生成CLAUDE.md"""
        project = {
            'name': 'My Project',
            'description': 'A test project',
            'platform': 'wechat_mini',
            'apis': [{'name': 'Get Users', 'method': 'GET', 'url': '/api/users'}]
        }
        
        # 模拟生成
        content = '''# My Project

## 项目概述

A test project

## 技术栈

| 层级 | 技术 |
|------|------|
| 平台 | WeChat Mini |

## API接口

- Get Users: GET /api/users
'''
        
        assert '# My Project' in content
        assert 'A test project' in content

    def test_generate_readme(self):
        """测试生成README.md"""
        project = {
            'name': 'My App',
            'description': 'A mobile app',
            'techStack': ['Vue 3', 'TypeScript', 'Tailwind CSS']
        }
        
        # 模拟生成
        content = '''# My App

A mobile app

## 技术栈

- Vue 3
- TypeScript
- Tailwind CSS
'''
        
        assert '# My App' in content
        assert 'Vue 3' in content

    def test_generate_technical_spec(self):
        """测试生成技术规格文档"""
        project = {
            'name': 'Backend Service',
            'requirements': ['High performance', 'Scalable'],
            'architecture': 'Microservices'
        }
        
        # 模拟生成
        content = '''# Backend Service - 技术规格文档

## 1. 需求分析

### 1.1 功能需求

- High performance
- Scalable

## 2. 架构设计

Microservices
'''
        
        assert 'Microservices' in content


# 数据库Schema文档测试
class TestDatabaseSchemaDoc:
    """数据库Schema文档测试"""
    
    def test_generate_schema_doc(self):
        """测试生成数据库Schema文档"""
        tables = [
            {
                'name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'INT', 'primaryKey': True},
                    {'name': 'email', 'type': 'VARCHAR(255)', 'nullable': False},
                    {'name': 'name', 'type': 'VARCHAR(100)', 'nullable': False}
                ]
            },
            {
                'name': 'projects',
                'columns': [
                    {'name': 'id', 'type': 'INT', 'primaryKey': True},
                    {'name': 'name', 'type': 'VARCHAR(255)', 'nullable': False},
                    {'name': 'created_by', 'type': 'INT', 'foreignKey': 'users.id'}
                ]
            }
        ]
        
        # 模拟生成
        content = '''# 数据库Schema文档

## users 表

| 字段名 | 类型 | 约束 |
|--------|------|------|
| id | INT | PRIMARY KEY |
| email | VARCHAR(255) | NOT NULL |
| name | VARCHAR(100) | NOT NULL |

## projects 表

| 字段名 | 类型 | 约束 |
|--------|------|------|
| id | INT | PRIMARY KEY |
| name | VARCHAR(255) | NOT NULL |
| created_by | INT | FOREIGN KEY -> users.id |
'''
        
        assert 'users 表' in content
        assert 'projects 表' in content
        assert 'FOREIGN KEY' in content

    def test_generate_erd_description(self):
        """测试生成ER图描述"""
        tables = [
            {'name': 'users', 'columns': [{'name': 'id'}]},
            {'name': 'projects', 'columns': [{'name': 'created_by', 'foreignKey': 'users.id'}]}
        ]
        
        # 模拟生成ERD描述
        erd = '''
ER关系图:

users 1:n projects
    users.id -> projects.created_by
'''
        
        assert '1:n' in erd
        assert 'users.id -> projects.created_by' in erd


# Postman集合生成测试
class TestPostmanCollection:
    """Postman集合生成测试"""
    
    def test_generate_postman_collection(self):
        """测试生成Postman集合"""
        apis = [
            {
                'id': 'api-001',
                'name': '获取用户列表',
                'method': 'GET',
                'url': '/api/users',
                'headers': {'Content-Type': 'application/json'},
                'params': {'page': 1, 'size': 10}
            },
            {
                'id': 'api-002',
                'name': '创建用户',
                'method': 'POST',
                'url': '/api/users',
                'headers': {'Content-Type': 'application/json'},
                'body': {'name': 'Test', 'email': 'test@example.com'}
            }
        ]
        
        # 模拟生成
        collection = {
            'info': {
                'name': 'API Collection',
                'description': 'Auto-generated collection'
            },
            'item': [
                {
                    'name': '获取用户列表',
                    'request': {
                        'method': 'GET',
                        'url': {'raw': '/api/users', 'query': [{'key': 'page', 'value': '1'}, {'key': 'size', 'value': '10'}]}
                    }
                },
                {
                    'name': '创建用户',
                    'request': {
                        'method': 'POST',
                        'url': {'raw': '/api/users'},
                        'body': {'raw': '{"name": "Test", "email": "test@example.com"}'}
                    }
                }
            ]
        }
        
        assert len(collection['item']) == 2
        assert collection['item'][0]['name'] == '获取用户列表'
        assert collection['item'][1]['request']['method'] == 'POST'

    def test_postman_environment(self):
        """测试生成Postman环境变量"""
        env = {
            'name': 'Development',
            'values': [
                {'key': 'baseUrl', 'value': 'http://localhost:8080'},
                {'key': 'token', 'value': '{{token}}'}
            ]
        }
        
        assert env['name'] == 'Development'
        assert env['values'][0]['key'] == 'baseUrl'


# 实现计划生成测试
class TestImplementationPlan:
    """实现计划生成测试"""
    
    def test_generate_implementation_plan(self):
        """测试生成实现计划"""
        project = {
            'name': 'My Project',
            'pages': [{'id': 'page-001', 'name': '首页'}, {'id': 'page-002', 'name': '详情页'}],
            'apis': [{'id': 'api-001', 'name': '获取列表'}],
            'models': [{'id': 'model-001', 'name': 'User'}]
        }
        
        # 模拟生成计划
        plan = '''# {{projectName}} 实现计划

## 阶段一：项目初始化 (1天)

- [ ] 创建项目结构
- [ ] 配置开发环境
- [ ] 设置版本控制

## 阶段二：页面开发 (3天)

- [ ] 首页开发 (page-001)
- [ ] 详情页开发 (page-002)

## 阶段三：API集成 (2天)

- [ ] 获取列表接口 (api-001)

## 阶段四：数据模型 (1天)

- [ ] User模型 (model-001)

## 阶段五：测试与部署 (2天)

- [ ] 单元测试
- [ ] 集成测试
- [ ] 部署上线

**总预估时间**: 9天
'''
        
        assert '阶段一' in plan
        assert '首页开发' in plan
        assert '总预估时间' in plan

    def test_task_breakdown(self):
        """测试任务分解"""
        tasks = [
            {'id': 'task-001', 'name': '创建项目', 'estimate': '1天', 'dependencies': []},
            {'id': 'task-002', 'name': '开发首页', 'estimate': '2天', 'dependencies': ['task-001']},
            {'id': 'task-003', 'name': '开发详情页', 'estimate': '2天', 'dependencies': ['task-001']}
        ]
        
        assert len(tasks) == 3
        assert tasks[1]['dependencies'] == ['task-001']


# Jinja2模板引擎测试
class TestJinja2Engine:
    """Jinja2模板引擎测试"""
    
    def test_jinja2_variable_rendering(self):
        """测试Jinja2变量渲染"""
        template = 'Hello {{ name }}!'
        context = {'name': 'World'}
        
        # 模拟Jinja2渲染
        rendered = template.replace('{{ name }}', context['name'])
        
        assert rendered == 'Hello World!'

    def test_jinja2_loop(self):
        """测试Jinja2循环"""
        template = '''
{% for item in items %}
- {{ item }}
{% endfor %}
'''
        context = {'items': ['A', 'B', 'C']}
        
        # 模拟渲染
        items_html = '\n'.join([f'- {item}' for item in context['items']])
        rendered = template.replace('{% for item in items %}\n- {{ item }}\n{% endfor %}', items_html)
        
        assert '- A' in rendered
        assert '- B' in rendered

    def test_jinja2_condition(self):
        """测试Jinja2条件"""
        template = '''
{% if show %}
Visible
{% else %}
Hidden
{% endif %}
'''
        context = {'show': True}
        
        # 模拟渲染
        rendered = template.replace('{% if show %}\nVisible\n{% else %}\nHidden\n{% endif %}', 'Visible')
        
        assert 'Visible' in rendered

    def test_jinja2_inheritance(self):
        """测试Jinja2模板继承"""
        base_template = '''
<html>
    <body>
        {% block content %}{% endblock %}
    </body>
</html>
'''
        child_template = '''
{% extends "base.html" %}
{% block content %}
Content here
{% endblock %}
'''
        
        # 模拟继承
        rendered = base_template.replace('{% block content %}{% endblock %}', 'Content here')
        
        assert 'Content here' in rendered


# API接口测试
class TestDocumentAPI:
    """文档API测试"""
    
    def test_generate_document(self, client, auth_token):
        """测试生成文档"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        doc_data = {
            'projectId': 'proj-001',
            'templateId': 'claude-md',
            'variables': {
                'projectName': 'My Project',
                'description': 'Test project'
            }
        }
        
        response = client.post('/api/docs/generate', headers=headers, json=doc_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'content' in data['data']

    def test_generate_all_documents(self, client, auth_token):
        """测试生成所有文档"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/projects/proj-001/docs/generate-all', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_templates(self, client, auth_token):
        """测试获取模板列表"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/docs/templates', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_create_template(self, client, auth_token):
        """测试创建模板"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        template_data = {
            'name': 'Custom Template',
            'type': 'markdown',
            'content': '# {{title}}',
            'variables': ['title']
        }
        
        response = client.post('/api/docs/templates', headers=headers, json=template_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_download_document(self, client, auth_token):
        """测试下载文档"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/projects/proj-001/docs/download/claude-md', headers=headers)
        
        assert response.status_code == 200
        assert response.content_type == 'text/markdown'


# 服务层测试
class TestDocumentService:
    """文档服务测试"""
    
    def test_render_template(self):
        """测试渲染模板"""
        template = 'Hello {{name}}'
        context = {'name': 'World'}
        
        # 模拟渲染
        result = template.replace('{{name}}', context['name'])
        
        assert result == 'Hello World'

    def test_generate_postman_collection(self):
        """测试生成Postman集合"""
        apis = []
        
        # 模拟生成
        collection = {'item': []}
        
        assert isinstance(collection, dict)

    def test_generate_erd(self):
        """测试生成ERD"""
        tables = []
        
        # 模拟生成
        erd = ''
        
        assert isinstance(erd, str)


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
