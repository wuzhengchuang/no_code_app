# CLAUDE.md - Frontend

This file provides guidance for working with the frontend of the NoCode App Platform.

## Overview

The frontend is built with **Vue 3 + TypeScript** and provides the visual interface for the no-code platform.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Language**: TypeScript
- **State Management**: Pinia
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Preview Engine**: Vue-based preview runtime

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── editor/           # Visual editor components
│   │   ├── property-editors/  # Property editors
│   │   └── preview-components/ # Preview/runtime components
│   ├── stores/                # Pinia stores
│   ├── composables/           # Reusable composables
│   ├── types/                 # TypeScript types
│   ├── utils/                 # Utilities
│   ├── views/                 # Page views
│   ├── router/                # Router configuration
│   └── main.ts                # Entry point
├── public/                    # Static assets
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## Core Modules

### 1. Visual Editor
Located in `src/components/editor/` - main editor interface with:
- Component library panel
- Canvas (WYSIWYG)
- Property panel
- Toolbar (undo/redo, save, preview, generate)

### 2. Component Library
- 基础组件 (Basic): Button, Text, Image, Icon, Divider
- 表单组件 (Form): Input, Textarea, Select, Radio, Checkbox, Switch, DatePicker
- 列表组件 (List): List, Card, Grid, Carousel
- 导航组件 (Navigation): TabBar, NavBar, Tabs, Segmented
- 展示组件 (Display): Avatar, Badge, Tag, Progress, Collapse, Steps

### 3. Preview System
- Isolated iframe environment
- Real API calls in preview
- Action execution engine
- Expression evaluator

## Design Docs Reference

Read these design documents before implementation:
- **Main spec**: `../docs/superpowers/specs/2026-05-09-无代码平台设计文档.md`
- **Visual editor**: `../docs/superpowers/specs/modules/03-可视化编辑器子模块.md`
- **Logic orchestration**: `../docs/superpowers/specs/modules/05-逻辑编排子模块.md`
- **App preview**: `../docs/superpowers/specs/modules/06-App预览子模块.md`

## Getting Started

1. Read the design documents thoroughly
2. Set up the basic Vue 3 + Vite project structure
3. Implement the component registry first
4. Build the visual editor canvas and drag-drop
5. Add property panel and component manipulation
6. Implement the preview engine

## Important Notes

- Follow the component architecture from the design docs
- The preview system has its own component registry
- Use Pinia for state management
- Implement undo/redo history early on
- Type safety is important - use TypeScript properly
