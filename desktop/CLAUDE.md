# CLAUDE.md - Desktop App

This file provides guidance for working with the desktop application of the NoCode App Platform.

## Overview

The desktop app is an **Electron** wrapper around the Vue 3 frontend, with local MySQL database support.

## Tech Stack

- **Runtime**: Electron 28+
- **Frontend**: Vue 3 (shared with web frontend)
- **Language**: TypeScript
- **Local Database**: MySQL 8.0+
- **ORM**: Prisma
- **Updates**: electron-updater
- **Build**: electron-builder

## Project Structure

```
desktop/
├── main/                      # Electron main process
│   ├── main.ts               # Entry point
│   ├── ipc-handlers.ts       # IPC handlers
│   ├── window-manager.ts     # Window management
│   ├── menu.ts               # Menu bar
│   ├── auto-updater.ts       # Auto-update logic
│   └── database/             # Database operations
│       ├── db.ts             # Database connection wrapper
│       └── queries.ts        # Database queries
├── preload/                  # Preload scripts
│   └── preload.ts
├── renderer/                 # Renderer (symlink/reused from frontend)
├── shared/                   # Shared types
├── resources/                # Icons and assets
│   └── icons/
├── electron-builder.yml      # Build config
├── package.json
├── tsconfig.json
├── vite.config.ts            # For renderer (if separate)
├── prisma/                   # Prisma ORM
│   └── schema.prisma         # Database schema
└── .env                      # Environment variables (database config)
```

## Main Process Responsibilities

### 1. Window Management

- Create and manage application windows
- Handle window events
- Multi-window support (main editor + preview)

### 2. IPC Handlers

- Project save/load
- Project export/import
- File system operations
- Settings management

### 3. Database Management

- Local project storage
- Offline-first data persistence
- Sync with cloud when online (future)

**开发阶段配置** (MySQL 8.0+):

- 使用本地 MySQL 数据库进行测试
- 数据库连接配置通过 `.env` 文件管理
- 开发阶段使用本地资源，不依赖外部服务

**数据库表结构** (MySQL):

**local_projects 表**:
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 主键 |
| name | VARCHAR(255) | NOT NULL, INDEX | 项目名称 |
| data | LONGTEXT | NOT NULL | 项目数据(JSON格式) |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**settings 表**:
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| key | VARCHAR(100) | PRIMARY KEY | 设置键名 |
| value | TEXT | NOT NULL | 设置值 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**约束说明**:

- `local_projects.name` 字段添加索引优化查询
- `created_at` 和 `updated_at` 使用自动时间戳
- `id` 使用 UUID 格式保证唯一性
- 所有字段都有适当的 NOT NULL 约束

### 4. Menu System

- File: New, Open, Save, Save As, Export, Import
- Edit: Undo, Redo, Cut, Copy, Paste
- View: Reload, Toggle DevTools, Zoom, Fullscreen
- Generate: Code, Docs
- Help: Documentation, Issues

### 5. Auto-Update

- Check for updates
- Download updates
- Install and restart

## Preload API

The preload script exposes a safe API to the renderer:

```typescript
// window.electronAPI
{
  // Project operations
  projectSave,
  projectLoad,
  projectList,
  projectDelete,
  projectExport,
  projectImport,

  // App info
  getAppVersion,
  getAppPath,

  // File system
  fsWriteFile,
  fsReadFile,

  // Flag
  isDesktop: true
}
```

## Reusing Frontend Code

The renderer should reuse the web frontend with minimal changes:

- Use conditional logic (`window.electronAPI?.isDesktop`)
- Abstract data layer to work with both web API and IPC
- Share Vue components, stores, utilities

## Design Docs Reference

Read these design documents before implementation:

- **Main spec**: `../docs/superpowers/specs/2026-05-09-无代码平台设计文档.md`
- **Desktop module**: `../docs/superpowers/specs/modules/11-桌面应用子模块.md`

## Getting Started

1. Read the desktop design document
2. Set up Electron with TypeScript
3. Create the main process entry point
4. Implement window management
5. Add IPC handlers for project operations
6. 配置本地 MySQL 数据库
   - 安装 MySQL 8.0+ 并创建数据库
   - 配置 `.env` 文件设置数据库连接
   - 使用 Prisma 进行数据库迁移
7. Build the menu system
8. Add auto-update capability
9. Integrate with the frontend

## Important Notes

- **Context isolation** must be enabled for security
- **Node integration** should be disabled
- Use the preload script to expose only necessary APIs
- 使用本地 MySQL 数据库，配置通过 `.env` 文件管理
- 数据库操作应通过 Prisma ORM 统一处理
- 使用本地资源，不依赖外部服务
- Consider offline-first architecture from the start
- Follow electron-builder best practices for production builds
- Code signing is required for distribution

## Platform Support

- macOS (primary)
- Windows
- Linux

Build targets configured in electron-builder.yml
