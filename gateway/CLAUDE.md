# CLAUDE.md - Gateway

This file provides guidance for working with the service gateway of the NoCode App Platform.

## Overview

The gateway is a Node.js service that provides API routing, authentication, rate limiting, and acts as a reverse proxy for the Python backend services.

## Tech Stack

- **Runtime**: Node.js 20+
- **Framework**: Express.js
- **Authentication**: JWT
- **Rate Limiting**: Redis + express-rate-limit
- **Proxy**: http-proxy-middleware
- **Logging**: Winston
- **CORS**: CORS middleware

## Project Structure

```
gateway/
├── src/
│   ├── index.ts                # Entry point
│   ├── config.ts               # Configuration
│   ├── middleware/
│   │   ├── auth.ts             # JWT authentication
│   │   ├── rate-limit.ts       # Rate limiting
│   │   ├── cors.ts             # CORS handling
│   │   ├── logger.ts           # Request logging
│   │   └── error-handler.ts    # Error handling
│   ├── proxy/
│   │   └── routes.ts           # Proxy routes to backend
│   └── health.ts               # Health check endpoints
├── tests/
├── package.json
├── tsconfig.json
└── .env.example
```

## Core Responsibilities

1. **API Gateway**
   - Route requests to appropriate backend services
   - Request/response transformation if needed

2. **Authentication & Authorization**
   - Verify JWT tokens
   - Basic permission checking (fine-grained auth in Python backend)

3. **Rate Limiting**
   - Per-IP/user rate limits
   - Redis storage

4. **Logging & Monitoring**
   - Request/response logging
   - Request ID propagation
   - Error tracking

5. **CORS Handling**
   - Cross-origin requests management

## Design Docs Reference

Read these design documents before implementation:

- **Main spec**: `../docs/superpowers/specs/2026-05-09-无代码平台设计文档.md`

## Getting Started

1. Read the main design document for architecture
2. Set up Express.js with TypeScript
3. Add middleware layers in order (auth, rate limit, etc.)
4. Configure proxy routes to backend
5. Set up logging and error handling
6. Add health check endpoints

## Important Notes

- The gateway should be stateless
- Use Redis for rate limiting (important for production)
- JWT verification is lightweight here, permission checks still in Python
- Log all requests with request IDs for tracing
- Add request timeout handling
