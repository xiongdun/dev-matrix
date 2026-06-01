# 智能代码审查与质量门禁（Code Review AI）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 DevMatrix 增加智能代码审查能力，在开发阶段 Agent 生成代码补丁后，自动进行多维度质量审查并生成报告，作为人工审批的前置质量门禁。

**Architecture:** 采用混合方案（LLM + 静态分析）。Phase 1 先实现基于 LLM 的审查 Agent 和报告展示；Phase 2 集成 semgrep 静态分析工具增强审查准确性；Phase 3 实现可配置的质量门禁规则。

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, semgrep, LLM (OpenAI/Anthropic/DeepSeek)

---

## 文件结构

### 后端新增/修改

| 文件 | 职责 |
|------|------|
| `app/agents/code_reviewer.py` | Code Reviewer Agent 实现，封装 LLM 审查逻辑 |
| `app/api/code_review.py` | 代码审查 REST API（创建审查、获取报告、列表查询） |
| `app/state/models.py` | 新增 CodeReviewModel 数据库模型 |
| `app/prompts/code_review.py` | 代码审查 prompt 模板 |
| `app/static_analysis/` | 静态分析模块（Phase 2） |
| `app/static_analysis/engine.py` | 静态分析引擎，封装 semgrep 调用 |
| `app/static_analysis/rules/` | 自定义规则库 |
| `app/api/__init__.py` | 注册 code_review 路由 |
| `app/agents/__init__.py` | 注册 Code Reviewer Agent |

### 前端新增/修改

| 文件 | 职责 |
|------|------|
| `frontend/src/pages/CodeReviewPage.vue` | 代码审查报告详情页 |
| `frontend/src/pages/CodeReviewListPage.vue` | 审查历史列表页 |
| `frontend/src/components/code-review/` | 审查相关组件 |
| `frontend/src/components/code-review/ReviewReport.vue` | 审查报告展示组件 |
| `frontend/src/components/code-review/IssueCard.vue` | 单个问题卡片 |
| `frontend/src/components/code-review/ScoreBadge.vue` | 质量分数徽章 |
| `frontend/src/api/index.ts` | 新增代码审查 API 方法 |
| `frontend/src/router.ts` | 新增代码审查路由 |
| `frontend/src/components/Sidebar.vue` | 新增代码审查菜单 |
| `frontend/src/i18n/locales/zh.json` | 新增中文翻译 |
| `frontend/src/i18n/locales/en.json` | 新增英文翻译 |

---

## Phase 1: LLM 审查（基础功能）

### Task 1: 数据库模型

**Files:**
- Create: `app/state/models.py` (在现有文件中追加)

**目标:** 创建 CodeReviewModel 存储审查结果。

- [ ] **Step 1: 定义 CodeReviewModel**

在 `app/state/models.py` 的 `WorkflowInstanceModel` 类之后追加：

```python
class CodeReviewModel(Base):
    """代码审查记录模型。"""

    __tablename__ = "code_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workflow_tasks.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / running / completed / failed
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 0-100 质量分数
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 审查总结
    issues_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON 序列化的问题列表
    improvements_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSON 序列化的改进建议
    raw_diff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 原始代码 diff
    llm_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # 使用的 LLM 模型
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # 审查耗时
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    task: Mapped["WorkflowTaskModel"] = relationship("WorkflowTaskModel")
```

- [ ] **Step 2: 更新数据库初始化**

确保 `init_db()` 函数会创建 `code_reviews` 表。检查 `app/state/models.py` 中 `init_db` 是否使用 `Base.metadata.create_all(bind=engine)`，如果是则自动包含新表。

- [ ] **Step 3: 提交**

```bash
git add app/state/models.py
git commit -m "feat(code-review): add CodeReviewModel database model"
```

---

### Task 2: 代码审查 Prompt 模板

**Files:**
- Create: `app/prompts/code_review.py`

**目标:** 创建结构化 prompt 模板，指导 LLM 输出标准化的审查报告。

- [ ] **Step 1: 创建 prompt 文件**

```python
"""代码审查 Prompt 模板。"""

from typing import Final

CODE_REVIEW_SYSTEM_PROMPT: Final[str] = (
    "你是一位资深的代码审查专家，拥有 10 年以上的软件开发经验。"
    "你的任务是对代码补丁进行全面的质量审查，并输出结构化的审查报告。"
    "\n\n审查维度：\n"
    "1. 代码规范：命名规范、代码格式、注释完整性\n"
    "2. 安全漏洞：SQL 注入、XSS、敏感信息泄露、依赖漏洞\n"
    "3. 性能问题：时间复杂度、内存泄漏、N+1 查询、循环内 IO\n"
    "4. 可维护性：圈复杂度、重复代码、函数过长、职责单一\n"
    "5. 测试覆盖：新增代码是否有对应的单元测试\n"
    "6. 架构合规：是否符合项目的架构约定和设计模式\n\n"
    "严重级别定义：\n"
    "- must_fix: 必须修复，存在安全漏洞、性能问题或明显 bug\n"
    "- should_fix: 建议修复，影响代码质量或可读性\n"
    "- nice_to_have: 可选优化，锦上添花\n\n"
    "输出格式要求（必须严格遵循 JSON 格式）：\n"
    '{\n'
    '  "score": <0-100 的整数分数>,\n'
    '  "summary": "<一句话总结审查结果>",\n'
    '  "issues": [\n'
    '    {\n'
    '      "file": "<文件路径>",\n'
    '      "line": <行号或 null>,\n'
    '      "severity": "must_fix|should_fix|nice_to_have",\n'
    '      "category": "security|performance|maintainability|style|testing|architecture",\n'
    '      "title": "<问题标题>",\n'
    '      "description": "<问题详细描述>",\n'
    '      "suggestion": "<具体的修复建议，包含代码示例>"\n'
    '    }\n'
    '  ],\n'
    '  "improvements": [\n'
    '    {\n'
    '      "category": "<类别>",\n'
    '      "suggestion": "<改进建议>"\n'
    '    }\n'
    '  ]\n'
    '}'
)


def build_code_review_prompt(diff: str, project_context: str = "") -> str:
    """构建代码审查用户 prompt。

    Args:
        diff: 代码 diff 内容。
        project_context: 项目上下文信息（技术栈、架构约定等）。

    Returns:
        str: 完整的用户 prompt。
    """
    context_section = f"\n\n项目上下文：\n{project_context}\n" if project_context else ""

    return (
        f"请对以下代码补丁进行审查：{context_section}\n\n"
        f"```diff\n{diff}\n```\n\n"
        f"请输出 JSON 格式的审查报告，不要包含任何其他内容。"
    )
```

- [ ] **Step 2: 提交**

```bash
git add app/prompts/code_review.py
git commit -m "feat(code-review): add code review prompt templates"
```

---

### Task 3: Code Reviewer Agent

**Files:**
- Create: `app/agents/code_reviewer.py`
- Modify: `app/agents/__init__.py`

**目标:** 实现 Code Reviewer Agent，调用 LLM 进行代码审查。

- [ ] **Step 1: 创建 Agent 文件**

```python
"""Code Reviewer Agent - 智能代码审查。"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base import Agent, AgentRegistry
from app.prompts.code_review import (
    CODE_REVIEW_SYSTEM_PROMPT,
    build_code_review_prompt,
)
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


@AgentRegistry.register("code_reviewer")
class CodeReviewerAgent(Agent):
    """代码审查 Agent，使用 LLM 对代码补丁进行质量审查。"""

    name = "code_reviewer"
    display_name = "Code Reviewer"
    description = "智能代码审查专家，自动检测代码质量、安全漏洞和性能问题"

    def __init__(self) -> None:
        super().__init__()
        self.llm_client = LLMClient()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码审查。

        Args:
            context: 包含以下字段：
                - diff: 代码 diff 字符串
                - project_context: 项目上下文（可选）
                - model: 指定 LLM 模型（可选）

        Returns:
            Dict: 审查报告，包含 score、issues、improvements 等。
        """
        diff = context.get("diff", "")
        project_context = context.get("project_context", "")
        model = context.get("model")

        if not diff:
            return {
                "score": 0,
                "summary": "没有提供代码 diff",
                "issues": [],
                "improvements": [],
            }

        prompt = build_code_review_prompt(diff, project_context)

        start_time = time.time()
        try:
            response = await self.llm_client.chat_completion(
                system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=model,
                temperature=0.2,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            # 解析 JSON 响应
            content = response.get("content", "")
            # 尝试提取 JSON 部分（LLM 可能会包裹在 markdown 代码块中）
            json_str = self._extract_json(content)
            report = json.loads(json_str)

            # 确保必要字段存在
            report.setdefault("score", 0)
            report.setdefault("summary", "")
            report.setdefault("issues", [])
            report.setdefault("improvements", [])

            # 标准化问题格式
            for issue in report["issues"]:
                issue.setdefault("line", None)
                issue.setdefault("file", "")

            report["duration_ms"] = duration_ms
            report["llm_model"] = response.get("model", model or "default")

            logger.info(
                "Code review completed: score=%d, issues=%d, duration=%dms",
                report["score"],
                len(report["issues"]),
                duration_ms,
            )

            return report

        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            return {
                "score": 0,
                "summary": f"审查结果解析失败：{e}",
                "issues": [],
                "improvements": [],
                "error": str(e),
                "raw_response": content if "content" in locals() else "",
            }
        except Exception as e:
            logger.exception("Code review failed")
            return {
                "score": 0,
                "summary": f"审查失败：{e}",
                "issues": [],
                "improvements": [],
                "error": str(e),
            }

    def _extract_json(self, content: str) -> str:
        """从 LLM 响应中提取 JSON 字符串。"""
        content = content.strip()

        # 尝试查找 markdown 代码块
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()

        # 尝试查找 JSON 对象边界
        if content.startswith("{") and content.endswith("}"):
            return content

        # 查找第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]

        return content

    def get_system_prompt(self) -> str:
        return CODE_REVIEW_SYSTEM_PROMPT
```

- [ ] **Step 2: 注册 Agent**

修改 `app/agents/__init__.py`，确保导入 CodeReviewerAgent：

```python
"""Agent 模块入口。"""

from app.agents.base import Agent, AgentRegistry
from app.agents.business_analyst import BusinessAnalystAgent
from app.agents.product_manager import ProductManagerAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.qa import QAAgent
from app.agents.project_manager import ProjectManagerAgent
from app.agents.code_reviewer import CodeReviewerAgent

__all__ = [
    "Agent",
    "AgentRegistry",
    "BusinessAnalystAgent",
    "ProductManagerAgent",
    "ArchitectAgent",
    "DeveloperAgent",
    "QAAgent",
    "ProjectManagerAgent",
    "CodeReviewerAgent",
]
```

- [ ] **Step 3: 提交**

```bash
git add app/agents/code_reviewer.py app/agents/__init__.py
git commit -m "feat(code-review): add CodeReviewerAgent with LLM integration"
```

---

### Task 4: 代码审查 REST API

**Files:**
- Create: `app/api/code_review.py`
- Modify: `app/api/__init__.py`

**目标:** 创建代码审查的 REST API 端点。

- [ ] **Step 1: 创建 API 文件**

```python
"""代码审查 API 模块。"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.state.models import CodeReviewModel, WorkflowTaskModel
from app.agents.code_reviewer import CodeReviewerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/code-reviews", tags=["code-reviews"])


class CreateCodeReviewRequest(BaseModel):
    """创建代码审查请求。"""

    task_id: int = Field(..., description="关联的工作流任务 ID")
    diff: str = Field(..., description="代码 diff 内容")
    project_context: str = Field(default="", description="项目上下文信息")
    model: Optional[str] = Field(default=None, description="指定 LLM 模型")


class CodeReviewIssue(BaseModel):
    """代码审查问题项。"""

    file: str
    line: Optional[int] = None
    severity: str  # must_fix / should_fix / nice_to_have
    category: str  # security / performance / maintainability / style / testing / architecture
    title: str
    description: str
    suggestion: str


class CodeReviewResponse(BaseModel):
    """代码审查响应。"""

    id: int
    task_id: int
    project_id: str
    status: str
    score: Optional[int] = None
    summary: Optional[str] = None
    issues: List[CodeReviewIssue] = []
    improvements: List[Dict[str, str]] = []
    llm_model: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("", response_model=CodeReviewResponse)
async def create_code_review(
    payload: CreateCodeReviewRequest,
    db: Session = Depends(get_db),
) -> CodeReviewModel:
    """创建代码审查。

    异步触发 LLM 审查，返回审查记录 ID。
    """
    # 验证任务存在
    task = (
        db.query(WorkflowTaskModel)
        .filter(WorkflowTaskModel.id == payload.task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    # 创建审查记录
    review = CodeReviewModel(
        task_id=payload.task_id,
        project_id=task.project_id,
        status="running",
        raw_diff=payload.diff,
        llm_model=payload.model,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # 异步执行审查
    try:
        agent = CodeReviewerAgent()
        report = await agent.execute({
            "diff": payload.diff,
            "project_context": payload.project_context,
            "model": payload.model,
        })

        # 更新审查记录
        review.status = "completed"
        review.score = report.get("score")
        review.summary = report.get("summary")
        review.issues_json = json.dumps(report.get("issues", []))
        review.improvements_json = json.dumps(report.get("improvements", []))
        review.duration_ms = report.get("duration_ms")
        review.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(review)

    except Exception as e:
        logger.exception("Code review failed for task %d", payload.task_id)
        review.status = "failed"
        review.summary = f"审查失败：{e}"
        db.commit()
        db.refresh(review)

    return review


@router.get("/{review_id}", response_model=CodeReviewResponse)
async def get_code_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> CodeReviewModel:
    """获取代码审查详情。"""
    review = (
        db.query(CodeReviewModel)
        .filter(CodeReviewModel.id == review_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail=f"Code review {review_id} not found")
    return review


@router.get("", response_model=List[CodeReviewResponse])
async def list_code_reviews(
    task_id: Optional[int] = None,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[CodeReviewModel]:
    """列出代码审查记录。"""
    query = db.query(CodeReviewModel)

    if task_id:
        query = query.filter(CodeReviewModel.task_id == task_id)
    if project_id:
        query = query.filter(CodeReviewModel.project_id == project_id)
    if status:
        query = query.filter(CodeReviewModel.status == status)

    reviews = (
        query.order_by(CodeReviewModel.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return reviews


@router.post("/{review_id}/re-run")
async def rerun_code_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> CodeReviewResponse:
    """重新运行代码审查。"""
    review = (
        db.query(CodeReviewModel)
        .filter(CodeReviewModel.id == review_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail=f"Code review {review_id} not found")

    if not review.raw_diff:
        raise HTTPException(status_code=400, detail="No diff content to review")

    # 重置状态
    review.status = "running"
    review.score = None
    review.summary = None
    review.issues_json = None
    review.improvements_json = None
    review.completed_at = None
    db.commit()

    # 重新执行审查
    try:
        agent = CodeReviewerAgent()
        report = await agent.execute({
            "diff": review.raw_diff,
            "model": review.llm_model,
        })

        review.status = "completed"
        review.score = report.get("score")
        review.summary = report.get("summary")
        review.issues_json = json.dumps(report.get("issues", []))
        review.improvements_json = json.dumps(report.get("improvements", []))
        review.duration_ms = report.get("duration_ms")
        review.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(review)

    except Exception as e:
        logger.exception("Code review re-run failed for review %d", review_id)
        review.status = "failed"
        review.summary = f"审查失败：{e}"
        db.commit()
        db.refresh(review)

    return review
```

- [ ] **Step 2: 注册路由**

修改 `app/api/__init__.py`：

```python
from fastapi import APIRouter

from app.api import (
    projects,
    workflow_config,
    workflow_instances,
    task_management,
    scheduled_tasks,
    settings,
    workbench,
    events,
    code_review,  # 新增
)

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects")
api_router.include_router(workflow_config.router, prefix="/workflow-configs")
api_router.include_router(workflow_instances.router, prefix="/workflow-instances")
api_router.include_router(task_management.router, prefix="/task-management")
api_router.include_router(scheduled_tasks.router, prefix="/scheduled-tasks")
api_router.include_router(settings.router, prefix="/settings")
api_router.include_router(workbench.router, prefix="/workbench")
api_router.include_router(events.router, prefix="/events")
api_router.include_router(code_review.router, prefix="/code-reviews")  # 新增
```

- [ ] **Step 3: 提交**

```bash
git add app/api/code_review.py app/api/__init__.py
git commit -m "feat(code-review): add code review REST API endpoints"
```

---

### Task 5: 前端 API 层

**Files:**
- Modify: `frontend/src/api/index.ts`

**目标:** 新增代码审查相关的 API 方法。

- [ ] **Step 1: 添加 API 方法**

在 `frontend/src/api/index.ts` 的 `api` 对象中添加：

```typescript
  // ==================== 代码审查 API ====================

  async createCodeReview(data: {
    task_id: number
    diff: string
    project_context?: string
    model?: string
  }): Promise<any> {
    return request('/api/code-reviews', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async getCodeReview(reviewId: number): Promise<any> {
    return request(`/api/code-reviews/${reviewId}`)
  },

  async listCodeReviews(params?: {
    task_id?: number
    project_id?: string
    status?: string
    limit?: number
    offset?: number
  }): Promise<any> {
    const query = new URLSearchParams()
    if (params?.task_id) query.set('task_id', String(params.task_id))
    if (params?.project_id) query.set('project_id', params.project_id)
    if (params?.status) query.set('status', params.status)
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    return request(`/api/code-reviews?${query.toString()}`)
  },

  async rerunCodeReview(reviewId: number): Promise<any> {
    return request(`/api/code-reviews/${reviewId}/re-run`, {
      method: 'POST',
    })
  },
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/index.ts
git commit -m "feat(code-review): add frontend API methods for code review"
```

---

### Task 6: 前端审查报告组件

**Files:**
- Create: `frontend/src/components/code-review/ScoreBadge.vue`
- Create: `frontend/src/components/code-review/IssueCard.vue`
- Create: `frontend/src/components/code-review/ReviewReport.vue`

**目标:** 创建可复用的代码审查报告组件。

- [ ] **Step 1: ScoreBadge 组件**

```vue
<template>
  <div class="score-badge" :class="scoreClass">
    <span class="score-value">{{ score ?? '-' }}</span>
    <span class="score-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score?: number | null
}>()

const scoreClass = computed(() => {
  if (props.score == null) return 'unknown'
  if (props.score >= 80) return 'excellent'
  if (props.score >= 60) return 'good'
  if (props.score >= 40) return 'fair'
  return 'poor'
})

const label = computed(() => {
  if (props.score == null) return '未评分'
  if (props.score >= 80) return '优秀'
  if (props.score >= 60) return '良好'
  if (props.score >= 40) return '一般'
  return '需改进'
})
</script>

<style scoped>
.score-badge {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 20px;
  border-radius: 12px;
  min-width: 80px;
}
.score-badge.excellent { background: #dcfce7; color: #166534; }
.score-badge.good { background: #dbeafe; color: #1e40af; }
.score-badge.fair { background: #fef3c7; color: #92400e; }
.score-badge.poor { background: #fee2e2; color: #991b1b; }
.score-badge.unknown { background: #f3f4f6; color: #6b7280; }
.score-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}
.score-label {
  font-size: 12px;
  margin-top: 4px;
}
</style>
```

- [ ] **Step 2: IssueCard 组件**

```vue
<template>
  <div class="issue-card" :class="`severity-${issue.severity}`">
    <div class="issue-header">
      <span class="severity-badge">{{ severityLabel }}</span>
      <span class="category-badge">{{ categoryLabel }}</span>
      <span v-if="issue.file" class="file-path">{{ issue.file }}:{{ issue.line ?? '?' }}</span>
    </div>
    <h4 class="issue-title">{{ issue.title }}</h4>
    <p class="issue-description">{{ issue.description }}</p>
    <div v-if="issue.suggestion" class="issue-suggestion">
      <div class="suggestion-label">修复建议</div>
      <pre class="suggestion-code">{{ issue.suggestion }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Issue {
  file: string
  line?: number | null
  severity: string
  category: string
  title: string
  description: string
  suggestion?: string
}

const props = defineProps<{
  issue: Issue
}>()

const severityLabel = computed(() => {
  const map: Record<string, string> = {
    must_fix: '必须修复',
    should_fix: '建议修复',
    nice_to_have: '可选优化',
  }
  return map[props.issue.severity] || props.issue.severity
})

const categoryLabel = computed(() => {
  const map: Record<string, string> = {
    security: '安全',
    performance: '性能',
    maintainability: '可维护性',
    style: '代码规范',
    testing: '测试',
    architecture: '架构',
  }
  return map[props.issue.category] || props.issue.category
})
</script>

<style scoped>
.issue-card {
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid;
}
.issue-card.severity-must_fix {
  background: #fef2f2;
  border-left-color: #dc2626;
}
.issue-card.severity-should_fix {
  background: #fffbeb;
  border-left-color: #f59e0b;
}
.issue-card.severity-nice_to_have {
  background: #f0fdf4;
  border-left-color: #22c55e;
}
.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.severity-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.severity-must_fix .severity-badge { background: #fecaca; color: #991b1b; }
.severity-should_fix .severity-badge { background: #fde68a; color: #92400e; }
.severity-nice_to_have .severity-badge { background: #bbf7d0; color: #166534; }
.category-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #e5e7eb;
  color: #374151;
}
.file-path {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}
.issue-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #111827;
}
.issue-description {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 12px 0;
  line-height: 1.5;
}
.suggestion-label {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
}
.suggestion-code {
  background: #1f2937;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  overflow-x: auto;
  margin: 0;
}
</style>
```

- [ ] **Step 3: ReviewReport 组件**

```vue
<template>
  <div class="review-report">
    <!-- 头部摘要 -->
    <div class="report-header">
      <ScoreBadge :score="report.score" />
      <div class="report-meta">
        <div class="meta-item">
          <span class="meta-label">状态</span>
          <span class="meta-value" :class="`status-${report.status}`">{{ statusLabel }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">问题数</span>
          <span class="meta-value">{{ totalIssues }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">耗时</span>
          <span class="meta-value">{{ report.duration_ms ? `${report.duration_ms}ms` : '-' }}</span>
        </div>
      </div>
    </div>

    <!-- 总结 -->
    <div v-if="report.summary" class="report-summary">
      <p>{{ report.summary }}</p>
    </div>

    <!-- 问题统计 -->
    <div class="issues-stats">
      <div class="stat-item must-fix">
        <span class="stat-count">{{ mustFixCount }}</span>
        <span class="stat-label">必须修复</span>
      </div>
      <div class="stat-item should-fix">
        <span class="stat-count">{{ shouldFixCount }}</span>
        <span class="stat-label">建议修复</span>
      </div>
      <div class="stat-item nice-to-have">
        <span class="stat-count">{{ niceToHaveCount }}</span>
        <span class="stat-label">可选优化</span>
      </div>
    </div>

    <!-- 问题列表 -->
    <div v-if="issues.length > 0" class="issues-section">
      <h3>审查问题</h3>
      <IssueCard
        v-for="(issue, index) in issues"
        :key="index"
        :issue="issue"
      />
    </div>

    <!-- 改进建议 -->
    <div v-if="improvements.length > 0" class="improvements-section">
      <h3>改进建议</h3>
      <div
        v-for="(item, index) in improvements"
        :key="index"
        class="improvement-item"
      >
        <span class="improvement-category">{{ item.category }}</span>
        <p>{{ item.suggestion }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ScoreBadge from './ScoreBadge.vue'
import IssueCard from './IssueCard.vue'

interface ReviewReportData {
  score?: number | null
  status: string
  summary?: string
  issues?: any[]
  improvements?: any[]
  duration_ms?: number
}

const props = defineProps<{
  report: ReviewReportData
}>()

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '审查中',
    completed: '已完成',
    failed: '失败',
  }
  return map[props.report.status] || props.report.status
})

const issues = computed(() => props.report.issues || [])
const improvements = computed(() => props.report.improvements || [])

const totalIssues = computed(() => issues.value.length)
const mustFixCount = computed(() => issues.value.filter(i => i.severity === 'must_fix').length)
const shouldFixCount = computed(() => issues.value.filter(i => i.severity === 'should_fix').length)
const niceToHaveCount = computed(() => issues.value.filter(i => i.severity === 'nice_to_have').length)
</script>

<style scoped>
.review-report {
  padding: 20px;
}
.report-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}
.report-meta {
  display: flex;
  gap: 20px;
}
.meta-item {
  display: flex;
  flex-direction: column;
}
.meta-label {
  font-size: 12px;
  color: #6b7280;
}
.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.meta-value.status-pending { color: #6b7280; }
.meta-value.status-running { color: #3b82f6; }
.meta-value.status-completed { color: #22c55e; }
.meta-value.status-failed { color: #dc2626; }
.report-summary {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.report-summary p {
  margin: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
}
.issues-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
}
.stat-item.must-fix { background: #fef2f2; }
.stat-item.should-fix { background: #fffbeb; }
.stat-item.nice-to-have { background: #f0fdf4; }
.stat-count {
  font-size: 28px;
  font-weight: 700;
}
.must-fix .stat-count { color: #dc2626; }
.should-fix .stat-count { color: #f59e0b; }
.nice-to-have .stat-count { color: #22c55e; }
.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.issues-section h3,
.improvements-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #111827;
}
.improvement-item {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 8px;
}
.improvement-category {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
}
.improvement-item p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #374151;
}
</style>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/code-review/
git commit -m "feat(code-review): add review report UI components"
```

---

### Task 7: 前端审查详情页

**Files:**
- Create: `frontend/src/pages/CodeReviewPage.vue`

**目标:** 创建代码审查详情页面。

- [ ] **Step 1: 创建页面**

```vue
<template>
  <div class="code-review-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <button class="btn-back" @click="goBack">
        <ArrowLeft :size="16" />
        返回
      </button>
      <h1>代码审查报告 #{{ reviewId }}</h1>
      <div class="header-actions">
        <button
          v-if="review?.status === 'failed' || review?.status === 'completed'"
          class="btn-rerun"
          @click="rerunReview"
          :disabled="isRerunning"
        >
          <RefreshCw :size="14" :class="{ spinning: isRerunning }" />
          {{ isRerunning ? '审查中...' : '重新审查' }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载审查报告中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <AlertCircle :size="48" />
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadReview">重试</button>
    </div>

    <!-- 审查报告 -->
    <ReviewReport
      v-else-if="review"
      :report="reportData"
    />

    <!-- 原始 Diff -->
    <div v-if="review?.raw_diff" class="raw-diff-section">
      <h3>审查代码</h3>
      <pre class="diff-content">{{ review.raw_diff }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-vue-next'
import api from '../api'
import ReviewReport from '../components/code-review/ReviewReport.vue'

const route = useRoute()
const router = useRouter()

const reviewId = computed(() => Number(route.params.id))
const review = ref<any>(null)
const isLoading = ref(false)
const isRerunning = ref(false)
const error = ref('')

const reportData = computed(() => {
  if (!review.value) return null
  return {
    score: review.value.score,
    status: review.value.status,
    summary: review.value.summary,
    issues: review.value.issues_json ? JSON.parse(review.value.issues_json) : [],
    improvements: review.value.improvements_json ? JSON.parse(review.value.improvements_json) : [],
    duration_ms: review.value.duration_ms,
  }
})

async function loadReview() {
  isLoading.value = true
  error.value = ''
  try {
    const res = await api.getCodeReview(reviewId.value)
    review.value = res
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    isLoading.value = false
  }
}

async function rerunReview() {
  isRerunning.value = true
  try {
    const res = await api.rerunCodeReview(reviewId.value)
    review.value = res
  } catch (e: any) {
    error.value = e.message || '重新审查失败'
  } finally {
    isRerunning.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(loadReview)
</script>

<style scoped>
.code-review-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}
.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}
.btn-back:hover {
  background: #f9fafb;
}
.btn-rerun {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
.btn-rerun:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-rerun:hover:not(:disabled) {
  background: #2563eb;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 16px;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.btn-retry {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
}
.raw-diff-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}
.raw-diff-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
}
.diff-content {
  background: #1f2937;
  color: #e5e7eb;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  overflow-x: auto;
  line-height: 1.6;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/CodeReviewPage.vue
git commit -m "feat(code-review): add code review detail page"
```

---

### Task 8: 前端审查列表页

**Files:**
- Create: `frontend/src/pages/CodeReviewListPage.vue`

**目标:** 创建代码审查历史列表页面。

- [ ] **Step 1: 创建页面**

```vue
<template>
  <div class="code-review-list-page">
    <div class="page-header">
      <h1>代码审查</h1>
      <p class="page-desc">查看和管理代码审查记录</p>
    </div>

    <!-- 过滤器 -->
    <div class="filters">
      <select v-model="filterStatus" @change="loadReviews">
        <option value="">全部状态</option>
        <option value="completed">已完成</option>
        <option value="running">审查中</option>
        <option value="failed">失败</option>
      </select>
    </div>

    <!-- 列表 -->
    <div v-if="isLoading" class="loading">加载中...</div>
    <div v-else-if="reviews.length === 0" class="empty">
      <FileSearch :size="48" />
      <p>暂无代码审查记录</p>
    </div>
    <div v-else class="review-list">
      <div
        v-for="review in reviews"
        :key="review.id"
        class="review-item"
        @click="goToDetail(review.id)"
      >
        <div class="review-main">
          <div class="review-id">#{{ review.id }}</div>
          <div class="review-project">{{ review.project_id }}</div>
          <div class="review-status" :class="`status-${review.status}`">
            {{ statusLabel(review.status) }}
          </div>
        </div>
        <div class="review-meta">
          <ScoreBadge v-if="review.score != null" :score="review.score" />
          <span v-else class="no-score">-</span>
          <span class="review-time">{{ formatTime(review.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { FileSearch } from 'lucide-vue-next'
import api from '../api'
import ScoreBadge from '../components/code-review/ScoreBadge.vue'

const router = useRouter()

const reviews = ref<any[]>([])
const isLoading = ref(false)
const filterStatus = ref('')

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '审查中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function formatTime(time: string): string {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

async function loadReviews() {
  isLoading.value = true
  try {
    const params: any = { limit: 50 }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const res = await api.listCodeReviews(params)
    reviews.value = res
  } catch (e) {
    console.error('Failed to load reviews:', e)
  } finally {
    isLoading.value = false
  }
}

function goToDetail(id: number) {
  router.push(`/code-reviews/${id}`)
}

onMounted(loadReviews)
</script>

<style scoped>
.code-review-list-page {
  padding: 24px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
.page-desc {
  color: #6b7280;
  margin: 4px 0 0 0;
}
.filters {
  margin-bottom: 16px;
}
.filters select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}
.review-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.review-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.review-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.review-main {
  display: flex;
  align-items: center;
  gap: 16px;
}
.review-id {
  font-weight: 600;
  color: #111827;
}
.review-project {
  color: #6b7280;
  font-size: 14px;
}
.review-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.review-status.status-completed {
  background: #dcfce7;
  color: #166534;
}
.review-status.status-running {
  background: #dbeafe;
  color: #1e40af;
}
.review-status.status-failed {
  background: #fee2e2;
  color: #991b1b;
}
.review-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}
.no-score {
  color: #9ca3af;
  font-size: 14px;
}
.review-time {
  font-size: 12px;
  color: #9ca3af;
}
.loading,
.empty {
  text-align: center;
  padding: 60px;
  color: #6b7280;
}
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/CodeReviewListPage.vue
git commit -m "feat(code-review): add code review list page"
```

---

### Task 9: 路由和菜单

**Files:**
- Modify: `frontend/src/router.ts`
- Modify: `frontend/src/components/Sidebar.vue`

**目标:** 注册代码审查页面路由和菜单。

- [ ] **Step 1: 添加路由**

在 `frontend/src/router.ts` 中添加：

```typescript
// 在现有路由中追加
{
  path: '/code-reviews',
  name: 'CodeReviewList',
  component: () => import('./pages/CodeReviewListPage.vue'),
},
{
  path: '/code-reviews/:id',
  name: 'CodeReviewDetail',
  component: () => import('./pages/CodeReviewPage.vue'),
},
```

- [ ] **Step 2: 添加菜单**

修改 `frontend/src/components/Sidebar.vue`，在菜单列表中添加：

```typescript
// 在 menuItems 数组中添加
{
  key: 'code-reviews',
  label: '代码审查',
  icon: GitPullRequest,
  route: '/code-reviews',
},
```

确保导入 `GitPullRequest` 图标：

```typescript
import {
  LayoutDashboard,
  Bot,
  FolderKanban,
  ClipboardList,
  CalendarClock,
  BrainCircuit,
  Wrench,
  Workflow,
  Settings,
  GitPullRequest,  // 新增
} from 'lucide-vue-next'
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/router.ts frontend/src/components/Sidebar.vue
git commit -m "feat(code-review): add routes and sidebar menu"
```

---

### Task 10: 国际化

**Files:**
- Modify: `frontend/src/i18n/locales/zh.json`
- Modify: `frontend/src/i18n/locales/en.json`

**目标:** 添加代码审查相关的国际化翻译。

- [ ] **Step 1: 中文翻译**

在 `frontend/src/i18n/locales/zh.json` 中添加：

```json
"codeReview": {
  "title": "代码审查",
  "description": "智能代码质量审查",
  "score": "分数",
  "status": "状态",
  "issues": "问题",
  "improvements": "改进建议",
  "mustFix": "必须修复",
  "shouldFix": "建议修复",
  "niceToHave": "可选优化",
  "rerun": "重新审查",
  "noReviews": "暂无审查记录",
  "reviewing": "审查中...",
  "security": "安全",
  "performance": "性能",
  "maintainability": "可维护性",
  "style": "代码规范",
  "testing": "测试",
  "architecture": "架构"
}
```

- [ ] **Step 2: 英文翻译**

在 `frontend/src/i18n/locales/en.json` 中添加：

```json
"codeReview": {
  "title": "Code Review",
  "description": "Intelligent code quality review",
  "score": "Score",
  "status": "Status",
  "issues": "Issues",
  "improvements": "Improvements",
  "mustFix": "Must Fix",
  "shouldFix": "Should Fix",
  "niceToHave": "Nice to Have",
  "rerun": "Re-run Review",
  "noReviews": "No review records",
  "reviewing": "Reviewing...",
  "security": "Security",
  "performance": "Performance",
  "maintainability": "Maintainability",
  "style": "Code Style",
  "testing": "Testing",
  "architecture": "Architecture"
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/i18n/locales/zh.json frontend/src/i18n/locales/en.json
git commit -m "feat(code-review): add i18n translations"
```

---

## Phase 2: 静态分析集成（semgrep）

### Task 11: 静态分析引擎

**Files:**
- Create: `app/static_analysis/engine.py`
- Create: `app/static_analysis/__init__.py`

**目标:** 封装 semgrep 调用，提供静态分析接口。

- [ ] **Step 1: 创建引擎**

```python
"""静态分析引擎，封装 semgrep 调用。"""

import json
import logging
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StaticAnalysisEngine:
    """静态分析引擎。"""

    def __init__(self) -> None:
        self._check_semgrep()

    def _check_semgrep(self) -> None:
        """检查 semgrep 是否已安装。"""
        try:
            subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(
                "semgrep not found. Static analysis will be disabled. "
                "Install with: pip install semgrep"
            )

    def analyze_diff(self, diff: str) -> List[Dict[str, Any]]:
        """分析代码 diff。

        Args:
            diff: 代码 diff 字符串。

        Returns:
            List[Dict]: 发现的问题列表。
        """
        try:
            # 将 diff 写入临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".diff", delete=False
            ) as f:
                f.write(diff)
                diff_path = f.name

            # 运行 semgrep
            result = subprocess.run(
                [
                    "semgrep",
                    "--config=auto",
                    "--json",
                    "--quiet",
                    diff_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode not in (0, 1):  # 0 = no findings, 1 = findings
                logger.error("semgrep failed: %s", result.stderr)
                return []

            output = json.loads(result.stdout)
            findings = output.get("results", [])

            # 转换为统一格式
            issues = []
            for finding in findings:
                issue = {
                    "file": finding.get("path", ""),
                    "line": finding.get("start", {}).get("line"),
                    "severity": self._map_severity(finding.get("extra", {}).get("severity", "WARNING")),
                    "category": self._map_category(finding.get("check_id", "")),
                    "title": finding.get("extra", {}).get("message", "Unknown issue"),
                    "description": finding.get("extra", {}).get("message", ""),
                    "suggestion": finding.get("extra", {}).get("fix", ""),
                }
                issues.append(issue)

            return issues

        except subprocess.TimeoutExpired:
            logger.error("semgrep timed out")
            return []
        except Exception as e:
            logger.exception("Static analysis failed")
            return []

    def _map_severity(self, severity: str) -> str:
        """映射 semgrep 严重级别到内部级别。"""
        mapping = {
            "ERROR": "must_fix",
            "WARNING": "should_fix",
            "INFO": "nice_to_have",
        }
        return mapping.get(severity.upper(), "should_fix")

    def _map_category(self, check_id: str) -> str:
        """映射 semgrep check_id 到内部类别。"""
        check_id_lower = check_id.lower()
        if "security" in check_id_lower or "sql" in check_id_lower or "xss" in check_id_lower:
            return "security"
        if "performance" in check_id_lower:
            return "performance"
        if "style" in check_id_lower or "format" in check_id_lower:
            return "style"
        if "test" in check_id_lower:
            return "testing"
        return "maintainability"
```

- [ ] **Step 2: 提交**

```bash
git add app/static_analysis/
git commit -m "feat(code-review): add static analysis engine with semgrep"
```

---

### Task 12: 融合静态分析与 LLM 结果

**Files:**
- Modify: `app/agents/code_reviewer.py`
- Modify: `app/api/code_review.py`

**目标:** 在 CodeReviewerAgent 中集成静态分析结果。

- [ ] **Step 1: 修改 Agent**

修改 `app/agents/code_reviewer.py` 的 `execute` 方法：

```python
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码审查（LLM + 静态分析）。"""
        diff = context.get("diff", "")
        project_context = context.get("project_context", "")
        model = context.get("model")

        if not diff:
            return {
                "score": 0,
                "summary": "没有提供代码 diff",
                "issues": [],
                "improvements": [],
            }

        # 1. 静态分析（快速筛选）
        static_issues = []
        try:
            from app.static_analysis.engine import StaticAnalysisEngine
            engine = StaticAnalysisEngine()
            static_issues = engine.analyze_diff(diff)
            logger.info("Static analysis found %d issues", len(static_issues))
        except Exception as e:
            logger.warning("Static analysis failed: %s", e)

        # 2. LLM 深度审查
        prompt = build_code_review_prompt(diff, project_context)

        start_time = time.time()
        try:
            response = await self.llm_client.chat_completion(
                system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=model,
                temperature=0.2,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            content = response.get("content", "")
            json_str = self._extract_json(content)
            report = json.loads(json_str)

            report.setdefault("score", 0)
            report.setdefault("summary", "")
            report.setdefault("issues", [])
            report.setdefault("improvements", [])

            # 3. 合并结果（静态分析结果优先）
            merged_issues = static_issues.copy()
            static_files = {i["file"] + str(i.get("line")) for i in static_issues}

            for issue in report["issues"]:
                issue.setdefault("line", None)
                issue.setdefault("file", "")
                key = issue["file"] + str(issue.get("line"))
                if key not in static_files:
                    merged_issues.append(issue)

            report["issues"] = merged_issues
            report["duration_ms"] = duration_ms
            report["llm_model"] = response.get("model", model or "default")
            report["static_analysis_count"] = len(static_issues)

            return report

        except Exception as e:
            logger.exception("Code review failed")
            # 即使 LLM 失败，也返回静态分析结果
            if static_issues:
                return {
                    "score": max(0, 100 - len(static_issues) * 10),
                    "summary": f"LLM 审查失败，仅显示静态分析结果：{e}",
                    "issues": static_issues,
                    "improvements": [],
                    "error": str(e),
                }
            return {
                "score": 0,
                "summary": f"审查失败：{e}",
                "issues": [],
                "improvements": [],
                "error": str(e),
            }
```

- [ ] **Step 2: 提交**

```bash
git add app/agents/code_reviewer.py
git commit -m "feat(code-review): integrate static analysis with LLM review"
```

---

## Phase 3: 质量门禁规则配置

### Task 13: 门禁规则配置 API

**Files:**
- Modify: `app/api/settings.py`

**目标:** 在设置系统中增加质量门禁规则配置。

- [ ] **Step 1: 添加配置项**

在 `DEFAULT_CONFIGS` 中追加：

```python
    # 代码审查质量门禁
    "code_review_enabled": ("true", "llm", "启用代码审查", False),
    "code_review_auto_trigger": ("true", "llm", "开发完成后自动触发审查", False),
    "code_review_score_threshold": ("60", "llm", "审查通过分数阈值", False),
    "code_review_must_fix_block": ("true", "llm", "Must Fix 问题阻止通过", False),
    "code_review_models": ("gpt-4,claude-3-opus", "llm", "代码审查可用模型", False),
```

- [ ] **Step 2: 提交**

```bash
git add app/api/settings.py
git commit -m "feat(code-review): add quality gate configuration options"
```

---

### Task 14: 前端门禁配置

**Files:**
- Modify: `frontend/src/pages/settings/LLMSettingsPage.vue`

**目标:** 在 LLM 设置页面增加质量门禁配置区域。

- [ ] **Step 1: 添加配置区域**

在 `LLMSettingsPage.vue` 中添加：

```vue
      <SettingsSection title="代码审查" description="质量门禁规则配置">
        <SettingItem
          label="启用代码审查"
          description="开启后开发阶段完成后自动触发代码审查"
          type="checkbox"
          v-model="configs.code_review_enabled"
        />
        <SettingItem
          label="自动触发审查"
          description="开发 Agent 生成补丁后自动发起审查"
          type="checkbox"
          v-model="configs.code_review_auto_trigger"
        />
        <SettingItem
          label="通过分数阈值"
          description="审查分数达到此值才能通过门禁"
          type="text"
          v-model="configs.code_review_score_threshold"
        />
        <SettingItem
          label="Must Fix 阻止通过"
          description="存在 Must Fix 级别问题时阻止通过"
          type="checkbox"
          v-model="configs.code_review_must_fix_block"
        />
      </SettingsSection>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/settings/LLMSettingsPage.vue
git commit -m "feat(code-review): add quality gate settings UI"
```

---

## 验证清单

- [ ] 创建审查 API 正常工作（`POST /api/code-reviews`）
- [ ] 获取审查详情 API 正常工作（`GET /api/code-reviews/{id}`）
- [ ] 列表查询 API 正常工作（`GET /api/code-reviews`）
- [ ] 重新审查 API 正常工作（`POST /api/code-reviews/{id}/re-run`）
- [ ] 前端审查列表页可访问（`/code-reviews`）
- [ ] 前端审查详情页可访问（`/code-reviews/{id}`）
- [ ] 审查报告正确显示分数、问题列表、改进建议
- [ ] 静态分析结果与 LLM 结果正确合并
- [ ] 质量门禁配置可保存和读取
- [ ] 国际化翻译正确显示

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-22-code-review-ai.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review

**Which approach?**