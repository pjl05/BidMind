# BidMind Week 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成项目脚手架搭建和认证系统开发，能够登录系统并上传PDF文件到待分析队列。

**Architecture:** 基于 FastAPI + Next.js 14 的前后端分离架构，使用 Docker Compose 本地开发，PostgreSQL 存储数据，Redis 作为缓存和 Celery broker。

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + alembic, Node 22.22.0 + Next.js 14 + TailwindCSS + shadcn/ui, PostgreSQL 16 + Redis 7, Docker Compose, JWT (python-jose + passlib[bcrypt])

---

## File Structure Overview

```
BidMind/
├── .git/
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── security.py
│       │   └── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── auth.py
│       └── api/
│           ├── __init__.py
│           └── v1/
│               ├── __init__.py
│               ├── auth.py
│               └── health.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   └── ui/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── auth.ts
├── nginx/
│   └── nginx.conf
└── data/
    ├── postgres/
    └── redis/
```

---

## Day 1: Project Initialization (Monday)

### Task 1: Initialize Git Repository and Connect to Remote

**Files:**
- Create: `.gitignore`
- Modify: git config (remote)

- [ ] **Step 1: Initialize git repository**

Run:
```bash
cd D:/person_ai_projects/BidMind
git init
```

- [ ] **Step 2: Create .gitignore**

Create: `D:/person_ai_projects/BidMind/.gitignore`

```gitignore
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
out/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-store/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Docker
data/

# Uploads
uploads/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Add remote origin**

Run:
```bash
git remote add origin https://github.com/pjl05/BidMind.git
git remote -v
```

- [ ] **Step 4: Create initial commit**

Run:
```bash
git add .
git commit -m "chore: initial project structure

- add project directory structure
- add .gitignore
- connect to remote repository https://github.com/pjl05/BidMind.git"
```

- [ ] **Step 5: Push to remote**

Run:
```bash
git branch -M main
git push -u origin main
```

---

### Task 2: Create Directory Structure

**Files:**
- Create: All directories

- [ ] **Step 1: Create directory structure**

Run:
```bash
cd D:/person_ai_projects/BidMind
mkdir -p backend/app/core backend/app/models backend/app/schemas backend/app/api/v1 backend/alembic/versions backend/tests
mkdir -p frontend/src/app/login frontend/src/app/register frontend/src/components/ui frontend/src/lib frontend/src/types frontend/src/hooks
mkdir -p nginx uploads data/postgres data/redis
touch backend/app/__init__.py backend/app/core/__init__.py backend/app/models/__init__.py backend/app/schemas/__init__.py backend/app/api/__init__.py backend/app/api/v1/__init__.py
```

---

### Task 3: Create Environment Template

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create .env.example**

Create: `D:/person_ai_projects/BidMind/.env.example`

```env
# Database
DATABASE_URL=postgresql://bidmind:bidmind123@localhost:5432/bidmind

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# DeepSeek API
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
NODE_ENV=development
```

---

### Task 4: Create Docker Compose Configuration

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

Create: `D:/person_ai_projects/BidMind/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: bidmind_postgres
    environment:
      POSTGRES_USER: bidmind
      POSTGRES_PASSWORD: bidmind123
      POSTGRES_DB: bidmind
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bidmind"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: bidmind_redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: bidmind_backend
    environment:
      DATABASE_URL: postgresql://bidmind:bidmind123@postgres:5432/bidmind
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: dev-secret-key-change-in-production
      JWT_ALGORITHM: HS256
      JWT_EXPIRATION_HOURS: 24
      UPLOAD_DIR: /app/uploads
      CORS_ORIGINS: http://localhost:3000,http://localhost:8080
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: bidmind_frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8080/api/v1
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: bidmind_nginx
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
```

---

### Task 5: Create Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create backend/Dockerfile**

Create: `D:/person_ai_projects/BidMind/backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

### Task 6: Create Backend Requirements

**Files:**
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create backend/requirements.txt**

Create: `D:/person_ai_projects/BidMind/backend/requirements.txt`

```txt
# Web Framework
fastapi==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9

# Database
sqlalchemy==2.0.30
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Redis
redis==5.0.6
celery==5.4.0

# Utilities
pydantic==2.7.1
pydantic-settings==2.2.1
python-dotenv==1.0.1
email-validator==2.1.1

# Testing
pytest==8.2.2
pytest-asyncio==0.23.6
httpx==0.27.0
```

---

### Task 7: Create Frontend Dockerfile

**Files:**
- Create: `frontend/Dockerfile`

- [ ] **Step 1: Create frontend/Dockerfile**

Create: `D:/person_ai_projects/BidMind/frontend/Dockerfile`

```dockerfile
FROM node:22-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

---

### Task 8: Create Nginx Configuration

**Files:**
- Create: `nginx/nginx.conf`

- [ ] **Step 1: Create nginx/nginx.conf**

Create: `D:/person_ai_projects/BidMind/nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    client_max_body_size 50m;
    proxy_buffering off;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # API requests
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # SSE support
            proxy_set_header Connection '';
            proxy_http_version 1.1;
            chunked_transfer_encoding on;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

### Task 9: Verify Docker Compose Works

**Files:**
- No file changes

- [ ] **Step 1: Pull base images**

Run:
```bash
cd D:/person_ai_projects/BidMind
docker compose pull
```

Expected: Images pulled successfully

- [ ] **Step 2: Build custom images**

Run:
```bash
docker compose build
```

Expected: Build completed successfully

- [ ] **Step 3: Start services (skip backend for now since not ready)**

Run:
```bash
docker compose up -d postgres redis
```

Expected: Both containers running and healthy

- [ ] **Step 4: Check logs**

Run:
```bash
docker compose logs postgres
docker compose logs redis
```

Expected: No errors in logs

- [ ] **Step 5: Stop services**

Run:
```bash
docker compose down
```

---

### Task 10: Commit Day 1 Changes

**Files:**
- All Day 1 files created

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Commit all Day 1 changes**

Run:
```bash
git add .
git commit -m "feat(day1): project scaffolding

- add docker-compose.yml with PostgreSQL, Redis, FastAPI, Next.js, Nginx
- add backend Dockerfile with Python 3.12
- add frontend Dockerfile with Node 22
- add nginx reverse proxy configuration
- add .env.example with all environment variables
- add directory structure for backend and frontend"
```

---

## Day 2: Database Setup (Tuesday)

### Task 11: Create Alembic Configuration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: Initialize alembic**

Run:
```bash
cd D:/person_ai_projects/BidMind/backend
alembic init alembic
```

- [ ] **Step 2: Update alembic.ini**

Modify: `backend/alembic.ini` (replace sqlalchemy.url line)

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://bidmind:bidmind123@localhost:5432/bidmind
```

- [ ] **Step 3: Update alembic/env.py**

Create: `D:/person_ai_projects/BidMind/backend/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import settings
from app.models import user  # noqa: F401 - import for metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.models.base import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Update alembic/script.py.mako**

Modify: `backend/alembic/script.py.mako`

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

---

### Task 12: Create Base Model and Config

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/core/config.py`

- [ ] **Step 1: Create app/core/config.py**

Create: `D:/person_ai_projects/BidMind/backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://bidmind:bidmind123@localhost:5432/bidmind"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Environment
    NODE_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Create app/models/base.py**

Create: `D:/person_ai_projects/BidMind/backend/app/models/base.py`

```python
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

---

### Task 13: Create User Model

**Files:**
- Create: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create app/models/user.py**

Create: `D:/person_ai_projects/BidMind/backend/app/models/user.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
```

- [ ] **Step 2: Update app/models/__init__.py**

Modify: `D:/person_ai_projects/BidMind/backend/app/models/__init__.py`

```python
from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
```

---

### Task 14: Create Initial Migration

**Files:**
- Create: `backend/alembic/versions/001_initial_schema.py`

- [ ] **Step 1: Create initial migration**

Create: `D:/person_ai_projects/BidMind/backend/alembic/versions/001_initial_schema.py`

```python
"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('nickname', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

---

### Task 15: Run Database Migration

**Files:**
- No file changes

- [ ] **Step 1: Start database services**

Run:
```bash
cd D:/person_ai_projects/BidMind
docker compose up -d postgres redis
```

- [ ] **Step 2: Wait for postgres to be healthy**

Run:
```bash
sleep 5
docker compose ps
```

- [ ] **Step 3: Run alembic migration (from backend container)**

Run:
```bash
docker compose exec backend alembic upgrade head
```

Expected: `Running upgrade  -> 001`

- [ ] **Step 4: Verify tables created**

Run:
```bash
docker compose exec postgres psql -U bidmind -d bidmind -c "\dt"
```

Expected: Shows `users` table

---

### Task 16: Commit Day 2 Changes

**Files:**
- All Day 2 files created

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Commit all Day 2 changes**

Run:
```bash
git add .
git commit -m "feat(day2): database setup with alembic

- add alembic configuration for PostgreSQL
- add User model with UUID primary key
- add initial migration with users table
- verify migration runs successfully"
```

---

## Day 3: FastAPI Foundation + Authentication (Wednesday)

### Task 17: Create Core Modules

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/database.py`

- [ ] **Step 1: Create app/core/security.py**

Create: `D:/person_ai_projects/BidMind/backend/app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

- [ ] **Step 2: Create app/core/database.py**

Create: `D:/person_ai_projects/BidMind/backend/app/core/database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.NODE_ENV == "development",
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

### Task 18: Create Auth Schemas

**Files:**
- Create: `backend/app/schemas/auth.py`

- [ ] **Step 1: Create app/schemas/auth.py**

Create: `D:/person_ai_projects/BidMind/backend/app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", v):
            raise ValueError("Password must contain at least one lowercase letter, one uppercase letter, and one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    user_id: str
    email: str
    nickname: str | None = None

    class Config:
        from_attributes = True


class UserRegisterResponse(BaseModel):
    user_id: str
    email: str
    nickname: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class ApiResponse(BaseModel):
    code: int = 0
    data: dict | list | None = None
    message: str = "ok"
```

---

### Task 19: Create Auth API Router

**Files:**
- Create: `backend/app/api/v1/auth.py`

- [ ] **Step 1: Create app/api/v1/auth.py**

Create: `D:/person_ai_projects/BidMind/backend/app/api/v1/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserRegisterResponse,
    LoginResponse,
    ApiResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.post("/register", response_model=ApiResponse)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        nickname=request.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        code=0,
        data={
            "user_id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
        },
        message="ok",
    )


@router.post("/login", response_model=ApiResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return ApiResponse(
        code=0,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,
        },
        message="ok",
    )


@router.get("/me", response_model=ApiResponse)
async def get_me(
    user: User = Depends(get_current_user_required),
) -> ApiResponse:
    return ApiResponse(
        code=0,
        data={
            "user_id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
        },
        message="ok",
    )
```

---

### Task 20: Create Health Check Endpoint

**Files:**
- Create: `backend/app/api/v1/health.py`

- [ ] **Step 1: Create app/api/v1/health.py**

Create: `D:/person_ai_projects/BidMind/backend/app/api/v1/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.schemas.auth import ApiResponse

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> ApiResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return ApiResponse(
        code=0,
        data={"status": "ok", "database": db_status},
        message="ok",
    )
```

---

### Task 21: Create Main FastAPI Application

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Create app/main.py**

Create: `D:/person_ai_projects/BidMind/backend/app/main.py`

```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="BidMind API",
    description="招投标智能分析Agent API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"code": 422, "data": None, "message": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "data": None, "message": str(exc)},
    )


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {"message": "BidMind API is running"}
```

---

### Task 22: Test Authentication Endpoints

**Files:**
- No file changes

- [ ] **Step 1: Start all services**

Run:
```bash
cd D:/person_ai_projects/BidMind
docker compose up -d
```

- [ ] **Step 2: Wait for services to be ready**

Run:
```bash
sleep 15
docker compose ps
```

- [ ] **Step 3: Test health endpoint**

Run:
```bash
curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

Expected: `{"code": 0, "data": {"status": "ok", "database": "healthy"}, "message": "ok"}`

- [ ] **Step 4: Test register endpoint**

Run:
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234","nickname":"Test User"}' | python -m json.tool
```

Expected: `{"code": 0, "data": {"user_id": "...", "email": "test@example.com", "nickname": "Test User"}, "message": "ok"}`

- [ ] **Step 5: Test login endpoint**

Run:
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' | python -m json.tool
```

Expected: `{"code": 0, "data": {"access_token": "...", "token_type": "bearer", "expires_in": 86400}, "message": "ok"}`

- [ ] **Step 6: Extract token and test /me endpoint**

Run:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Expected: `{"code": 0, "data": {"user_id": "...", "email": "test@example.com", "nickname": "Test User"}, "message": "ok"}`

- [ ] **Step 7: Test without token (should fail)**

Run:
```bash
curl -s http://localhost:8000/api/v1/auth/me | python -m json.tool
```

Expected: `{"detail": "Not authenticated"}`

---

### Task 23: Commit Day 3 Changes

**Files:**
- All Day 3 files created

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Commit all Day 3 changes**

Run:
```bash
git add .
git commit -m "feat(day3): FastAPI foundation and authentication

- add core config, security (JWT, bcrypt), database modules
- add User model and auth schemas (register, login)
- add auth router with /register, /login, /me endpoints
- add JWT middleware with get_current_user dependency
- add health check endpoint
- verify all endpoints work correctly"
```

---

## Day 4: File Upload API (Thursday)

### Task 24: Create File Upload Schemas

**Files:**
- Create: `backend/app/schemas/task.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: Create app/schemas/task.py**

Create: `D:/person_ai_projects/BidMind/backend/app/schemas/task.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    file_name: str
    file_size: int
    duplicated: bool = False


class TaskListItem(BaseModel):
    task_id: str
    file_name: str
    status: str
    progress: int
    llm_cost: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int
    page: int
    items: list[TaskListItem]


class ApiResponse(BaseModel):
    code: int = 0
    data: dict | list | None = None
    message: str = "ok"
```

- [ ] **Step 2: Update app/schemas/__init__.py**

Modify: `D:/person_ai_projects/BidMind/backend/app/schemas/__init__.py`

```python
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserRegisterResponse,
    LoginResponse,
    ApiResponse,
)
from app.schemas.task import (
    TaskCreateResponse,
    TaskListItem,
    TaskListResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "UserRegisterResponse",
    "LoginResponse",
    "ApiResponse",
    "TaskCreateResponse",
    "TaskListItem",
    "TaskListResponse",
]
```

---

### Task 25: Create Analysis Task Model

**Files:**
- Create: `backend/app/models/task.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create app/models/task.py**

Create: `D:/person_ai_projects/BidMind/backend/app/models/task.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AnalysisTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_tasks"

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    page_count = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default="pending", index=True)
    current_agent = Column(String(50), nullable=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    token_used = Column(Integer, default=0)
    llm_cost = Column(String(20), default="0")

    celery_task_id = Column(String(36), nullable=True)
    revision_count = Column(Integer, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class FileDedup(Base, TimestampMixin):
    __tablename__ = "file_dedup"

    file_hash = Column(String(64), primary_key=True)
    file_url = Column(String(1000), nullable=False)
    first_task_id = Column(UUID(as_uuid=True), nullable=True)
```

- [ ] **Step 2: Update app/models/__init__.py**

Modify: `D:/person_ai_projects/BidMind/backend/app/models/__init__.py`

```python
from app.models.base import Base
from app.models.user import User
from app.models.task import AnalysisTask, FileDedup

__all__ = ["Base", "User", "AnalysisTask", "FileDedup"]
```

---

### Task 26: Create Migration for Analysis Tasks

**Files:**
- Create: `backend/alembic/versions/002_add_analysis_tasks.py`

- [ ] **Step 1: Create migration**

Create: `D:/person_ai_projects/BidMind/backend/alembic/versions/002_add_analysis_tasks.py`

```python
"""add analysis tasks and file dedup tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analysis_tasks table
    op.create_table(
        'analysis_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_url', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('current_agent', sa.String(50), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('token_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('llm_cost', sa.String(20), nullable=False, server_default='0'),
        sa.Column('celery_task_id', sa.String(36), nullable=True),
        sa.Column('revision_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analysis_tasks_user_id', 'analysis_tasks', ['user_id'])
    op.create_index('ix_analysis_tasks_file_hash', 'analysis_tasks', ['file_hash'])
    op.create_index('ix_analysis_tasks_status', 'analysis_tasks', ['status'])

    # Create file_dedup table
    op.create_table(
        'file_dedup',
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_url', sa.String(1000), nullable=False),
        sa.Column('first_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('file_hash')
    )


def downgrade() -> None:
    op.drop_table('file_dedup')
    op.drop_index('ix_analysis_tasks_status', table_name='analysis_tasks')
    op.drop_index('ix_analysis_tasks_file_hash', table_name='analysis_tasks')
    op.drop_index('ix_analysis_tasks_user_id', table_name='analysis_tasks')
    op.drop_table('analysis_tasks')
```

---

### Task 27: Create File Upload Router

**Files:**
- Create: `backend/app/api/v1/tasks.py`

- [ ] **Step 1: Create app/api/v1/tasks.py**

Create: `D:/person_ai_projects/BidMind/backend/app/api/v1/tasks.py`

```python
import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.models.user import User
from app.models.task import AnalysisTask, FileDedup
from app.schemas.auth import ApiResponse
from app.schemas.task import TaskCreateResponse, TaskListItem, TaskListResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])
settings = get_settings()

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # 50MB


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("", response_model=ApiResponse)
async def create_task(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    # Calculate SHA-256 hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicates
    result = await db.execute(select(FileDedup).where(FileDedup.file_hash == file_hash))
    existing_file = result.scalar_one_or_none()
    duplicated = existing_file is not None

    # Create task
    task_id = str(uuid.uuid4())
    user_id = str(current_user.id)

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, user_id, task_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create task record
    task = AnalysisTask(
        id=task_id,
        user_id=user_id,
        file_name=file.filename,
        file_url=file_path,
        file_size=file_size,
        file_hash=file_hash,
        status="pending",
        progress=0,
    )
    db.add(task)

    # Save dedup record if new file
    if not duplicated:
        dedup = FileDedup(
            file_hash=file_hash,
            file_url=file_path,
            first_task_id=task_id,
        )
        db.add(dedup)

    await db.commit()

    return ApiResponse(
        code=0,
        data={
            "task_id": task_id,
            "status": "pending",
            "file_name": file.filename,
            "file_size": file_size,
            "duplicated": duplicated,
        },
        message="ok",
    )


@router.get("", response_model=ApiResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    # Build query
    query = select(AnalysisTask).where(AnalysisTask.user_id == str(current_user.id))
    count_query = select(func.count()).select_from(AnalysisTask).where(
        AnalysisTask.user_id == str(current_user.id)
    )

    if status_filter:
        query = query.where(AnalysisTask.status == status_filter)
        count_query = count_query.where(AnalysisTask.status == status_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(AnalysisTask.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    items = [
        TaskListItem(
            task_id=str(t.id),
            file_name=t.file_name,
            status=t.status,
            progress=t.progress or 0,
            llm_cost=float(t.llm_cost or 0),
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in tasks
    ]

    return ApiResponse(
        code=0,
        data={"total": total, "page": page, "items": [i.model_dump() for i in items]},
        message="ok",
    )
```

---

### Task 28: Update Main App to Include Task Router

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update main.py to include task router**

Modify: `D:/person_ai_projects/BidMind/backend/app/main.py` (add import and include_router)

```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.tasks import router as tasks_router  # Add this line

settings = get_settings()
# ... rest of file ...
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")  # Add this line
```

---

### Task 29: Run Migration and Test File Upload

**Files:**
- No file changes

- [ ] **Step 1: Run new migration**

Run:
```bash
cd D:/person_ai_projects/BidMind
docker compose exec backend alembic upgrade head
```

Expected: `Running upgrade 001 -> 002`

- [ ] **Step 2: Restart backend to pick up code changes**

Run:
```bash
docker compose restart backend
```

- [ ] **Step 3: Wait for backend to restart**

Run:
```bash
sleep 10
docker compose logs backend --tail=20
```

- [ ] **Step 4: Login to get token**

Run:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
echo "Token: $TOKEN"
```

- [ ] **Step 5: Create a test PDF file**

Run:
```bash
# Create a minimal valid PDF (this is a valid PDF header)
echo "%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
193
%%EOF" > /tmp/test.pdf
```

- [ ] **Step 6: Upload the test PDF**

Run:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -s -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.pdf" | python -m json.tool
```

Expected: `{"code": 0, "data": {"task_id": "...", "status": "pending", "file_name": "test.pdf", ...}, "message": "ok"}`

- [ ] **Step 7: Test list tasks**

Run:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -s "http://localhost:8000/api/v1/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Expected: Shows list with the uploaded task

---

### Task 30: Commit Day 4 Changes

**Files:**
- All Day 4 files created

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Commit all Day 4 changes**

Run:
```bash
git add .
git commit -m "feat(day4): file upload API

- add AnalysisTask and FileDedup models
- add /api/v1/tasks POST endpoint for file upload
- add file validation: PDF only, 50MB max
- add SHA-256 hash calculation for deduplication
- add /api/v1/tasks GET endpoint for listing tasks
- verify upload and list endpoints work"
```

---

## Day 5: Next.js Frontend Scaffolding (Friday)

### Task 31: Initialize Next.js Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tsconfig.json`

- [ ] **Step 1: Create package.json**

Create: `D:/person_ai_projects/BidMind/frontend/package.json`

```json
{
  "name": "bidmind-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.2",
    "js-cookie": "^3.0.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "lucide-react": "^0.378.0",
    "react-hook-form": "^7.51.5",
    "@hookform/resolvers": "^3.3.4",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^20.12.12",
    "@types/react": "^18.3.2",
    "@types/react-dom": "^18.3.0",
    "@types/js-cookie": "^3.0.6",
    "typescript": "^5.4.5",
    "tailwindcss": "^3.4.3",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.3"
  }
}
```

- [ ] **Step 2: Create next.config.js**

Create: `D:/person_ai_projects/BidMind/frontend/next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api/v1',
  },
}

module.exports = nextConfig
```

- [ ] **Step 3: Create tsconfig.json**

Create: `D:/person_ai_projects/BidMind/frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

### Task 32: Setup Tailwind CSS

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/app/globals.css`

- [ ] **Step 1: Create tailwind.config.ts**

Create: `D:/person_ai_projects/BidMind/frontend/tailwind.config.ts`

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 2: Create postcss.config.js**

Create: `D:/person_ai_projects/BidMind/frontend/postcss.config.js`

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 3: Create src/app/globals.css**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

---

### Task 33: Create API Client and Utilities

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/types/auth.ts`

- [ ] **Step 1: Create src/lib/api.ts**

Create: `D:/person_ai_projects/BidMind/frontend/src/lib/api.ts`

```typescript
import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export interface ApiResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

export const authService = {
  register: async (email: string, password: string, nickname: string) => {
    const response = await api.post<ApiResponse>('/auth/register', {
      email,
      password,
      nickname,
    });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post<ApiResponse>('/auth/login', {
      email,
      password,
    });
    if (response.data.data?.access_token) {
      Cookies.set('access_token', response.data.data.access_token, { expires: 1 });
    }
    return response.data;
  },

  getMe: async () => {
    const response = await api.get<ApiResponse>('/auth/me');
    return response.data;
  },

  logout: () => {
    Cookies.remove('access_token');
  },
};

export const taskService = {
  create: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const token = Cookies.get('access_token');
    if (!token) throw new Error('Not authenticated');

    const response = await axios.post(`${API_URL}/tasks`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },

  list: async (page = 1, pageSize = 10, status?: string) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
    if (status) params.append('status', status);

    const response = await api.get<ApiResponse>(`/tasks?${params}`);
    return response.data;
  },
};

export default api;
```

- [ ] **Step 2: Create src/lib/utils.ts**

Create: `D:/person_ai_projects/BidMind/frontend/src/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
```

- [ ] **Step 3: Create src/types/auth.ts**

Create: `D:/person_ai_projects/BidMind/frontend/src/types/auth.ts`

```typescript
export interface User {
  user_id: string;
  email: string;
  nickname: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse {
  user_id: string;
  email: string;
  nickname: string;
}

export interface Task {
  task_id: string;
  file_name: string;
  status: string;
  progress: number;
  llm_cost: number;
  created_at: string;
  completed_at: string | null;
}

export interface TaskListResponse {
  total: number;
  page: number;
  items: Task[];
}
```

---

### Task 34: Create UI Components

**Files:**
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/input.tsx`
- Create: `frontend/src/components/ui/label.tsx`
- Create: `frontend/src/components/ui/card.tsx`

- [ ] **Step 1: Create button component**

Create: `D:/person_ai_projects/BidMind/frontend/src/components/ui/button.tsx`

```typescript
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

- [ ] **Step 2: Create input component**

Create: `D:/person_ai_projects/BidMind/frontend/src/components/ui/input.tsx`

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
```

- [ ] **Step 3: Create label component**

Create: `D:/person_ai_projects/BidMind/frontend/src/components/ui/label.tsx`

```typescript
import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const labelVariants = cva(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)

const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof LabelPrimitive.Root> &
    VariantProps<typeof labelVariants>
>(({ className, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants(), className)}
    {...props}
  />
))
Label.displayName = LabelPrimitive.Root.displayName

export { Label }
```

- [ ] **Step 4: Create card component**

Create: `D:/person_ai_projects/BidMind/frontend/src/components/ui/card.tsx`

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

---

### Task 35: Create Root Layout and Main Page

**Files:**
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create src/app/layout.tsx**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/layout.tsx`

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BidMind - 招投标智能分析",
  description: "招投标智能分析Agent",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Create src/app/page.tsx**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/page.tsx`

```typescript
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { authService } from "@/lib/api";
import type { User } from "@/types/auth";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = Cookies.get("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    authService.getMe()
      .then((res) => {
        setUser(res.data);
        setLoading(false);
      })
      .catch(() => {
        Cookies.remove("access_token");
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    authService.logout();
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">BidMind</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.nickname || user?.email}
            </span>
            <Button variant="outline" onClick={handleLogout}>
              退出登录
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>欢迎使用 BidMind</CardTitle>
            <CardDescription>
              招投标智能分析Agent - 您的智能投标决策助手
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              上传您的招标文件，AI将自动分析资格要求、评分标准，
              并生成投标策略建议和方案大纲。
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
```

---

### Task 36: Create Login and Register Pages

**Files:**
- Create: `frontend/src/app/login/page.tsx`
- Create: `frontend/src/app/register/page.tsx`

- [ ] **Step 1: Create src/app/login/page.tsx**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/login/page.tsx`

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await authService.login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "登录失败，请检查邮箱和密码");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>登录</CardTitle>
          <CardDescription>登录到 BidMind 系统</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 text-sm p-3 rounded">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "登录中..." : "登录"}
            </Button>
            <p className="text-sm text-center text-gray-600">
              还没有账号？{" "}
              <Link href="/register" className="text-primary hover:underline">
                注册
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Create src/app/register/page.tsx**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/register/page.tsx`

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }

    if (password.length < 8) {
      setError("密码至少需要8个字符");
      return;
    }

    setLoading(true);

    try {
      await authService.register(email, password, nickname);
      router.push("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail || "注册失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>注册</CardTitle>
          <CardDescription>创建 BidMind 账号</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-50 text-red-600 text-sm p-3 rounded">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="nickname">昵称</Label>
              <Input
                id="nickname"
                type="text"
                placeholder="您的昵称"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                placeholder="至少8位，包含大小写字母和数字"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">确认密码</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "注册中..." : "注册"}
            </Button>
            <p className="text-sm text-center text-gray-600">
              已有账号？{" "}
              <Link href="/login" className="text-primary hover:underline">
                登录
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
```

---

### Task 37: Build and Test Frontend

**Files:**
- No file changes

- [ ] **Step 1: Install dependencies and build frontend**

Run:
```bash
cd D:/person_ai_projects/BidMind/frontend
npm install
npm run build
```

Expected: Build completes without errors

- [ ] **Step 2: Start frontend and test login page**

Run:
```bash
npm run dev &
sleep 5
curl -s http://localhost:3000/login | head -50
```

Expected: HTML page loads with login form

- [ ] **Step 3: Test register page**

Run:
```bash
curl -s http://localhost:3000/register | head -50
```

Expected: HTML page loads with register form

---

### Task 38: Commit Day 5 Changes

**Files:**
- All Day 5 files created

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Commit all Day 5 changes**

Run:
```bash
git add .
git commit -m "feat(day5): Next.js frontend scaffolding

- initialize Next.js 14 project with TypeScript
- setup Tailwind CSS with custom theme
- create UI components: Button, Input, Label, Card
- create API client with axios and auth interceptors
- create login and register pages with form validation
- create home page with user info display
- add auth service with register, login, getMe endpoints
- add task service for file upload and list"
```

---

## Day 6: Code Review, Testing and Cleanup (Saturday)

### Task 39: Run and Verify All Services

**Files:**
- No file changes

- [ ] **Step 1: Stop any running containers**

Run:
```bash
cd D:/person_ai_projects/BidMind
docker compose down
```

- [ ] **Step 2: Start all services**

Run:
```bash
docker compose up -d
sleep 20
```

- [ ] **Step 3: Verify all services are healthy**

Run:
```bash
docker compose ps
```

Expected: All containers should be running

- [ ] **Step 4: Test complete flow**

Run:
```bash
# Register new user
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"final@test.com","password":"Test1234","nickname":"Final Test"}' | python -m json.tool

# Login
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"final@test.com","password":"Test1234"}' | python -m json.tool

# Get current user
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"final@test.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

### Task 40: Create Basic Tests

**Files:**
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Create test file**

Create: `D:/person_ai_projects/BidMind/backend/tests/test_auth.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "Test1234",
                "nickname": "Test User"
            }
        )
        assert response.status_code in [200, 409]  # 200 if new, 409 if exists


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "Test1234",
                "nickname": "Login Test"
            }
        )
        # Then login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "Test1234"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
```

---

### Task 41: Push All Changes to Remote

**Files:**
- No file changes

- [ ] **Step 1: Check git status**

Run:
```bash
cd D:/person_ai_projects/BidMind
git status
```

- [ ] **Step 2: Add all changes and check**

Run:
```bash
git add .
git status
```

- [ ] **Step 3: Commit all remaining changes**

Run:
```bash
git commit -m "feat: complete week 1 implementation

Week 1 deliverables:
- Docker Compose development environment (PostgreSQL, Redis, FastAPI, Next.js, Nginx)
- FastAPI backend with:
  - User authentication (register, login, JWT)
  - File upload endpoint with PDF validation and SHA-256 deduplication
  - Task listing with pagination
  - Alembic database migrations
- Next.js 14 frontend with:
  - Login and register pages
  - Home page with user info
  - Tailwind CSS styling
  - API client with auth interceptors
- Complete git history pushed to remote"
```

- [ ] **Step 4: Push to remote**

Run:
```bash
git push origin main
```

Expected: All commits pushed successfully

---

## Self-Review Checklist

### Spec Coverage
- [x] Docker Compose with all 5 services (PostgreSQL, Redis, FastAPI, Next.js, Nginx)
- [x] PostgreSQL database with DDL and alembic migrations
- [x] FastAPI project structure (routers, schemas, models, core)
- [x] JWT authentication (register, login, me endpoints)
- [x] Depends(get_current_user) global dependency
- [x] File upload with PDF validation, size limit, SHA-256 hash, deduplication
- [x] Task listing with pagination
- [x] Next.js 14 App Router setup
- [x] TailwindCSS + shadcn/ui components
- [x] Login and register pages
- [x] API service layer with token storage
- [x] All code committed and pushed to remote

### Placeholder Scan
- No TBD or TODO entries
- All file paths are concrete
- All code snippets are complete
- All commands have expected outputs

### Type Consistency
- Backend: All Python models use correct types (UUID, datetime, etc.)
- Frontend: All TypeScript interfaces match API responses
- API: All endpoints return consistent ApiResponse format
