# CLAUDE.md - Backend

This file provides guidance for working with the backend of the NoCode App Platform.

## Overview

The backend is built with **Python** and provides all the core business services, data management, and integration with LLMs for code generation.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0
- **Async Support**: Yes, with asyncio/aiohttp
- **LLM Integration**: Claude (Anthropic), OpenAI, Gemini, Qwen APIs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── dependencies.py         # Dependencies (auth, etc.)
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── api/                    # API routes
│   └── utils/                  # Utilities
├── migrations/                 # Alembic migrations
├── scripts/
│   └── init_db.py
├── tests/                      # Tests
├── requirements.txt
├── alembic.ini
└── .env.example
```

## Core Modules

### 1. User & Auth Service

- User registration and login
- JWT token management
- Team and role management
- Permission checking

### 2. Project Service

- Project CRUD
- Project snapshots (versions)
- Project sharing
- Project export/import

### 3. API & Data Model Service

- API configuration management
- JSON to data model parsing
- Type generation utilities

### 4. LLM Integration Service

- LLM provider abstraction (Claude/OpenAI)
- Prompt template management
- Code generation orchestration
- Document generation

### 5. Code Generation Engine

- Plugin-based architecture
- Generator base class
- Platform-specific generators (8+ platforms)
- Template engine

### 6. Document Generation Service

- CLAUDE.md generator
- Technical spec generator
- Implementation plan generator
- Directory tree generator

## Database Schema

**Important**: The complete database schema is documented in these design docs:

- `modules/01-用户与权限子模块.md`
- `modules/02-项目管理子模块.md`
- `modules/04-接口配置与数据模型子模块.md`

**Core Tables** (see design docs for complete schema):

- users, teams, team_members, user_project_permissions
- projects, pages, components, page_states
- api_configs, data_models
- event_bindings
- project_shares, project_snapshots
- llm_configs, generation_logs
- code_generations, generated_documents

## Design Docs Reference

Read these design documents before implementation:

- **Main spec**: `../docs/superpowers/specs/2026-05-09-无代码平台设计文档.md`
- **Users & Permissions**: `../docs/superpowers/specs/modules/01-用户与权限子模块.md`
- **Project Management**: `../docs/superpowers/specs/modules/02-项目管理子模块.md`
- **API & Data Models**: `../docs/superpowers/specs/modules/04-接口配置与数据模型子模块.md`
- **LLM Integration**: `../docs/superpowers/specs/modules/07-大模型集成子模块.md`
- **Code Generation**: `../docs/superpowers/specs/modules/08-代码生成引擎子模块.md`
- **Document Generation**: `../docs/superpowers/specs/modules/09-文档生成子模块.md`

## Getting Started

1. Read all the relevant design documents
2. Set up the database first (create MySQL tables)
3. Configure FastAPI project
4. Implement SQLAlchemy models
5. Add authentication and authorization
6. Implement services in order
7. Add API endpoints

## Important Notes

- Database schema must match the spec exactly
- Use async SQLAlchemy for better performance
- The code generation engine is plugin-based - follow that pattern
- LLM integration must support both Claude and OpenAI via an abstraction layer
- Generated code should be production-quality with comments
