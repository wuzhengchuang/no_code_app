# 子模块 06: App预览子模块设计文档

## 概述

负责实时预览、交互模拟、真实接口调用。提供多设备预览模式，支持实时同步编辑器变更，提供隔离的预览环境。

## 目录结构

```
preview/
├── frontend/
│   ├── src/
│   │   ├── preview/
│   │   │   ├── engine/
│   │   │   │   ├── PreviewEngine.ts      # 预览引擎核心
│   │   │   │   ├── ExpressionEvaluator.ts # 表达式求值器
│   │   │   │   ├── ActionExecutor.ts      # 动作执行器
│   │   │   │   └── ComponentRenderer.ts   # 组件渲染器
│   │   │   ├── bridge/
│   │   │   │   └── PreviewBridge.ts       # 编辑器-预览通信桥
│   │   │   ├── components/
│   │   │   │   ├── PreviewApp.vue         # 预览应用根组件
│   │   │   │   ├── PreviewPage.vue        # 页面渲染组件
│   │   │   │   └── preview-components/    # 预览组件库
│   │   │   │       ├── ButtonPreview.vue
│   │   │   │       ├── TextPreview.vue
│   │   │   │       ├── InputPreview.vue
│   │   │   │       ├── ImagePreview.vue
│   │   │   │       ├── ListPreview.vue
│   │   │   │       └── ...
│   │   │   └── main.ts                    # 预览入口
│   │   ├── views/
│   │   │   └── PreviewView.vue            # 预览视图
│   │   └── components/
│   │       ├── preview/
│   │       │   ├── PreviewToolbar.vue     # 预览工具栏
│   │       │   ├── DeviceSelector.vue     # 设备选择器
│   │       │   ├── RefreshButton.vue      # 刷新按钮
│   │       │   ├── ZoomControl.vue        # 缩放控制
│   │       │   ├── PreviewIFrame.vue      # 预览容器
│   │       │   └── PreviewUrlBar.vue      # 预览地址栏
│   │       └── ...
│   ├── package.json
│   └── vite.config.preview.ts             # 预览构建配置
├── server/
│   ├── src/
│   │   ├── server.ts                      # Express服务器入口
│   │   ├── proxy.ts                       # API代理
│   │   ├── preview-routes.ts              # 预览路由
│   │   └── cors.ts                        # CORS配置
│   ├── package.json
│   └── tsconfig.json
└── __init__.py
```

## 数据模型

### 预览配置

| 字段 | 类型 | 说明 |
|------|------|------|
| projectId | string | 项目ID |
| deviceType | DeviceType | 设备类型 |
| scale | number | 缩放比例 |
| enableHotReload | boolean | 启用热重载 |
| enableConsole | boolean | 启用控制台 |

### 设备类型

```typescript
type DeviceType =
  | 'mobile'        // iPhone 375x667
  | 'mobile-large'  // iPhone Plus 414x896
  | 'tablet'        // iPad 768x1024
  | 'tablet-large'  // iPad Pro 1024x1366
  | 'desktop'       // 桌面 1280x720
  | 'desktop-hd'    // 桌面高清 1920x1080
  | 'wechat-miniapp' // 微信小程序
  | 'custom'        // 自定义尺寸
```

### 设备配置

```typescript
interface DeviceConfig {
  type: DeviceType
  name: string
  width: number
  height: number
  devicePixelRatio: number
  userAgent?: string
  isTouch?: boolean
  isMobile?: boolean
  icon?: string
}

const DEVICES: Record<DeviceType, DeviceConfig> = {
  'mobile': {
    type: 'mobile',
    name: 'iPhone 12',
    width: 375,
    height: 667,
    devicePixelRatio: 2,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    isTouch: true,
    isMobile: true
  },
  'mobile-large': {
    type: 'mobile-large',
    name: 'iPhone 14 Pro Max',
    width: 430,
    height: 932,
    devicePixelRatio: 3,
    isTouch: true,
    isMobile: true
  },
  'tablet': {
    type: 'tablet',
    name: 'iPad 9',
    width: 768,
    height: 1024,
    devicePixelRatio: 2,
    isTouch: true,
    isMobile: false
  },
  'tablet-large': {
    type: 'tablet-large',
    name: 'iPad Pro 12.9',
    width: 1024,
    height: 1366,
    devicePixelRatio: 2,
    isTouch: true,
    isMobile: false
  },
  'desktop': {
    type: 'desktop',
    name: 'Desktop HD',
    width: 1280,
    height: 720,
    devicePixelRatio: 1,
    isTouch: false,
    isMobile: false
  },
  'desktop-hd': {
    type: 'desktop-hd',
    name: 'Desktop Full HD',
    width: 1920,
    height: 1080,
    devicePixelRatio: 1,
    isTouch: false,
    isMobile: false
  },
  'wechat-miniapp': {
    type: 'wechat-miniapp',
    name: '微信小程序',
    width: 375,
    height: 667,
    devicePixelRatio: 2,
    isTouch: true,
    isMobile: true
  },
  'custom': {
    type: 'custom',
    name: '自定义',
    width: 375,
    height: 667,
    devicePixelRatio: 2
  }
}
```

## 预览引擎核心

```typescript
// src/preview/engine/PreviewEngine.ts
import { reactive, computed } from 'vue'
import type { Project, Page, ComponentInstance, EventBinding, Action, ApiConfig } from '../../types'
import { ExpressionEvaluator } from './ExpressionEvaluator'
import { ActionExecutor } from './ActionExecutor'
import { ComponentRenderer } from './ComponentRenderer'

export interface PreviewState {
  currentPageId: string | null
  pageStates: Record<string, Record<string, any>>
  globalState: Record<string, any>
  storage: Record<string, any>
  apiResponses: Record<string, any>
  apiLoading: Record<string, boolean>
  loadingCount: number
  componentStates: Record<string, any>
  logs: PreviewLog[]
}

export interface PreviewLog {
  id: string
  timestamp: number
  type: 'info' | 'warn' | 'error' | 'log'
  message: string
  data?: any
}

export class PreviewEngine {
  private _project: Project | null = null
  private _state: PreviewState
  private _evaluator: ExpressionEvaluator
  private _actionExecutor: ActionExecutor
  private _componentRenderer: ComponentRenderer
  private _listeners: Set<() => void> = new Set()
  private _initialized = false

  constructor() {
    this._state = reactive({
      currentPageId: null,
      pageStates: {},
      globalState: {},
      storage: {},
      apiResponses: {},
      apiLoading: {},
      loadingCount: 0,
      componentStates: {},
      logs: []
    })

    this._evaluator = new ExpressionEvaluator(this)
    this._actionExecutor = new ActionExecutor(this)
    this._componentRenderer = new ComponentRenderer(this)
  }

  get project(): Project | null {
    return this._project
  }

  get state(): Readonly<PreviewState> {
    return this._state
  }

  get currentPage(): Page | null {
    if (!this._project || !this._state.currentPageId) return null
    return this._project.pages?.find(p => p.id === this._state.currentPageId) || null
  }

  get isInitialized(): boolean {
    return this._initialized
  }

  subscribe(listener: () => void): () => void {
    this._listeners.add(listener)
    return () => this._listeners.delete(listener)
  }

  private notify(): void {
    this._listeners.forEach(l => l())
  }

  async loadProject(project: Project): Promise<void> {
    this._project = project
    this._state.pageStates = {}
    this._state.apiResponses = {}
    this._state.componentStates = {}

    const homePage = project.pages?.find(p => p.isHome)
    if (homePage) {
      await this.loadPage(homePage.id)
    }

    this._initialized = true
    this.notify()
  }

  async loadPage(pageId: string, params: Record<string, any> = {}): Promise<void> {
    if (!this._project) return

    const page = this._project.pages?.find(p => p.id === pageId)
    if (!page) {
      this._addLog('warn', `页面不存在: ${pageId}`)
      return
    }

    this._state.currentPageId = pageId

    if (!this._state.pageStates[pageId]) {
      const initialState: Record<string, any> = {}
      for (const stateDef of page.states || []) {
        initialState[stateDef.name] = stateDef.defaultValue
      }
      this._state.pageStates[pageId] = initialState
    }

    this._state.componentStates = {}
    if (page.components) {
      for (const comp of page.components) {
        this._state.componentStates[comp.id] = {
          value: comp.props.value,
          ...comp.props
        }
      }
    }

    this._addLog('info', `加载页面: ${page.name}`, params)

    await this.triggerEvent(pageId, 'load', params)

    this.notify()
  }

  async triggerEvent(
    targetId: string,
    eventName: string,
    eventData: any = {}
  ): Promise<void> {
    if (!this._project) return

    const bindings = (this._project.eventBindings || []).filter(b => {
      const targetMatch = b.componentId === targetId || b.pageId === targetId
      const eventMatch = b.eventName === eventName
      return targetMatch && eventMatch
    })

    const sortedBindings = bindings.sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))

    for (const binding of sortedBindings) {
      try {
        await this._actionExecutor.executeActions(binding.actions, eventData)
      } catch (err) {
        this._addLog('error', `执行动作失败`, err)
      }
    }
  }

  async callApi(apiId: string, params: Record<string, any> = {}): Promise<any> {
    if (!this._project) throw new Error('项目未加载')

    const api = this._project.apis?.find(a => a.id === apiId)
    if (!api) throw new Error(`API不存在: ${apiId}`)

    this._state.apiLoading[apiId] = true
    this._state.loadingCount++
    this.notify()

    try {
      const url = this._evaluator.interpolateUrl(api.url, params)
      const headers = this._evaluator.evalHeaders(api.headers || {}, params)
      const body = api.method !== 'GET' ? JSON.stringify(params) : undefined

      const response = await fetch('/api/preview/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, method: api.method, headers, body })
      })

      const data = await response.json()
      this._state.apiResponses[apiId] = data
      this._addLog('info', `API调用成功: ${api.name}`, data)
      return data
    } catch (err) {
      this._addLog('error', `API调用失败: ${api.name}`, err)
      throw err
    } finally {
      this._state.apiLoading[apiId] = false
      this._state.loadingCount = Math.max(0, this._state.loadingCount - 1)
      this.notify()
    }
  }

  navigate(pageId: string, params: Record<string, any> = {}, replace = false): void {
    this.loadPage(pageId, params)
  }

  setGlobalState(key: string, value: any): void {
    this._state.globalState[key] = value
    this.notify()
  }

  getGlobalState(key: string): any {
    return this._state.globalState[key]
  }

  setPageState(key: string, value: any): void {
    if (!this._state.currentPageId) return
    this._state.pageStates[this._state.currentPageId][key] = value
    this.notify()
  }

  getPageState(key: string): any {
    if (!this._state.currentPageId) return undefined
    return this._state.pageStates[this._state.currentPageId][key]
  }

  setComponentState(componentId: string, key: string, value: any): void {
    if (!this._state.componentStates[componentId]) {
      this._state.componentStates[componentId] = {}
    }
    this._state.componentStates[componentId][key] = value
    this.notify()
  }

  getComponentState(componentId: string, key: string): any {
    return this._state.componentStates[componentId]?.[key]
  }

  setStorage(key: string, value: any): void {
    this._state.storage[key] = value
    localStorage.setItem(`preview_${key}`, JSON.stringify(value))
    this.notify()
  }

  getStorage(key: string): any {
    if (key in this._state.storage) {
      return this._state.storage[key]
    }
    const stored = localStorage.getItem(`preview_${key}`)
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  }

  showLoading(): void {
    this._state.loadingCount++
    this.notify()
  }

  hideLoading(): void {
    this._state.loadingCount = Math.max(0, this._state.loadingCount - 1)
    this.notify()
  }

  getComponentValues(): Record<string, any> {
    const result: Record<string, any> = {}
    for (const [id, state] of Object.entries(this._state.componentStates)) {
      result[id] = state
    }
    return result
  }

  getEvaluator(): ExpressionEvaluator {
    return this._evaluator
  }

  private _addLog(type: PreviewLog['type'], message: string, data?: any): void {
    this._state.logs.push({
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      type,
      message,
      data
    })
    if (this._state.logs.length > 100) {
      this._state.logs.shift()
    }
  }

  clearLogs(): void {
    this._state.logs = []
    this.notify()
  }
}
```

## 表达式求值器

```typescript
// src/preview/engine/ExpressionEvaluator.ts
import type { PreviewEngine } from './PreviewEngine'

export class ExpressionEvaluator {
  private engine: PreviewEngine

  constructor(engine: PreviewEngine) {
    this.engine = engine
  }

  eval(expression: string, context: Record<string, any> = {}): any {
    if (!expression || typeof expression !== 'string') {
      return expression
    }

    if (expression.startsWith('{{') && expression.endsWith('}}')) {
      expression = expression.slice(2, -2).trim()
    }

    const fullContext = this._buildContext(context)

    try {
      const func = new Function(...Object.keys(fullContext), `return ${expression}`)
      return func(...Object.values(fullContext))
    } catch (err) {
      console.warn('表达式求值失败:', expression, err)
      return undefined
    }
  }

  evalString(template: string, context: Record<string, any> = {}): string {
    if (!template || typeof template !== 'string') {
      return String(template ?? '')
    }

    return template.replace(/\{\{([^}]+)\}\}/g, (_, expr) => {
      try {
        const result = this.eval(expr.trim(), context)
        return String(result ?? '')
      } catch {
        return ''
      }
    })
  }

  interpolateUrl(url: string, params: Record<string, any> = {}): string {
    let result = url
    result = result.replace(/:([a-zA-Z_][a-zA-Z0-9_]*)/g, (_, key) => {
      return String(params[key] ?? '')
    })
    return this.evalString(result, params)
  }

  evalHeaders(
    headers: Record<string, string>,
    params: Record<string, any> = {}
  ): Record<string, string> {
    const result: Record<string, string> = {}
    for (const [key, value] of Object.entries(headers)) {
      result[key] = this.evalString(value, params)
    }
    return result
  }

  private _buildContext(context: Record<string, any>): Record<string, any> {
    const state = this.engine.state
    const componentValues = this.engine.getComponentValues()
    const pageState = state.currentPageId ? state.pageStates[state.currentPageId] || {} : {}

    return {
      $component: componentValues,
      $state: pageState,
      $global: state.globalState,
      $storage: state.storage,
      $api: state.apiResponses,
      $loading: state.apiLoading,
      $params: context,
      ...context
    }
  }
}
```

## 动作执行器

```typescript
// src/preview/engine/ActionExecutor.ts
import type { PreviewEngine } from './PreviewEngine'
import type { Action } from '../../types'

export type ActionType =
  | 'setState'
  | 'setGlobalState'
  | 'navigate'
  | 'callApi'
  | 'showLoading'
  | 'hideLoading'
  | 'showToast'
  | 'setStorage'
  | 'removeStorage'
  | 'confirm'
  | 'delay'
  | 'condition'
  | 'loop'

export interface SetStateAction extends Action {
  type: 'setState'
  state: {
    key: string
    value: string | number | boolean | object | null
    valueType?: 'expression' | 'static'
  }[]
}

export interface NavigateAction extends Action {
  type: 'navigate'
  pageId: string
  params?: Record<string, any>
}

export interface CallApiAction extends Action {
  type: 'callApi'
  apiId: string
  params?: Record<string, any>
  onSuccess?: Action[]
  onError?: Action[]
}

export class ActionExecutor {
  private engine: PreviewEngine

  constructor(engine: PreviewEngine) {
    this.engine = engine
  }

  async executeActions(actions: Action[], eventData: any = {}): Promise<void> {
    if (!actions || actions.length === 0) return

    for (const action of actions) {
      await this._executeAction(action, eventData)
    }
  }

  private async _executeAction(action: Action, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()

    switch (action.type) {
      case 'setState':
        await this._executeSetState(action as SetStateAction, eventData)
        break
      case 'setGlobalState':
        await this._executeSetGlobalState(action as any, eventData)
        break
      case 'navigate':
        await this._executeNavigate(action as NavigateAction, eventData)
        break
      case 'callApi':
        await this._executeCallApi(action as CallApiAction, eventData)
        break
      case 'showLoading':
        this.engine.showLoading()
        break
      case 'hideLoading':
        this.engine.hideLoading()
        break
      case 'showToast':
        await this._executeShowToast(action as any, eventData)
        break
      case 'setStorage':
        await this._executeSetStorage(action as any, eventData)
        break
      case 'removeStorage':
        await this._executeRemoveStorage(action as any, eventData)
        break
      case 'confirm':
        await this._executeConfirm(action as any, eventData)
        break
      case 'delay':
        await this._executeDelay(action as any)
        break
      case 'condition':
        await this._executeCondition(action as any, eventData)
        break
      case 'loop':
        await this._executeLoop(action as any, eventData)
        break
      default:
        console.warn('未知动作类型:', action.type)
    }
  }

  private async _executeSetState(action: SetStateAction, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    for (const stateItem of action.state) {
      let value = stateItem.value
      if (stateItem.valueType === 'expression' && typeof value === 'string') {
        value = evaluator.eval(value, eventData)
      }
      this.engine.setPageState(stateItem.key, value)
    }
  }

  private async _executeSetGlobalState(action: any, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    let value = action.value
    if (action.valueType === 'expression' && typeof value === 'string') {
      value = evaluator.eval(value, eventData)
    }
    this.engine.setGlobalState(action.key, value)
  }

  private async _executeNavigate(action: NavigateAction, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    const params: Record<string, any> = {}

    if (action.params) {
      for (const [key, value] of Object.entries(action.params)) {
        params[key] = evaluator.eval(value, eventData)
      }
    }

    this.engine.navigate(action.pageId, params)
  }

  private async _executeCallApi(action: CallApiAction, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    const params: Record<string, any> = {}

    if (action.params) {
      for (const [key, value] of Object.entries(action.params)) {
        params[key] = evaluator.eval(value, eventData)
      }
    }

    try {
      const result = await this.engine.callApi(action.apiId, params)
      if (action.onSuccess) {
        await this.executeActions(action.onSuccess, { ...eventData, $result: result })
      }
    } catch (err) {
      if (action.onError) {
        await this.executeActions(action.onError, { ...eventData, $error: err })
      }
    }
  }

  private async _executeShowToast(action: any, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    const message = evaluator.evalString(action.message, eventData)

    if (typeof window !== 'undefined') {
      const toast = document.createElement('div')
      toast.className = `preview-toast preview-toast--${action.type || 'info'}`
      toast.textContent = message
      toast.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 9999;
        animation: toastIn 0.3s ease-out;
      `
      document.body.appendChild(toast)

      setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease-in forwards'
        setTimeout(() => toast.remove(), 300)
      }, action.duration || 2000)
    }
  }

  private async _executeSetStorage(action: any, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    let value = action.value
    if (action.valueType === 'expression' && typeof value === 'string') {
      value = evaluator.eval(value, eventData)
    }
    this.engine.setStorage(action.key, value)
  }

  private async _executeRemoveStorage(action: any): Promise<void> {
    this.engine.setStorage(action.key, null)
  }

  private async _executeConfirm(action: any, eventData: any): Promise<boolean> {
    const evaluator = this.engine.getEvaluator()
    const message = evaluator.evalString(action.message, eventData)

    const confirmed = confirm(message)

    if (confirmed && action.onConfirm) {
      await this.executeActions(action.onConfirm, eventData)
    } else if (!confirmed && action.onCancel) {
      await this.executeActions(action.onCancel, eventData)
    }

    return confirmed
  }

  private async _executeDelay(action: any): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, action.duration || 1000))
  }

  private async _executeCondition(action: any, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    const result = evaluator.eval(action.condition, eventData)

    if (result) {
      if (action.onTrue) {
        await this.executeActions(action.onTrue, eventData)
      }
    } else {
      if (action.onFalse) {
        await this.executeActions(action.onFalse, eventData)
      }
    }
  }

  private async _executeLoop(action: any, eventData: any): Promise<void> {
    const evaluator = this.engine.getEvaluator()
    const iterable = evaluator.eval(action.iterable, eventData) || []
    const keyName = action.keyName || '$index'
    const valueName = action.valueName || '$item'

    for (let i = 0; i < iterable.length; i++) {
      const loopContext = {
        ...eventData,
        [keyName]: i,
        [valueName]: iterable[i]
      }
      await this.executeActions(action.body, loopContext)
    }
  }
}
```

## 预览通信桥

```typescript
// src/preview/bridge/PreviewBridge.ts
export type BridgeMessageType =
  | 'preview-ready'
  | 'project-data'
  | 'component-update'
  | 'page-update'
  | 'switch-page'
  | 'full-reload'
  | 'device-change'
  | 'log'
  | 'action-executed'

export interface BridgeMessage {
  type: BridgeMessageType
  data?: any
  timestamp: number
}

export class PreviewBridge {
  private channel: BroadcastChannel | null = null
  private useBroadcastChannel: boolean
  private listeners: Map<BridgeMessageType, Set<(data?: any) => void>> = new Map()

  constructor() {
    this.useBroadcastChannel = typeof BroadcastChannel !== 'undefined'

    if (this.useBroadcastChannel) {
      this.channel = new BroadcastChannel('nocode-preview')
      this._setupChannelListener()
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('message', this._handleWindowMessage.bind(this))
    }
  }

  private _setupChannelListener(): void {
    if (!this.channel) return

    this.channel.onmessage = (event) => {
      const message = event.data as BridgeMessage
      this._dispatchMessage(message)
    }
  }

  private _handleWindowMessage(event: MessageEvent): void {
    if (event.data?.type) {
      this._dispatchMessage(event.data)
    }
  }

  private _dispatchMessage(message: BridgeMessage): void {
    const listeners = this.listeners.get(message.type)
    if (listeners) {
      listeners.forEach(callback => callback(message.data))
    }
  }

  on(type: BridgeMessageType, callback: (data?: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set())
    }
    this.listeners.get(type)!.add(callback)

    return () => {
      this.listeners.get(type)?.delete(callback)
    }
  }

  send(type: BridgeMessageType, data?: any): void {
    const message: BridgeMessage = {
      type,
      data,
      timestamp: Date.now()
    }

    if (this.channel) {
      this.channel.postMessage(message)
    }

    if (typeof window !== 'undefined') {
      if (window.parent !== window) {
        window.parent.postMessage(message, '*')
      }
    }
  }

  notifyReady(): void {
    this.send('preview-ready')
  }

  sendProjectData(project: any): void {
    this.send('project-data', project)
  }

  sendComponentUpdate(componentId: string, updates: any): void {
    this.send('component-update', { componentId, updates })
  }

  sendPageUpdate(pageId: string, updates: any): void {
    this.send('page-update', { pageId, updates })
  }

  sendSwitchPage(pageId: string): void {
    this.send('switch-page', { pageId })
  }

  sendDeviceChange(device: any): void {
    this.send('device-change', device)
  }

  sendFullReload(): void {
    this.send('full-reload')
  }

  sendLog(log: any): void {
    this.send('log', log)
  }

  destroy(): void {
    if (this.channel) {
      this.channel.close()
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('message', this._handleWindowMessage.bind(this))
    }
    this.listeners.clear()
  }
}
```

## 预览组件 - 预览App

```vue
<!-- src/preview/components/PreviewApp.vue -->
<template>
  <div class="preview-app">
    <div v-if="!engine.isInitialized" class="preview-loading">
      <div class="loading-spinner"></div>
      <p>加载预览中...</p>
    </div>

    <template v-else>
      <PreviewPage
        v-if="engine.currentPage"
        :page="engine.currentPage"
        :engine="engine"
      />
      <div v-else class="preview-empty">
        <p>请选择首页</p>
      </div>
    </template>

    <div v-if="engine.state.loadingCount > 0" class="preview-loading-overlay">
      <div class="loading-spinner"></div>
    </div>

    <div v-if="showConsole" class="preview-console">
      <div class="console-header">
        <span>控制台</span>
        <button @click="showConsole = false" class="console-close">×</button>
      </div>
      <div class="console-logs">
        <div
          v-for="log in engine.state.logs"
          :key="log.id"
          :class="['console-log', `console-log--${log.type}`]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-message">{{ log.message }}</span>
          <div v-if="log.data" class="log-data">
            <pre>{{ formatData(log.data) }}</pre>
          </div>
        </div>
      </div>
      <button @click="engine.clearLogs()" class="console-clear">清空</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import PreviewPage from './PreviewPage.vue'
import { PreviewEngine } from '../engine/PreviewEngine'
import { PreviewBridge } from '../bridge/PreviewBridge'

const engine = new PreviewEngine()
const bridge = new PreviewBridge()
const showConsole = ref(false)

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

function formatData(data: any): string {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

onMounted(async () => {
  bridge.on('project-data', async (project) => {
    await engine.loadProject(project)
  })

  bridge.on('switch-page', (data) => {
    if (data?.pageId) {
      engine.loadPage(data.pageId)
    }
  })

  bridge.on('component-update', (data) => {
    console.log('组件更新:', data)
  })

  bridge.on('page-update', (data) => {
    console.log('页面更新:', data)
  })

  bridge.on('full-reload', () => {
    window.location.reload()
  })

  bridge.notifyReady()
})

onUnmounted(() => {
  bridge.destroy()
})
</script>

<style scoped>
.preview-app {
  position: relative;
  width: 100%;
  height: 100%;
  background: white;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.preview-loading,
.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
}

.preview-console {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: #1e1e1e;
  color: #d4d4d4;
  z-index: 9999;
  display: flex;
  flex-direction: column;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.console-close {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
}

.console-close:hover {
  color: white;
}

.console-logs {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  font-size: 12px;
}

.console-log {
  margin-bottom: 4px;
  padding: 2px 4px;
  border-radius: 2px;
}

.console-log--info { color: #9cdcfe; }
.console-log--warn { color: #dcdcaa; }
.console-log--error { color: #f48771; }
.console-log--log { color: #d4d4d4; }

.log-time {
  color: #6a9955;
  margin-right: 8px;
}

.log-data {
  margin-left: 20px;
  margin-top: 4px;
}

.log-data pre {
  margin: 0;
  color: #ce9178;
}

.console-clear {
  margin: 4px 8px 8px;
  padding: 4px 12px;
  background: #404040;
  border: none;
  color: #d4d4d4;
  cursor: pointer;
  border-radius: 3px;
  align-self: flex-start;
}
</style>
```

## 预览页面组件

```vue
<!-- src/preview/components/PreviewPage.vue -->
<template>
  <div class="preview-page" :style="pageStyle">
    <template v-for="component in sortedComponents" :key="component.id">
      <component
        :is="getComponentRenderer(component.type)"
        :component="component"
        :engine="engine"
        :key="component.id"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Page, ComponentInstance } from '../../types'
import type { PreviewEngine } from '../engine/PreviewEngine'
import ButtonPreview from './preview-components/ButtonPreview.vue'
import TextPreview from './preview-components/TextPreview.vue'
import InputPreview from './preview-components/InputPreview.vue'
import ImagePreview from './preview-components/ImagePreview.vue'
import ListPreview from './preview-components/ListPreview.vue'
import ContainerPreview from './preview-components/ContainerPreview.vue'

interface Props {
  page: Page
  engine: PreviewEngine
}

const props = defineProps<Props>()

const pageStyle = computed(() => {
  const styles: Record<string, string> = {}
  if (props.page.style?.backgroundColor) {
    styles.backgroundColor = props.page.style.backgroundColor
  }
  return styles
})

const sortedComponents = computed(() => {
  const comps = [...(props.page.components || [])]
  return comps.sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
})

function getComponentRenderer(type: string): any {
  const renderers: Record<string, any> = {
    button: ButtonPreview,
    text: TextPreview,
    input: InputPreview,
    image: ImagePreview,
    list: ListPreview,
    container: ContainerPreview
  }
  return renderers[type] || ContainerPreview
}
</script>

<style scoped>
.preview-page {
  min-height: 100%;
  padding: 16px;
  box-sizing: border-box;
}
</style>
```

## 预览组件 - 按钮

```vue
<!-- src/preview/components/preview-components/ButtonPreview.vue -->
<template>
  <button
    :id="component.id"
    :class="['preview-button', { 'preview-button--disabled': component.props.disabled }]"
    :style="component.style"
    :disabled="component.props.disabled"
    @click="handleClick"
  >
    {{ displayText }}
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentInstance } from '../../../types'
import type { PreviewEngine } from '../../engine/PreviewEngine'

interface Props {
  component: ComponentInstance
  engine: PreviewEngine
}

const props = defineProps<Props>()

const displayText = computed(() => {
  const evaluator = props.engine.getEvaluator()
  return evaluator.evalString(props.component.props.text || '按钮')
})

function handleClick(event: MouseEvent): void {
  props.engine.triggerEvent(props.component.id, 'click', { event })
}
</script>

<style scoped>
.preview-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.preview-button:hover:not(.preview-button--disabled) {
  background: #2563eb;
}

.preview-button:active:not(.preview-button--disabled) {
  background: #1d4ed8;
}

.preview-button--disabled {
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}
</style>
```

## 预览组件 - 文本

```vue
<!-- src/preview/components/preview-components/TextPreview.vue -->
<template>
  <div :id="component.id" class="preview-text" :style="component.style">
    {{ displayText }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentInstance } from '../../../types'
import type { PreviewEngine } from '../../engine/PreviewEngine'

interface Props {
  component: ComponentInstance
  engine: PreviewEngine
}

const props = defineProps<Props>()

const displayText = computed(() => {
  const evaluator = props.engine.getEvaluator()
  return evaluator.evalString(props.component.props.text || '')
})
</script>

<style scoped>
.preview-text {
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
}
</style>
```

## 预览组件 - 输入框

```vue
<!-- src/preview/components/preview-components/InputPreview.vue -->
<template>
  <div :id="component.id" class="preview-input-wrapper" :style="component.style">
    <input
      :type="component.props.inputType || 'text'"
      :placeholder="component.props.placeholder || ''"
      :disabled="component.props.disabled"
      :value="value"
      @input="handleInput"
      @change="handleChange"
      @focus="handleFocus"
      @blur="handleBlur"
      class="preview-input"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ComponentInstance } from '../../../types'
import type { PreviewEngine } from '../../engine/PreviewEngine'

interface Props {
  component: ComponentInstance
  engine: PreviewEngine
}

const props = defineProps<Props>()

const value = computed(() => {
  return props.engine.getComponentState(props.component.id, 'value') ?? props.component.props.value ?? ''
})

function handleInput(event: Event): void {
  const target = event.target as HTMLInputElement
  props.engine.setComponentState(props.component.id, 'value', target.value)
  props.engine.triggerEvent(props.component.id, 'input', { value: target.value })
}

function handleChange(event: Event): void {
  const target = event.target as HTMLInputElement
  props.engine.triggerEvent(props.component.id, 'change', { value: target.value })
}

function handleFocus(event: Event): void {
  props.engine.triggerEvent(props.component.id, 'focus', { event })
}

function handleBlur(event: Event): void {
  props.engine.triggerEvent(props.component.id, 'blur', { event })
}
</script>

<style scoped>
.preview-input-wrapper {
  width: 100%;
}

.preview-input {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  outline: none;
  transition: all 0.2s;
  box-sizing: border-box;
}

.preview-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
```

## 预览视图 - 编辑器侧

```vue
<!-- src/views/PreviewView.vue -->
<template>
  <div class="preview-view">
    <PreviewToolbar
      :device="currentDevice"
      :scale="scale"
      @device-change="handleDeviceChange"
      @scale-change="handleScaleChange"
      @refresh="handleRefresh"
      @toggle-console="showConsole = !showConsole"
    />

    <div class="preview-container">
      <div
        class="preview-frame"
        :style="{
          width: `${currentDevice.width * scale}px`,
          height: `${currentDevice.height * scale}px`,
          transform: `scale(${scale})`,
          transformOrigin: 'top left'
        }"
      >
        <iframe
          ref="iframeRef"
          :src="previewUrl"
          class="preview-iframe"
          @load="handleIframeLoad"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '../store/project'
import PreviewToolbar from '../components/preview/PreviewToolbar.vue'
import { PreviewBridge } from '../preview/bridge/PreviewBridge'
import type { DeviceType, DeviceConfig } from '../preview/types'

const projectStore = useProjectStore()

const iframeRef = ref<HTMLIFrameElement | null>(null)
const currentDevice = ref<DeviceConfig>({
  type: 'mobile',
  name: 'iPhone 12',
  width: 375,
  height: 667,
  devicePixelRatio: 2
})
const scale = ref(1)
const showConsole = ref(false)
const bridge = ref<PreviewBridge | null>(null)

const previewUrl = computed(() => {
  return `/preview/${projectStore.currentProject?.id}?t=${Date.now()}`
})

function handleDeviceChange(device: DeviceConfig): void {
  currentDevice.value = device
  bridge.value?.sendDeviceChange(device)
}

function handleScaleChange(newScale: number): void {
  scale.value = newScale
}

function handleRefresh(): void {
  if (iframeRef.value) {
    iframeRef.value.src = iframeRef.value.src
  }
}

function handleIframeLoad(): void {
  if (projectStore.currentProject) {
    bridge.value?.sendProjectData(projectStore.currentProject)
  }
}

onMounted(() => {
  bridge.value = new PreviewBridge()

  bridge.value.on('preview-ready', () => {
    if (projectStore.currentProject) {
      bridge.value?.sendProjectData(projectStore.currentProject)
    }
  })
})

onUnmounted(() => {
  bridge.value?.destroy()
})
</script>

<style scoped>
.preview-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f3f4f6;
}

.preview-container {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px;
  overflow: auto;
}

.preview-frame {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>
```

## 预览工具栏

```vue
<!-- src/components/preview/PreviewToolbar.vue -->
<template>
  <div class="preview-toolbar">
    <div class="toolbar-left">
      <DeviceSelector
        :value="device"
        @change="$emit('device-change', $event)"
      />
      <ZoomControl
        :value="scale"
        @change="$emit('scale-change', $event)"
      />
    </div>

    <div class="toolbar-right">
      <button class="toolbar-btn" @click="$emit('refresh')" title="刷新">
        <RefreshIcon />
      </button>
      <button class="toolbar-btn" @click="$emit('toggle-console')" title="控制台">
        <ConsoleIcon />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import DeviceSelector from './DeviceSelector.vue'
import ZoomControl from './ZoomControl.vue'
import RefreshIcon from './icons/RefreshIcon.vue'
import ConsoleIcon from './icons/ConsoleIcon.vue'
import type { DeviceConfig } from '../../preview/types'

interface Props {
  device: DeviceConfig
  scale: number
}

defineProps<Props>()

defineEmits<{
  (e: 'device-change', device: DeviceConfig): void
  (e: 'scale-change', scale: number): void
  (e: 'refresh'): void
  (e: 'toggle-console'): void
}>()
</script>

<style scoped>
.preview-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar-btn {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.toolbar-btn:hover {
  background: #f9fafb;
}
</style>
```

## 设备选择器

```vue
<!-- src/components/preview/DeviceSelector.vue -->
<template>
  <div class="device-selector">
    <button class="device-btn" @click="showDropdown = !showDropdown">
      {{ value.name }}
      <ChevronDownIcon />
    </button>

    <div v-if="showDropdown" class="device-dropdown" @click="showDropdown = false">
      <div class="device-list">
        <div
          v-for="device in devices"
          :key="device.type"
          :class="['device-item', { active: device.type === value.type }]"
          @click.stop="$emit('change', device)"
        >
          <span class="device-icon">{{ getDeviceIcon(device.type) }}</span>
          <span class="device-name">{{ device.name }}</span>
          <span class="device-size">{{ device.width }} × {{ device.height }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ChevronDownIcon from './icons/ChevronDownIcon.vue'
import type { DeviceConfig, DeviceType } from '../../preview/types'
import { DEVICES } from '../../preview/types'

interface Props {
  value: DeviceConfig
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'change', device: DeviceConfig): void
}>()

const showDropdown = ref(false)
const devices = Object.values(DEVICES)

function getDeviceIcon(type: DeviceType): string {
  const icons: Record<DeviceType, string> = {
    'mobile': '📱',
    'mobile-large': '📱',
    'tablet': '📟',
    'tablet-large': '📟',
    'desktop': '🖥️',
    'desktop-hd': '🖥️',
    'wechat-miniapp': '💬',
    'custom': '🔧'
  }
  return icons[type] || '📱'
}

function handleClickOutside(event: MouseEvent): void {
  const target = event.target as Element
  if (!target.closest('.device-selector')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.device-selector {
  position: relative;
}

.device-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}

.device-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 220px;
}

.device-list {
  padding: 4px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.device-item:hover {
  background: #f3f4f6;
}

.device-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.device-icon {
  font-size: 16px;
}

.device-name {
  flex: 1;
  font-size: 14px;
}

.device-size {
  font-size: 12px;
  color: #9ca3af;
}
</style>
```

## 缩放控制

```vue
<!-- src/components/preview/ZoomControl.vue -->
<template>
  <div class="zoom-control">
    <button class="zoom-btn" @click="decrease" :disabled="value <= 0.25">
      <MinusIcon />
    </button>
    <span class="zoom-value">{{ Math.round(value * 100) }}%</span>
    <button class="zoom-btn" @click="increase" :disabled="value >= 2">
      <PlusIcon />
    </button>
    <button class="zoom-btn" @click="reset" title="重置">
      <RefreshIcon />
    </button>
  </div>
</template>

<script setup lang="ts">
import MinusIcon from './icons/MinusIcon.vue'
import PlusIcon from './icons/PlusIcon.vue'
import RefreshIcon from './icons/RefreshIcon.vue'

interface Props {
  value: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'change', scale: number): void
}>()

function decrease(): void {
  emit('change', Math.max(0.25, props.value - 0.25))
}

function increase(): void {
  emit('change', Math.min(2, props.value + 0.25))
}

function reset(): void {
  emit('change', 1)
}
</script>

<style scoped>
.zoom-control {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: #f9fafb;
  border-radius: 6px;
}

.zoom-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.zoom-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.zoom-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.zoom-value {
  font-size: 12px;
  color: #6b7280;
  min-width: 40px;
  text-align: center;
}
</style>
```

## 预览服务器

```typescript
// server/src/server.ts
import express from 'express'
import cors from 'cors'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { setupPreviewRoutes } from './preview-routes'
import { setupProxyRoute } from './proxy'
import path from 'path'

const app = express()
const PORT = process.env.PREVIEW_PORT || 3001

app.use(cors())
app.use(express.json())

app.use('/api/preview', setupPreviewRoutes())
app.use('/api/preview/proxy', setupProxyRoute())

app.use('/preview-assets', express.static(path.join(__dirname, '../../frontend/dist/preview')))

app.get('/preview/:projectId', (req, res) => {
  res.sendFile(path.join(__dirname, '../../../frontend/public/preview.html'))
})

app.listen(PORT, () => {
  console.log(`预览服务器运行在 http://localhost:${PORT}`)
})
```

## API代理

```typescript
// server/src/proxy.ts
import express from 'express'
import fetch from 'node-fetch'

interface ProxyRequest {
  url: string
  method: string
  headers: Record<string, string>
  body: string
}

export function setupProxyRoute(): express.Router {
  const router = express.Router()

  router.post('/', async (req, res) => {
    try {
      const { url, method, headers, body } = req.body as ProxyRequest

      if (!url) {
        return res.status(400).json({ error: 'URL is required' })
      }

      const response = await fetch(url, {
        method: method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        },
        body: method !== 'GET' ? body : undefined
      })

      const contentType = response.headers.get('content-type') || ''
      const isJson = contentType.includes('application/json')

      const responseHeaders: Record<string, string> = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*'
      }

      if (contentType) {
        responseHeaders['Content-Type'] = contentType
      }

      for (const [key, value] of response.headers.entries()) {
        if (['content-type', 'content-length'].includes(key.toLowerCase())) {
          responseHeaders[key] = value
        }
      }

      res.status(response.status).set(responseHeaders)

      if (isJson) {
        const data = await response.json()
        res.json(data)
      } else {
        const text = await response.text()
        res.send(text)
      }
    } catch (err) {
      console.error('Proxy error:', err)
      res.status(500).json({
        error: err instanceof Error ? err.message : 'Proxy error'
      })
    }
  })

  return router
}
```

## 预览路由

```typescript
// server/src/preview-routes.ts
import express from 'express'

export function setupPreviewRoutes(): express.Router {
  const router = express.Router()

  router.get('/health', (req, res) => {
    res.json({ status: 'ok' })
  })

  router.get('/config/:projectId', (req, res) => {
    res.json({
      projectId: req.params.projectId,
      features: {
        hotReload: true,
        console: true,
        breakpoints: false
      }
    })
  })

  return router
}
```

## CORS配置

```typescript
// server/src/cors.ts
import cors from 'cors'

const corsOptions = {
  origin: [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:3001'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}

export default cors(corsOptions)
```

## API接口

### 1. 获取预览配置

**接口**: `GET /api/preview/config/:projectId`

**响应**:
```json
{
  "success": true,
  "data": {
    "projectId": "proj_123",
    "features": {
      "hotReload": true,
      "console": true,
      "breakpoints": false
    }
  }
}
```

### 2. API代理

**接口**: `POST /api/preview/proxy`

**请求体**:
```json
{
  "url": "https://api.example.com/users",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer xxx"
  },
  "body": "{}"
}
```

**响应**: 直接转发目标API响应

### 3. 健康检查

**接口**: `GET /api/preview/health`

**响应**:
```json
{
  "status": "ok"
}
```

## package.json

```json
{
  "name": "nocode-preview",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "concurrently \"npm run dev:frontend\" \"npm run dev:server\"",
    "dev:frontend": "vite",
    "dev:server": "tsx watch server/src/server.ts",
    "build": "npm run build:frontend && npm run build:server",
    "build:frontend": "vite build",
    "build:server": "tsc -p server/tsconfig.json",
    "start": "node dist/server/server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "http-proxy-middleware": "^2.0.6",
    "node-fetch": "^3.3.2"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "vue": "^3.4.0",
    "typescript": "^5.3.0",
    "@vitejs/plugin-vue": "^4.5.0",
    "concurrently": "^8.2.2",
    "tsx": "^4.6.2",
    "@types/express": "^4.17.21",
    "@types/cors": "^2.8.17"
  }
}
```

## 安全考虑

### 1. CSP策略
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https:;
">
```

### 2. 预览隔离
- 使用iframe隔离预览环境
- 禁止预览访问主应用存储
- 限制postMessage通信来源

### 3. API代理安全
- 白名单允许的域名
- 请求频率限制
- 过滤敏感请求头

### 4. XSS防护
- 表达式求值使用安全沙箱
- 用户输入转义显示
- contenteditable禁用

## 实现计划

### 阶段 1: 预览引擎
- [ ] 实现PreviewEngine核心类
- [ ] 实现ExpressionEvaluator表达式求值器
- [ ] 实现ActionExecutor动作执行器
- [ ] 页面状态管理
- [ ] 组件状态管理
- [ ] 全局状态管理
- [ ] 存储管理

### 阶段 2: 预览组件
- [ ] PreviewApp根组件
- [ ] PreviewPage页面组件
- [ ] ButtonPreview按钮组件
- [ ] TextPreview文本组件
- [ ] InputPreview输入组件
- [ ] ImagePreview图片组件
- [ ] ListPreview列表组件
- [ ] ContainerPreview容器组件
- [ ] 组件事件绑定

### 阶段 3: 实时同步
- [ ] PreviewBridge通信桥
- [ ] BroadcastChannel通信
- [ ] PostMessage通信
- [ ] 项目数据同步
- [ ] 组件增量更新
- [ ] 页面更新

### 阶段 4: API代理
- [ ] Express预览服务器
- [ ] API代理中间件
- [ ] CORS配置
- [ ] 预览路由

### 阶段 5: 多设备预览
- [ ] 设备配置管理
- [ ] DeviceSelector设备选择器
- [ ] ZoomControl缩放控制
- [ ] PreviewToolbar工具栏
- [ ] 设备尺寸切换
- [ ] 缩放控制

### 阶段 6: 前端界面
- [ ] PreviewView预览视图
- [ ] PreviewIFrame预览容器
- [ ] 预览控制台
- [ ] 加载状态
- [ ] 错误处理

### 阶段 7: 测试优化
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 安全加固
