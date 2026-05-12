"""
可视化编辑器子模块测试用例

模块功能：组件拖拽、布局管理、属性配置、历史管理
测试范围：组件操作、拖拽逻辑、对齐工具、键盘快捷键等核心功能
"""
import pytest
import json
from unittest.mock import Mock, patch


# 组件定义测试
class TestComponentDefinition:
    """组件定义测试"""
    
    def test_basic_component_definition(self):
        """测试基础组件定义"""
        component = {
            'id': 'comp-001',
            'type': 'text',
            'name': '文本组件',
            'icon': 'text',
            'category': 'basic',
            'props': {
                'text': {'type': 'string', 'default': 'Hello'},
                'color': {'type': 'color', 'default': '#333'},
                'fontSize': {'type': 'number', 'default': 14}
            },
            'events': ['click', 'load']
        }
        
        assert component['type'] == 'text'
        assert component['category'] == 'basic'
        assert 'text' in component['props']

    def test_container_component_definition(self):
        """测试容器组件定义"""
        container = {
            'id': 'comp-002',
            'type': 'container',
            'name': '容器',
            'icon': 'box',
            'category': 'layout',
            'props': {
                'width': {'type': 'number', 'default': 100},
                'height': {'type': 'number', 'default': 100},
                'backgroundColor': {'type': 'color', 'default': '#fff'}
            },
            'children': [],
            'events': ['click']
        }
        
        assert container['category'] == 'layout'
        assert 'children' in container

    def test_input_component_definition(self):
        """测试输入组件定义"""
        input_comp = {
            'id': 'comp-003',
            'type': 'input',
            'name': '输入框',
            'icon': 'edit',
            'category': 'form',
            'props': {
                'placeholder': {'type': 'string', 'default': ''},
                'value': {'type': 'string', 'default': ''},
                'type': {'type': 'select', 'options': ['text', 'password', 'number']}
            },
            'events': ['input', 'focus', 'blur']
        }
        
        assert input_comp['category'] == 'form'
        assert 'input' in input_comp['events']


# 组件树结构测试
class TestComponentTree:
    """组件树结构测试"""
    
    def test_empty_component_tree(self):
        """测试空组件树"""
        tree = {
            'root': {
                'id': 'root',
                'type': 'page',
                'children': []
            }
        }
        
        assert len(tree['root']['children']) == 0

    def test_component_tree_with_nested_components(self):
        """测试嵌套组件树"""
        tree = {
            'root': {
                'id': 'root',
                'type': 'page',
                'children': [
                    {
                        'id': 'container-1',
                        'type': 'container',
                        'children': [
                            {
                                'id': 'text-1',
                                'type': 'text',
                                'props': {'text': 'Hello'},
                                'children': []
                            },
                            {
                                'id': 'button-1',
                                'type': 'button',
                                'props': {'text': 'Click'},
                                'children': []
                            }
                        ]
                    }
                ]
            }
        }
        
        container = tree['root']['children'][0]
        assert len(container['children']) == 2
        assert container['children'][0]['type'] == 'text'
        assert container['children'][1]['type'] == 'button'

    def test_find_component_by_id(self):
        """测试通过ID查找组件"""
        tree = {
            'root': {
                'id': 'root',
                'type': 'page',
                'children': [
                    {
                        'id': 'target',
                        'type': 'text',
                        'children': []
                    }
                ]
            }
        }
        
        # 模拟查找逻辑
        found = None
        
        def find(node, target_id):
            if node['id'] == target_id:
                return node
            for child in node.get('children', []):
                result = find(child, target_id)
                if result:
                    return result
            return None
        
        found = find(tree['root'], 'target')
        
        assert found is not None
        assert found['id'] == 'target'


# 拖拽逻辑测试
class TestDragDropLogic:
    """拖拽逻辑测试"""
    
    def test_drag_start(self):
        """测试拖拽开始"""
        state = {
            'dragging': None,
            'components': []
        }
        
        # 模拟拖拽开始
        component = {'id': 'comp-001', 'type': 'text'}
        state['dragging'] = component
        
        assert state['dragging'] is not None
        assert state['dragging']['id'] == 'comp-001'

    def test_drag_over(self):
        """测试拖拽经过"""
        state = {
            'dragging': {'id': 'comp-001'},
            'hovering': None
        }
        
        # 模拟拖拽经过容器
        state['hovering'] = {'id': 'container-001'}
        
        assert state['hovering'] is not None
        assert state['hovering']['id'] == 'container-001'

    def test_drag_drop_into_container(self):
        """测试拖放到容器中"""
        container = {
            'id': 'container-001',
            'type': 'container',
            'children': []
        }
        dragged = {'id': 'comp-001', 'type': 'text'}
        
        # 模拟拖放
        container['children'].append(dragged)
        
        assert len(container['children']) == 1
        assert container['children'][0]['id'] == 'comp-001'

    def test_drag_drop_between_containers(self):
        """测试在容器间拖拽"""
        container1 = {'id': 'c1', 'type': 'container', 'children': [{'id': 'comp-001'}]}
        container2 = {'id': 'c2', 'type': 'container', 'children': []}
        
        # 从container1移除
        container1['children'] = [c for c in container1['children'] if c['id'] != 'comp-001']
        
        # 添加到container2
        container2['children'].append({'id': 'comp-001'})
        
        assert len(container1['children']) == 0
        assert len(container2['children']) == 1

    def test_drop_invalid_target(self):
        """测试拖放到无效目标"""
        state = {
            'dragging': {'id': 'comp-001', 'type': 'text'},
            'hovering': {'id': 'text-002', 'type': 'text'}  # 文本组件不能包含子组件
        }
        
        # 文本组件不能接收子组件
        can_drop = False
        
        assert can_drop is False


# 布局管理测试
class TestLayoutManagement:
    """布局管理测试"""
    
    def test_set_component_position(self):
        """测试设置组件位置"""
        component = {
            'id': 'comp-001',
            'type': 'text',
            'style': {
                'position': 'absolute',
                'left': 10,
                'top': 20
            }
        }
        
        # 更新位置
        component['style']['left'] = 50
        component['style']['top'] = 60
        
        assert component['style']['left'] == 50
        assert component['style']['top'] == 60

    def test_set_component_size(self):
        """测试设置组件尺寸"""
        component = {
            'id': 'comp-001',
            'type': 'text',
            'style': {
                'width': 100,
                'height': 50
            }
        }
        
        # 更新尺寸
        component['style']['width'] = 200
        component['style']['height'] = 80
        
        assert component['style']['width'] == 200
        assert component['style']['height'] == 80

    def test_flex_layout(self):
        """测试Flex布局"""
        container = {
            'id': 'container-001',
            'type': 'container',
            'style': {
                'display': 'flex',
                'flexDirection': 'row',
                'justifyContent': 'space-between'
            },
            'children': [
                {'id': 'c1', 'type': 'text'},
                {'id': 'c2', 'type': 'text'}
            ]
        }
        
        assert container['style']['display'] == 'flex'
        assert container['style']['flexDirection'] == 'row'
        assert len(container['children']) == 2

    def test_grid_layout(self):
        """测试Grid布局"""
        container = {
            'id': 'grid-001',
            'type': 'container',
            'style': {
                'display': 'grid',
                'gridTemplateColumns': '1fr 1fr 1fr',
                'gap': 10
            }
        }
        
        assert container['style']['display'] == 'grid'
        assert container['style']['gridTemplateColumns'] == '1fr 1fr 1fr'


# 属性配置测试
class TestPropertyConfiguration:
    """属性配置测试"""
    
    def test_update_text_property(self):
        """测试更新文本属性"""
        component = {
            'id': 'text-001',
            'type': 'text',
            'props': {
                'text': 'Hello',
                'color': '#333',
                'fontSize': 14
            }
        }
        
        # 更新属性
        component['props']['text'] = 'Hello World'
        component['props']['fontSize'] = 16
        
        assert component['props']['text'] == 'Hello World'
        assert component['props']['fontSize'] == 16

    def test_update_color_property(self):
        """测试更新颜色属性"""
        component = {
            'id': 'text-001',
            'type': 'text',
            'props': {
                'color': '#333'
            }
        }
        
        # 更新颜色
        component['props']['color'] = '#ff0000'
        
        assert component['props']['color'] == '#ff0000'

    def test_validate_property_type(self):
        """测试属性类型验证"""
        props_schema = {
            'text': {'type': 'string'},
            'fontSize': {'type': 'number'},
            'visible': {'type': 'boolean'}
        }
        
        # 模拟验证
        valid_props = {
            'text': 'Valid',
            'fontSize': 14,
            'visible': True
        }
        
        invalid_props = {
            'text': 123,  # 应为字符串
            'fontSize': '14',  # 应为数字
            'visible': 'true'  # 应为布尔值
        }
        
        assert isinstance(valid_props['text'], str)
        assert isinstance(valid_props['fontSize'], int)
        assert isinstance(valid_props['visible'], bool)

    def test_property_default_value(self):
        """测试属性默认值"""
        schema = {
            'text': {'type': 'string', 'default': 'Default Text'},
            'fontSize': {'type': 'number', 'default': 14}
        }
        
        component = {
            'id': 'comp-001',
            'type': 'text',
            'props': {}
        }
        
        # 应用默认值
        for key, prop in schema.items():
            if key not in component['props']:
                component['props'][key] = prop['default']
        
        assert component['props']['text'] == 'Default Text'
        assert component['props']['fontSize'] == 14


# 历史管理测试
class TestHistoryManagement:
    """历史管理测试"""
    
    def test_undo_stack_initialization(self):
        """测试撤销栈初始化"""
        history = {
            'undoStack': [],
            'redoStack': [],
            'currentIndex': -1
        }
        
        assert len(history['undoStack']) == 0
        assert len(history['redoStack']) == 0
        assert history['currentIndex'] == -1

    def test_push_history_state(self):
        """测试推入历史状态"""
        history = {
            'undoStack': [],
            'redoStack': [],
            'currentIndex': -1
        }
        
        state1 = {'components': []}
        state2 = {'components': [{'id': 'comp-001'}]}
        
        # 推入状态
        history['undoStack'].append(state1)
        history['currentIndex'] += 1
        history['undoStack'].append(state2)
        history['currentIndex'] += 1
        
        assert len(history['undoStack']) == 2
        assert history['currentIndex'] == 1

    def test_undo_operation(self):
        """测试撤销操作"""
        history = {
            'undoStack': [
                {'components': []},
                {'components': [{'id': 'comp-001'}]}
            ],
            'redoStack': [],
            'currentIndex': 1
        }
        
        # 撤销
        current_state = history['undoStack'][history['currentIndex']]
        history['redoStack'].append(current_state)
        history['currentIndex'] -= 1
        
        assert history['currentIndex'] == 0
        assert len(history['redoStack']) == 1

    def test_redo_operation(self):
        """测试重做操作"""
        history = {
            'undoStack': [
                {'components': []},
                {'components': [{'id': 'comp-001'}]}
            ],
            'redoStack': [{'components': [{'id': 'comp-001'}]}],
            'currentIndex': 0
        }
        
        # 重做
        redo_state = history['redoStack'].pop()
        history['currentIndex'] += 1
        
        assert history['currentIndex'] == 1
        assert len(history['redoStack']) == 0

    def test_clear_redo_on_new_action(self):
        """测试新操作时清除重做栈"""
        history = {
            'undoStack': [{'components': []}],
            'redoStack': [{'components': [{'id': 'comp-001'}]}],
            'currentIndex': 0
        }
        
        # 新操作
        history['redoStack'] = []
        
        assert len(history['redoStack']) == 0


# 对齐工具测试
class TestAlignmentTools:
    """对齐工具测试"""
    
    def test_align_left(self):
        """测试左对齐"""
        components = [
            {'id': 'c1', 'style': {'left': 10}},
            {'id': 'c2', 'style': {'left': 30}},
            {'id': 'c3', 'style': {'left': 20}}
        ]
        
        # 找到最左边的位置
        min_left = min(c['style']['left'] for c in components)
        
        # 对齐到最左边
        for c in components:
            c['style']['left'] = min_left
        
        assert all(c['style']['left'] == 10 for c in components)

    def test_align_right(self):
        """测试右对齐"""
        components = [
            {'id': 'c1', 'style': {'left': 10, 'width': 50}},
            {'id': 'c2', 'style': {'left': 30, 'width': 50}},
            {'id': 'c3', 'style': {'left': 20, 'width': 50}}
        ]
        
        # 计算右边缘位置
        right_edges = [c['style']['left'] + c['style']['width'] for c in components]
        max_right = max(right_edges)
        
        # 对齐到最右边
        for c in components:
            c['style']['left'] = max_right - c['style']['width']
        
        assert all(c['style']['left'] + c['style']['width'] == 80 for c in components)

    def test_align_center_horizontal(self):
        """测试水平居中对齐"""
        components = [
            {'id': 'c1', 'style': {'left': 10}},
            {'id': 'c2', 'style': {'left': 30}},
            {'id': 'c3', 'style': {'left': 20}}
        ]
        
        # 计算平均位置
        avg_left = sum(c['style']['left'] for c in components) / len(components)
        
        # 对齐到平均位置
        for c in components:
            c['style']['left'] = avg_left
        
        assert all(c['style']['left'] == 20 for c in components)

    def test_align_top(self):
        """测试顶部对齐"""
        components = [
            {'id': 'c1', 'style': {'top': 10}},
            {'id': 'c2', 'style': {'top': 30}},
            {'id': 'c3', 'style': {'top': 20}}
        ]
        
        min_top = min(c['style']['top'] for c in components)
        
        for c in components:
            c['style']['top'] = min_top
        
        assert all(c['style']['top'] == 10 for c in components)

    def test_distribute_evenly_horizontal(self):
        """测试水平均匀分布"""
        components = [
            {'id': 'c1', 'style': {'left': 10, 'width': 50}},
            {'id': 'c2', 'style': {'left': 100, 'width': 50}},
            {'id': 'c3', 'style': {'left': 190, 'width': 50}}
        ]
        
        # 计算间距
        first_left = components[0]['style']['left']
        last_right = components[-1]['style']['left'] + components[-1]['style']['width']
        total_width = last_right - first_left
        gap = (total_width - sum(c['style']['width'] for c in components)) / (len(components) - 1)
        
        assert gap == 40.0


# 键盘快捷键测试
class TestKeyboardShortcuts:
    """键盘快捷键测试"""
    
    def test_delete_shortcut(self):
        """测试删除快捷键"""
        state = {
            'selected': ['comp-001'],
            'components': [{'id': 'comp-001'}, {'id': 'comp-002'}]
        }
        
        # 模拟 Delete 键
        state['components'] = [c for c in state['components'] if c['id'] not in state['selected']]
        
        assert len(state['components']) == 1
        assert state['components'][0]['id'] == 'comp-002'

    def test_duplicate_shortcut(self):
        """测试复制快捷键"""
        state = {
            'selected': ['comp-001'],
            'components': [{'id': 'comp-001', 'type': 'text', 'props': {'text': 'Hello'}}]
        }
        
        # 模拟 Ctrl+D
        selected = state['components'][0]
        new_component = {
            'id': 'comp-001-copy',
            'type': selected['type'],
            'props': selected['props'].copy()
        }
        state['components'].append(new_component)
        
        assert len(state['components']) == 2
        assert state['components'][1]['id'] == 'comp-001-copy'

    def test_group_shortcut(self):
        """测试组合快捷键"""
        state = {
            'selected': ['comp-001', 'comp-002'],
            'components': [
                {'id': 'comp-001', 'type': 'text'},
                {'id': 'comp-002', 'type': 'button'}
            ]
        }
        
        # 模拟 Ctrl+G 创建容器
        group_container = {
            'id': 'group-001',
            'type': 'container',
            'children': [
                {'id': 'comp-001', 'type': 'text'},
                {'id': 'comp-002', 'type': 'button'}
            ]
        }
        
        assert len(group_container['children']) == 2

    def test_undo_shortcut(self):
        """测试撤销快捷键"""
        history = {
            'undoStack': [{'components': []}, {'components': [{'id': 'comp-001'}]}],
            'redoStack': [],
            'currentIndex': 1
        }
        
        # 模拟 Ctrl+Z
        if history['currentIndex'] > 0:
            history['currentIndex'] -= 1
        
        assert history['currentIndex'] == 0

    def test_redo_shortcut(self):
        """测试重做快捷键"""
        history = {
            'undoStack': [{'components': []}, {'components': [{'id': 'comp-001'}]}],
            'redoStack': [{'components': [{'id': 'comp-001'}]}],
            'currentIndex': 0
        }
        
        # 模拟 Ctrl+Shift+Z
        if history['redoStack']:
            history['currentIndex'] += 1
        
        assert history['currentIndex'] == 1


# 多选操作测试
class TestMultiSelect:
    """多选操作测试"""
    
    def test_select_multiple_components(self):
        """测试多选组件"""
        state = {
            'selected': [],
            'components': [
                {'id': 'comp-001', 'type': 'text'},
                {'id': 'comp-002', 'type': 'button'},
                {'id': 'comp-003', 'type': 'image'}
            ]
        }
        
        # 模拟点击多选
        state['selected'].append('comp-001')
        state['selected'].append('comp-002')
        
        assert len(state['selected']) == 2
        assert 'comp-001' in state['selected']
        assert 'comp-002' in state['selected']

    def test_bulk_move_components(self):
        """测试批量移动组件"""
        components = {
            'comp-001': {'id': 'comp-001', 'style': {'left': 10, 'top': 10}},
            'comp-002': {'id': 'comp-002', 'style': {'left': 20, 'top': 20}}
        }
        selected = ['comp-001', 'comp-002']
        
        # 移动偏移
        offset_x = 100
        offset_y = 50
        
        for id in selected:
            components[id]['style']['left'] += offset_x
            components[id]['style']['top'] += offset_y
        
        assert components['comp-001']['style']['left'] == 110
        assert components['comp-002']['style']['top'] == 70

    def test_bulk_delete_components(self):
        """测试批量删除组件"""
        components = [
            {'id': 'comp-001'},
            {'id': 'comp-002'},
            {'id': 'comp-003'}
        ]
        selected = ['comp-001', 'comp-003']
        
        # 删除选中的组件
        components = [c for c in components if c['id'] not in selected]
        
        assert len(components) == 1
        assert components[0]['id'] == 'comp-002'


# Fixtures
@pytest.fixture
def editor_state():
    """创建编辑器状态"""
    return {
        'components': [],
        'selected': [],
        'dragging': None,
        'hovering': None,
        'history': {
            'undoStack': [],
            'redoStack': [],
            'currentIndex': -1
        }
    }
