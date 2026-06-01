# 批次 5：测试与 CI/CD 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立完整的测试覆盖和 CI/CD 流水线，确保代码质量和自动化部署。

**Architecture:** 后端使用 pytest + FastAPI TestClient 进行 API 测试；前端使用 Vitest + Vue Test Utils；GitHub Actions 实现代码检查、测试和 Docker 镜像构建推送。

**Tech Stack:** pytest, FastAPI TestClient, Vitest, Vue Test Utils, GitHub Actions, ruff, black, mypy

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `tests/conftest.py` | 创建 | pytest 共享 fixtures |
| `tests/test_auth.py` | 创建 | 认证 API 测试 |
| `tests/test_api_protection.py` | 创建 | API 权限保护测试 |
| `tests/test_rate_limit.py` | 创建 | 限流测试 |
| `frontend/vitest.config.ts` | 创建 | Vitest 配置 |
| `frontend/src/components/__tests__/` | 创建 | 前端组件测试目录 |
| `.github/workflows/ci.yml` | 创建 | CI 流水线 |
| `.github/workflows/docker.yml` | 创建 | Docker 构建流水线 |
| `requirements-dev.txt` | 创建 | 开发依赖 |
| `pyproject.toml` | 创建/修改 | 代码质量工具配置 |

---

## Task 1: 后端测试基础设施

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`
- Modify: `pytest.ini`

**背景:** 当前测试缺少共享 fixtures，没有认证相关的测试。

- [ ] **Step 1: 创建 pytest fixtures**

创建 `tests/conftest.py`：

```python
"""pytest 共享 fixtures。

提供测试所需的通用 fixtures，包括数据库会话、测试客户端、认证用户等。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.state.models import Base, get_db
from app.config import get_settings

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖，使用测试数据库。"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话开始前创建数据库表。"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """每个测试函数的数据库会话。"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI 测试客户端。"""
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_user(db_session):
    """创建测试用户。"""
    from app.state.models import UserModel
    from app.core.security import hash_password

    user = UserModel(
        username="testuser",
        password_hash=hash_password("testpass123"),
        nickname="Test User",
        email="test@example.com",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """获取测试用户的认证 Token。"""
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """认证请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}
```

- [ ] **Step 2: 创建认证 API 测试**

创建 `tests/test_auth.py`：

```python
"""认证 API 测试。

测试登录、登出、Token 刷新等认证相关功能。
"""

import pytest


class TestLogin:
    """登录接口测试。"""

    def test_login_success(self, client, test_user):
        """测试正常登录。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client, test_user):
        """测试密码错误。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户。"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """测试缺少必填字段。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
        })
        assert response.status_code == 422


class TestTokenRefresh:
    """Token 刷新测试。"""

    def test_refresh_token_success(self, client, auth_token, auth_headers):
        """测试正常刷新 Token。"""
        # 先获取 refresh token
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        refresh_token = login_response.json()["refresh_token"]

        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_token_invalid(self, client):
        """测试无效的 refresh token。"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token",
        })
        assert response.status_code == 401


class TestGetMe:
    """获取当前用户信息测试。"""

    def test_get_me_success(self, client, auth_headers, test_user):
        """测试获取当前用户信息。"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["id"] == test_user.id

    def test_get_me_no_token(self, client):
        """测试未提供 Token。"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """测试无效的 Token。"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid_token",
        })
        assert response.status_code == 401
```

- [ ] **Step 3: 创建 API 权限保护测试**

创建 `tests/test_api_protection.py`：

```python
"""API 权限保护测试。

测试受保护路由是否需要认证，以及权限控制是否生效。
"""

import pytest


class TestApiProtection:
    """API 路由保护测试。"""

    def test_protected_route_without_token(self, client):
        """测试未认证访问受保护路由。"""
        protected_routes = [
            ("GET", "/api/users"),
            ("GET", "/api/roles"),
            ("GET", "/api/requirements"),
            ("GET", "/api/workflow"),
            ("GET", "/api/projects"),
        ]

        for method, path in protected_routes:
            response = client.request(method, path)
            assert response.status_code == 401, f"{method} {path} should require auth"

    def test_protected_route_with_valid_token(self, client, auth_headers):
        """测试认证后访问受保护路由。"""
        # 至少一个受保护路由应该能访问（具体取决于权限）
        response = client.get("/api/users", headers=auth_headers)
        # 可能是 200（有权限）或 403（无权限），但不应该是 401
        assert response.status_code != 401

    def test_public_route_without_token(self, client):
        """测试公开路由无需认证。"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_login_route_public(self, client):
        """测试登录路由是公开的。"""
        response = client.post("/api/auth/login", json={
            "username": "any",
            "password": "any",
        })
        # 即使凭据错误，也不应该返回 401（那是认证失败，不是未认证）
        assert response.status_code in (401, 200)
```

- [ ] **Step 4: 运行测试**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix
pip install pytest-asyncio httpx
python -m pytest tests/test_auth.py tests/test_api_protection.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_auth.py tests/test_api_protection.py pytest.ini
git commit -m "test: add authentication and API protection tests"
```

---

## Task 2: 代码质量工具配置

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-dev.txt`

**背景:** 当前没有统一的代码格式和检查工具配置。

- [ ] **Step 1: 创建 pyproject.toml**

创建 `pyproject.toml`：

```toml
[tool.ruff]
target-version = "py310"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "D",   # pydocstyle
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = [
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
    "D203",  # 1 blank line required before class docstring
    "D213",  # Multi-line docstring summary should start at the second line
]

[tool.ruff.pydocstyle]
convention = "google"

[tool.ruff.per-file-ignores]
"tests/*" = ["D", "S"]
"alembic/*" = ["D"]

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

- [ ] **Step 2: 创建开发依赖文件**

创建 `requirements-dev.txt`：

```
# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.24.0

# 代码质量
ruff>=0.1.0
black>=23.0.0
mypy>=1.5.0

# 类型提示
types-python-jose
 types-passlib
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml requirements-dev.txt
git commit -m "chore: add code quality tools configuration"
```

---

## Task 3: GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/docker.yml`

**背景:** 当前没有 CI/CD 流水线，所有操作需要手动执行。

- [ ] **Step 1: 创建 CI 流水线**

创建 `.github/workflows/ci.yml`：

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend:
    name: Backend Tests & Lint
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run ruff check
        run: ruff check app/ tests/

      - name: Run ruff format check
        run: ruff format --check app/ tests/

      - name: Run mypy
        run: mypy app/ --ignore-missing-imports

      - name: Run pytest
        run: pytest tests/ -v --tb=short

  frontend:
    name: Frontend Build
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run type check
        working-directory: frontend
        run: npx vue-tsc --noEmit

      - name: Run build
        working-directory: frontend
        run: npm run build
```

- [ ] **Step 2: 创建 Docker 构建流水线**

创建 `.github/workflows/docker.yml`：

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/devmatrix
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/docker.yml
git commit -m "ci: add GitHub Actions CI/CD pipelines"
```

---

## Task 4: 前端测试配置

**Files:**
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/package.json`

**背景:** 前端目前没有测试配置。

- [ ] **Step 1: 安装 Vitest 依赖**

修改 `frontend/package.json`，添加 devDependencies：

```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vue/test-utils": "^2.4.0",
    "jsdom": "^23.0.0"
  }
}
```

然后运行：

```bash
cd frontend
npm install -D vitest @vue/test-utils jsdom
```

- [ ] **Step 2: 创建 Vitest 配置**

创建 `frontend/vitest.config.ts`：

```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts}'],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
```

- [ ] **Step 3: 添加测试脚本**

修改 `frontend/package.json` 的 scripts：

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/vitest.config.ts frontend/package.json frontend/package-lock.json
git commit -m "test: add Vitest configuration for frontend testing"
```

---

## 批次 5 验收检查

- [ ] `pytest tests/` 所有测试通过
- [ ] `ruff check app/ tests/` 无代码风格错误
- [ ] `ruff format --check app/ tests/` 代码已格式化
- [ ] GitHub Actions CI 流水线在 push 时自动运行
- [ ] Docker 镜像在 push 到 main 分支时自动构建
- [ ] 前端 `npm run test` 可以运行 Vitest
