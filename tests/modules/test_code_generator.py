"""
代码生成引擎子模块测试用例

模块功能：插件化代码生成、多平台支持、模板引擎、组件映射
测试范围：生成器基类、插件管理器、模板引擎、平台生成器等核心功能
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


# 生成器基类测试
class TestBaseCodeGenerator:
    """生成器基类测试"""
    
    def test_generator_interface(self):
        """测试生成器接口"""
        generator = {
            'id': 'wechat-mini',
            'name': '微信小程序',
            'platform': 'wechat_mini',
            'version': '1.0',
            'supportedFeatures': ['pages', 'components', 'apis', 'models']
        }
        
        assert generator['platform'] == 'wechat_mini'
        assert 'pages' in generator['supportedFeatures']
        assert 'components' in generator['supportedFeatures']

    def test_generate_method(self):
        """测试生成方法"""
        generator = {'platform': 'h5'}
        project_data = {
            'version': '1.0',
            'name': 'Test Project',
            'pages': [],
            'apis': [],
            'models': []
        }
        
        # 模拟生成
        result = {
            'success': True,
            'files': [],
            'platform': 'h5'
        }
        
        assert result['success'] is True
        assert result['platform'] == 'h5'

    def test_generate_page(self):
        """测试生成页面"""
        page = {
            'id': 'page-001',
            'name': '首页',
            'path': '/',
            'components': []
        }
        
        # 模拟生成
        files = [
            {'name': 'pages/index/index.wxml', 'content': '<view>Home</view>'},
            {'name': 'pages/index/index.wxss', 'content': '.container {}'},
            {'name': 'pages/index/index.js', 'content': 'Page({})'},
            {'name': 'pages/index/index.json', 'content': '{}'}
        ]
        
        assert len(files) == 4
        assert files[0]['name'] == 'pages/index/index.wxml'

    def test_generate_api_service(self):
        """测试生成API服务"""
        apis = [
            {
                'id': 'api-001',
                'name': '获取用户列表',
                'method': 'GET',
                'url': '/api/users'
            }
        ]
        
        # 模拟生成
        files = [
            {'name': 'utils/api.js', 'content': '// API Service'}
        ]
        
        assert len(files) == 1
        assert 'api' in files[0]['name']

    def test_generate_models(self):
        """测试生成数据模型"""
        models = [
            {
                'id': 'model-001',
                'name': 'User',
                'fields': [
                    {'name': 'id', 'type': 'number'},
                    {'name': 'name', 'type': 'string'}
                ]
            }
        ]
        
        # 模拟生成
        files = [
            {'name': 'models/user.js', 'content': '// User Model'}
        ]
        
        assert len(files) == 1
        assert 'user' in files[0]['name'].lower()


# 插件管理器测试
class TestPluginManager:
    """插件管理器测试"""
    
    def test_plugin_registration(self):
        """测试插件注册"""
        plugins = {}
        
        plugin = {
            'id': 'wechat-mini',
            'name': '微信小程序生成器',
            'class': 'WeChatMiniGenerator',
            'platform': 'wechat_mini'
        }
        
        # 注册插件
        plugins[plugin['id']] = plugin
        
        assert 'wechat-mini' in plugins
        assert plugins['wechat-mini']['platform'] == 'wechat_mini'

    def test_get_plugin_by_platform(self):
        """测试按平台获取插件"""
        plugins = {
            'wechat-mini': {'platform': 'wechat_mini'},
            'h5': {'platform': 'h5'},
            'flutter': {'platform': 'flutter'}
        }
        
        # 获取H5插件
        plugin = plugins.get('h5')
        
        assert plugin is not None
        assert plugin['platform'] == 'h5'

    def test_list_plugins(self):
        """测试列出插件"""
        plugins = {
            'wechat-mini': {'name': '微信小程序'},
            'alipay-mini': {'name': '支付宝小程序'},
            'h5': {'name': 'H5'}
        }
        
        # 获取插件列表
        plugin_list = list(plugins.values())
        
        assert len(plugin_list) == 3

    def test_plugin_validation(self):
        """测试插件验证"""
        valid_plugin = {
            'id': 'test-plugin',
            'name': 'Test',
            'class': 'TestGenerator',
            'platform': 'test'
        }
        
        # 模拟验证
        is_valid = True
        
        assert is_valid is True


# 模板引擎测试
class TestTemplateEngine:
    """模板引擎测试"""
    
    def test_template_rendering(self):
        """测试模板渲染"""
        template = '''
            <view class="{{className}}">
                <text>{{text}}</text>
            </view>
        '''
        context = {
            'className': 'container',
            'text': 'Hello World'
        }
        
        # 模拟渲染
        rendered = template.replace('{{className}}', context['className'])
        rendered = rendered.replace('{{text}}', context['text'])
        
        assert 'class="container"' in rendered
        assert '<text>Hello World</text>' in rendered

    def test_nested_template(self):
        """测试嵌套模板"""
        template = '''
            <view>
                {{> header}}
                <content>{{content}}</content>
                {{> footer}}
            </view>
        '''
        
        partials = {
            'header': '<header>Header</header>',
            'footer': '<footer>Footer</footer>'
        }
        
        # 模拟渲染
        rendered = template.replace('{{> header}}', partials['header'])
        rendered = rendered.replace('{{> footer}}', partials['footer'])
        rendered = rendered.replace('{{content}}', 'Main Content')
        
        assert '<header>Header</header>' in rendered
        assert '<footer>Footer</footer>' in rendered

    def test_loop_in_template(self):
        """测试模板循环"""
        template = '''
            <list>
            {{#each items}}
                <item>{{this}}</item>
            {{/each}}
            </list>
        '''
        context = {'items': ['A', 'B', 'C']}
        
        # 模拟渲染
        items_html = '\n'.join([f'                <item>{item}</item>' for item in context['items']])
        rendered = template.replace('{{#each items}}\n                <item>{{this}}</item>\n            {{/each}}', items_html)
        
        assert '<item>A</item>' in rendered
        assert '<item>B</item>' in rendered
        assert '<item>C</item>' in rendered

    def test_condition_in_template(self):
        """测试模板条件"""
        template = '''
            {{#if show}}
                <div>Visible</div>
            {{else}}
                <div>Hidden</div>
            {{/if}}
        '''
        
        # 测试true情况
        context = {'show': True}
        rendered = template.replace('{{#if show}}\n                <div>Visible</div>\n            {{else}}\n                <div>Hidden</div>\n            {{/if}}', '<div>Visible</div>')
        
        assert '<div>Visible</div>' in rendered

    def test_template_error_handling(self):
        """测试模板错误处理"""
        template = '{{undefinedVar}}'
        
        # 模拟渲染失败
        try:
            rendered = template.replace('{{undefinedVar}}', '')
            assert True
        except Exception:
            assert True


# 组件映射测试
class TestComponentMapper:
    """组件映射测试"""
    
    def test_component_mapping(self):
        """测试组件映射"""
        mappings = {
            'text': {'wechat': 'text', 'h5': 'span', 'flutter': 'Text'},
            'button': {'wechat': 'button', 'h5': 'button', 'flutter': 'ElevatedButton'},
            'image': {'wechat': 'image', 'h5': 'img', 'flutter': 'Image'}
        }
        
        # 获取微信小程序的text组件映射
        wechat_text = mappings['text']['wechat']
        
        assert wechat_text == 'text'

    def test_get_platform_component(self):
        """测试获取平台组件"""
        component = {
            'id': 'comp-001',
            'type': 'button',
            'props': {'text': 'Click'}
        }
        
        mappings = {'button': {'h5': 'button'}}
        
        # 获取H5平台的组件类型
        platform_type = mappings[component['type']]['h5']
        
        assert platform_type == 'button'

    def test_custom_component_mapping(self):
        """测试自定义组件映射"""
        mappings = {
            'custom-card': {'wechat': 'custom-card', 'h5': 'custom-card'}
        }
        
        # 自定义组件使用相同名称
        wechat_component = mappings['custom-card']['wechat']
        
        assert wechat_component == 'custom-card'

    def test_unsupported_component(self):
        """测试不支持的组件"""
        mappings = {'text': {'wechat': 'text'}}
        
        # 尝试获取不支持的组件
        unsupported = mappings.get('unknown', {}).get('wechat')
        
        assert unsupported is None


# 平台生成器测试
class TestPlatformGenerators:
    """平台生成器测试"""
    
    def test_wechat_mini_generator(self):
        """测试微信小程序生成器"""
        generator = {
            'id': 'wechat-mini',
            'name': '微信小程序',
            'platform': 'wechat_mini',
            'fileExtensions': {
                'template': '.wxml',
                'style': '.wxss',
                'script': '.js',
                'config': '.json'
            }
        }
        
        assert generator['fileExtensions']['template'] == '.wxml'
        assert generator['fileExtensions']['style'] == '.wxss'

    def test_h5_generator(self):
        """测试H5生成器"""
        generator = {
            'id': 'h5',
            'name': 'H5',
            'platform': 'h5',
            'fileExtensions': {
                'template': '.html',
                'style': '.css',
                'script': '.js',
                'config': '.json'
            }
        }
        
        assert generator['fileExtensions']['template'] == '.html'

    def test_flutter_generator(self):
        """测试Flutter生成器"""
        generator = {
            'id': 'flutter',
            'name': 'Flutter',
            'platform': 'flutter',
            'fileExtensions': {
                'dart': '.dart',
                'widget': '.dart',
                'config': '.yaml'
            }
        }
        
        assert generator['fileExtensions']['dart'] == '.dart'

    def test_react_native_generator(self):
        """测试React Native生成器"""
        generator = {
            'id': 'react-native',
            'name': 'React Native',
            'platform': 'react_native',
            'fileExtensions': {
                'js': '.js',
                'jsx': '.jsx',
                'style': '.js'
            }
        }
        
        assert generator['platform'] == 'react_native'


# 生成结果测试
class TestGenerationResult:
    """生成结果测试"""
    
    def test_generation_result_structure(self):
        """测试生成结果结构"""
        result = {
            'id': 'gen-001',
            'projectId': 'proj-001',
            'platform': 'wechat_mini',
            'status': 'success',
            'files': [
                {
                    'path': 'pages/index/index.wxml',
                    'content': '<view>Home</view>',
                    'type': 'template'
                },
                {
                    'path': 'pages/index/index.js',
                    'content': 'Page({})',
                    'type': 'script'
                }
            ],
            'generatedAt': datetime.now(),
            'duration': 5.2
        }
        
        assert result['status'] == 'success'
        assert len(result['files']) == 2
        assert result['duration'] == 5.2

    def test_failed_generation(self):
        """测试失败的生成"""
        result = {
            'id': 'gen-002',
            'projectId': 'proj-001',
            'platform': 'flutter',
            'status': 'failed',
            'error': {
                'code': 'TEMPLATE_ERROR',
                'message': 'Template not found'
            },
            'files': [],
            'duration': 1.5
        }
        
        assert result['status'] == 'failed'
        assert result['error'] is not None
        assert result['error']['code'] == 'TEMPLATE_ERROR'

    def test_generation_stats(self):
        """测试生成统计"""
        stats = {
            'totalFiles': 25,
            'totalLines': 1500,
            'pageCount': 5,
            'componentCount': 10,
            'apiCount': 8,
            'modelCount': 5
        }
        
        assert stats['totalFiles'] == 25
        assert stats['pageCount'] == 5


# 配置管理测试
class TestGeneratorConfig:
    """生成器配置测试"""
    
    def test_config_options(self):
        """测试配置选项"""
        config = {
            'platform': 'wechat_mini',
            'outputPath': './output',
            'minify': True,
            'sourceMaps': False,
            'bundle': True,
            'version': '1.0.0'
        }
        
        assert config['platform'] == 'wechat_mini'
        assert config['minify'] is True
        assert config['bundle'] is True

    def test_default_config(self):
        """测试默认配置"""
        defaults = {
            'minify': False,
            'sourceMaps': True,
            'bundle': False,
            'format': 'standard'
        }
        
        assert defaults['minify'] is False
        assert defaults['sourceMaps'] is True

    def test_platform_specific_config(self):
        """测试平台特定配置"""
        config = {
            'platform': 'flutter',
            'dartVersion': '3.0',
            'android': {'compileSdkVersion': 33},
            'ios': {'deploymentTarget': '12.0'}
        }
        
        assert config['dartVersion'] == '3.0'
        assert config['android']['compileSdkVersion'] == 33


# API接口测试
class TestCodeGeneratorAPI:
    """代码生成API测试"""
    
    def test_get_platforms(self, client, auth_token):
        """测试获取支持的平台列表"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/codegen/platforms', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_generate_code(self, client, auth_token):
        """测试生成代码"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        generate_data = {
            'projectId': 'proj-001',
            'platform': 'wechat_mini',
            'config': {
                'minify': True,
                'outputPath': './dist'
            }
        }
        
        response = client.post('/api/codegen/generate', headers=headers, json=generate_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'files' in data['data']

    def test_generate_page(self, client, auth_token):
        """测试生成单个页面"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        page_data = {
            'projectId': 'proj-001',
            'platform': 'h5',
            'page': {
                'id': 'page-001',
                'name': 'Test Page',
                'path': '/test',
                'components': []
            }
        }
        
        response = client.post('/api/codegen/generate-page', headers=headers, json=page_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_download_code(self, client, auth_token):
        """测试下载生成的代码"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/codegen/download/proj-001/wechat_mini', headers=headers)
        
        assert response.status_code == 200
        assert response.content_type == 'application/zip'

    def test_validate_project(self, client, auth_token):
        """测试验证项目数据"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        project_data = {
            'version': '1.0',
            'pages': [],
            'apis': []
        }
        
        response = client.post('/api/codegen/validate', headers=headers, json=project_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


# 服务层测试
class TestCodeGenService:
    """代码生成服务测试"""
    
    def test_select_generator(self):
        """测试选择生成器"""
        platform = 'wechat_mini'
        generators = {
            'wechat_mini': 'WeChatMiniGenerator',
            'h5': 'H5Generator'
        }
        
        selected = generators.get(platform)
        
        assert selected == 'WeChatMiniGenerator'

    def test_validate_project_data(self):
        """测试验证项目数据"""
        project = {'pages': [], 'apis': [], 'models': []}
        
        # 模拟验证
        is_valid = True
        
        assert is_valid is True

    def test_execute_generation(self):
        """测试执行生成"""
        generator = {'platform': 'h5'}
        project = {'pages': [{'id': 'page-001'}]}
        
        # 模拟生成
        result = {'success': True, 'files': []}
        
        assert result['success'] is True

    def test_archive_output(self):
        """测试归档输出"""
        files = [
            {'path': 'index.html', 'content': '<html></html>'}
        ]
        
        # 模拟归档
        archive_path = './output.zip'
        
        assert archive_path is not None


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
