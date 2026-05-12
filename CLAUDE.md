# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **NoCode App Platform** - a complete visual development platform for creating apps and mini-programs without writing code. It features drag-and-drop component editing, API configuration, logic orchestration, and AI-powered code generation for multiple platforms.

## Current Status

The project is currently in the **design/documentation phase**. The implementation has not started yet.

## Architecture Overview

The system is a multi-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  可视化编辑器  │  │   App预览器   │  │   项目管理界面    │  │
│  │  (Vue3)      │  │   (Vue3)      │  │    (Vue3)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      服务网关层 (Node.js)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │  认证授权  │  │  API网关  │  │  限流熔断  │  │  日志审计   │   │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    业务服务层 (Python)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ 项目服务    │  │ 组件服务    │  │ 接口服务    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ 逻辑编排服务│  │ 预览服务    │  │ 代码生成服务│            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    大模型集成层                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         LLM抽象接口 (可切换Claude/GPT等)          │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   代码生成引擎 (插件化)                       │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │微信小程序│ │支付宝小程序│ │  H5    │ │ReactN │ │ Flutter│   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│  ┌────────┐ ┌────────┐ ┌────────┐                          │
│  │原生iOS  │ │原生Android│ │Uni-app │                          │
│  └────────┘ └────────┘ └────────┘                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       数据存储层 (MySQL)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 用户表    │ │ 项目表    │ │ 组件表    │ │ 接口配置表 │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 逻辑配置表│ │ 数据模型表│ │ 分享表    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
no_code_app/
├── docs/
│   └── superpowers/
│       └── specs/          # Complete design documentation
│           ├── README.md
│           ├── 2026-05-09-无代码平台设计文档.md (Main spec)
│           └── modules/     # 11 submodule design docs
├── frontend/               # Vue 3 + TypeScript frontend
│   └── CLAUDE.md           # [NEW] Frontend-specific guidance
├── backend/                # Python backend services
│   └── CLAUDE.md           # [NEW] Backend-specific guidance
├── gateway/                # Node.js API gateway
│   └── CLAUDE.md           # [NEW] Gateway-specific guidance
├── desktop/                # Electron desktop app
│   └── CLAUDE.md           # [NEW] Desktop-specific guidance
├── CLAUDE.md               # This file
└── README.md
```

## Documentation

**Before writing any code, always refer to the design documentation:**

1. **Main spec document**: `docs/superpowers/specs/2026-05-09-无代码平台设计文档.md`
2. **Submodule specs**: `docs/superpowers/specs/modules/`
3. **Module-specific CLAUDE.md**:
   - `frontend/CLAUDE.md` - Frontend development guide
   - `backend/CLAUDE.md` - Backend development guide
   - `gateway/CLAUDE.md` - Gateway development guide
   - `desktop/CLAUDE.md` - Desktop app development guide

The 11 submodules are:

- `01-用户与权限子模块.md` - User authentication and permissions
- `02-项目管理子模块.md` - Project management
- `03-可视化编辑器子模块.md` - Visual drag-drop editor
- `04-接口配置与数据模型子模块.md` - API config and data models
- `05-逻辑编排子模块.md` - Logic orchestration
- `06-App预览子模块.md` - App preview
- `07-大模型集成子模块.md` - LLM integration (Claude/OpenAI)
- `08-代码生成引擎子模块.md` - Code generation engine
- `09-文档生成子模块.md` - Documentation generation
- `10-项目管理与用户权限子模块.md` - Team collaboration
- `11-桌面应用子模块.md` - Electron desktop app

## Tech Stack

| Layer           | Technologies                                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| Frontend        | Vue 3 + TypeScript + Pinia + Tailwind CSS + Vite                                                                    |
| Backend         | Python 3.11+ + FastAPI + SQLAlchemy 2.0 + Node.js (gateway) + MySQL 8.0+                                            |
| Desktop         | Electron 28+ + Vue 3 + MySQL 8.0+ (local database)                                                                 |
| Code Generation | Supports: WeChat Mini, Alipay Mini, H5, React Native, Flutter, iOS Native (Swift), Android Native (Kotlin), Uni-app |

## Design Principles

Follow the design decisions documented in the specs:

- Plugin-based architecture for code generators
- Event-action pattern for logic orchestration
- Isolated preview with real API calls
- Abstraction layer for LLM integration

## Common Development Tasks

**Note**: Build/run commands will be available after the implementation starts. The current phase is design.

When the implementation begins:

1. Follow the **7-phase implementation plan** in the main spec
2. Work on one submodule at a time
3. Ensure database schema matches the spec before writing code
4. Generate CLAUDE.md specs for projects created with this platform

## Plan State Management Constraint

**IMPORTANT: Plan Document State Synchronization**

When executing any implementation plan or working on tasks:

1. **Before starting work**:
   - Update the corresponding design document to mark the phase/submodule as "In Progress"
   - Record the start date and assignee in the document

2. **During execution**:
   - Keep the design document updated with progress notes
   - Document any deviations from the original plan and their justifications
   - Update task lists and checklists as items are completed

3. **Upon completion**:
   - Mark the phase/submodule as "Completed" in the design document
   - Record the completion date
   - Add a summary of what was implemented, including any key changes or decisions
   - Link to the relevant code commits/PRs if applicable

4. **State Tracking**:
   - The main spec document (`2026-05-09-无代码平台设计文档.md`) contains a master status table
   - Each submodule spec has its own status section
   - Both must be kept in sync with actual progress
   - Do not mark items as "Completed" without proper verification (tests passing, review done)

5. **Review Checkpoints**:
   - Before marking a phase as complete, use the `superpowers:requesting-code-review` skill
   - Ensure all verification steps are completed before updating status
   - Use `superpowers:verification-before-completion` to validate work

## Important Notes

- **All 11 submodules have detailed design docs** - read the relevant one before implementing
- The project has no existing code yet - it's a greenfield project
- Design documents contain detailed API specs, data models, and even code examples
- When in doubt, follow the examples in the design docs
