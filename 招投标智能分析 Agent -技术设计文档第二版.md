# 招投标智能分析 Agent — 最终技术设计文档

> 版本：v1.0 | 面向：MVP阶段独立开发者 | 更新日期：2025-05

---

## 一、系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户浏览器                                    │
│              Next.js 14 (App Router + SSE Client)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS + SSE
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理 + SSL                              │
│              client_max_body_size 50m;  proxy_buffering off;          │
└──────────┬──────────────────────────────────────┬───────────────────┘
           │ /api/*                               │ /*
           ▼                                      ▼
┌──────────────────────┐              ┌───────────────────────┐
│   FastAPI 后端        │              │   Next.js 前端         │
│   :8000              │              │   :3000               │
│                      │              │                       │
│  ┌────────────────┐  │              │  /                    │
│  │ JWT Auth       │  │              │  /login               │
│  │ 路由层          │  │              │  /dashboard           │
│  │ SSE Gateway    │  │              │  /analysis/[taskId]   │
│  │ 文件上传        │  │              └───────────────────────┘
│  └───────┬────────┘  │
│          │ publish   │
│          ▼           │
│  ┌────────────────┐  │
│  │ Redis          │  │
│  │ :6379          │  │ ←── Celery Worker 订阅任务
│  │ pub/sub + 锁   │  │
│  └───────┬────────┘  │
└──────────┼───────────┘
           │ enqueue
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Celery Worker                                   │
│                                                                    │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │              LangGraph StateGraph                           │  │
│   │                                                             │  │
│   │   [document_parser]                                         │  │
│   │         │                                                   │  │
│   │         ▼                                                   │  │
│   │   [qualification_checker]                                   │  │
│   │         │                                                   │  │
│   │    ─────┴──────────────────────────────┐                   │  │
│   │    │ overall=="不建议投标"              │ 否则              │  │
│   │    ▼                                   ▼                   │  │
│   │  [bid_abort_advisor]          [strategy_analyzer]          │  │
│   │    │                                   │                   │  │
│   │    ▼                                   ▼                   │  │
│   │   END                         [proposal_generator]         │  │
│   │                                        │                   │  │
│   │                                        ▼                   │  │
│   │                               [compliance_reviewer]        │  │
│   │                                        │                   │  │
│   │                          ─────────────┴──────────────┐    │  │
│   │                          │ needs_revision             │    │  │
│   │                          │ & revision_count < 2       │ END│  │
│   │                          ▼                            │    │  │
│   │                  [proposal_generator]  ───────────────┘    │  │
│   └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│   工具层：PDF解析 | pgvector检索 | 评分计算                           │
└──────────────────────────────────────────────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌──────────────────────┐
│   PostgreSQL     │       │   DeepSeek API        │
│   :5432          │       │   deepseek-chat (V3)  │
│   + pgvector     │       │   (统一使用，MVP阶段)  │
└──────────────────┘       └──────────────────────┘
```

---

## 二、完整数据库 DDL

```sql
-- ============================================================
-- 扩展
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector（替代Milvus）

-- ============================================================
-- 用户表
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nickname        VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 企业信息表（MVP阶段用表单替代企业知识库）
-- ============================================================
CREATE TABLE company_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name            VARCHAR(200),
    -- 资质类型，存为数组，例如 {"系统集成三级","ISO9001","CMMI3"}
    qualification_types     TEXT[],
    established_years       INTEGER,             -- 成立年限
    has_similar_projects    BOOLEAN DEFAULT FALSE,
    similar_project_desc    TEXT,                -- 类似业绩描述
    annual_revenue          VARCHAR(50),         -- 年营业额（如"5000万以上"）
    employee_count          INTEGER,
    extra_notes             TEXT,                -- 其他补充（自由填写）
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id)                             -- 一个用户一份企业画像
);

-- ============================================================
-- 分析任务表（核心表）
-- ============================================================
CREATE TABLE analysis_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- 文件信息
    file_name       VARCHAR(500) NOT NULL,
    file_url        VARCHAR(1000) NOT NULL,
    file_size       BIGINT,                      -- 字节数，用 BIGINT
    file_hash       VARCHAR(64),                 -- SHA-256，用于去重
    page_count      INTEGER,
    -- 状态
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending / parsing / qualifying / aborting / strategizing
    -- generating / reviewing / completed / failed / cancelled
    current_agent   VARCHAR(50),
    progress        SMALLINT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    error_message   TEXT,
    -- 费用追踪
    token_used      INTEGER DEFAULT 0,
    llm_cost        DECIMAL(10, 4) DEFAULT 0,    -- 单位：元
    -- 任务追踪
    celery_task_id  VARCHAR(36),
    revision_count  SMALLINT DEFAULT 0,
    -- 时间
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_tasks_user        ON analysis_tasks(user_id, created_at DESC);
CREATE INDEX idx_tasks_status      ON analysis_tasks(status);
CREATE INDEX idx_tasks_file_hash   ON analysis_tasks(file_hash);  -- 去重查询

-- ============================================================
-- 文件去重表
-- ============================================================
CREATE TABLE file_dedup (
    file_hash       VARCHAR(64) PRIMARY KEY,
    file_url        VARCHAR(1000) NOT NULL,
    first_task_id   UUID REFERENCES analysis_tasks(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 解析结果表
-- ============================================================
CREATE TABLE parsed_results (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id                     UUID NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    schema_version              SMALLINT DEFAULT 1,   -- Prompt迭代时递增
    -- 项目概况（平铺字段，方便查询）
    project_name                TEXT,
    project_code                TEXT,
    budget                      TEXT,
    bid_deadline                TEXT,
    bid_opening_time            TEXT,
    project_location            TEXT,
    purchaser                   TEXT,
    agent_contact               TEXT,
    -- 解析质量
    extraction_quality_score    FLOAT,               -- 0~1，低于0.6触发OCR降级
    -- 结构化 JSON
    qualification_requirements  JSONB,
    scoring_criteria            JSONB,
    technical_requirements      JSONB,
    risk_clauses                JSONB,
    -- 原始文本（分块存储，避免单行过大）
    raw_text                    TEXT,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_parsed_task ON parsed_results(task_id);

-- ============================================================
-- 资格评估结果表
-- ============================================================
CREATE TABLE qualification_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    requirement     TEXT NOT NULL,
    category        VARCHAR(50),
    -- 资质证书 / 业绩案例 / 人员配置 / 财务指标 / 其他
    is_mandatory    BOOLEAN DEFAULT TRUE,
    is_met          BOOLEAN,
    evidence        TEXT,
    risk_level      VARCHAR(10) CHECK (risk_level IN ('low','medium','high')),
    suggestion      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_qual_task ON qualification_assessments(task_id);

-- ============================================================
-- 策略分析结果表
-- ============================================================
CREATE TABLE strategy_analyses (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id                 UUID NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    overall_qualification   VARCHAR(20),   -- 建议投标 / 有风险 / 不建议投标
    abort_advice            TEXT,          -- 不建议时的放弃建议
    scoring_analysis        JSONB,
    competitive_strategy    JSONB,
    recommended_actions     JSONB,
    pricing_advice          TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_strategy_task ON strategy_analyses(task_id);

-- ============================================================
-- 投标方案大纲表
-- ============================================================
CREATE TABLE proposal_outlines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             UUID NOT NULL REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    revision_number     SMALLINT DEFAULT 1,        -- 第几次生成
    outline             JSONB NOT NULL,
    content_draft       TEXT,
    word_count          INTEGER,
    compliance_score    FLOAT,
    missing_items       JSONB,
    revision_suggestions JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_proposal_task ON proposal_outlines(task_id, revision_number DESC);

-- ============================================================
-- 向量嵌入表（替代 Milvus，使用 pgvector）
-- ============================================================
CREATE TABLE document_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    task_id     UUID REFERENCES analysis_tasks(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    chunk_text  TEXT NOT NULL,
    embedding   vector(1024),                      -- BGE-M3 输出维度
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 索引（比 IVFFlat 更适合中小数据量）
CREATE INDEX idx_embedding_hnsw ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- 审计日志表
-- ============================================================
CREATE TABLE audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id),
    task_id     UUID REFERENCES analysis_tasks(id),
    action      VARCHAR(50) NOT NULL,
    -- upload / analyze_start / analyze_complete / export / delete / cancel
    ip_address  INET,
    user_agent  TEXT,
    extra       JSONB,                             -- 其他上下文
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_task ON audit_logs(task_id);
```

---

## 三、API 接口定义

> 统一规范：
> - Base URL: `/api/v1`
> - 认证：除登录/注册外，所有接口需 `Authorization: Bearer <JWT>`
> - 响应格式：`{ "code": 0, "data": {...}, "message": "ok" }`
> - 错误格式：`{ "code": 4xx/5xx, "data": null, "message": "错误描述" }`

---

### 3.1 认证接口

#### POST `/auth/register` — 注册
```
请求体：
{
  "email": "user@example.com",
  "password": "Abc12345",
  "nickname": "张三"
}

响应 200：
{
  "code": 0,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "nickname": "张三"
  },
  "message": "ok"
}

错误：
  409 — 邮箱已注册
  422 — 参数校验失败
```

#### POST `/auth/login` — 登录
```
请求体：
{
  "email": "user@example.com",
  "password": "Abc12345"
}

响应 200：
{
  "code": 0,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400
  },
  "message": "ok"
}

错误：
  401 — 邮箱或密码错误
```

---

### 3.2 企业画像接口

#### PUT `/company-profile` — 创建或更新企业画像
```
请求体：
{
  "company_name": "XX科技有限公司",
  "qualification_types": ["系统集成三级", "ISO9001"],
  "established_years": 8,
  "has_similar_projects": true,
  "similar_project_desc": "曾承接某市政务云平台项目，合同额800万",
  "annual_revenue": "5000万以上",
  "employee_count": 120,
  "extra_notes": "拥有软件著作权15项"
}

响应 200：
{
  "code": 0,
  "data": { "profile_id": "uuid" },
  "message": "ok"
}
```

#### GET `/company-profile` — 获取企业画像
```
响应 200：
{
  "code": 0,
  "data": { ...企业画像字段... },
  "message": "ok"
}

错误：
  404 — 尚未填写企业画像
```

---

### 3.3 任务接口

#### POST `/tasks` — 上传文件并创建分析任务
```
Content-Type: multipart/form-data

请求体：
  file: <二进制文件>  (必须，PDF，≤50MB)

响应 201：
{
  "code": 0,
  "data": {
    "task_id": "uuid",
    "status": "pending",
    "file_name": "某项目招标文件.pdf",
    "file_size": 2048576,
    "duplicated": false    -- true 表示命中去重缓存
  },
  "message": "ok"
}

错误：
  400 — 非PDF文件
  413 — 文件超过50MB
  422 — 缺少文件
```

#### GET `/tasks` — 获取任务列表
```
Query 参数：
  page=1
  page_size=10
  status=completed   (可选过滤)

响应 200：
{
  "code": 0,
  "data": {
    "total": 42,
    "page": 1,
    "items": [
      {
        "task_id": "uuid",
        "file_name": "...",
        "status": "completed",
        "progress": 100,
        "llm_cost": 0.32,
        "created_at": "2025-05-01T10:00:00Z",
        "completed_at": "2025-05-01T10:03:22Z"
      }
    ]
  },
  "message": "ok"
}
```

#### GET `/tasks/{task_id}` — 获取任务详情
```
响应 200：
{
  "code": 0,
  "data": {
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "current_agent": "compliance_reviewer",
    "llm_cost": 0.32,
    "token_used": 18400,
    "result": {
      "project_info": { ...ProjectInfo... },
      "overall_qualification": "建议投标",
      "qualification_results": [ ...QualificationResult[] ... ],
      "scoring_analysis": { ... },
      "competitive_strategy": ["...", "..."],
      "recommended_actions": ["...", "..."],
      "proposal_outline": { ... },
      "compliance_score": 0.91,
      "missing_items": []
    }
  },
  "message": "ok"
}

错误：
  403 — 无权访问（task 不属于当前用户）
  404 — 任务不存在
```

#### DELETE `/tasks/{task_id}` — 取消或删除任务
```
响应 200：
{
  "code": 0,
  "data": { "cancelled": true },
  "message": "ok"
}

说明：
  - 进行中的任务：撤销 Celery 任务，状态改为 cancelled
  - 已完成的任务：逻辑删除（软删除，加 deleted_at 字段）

错误：
  403 — 无权操作
  404 — 任务不存在
```

---

### 3.4 SSE 流式接口

#### GET `/tasks/{task_id}/stream` — 订阅实时进度
```
需要认证（Bearer Token 放 Query 参数，因 EventSource 不支持自定义 Header）：
  GET /api/v1/tasks/{task_id}/stream?token=eyJ...

响应：Content-Type: text/event-stream

事件类型（event 字段）：

1. progress — Agent 进度更新
data: {
  "event": "progress",
  "agent": "document_parser",
  "progress": 20,
  "message": "正在解析文档结构..."
}

2. agent_output — 某个 Agent 完成输出
data: {
  "event": "agent_output",
  "agent": "qualification_checker",
  "data": { ...QualificationResult[] ... }
}

3. completed — 全流程完成
data: {
  "event": "completed",
  "task_id": "uuid",
  "total_cost": 0.32
}

4. error — 任务失败
data: {
  "event": "error",
  "message": "PDF解析失败，请检查文件是否损坏",
  "retryable": true
}
```

---

## 四、LangGraph StateGraph 完整定义

### 4.1 完整 AgentState

```python
# state.py
from typing import TypedDict, Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph import add_messages

# ---- 输入/中间 数据模型（见第五节 Pydantic 模型）----

class AgentState(TypedDict):
    # ── 任务元信息 ──────────────────────────────────
    task_id:        str
    user_id:        str
    file_path:      str

    # ── 企业画像（从DB注入，非LLM生成）──────────────
    company_profile: Optional[dict]   # CompanyProfile.model_dump()

    # ── 文档解析层输出（Agent 1）────────────────────
    raw_text:                   str
    extraction_quality_score:   float
    project_info:               dict   # ProjectInfo
    qualification_requirements: list   # list[QualificationItem]
    scoring_criteria:           list   # list[ScoringItem]
    technical_requirements:     list   # list[str]
    risk_clauses:               list   # list[str]

    # ── 资格评估输出（Agent 2）──────────────────────
    qualification_results:  list    # list[QualificationResult]
    overall_qualification:  str     # 建议投标 / 有风险 / 不建议投标
    abort_advice:           str     # 仅 overall=="不建议投标" 时有值

    # ── 策略分析输出（Agent 3）──────────────────────
    scoring_analysis:       dict
    competitive_strategy:   list    # list[str]
    recommended_actions:    list    # list[str]
    pricing_advice:         str

    # ── 方案生成输出（Agent 4）──────────────────────
    proposal_outline:   dict
    proposal_draft:     str
    revision_number:    int

    # ── 合规审查输出（Agent 5）──────────────────────
    compliance_score:       float
    missing_items:          list    # list[str]
    revision_suggestions:   list    # list[str]
    needs_revision:         bool

    # ── 控制流 ──────────────────────────────────────
    revision_count:     int         # 循环修订次数，上限 2
    current_step:       str
    error:              str
    token_used:         int
    messages:           Annotated[list, add_messages]
```

### 4.2 节点注册与边定义

```python
# graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

def build_graph(db_url: str) -> StateGraph:
    workflow = StateGraph(AgentState)

    # ── 注册节点 ─────────────────────────────────────────────
    workflow.add_node("document_parser",        parse_document)
    workflow.add_node("qualification_checker",  check_qualification)
    workflow.add_node("bid_abort_advisor",       generate_abort_advice)
    workflow.add_node("strategy_analyzer",       analyze_strategy)
    workflow.add_node("proposal_generator",      generate_proposal)
    workflow.add_node("compliance_reviewer",     compliance_review)

    # ── 入口 ──────────────────────────────────────────────────
    workflow.set_entry_point("document_parser")

    # ── 固定边 ────────────────────────────────────────────────
    workflow.add_edge("document_parser",    "qualification_checker")
    workflow.add_edge("bid_abort_advisor",  END)
    workflow.add_edge("strategy_analyzer",  "proposal_generator")

    # ── 条件边 1：资格评估后——是否放弃 ──────────────────────────
    def qualification_router(state: AgentState) -> str:
        return "abort" if state["overall_qualification"] == "不建议投标" else "continue"

    workflow.add_conditional_edges(
        "qualification_checker",
        qualification_router,
        {
            "abort":    "bid_abort_advisor",
            "continue": "strategy_analyzer",
        }
    )

    # ── 条件边 2：合规审查后——是否循环修订 ───────────────────────
    def compliance_router(state: AgentState) -> str:
        should_revise = (
            state["needs_revision"]
            and state.get("revision_count", 0) < 2
        )
        return "revise" if should_revise else "finish"

    workflow.add_conditional_edges(
        "compliance_reviewer",
        compliance_router,
        {
            "revise": "proposal_generator",
            "finish": END,
        }
    )

    # ── Checkpointer（PostgreSQL，支持多进程）─────────────────
    memory = PostgresSaver.from_conn_string(db_url)
    return workflow.compile(checkpointer=memory)
```

### 4.3 节点内 revision_count 递增（必须）

```python
# 在 compliance_reviewer 节点返回时递增
async def compliance_review(state: AgentState) -> dict:
    ...
    return {
        "compliance_score":     parsed["compliance_score"],
        "missing_items":        parsed["missing_items"],
        "revision_suggestions": parsed["revision_suggestions"],
        "needs_revision":       parsed["needs_revision"],
        "revision_count":       state.get("revision_count", 0) + 1,  # ← 必须
        "current_step":         "compliance_reviewed",
    }

# proposal_generator 节点也要记录修订轮次
async def generate_proposal(state: AgentState) -> dict:
    ...
    return {
        "proposal_outline": ...,
        "proposal_draft":   ...,
        "revision_number":  state.get("revision_number", 0) + 1,
        "current_step":     "proposal_generated",
    }
```

---

## 五、Pydantic 模型（输入/输出）

```python
# models.py
from pydantic import BaseModel, Field
from typing import Optional, Literal

# ============================================================
# Agent 1 输出：文档解析
# ============================================================

class ProjectInfo(BaseModel):
    project_name:      str = Field(default="", description="项目名称")
    project_code:      str = Field(default="", description="项目编号")
    budget:            str = Field(default="", description="预算金额，保留原文格式")
    bid_deadline:      str = Field(default="", description="投标截止时间，保留原文格式")
    bid_opening_time:  str = Field(default="", description="开标时间")
    project_location:  str = Field(default="", description="项目实施地点")
    purchaser:         str = Field(default="", description="采购人/招标人")
    agent_contact:     str = Field(default="", description="代理机构联系方式")

class QualificationItem(BaseModel):
    requirement:  str  = Field(description="要求原文，逐条拆分")
    category:     Literal["资质证书","业绩案例","人员配置","财务指标","其他"]
    is_mandatory: bool = Field(default=True, description="是否为否决性条件")
    risk_level:   Literal["low","medium","high"] = "low"

class ScoringItem(BaseModel):
    dimension:       str   = Field(description="评分维度名称")
    max_score:       float = Field(description="该维度满分", gt=0)
    scoring_method:  str   = Field(description="评分方法，如'最低价得满分'")
    weight:          float = Field(default=0.0, description="权重占比 0~1")

class ParsedDocument(BaseModel):
    project_info:               ProjectInfo
    qualification_requirements: list[QualificationItem]
    scoring_criteria:           list[ScoringItem]
    technical_requirements:     list[str]
    risk_clauses:               list[str]
    extraction_quality_score:   float = Field(ge=0.0, le=1.0)

    # 校验：评分总分应在 95~105 之间
    def validate_scoring_total(self) -> bool:
        total = sum(i.max_score for i in self.scoring_criteria)
        return 95 <= total <= 105 if self.scoring_criteria else True

# ============================================================
# Agent 2 输出：资格评估
# ============================================================

class QualificationResult(BaseModel):
    requirement:  str
    category:     str
    is_mandatory: bool
    is_met:       bool
    evidence:     str = Field(default="", description="满足/不满足的依据")
    risk_level:   Literal["low","medium","high"] = "low"
    suggestion:   str = Field(default="")

class QualificationAssessment(BaseModel):
    results:               list[QualificationResult]
    overall_qualification: Literal["建议投标","有风险","不建议投标"]
    high_risk_count:       int
    summary:               str

# ============================================================
# Agent 2b 输出：放弃建议（仅 overall=="不建议投标" 触发）
# ============================================================

class AbortAdvice(BaseModel):
    main_reasons:           list[str] = Field(description="主要不满足原因，逐条列出")
    joint_venture_possible: bool      = Field(description="是否可联合体投标")
    joint_venture_advice:   str       = Field(default="")
    remediation_suggestions: list[str] = Field(description="如何补资质/为下次投标做准备")

# ============================================================
# Agent 3 输出：策略分析
# ============================================================

class ScoringDimensionAnalysis(BaseModel):
    dimension:  str
    max_score:  float
    strategy:   str   = Field(description="如何在该维度得高分")
    difficulty: Literal["低","中","高"]
    priority:   Literal["核心","重要","一般"]

class StrategyAnalysis(BaseModel):
    scoring_analysis:     list[ScoringDimensionAnalysis]
    competitive_strategy: list[str]
    recommended_actions:  list[str]
    pricing_advice:       str

# ============================================================
# Agent 4 输出：方案大纲
# ============================================================

class OutlineSection(BaseModel):
    title:      str
    key_points: list[str]

class OutlineChapter(BaseModel):
    chapter_num:        str
    title:              str
    corresponding_score: str
    allocated_weight:   float
    sections:           list[OutlineSection]
    estimated_pages:    int

class ProposalOutline(BaseModel):
    title:                  str
    chapters:               list[OutlineChapter]
    total_estimated_pages:  int

class ProposalResult(BaseModel):
    outline:       ProposalOutline
    draft_content: str
    word_count:    int

# ============================================================
# Agent 5 输出：合规审查
# ============================================================

class ComplianceReview(BaseModel):
    compliance_score:     float        = Field(ge=0.0, le=1.0)
    covered_items:        list[str]
    missing_items:        list[str]
    contradictions:       list[str]
    revision_suggestions: list[str]
    needs_revision:       bool

# ============================================================
# API 响应模型（FastAPI 用）
# ============================================================

class TaskCreateResponse(BaseModel):
    task_id:    str
    status:     str
    file_name:  str
    file_size:  int
    duplicated: bool

class TaskDetailResponse(BaseModel):
    task_id:    str
    status:     str
    progress:   int
    llm_cost:   float
    token_used: int
    result:     Optional[dict] = None

class SSEEvent(BaseModel):
    event:    Literal["progress","agent_output","completed","error"]
    agent:    Optional[str]   = None
    progress: Optional[int]   = None
    message:  Optional[str]   = None
    data:     Optional[dict]  = None
```

---

## 六、每周开发任务详细拆解

> 说明：每周任务量按独立开发者每天 4-6 小时估算，共 8 周。
> 每周末留半天做 code review 和进度总结。

---

### 第 1 周：项目脚手架 & 认证系统

**目标：能登录，能上传文件（哪怕什么都不干）**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | 初始化仓库结构：`/backend` `/frontend` `/nginx` `.env.example` `docker-compose.yml` | git 仓库建好，目录结构清晰 |
| 周一 | 配置 Docker Compose：PostgreSQL + Redis + FastAPI + Next.js + Nginx | `docker compose up` 能跑通 |
| 周二 | PostgreSQL 建库：执行 DDL，跑通 alembic 迁移 | `alembic upgrade head` 成功 |
| 周二 | FastAPI 基础：项目结构 `routers/` `schemas/` `models/` `core/`，统一响应格式 | `GET /api/v1/health` 返回 200 |
| 周三 | 实现 `POST /auth/register` 和 `POST /auth/login`（JWT） | Postman 测试通过 |
| 周三 | JWT 中间件：`Depends(get_current_user)` 全局可用 | 受保护接口返回 401 |
| 周四 | 文件上传接口：`POST /tasks`（仅存文件到本地 `/uploads`，不触发分析） | 能上传 PDF，DB 写入一条 pending 任务 |
| 周四 | 文件校验：类型检查（仅PDF）+ 大小限制（50MB）+ SHA-256 hash 去重查询 | 超限和非PDF返回正确错误码 |
| 周五 | Next.js 脚手架：App Router + TailwindCSS + shadcn/ui 初始化 | `npm run dev` 跑通 |
| 周五 | 登录/注册页面（纯前端，连接后端 API） | 能注册、登录、存 token 到 localStorage |
| 周六下午 | code review + 补测试 + 整理 TODO | — |

---

### 第 2 周：PDF 解析引擎

**目标：能把招标文件变成干净的结构化文本**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | PyMuPDF 文本提取基础版：按页提取，合并，去页眉页脚 | 能提取3份真实招标文件的文本 |
| 周一 | 文本质量检测函数：计算中文密度、乱码率，返回 quality_score | 测试5份文件，score 分布合理 |
| 周二 | pdfplumber 表格提取：专门针对评分标准表格 | 能正确提取表格数据（对比原文验证） |
| 周二 | 降级策略：quality_score < 0.6 时触发 PaddleOCR | OCR 版和原版文本对比 |
| 周三 | 文档分块逻辑：chunk_size=3000 token，overlap=200 | 分块后拼接能还原原文 |
| 周三 | 关键章节定位：识别"资格条件""评分标准""技术要求"所在页范围 | 正确定位 3 份文件的关键章节 |
| 周四 | Celery 基础配置：broker=Redis，result_backend=Redis | Celery worker 启动正常 |
| 周四 | 将解析任务包装成 Celery task，触发后异步执行 | 上传文件 → 后台自动开始解析 |
| 周五 | 用 5 份不同类型招标文件全面测试（扫描件/双栏/表格为主） | 记录问题，整理 bad case 清单 |
| 周六下午 | 根据 bad case 优化分块和章节定位逻辑 | — |

---

### 第 3 周：Agent 1 & 2 实现

**目标：能解析出结构化信息，并给出资格评估结论**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | DeepSeek API 接入：配置 LangChain ChatOpenAI，封装通用 LLM 调用 | 能调通 deepseek-chat API |
| 周一 | 实现 Pydantic 模型：ProjectInfo, QualificationItem, ScoringItem | 模型定义完整，字段注释清晰 |
| 周二 | Agent 1 - ProjectInfo 提取 Prompt + Chain：提取项目基本信息 | 测试3份文件，字段提取准确率 > 80% |
| 周二 | Agent 1 - QualificationItem 提取：分块处理 + 去重合并 | 逐条拆分，无明显遗漏 |
| 周三 | Agent 1 - ScoringItem 提取 + 评分总分校验 | 总分校验能捕捉幻觉 |
| 周三 | LangGraph StateGraph 搭建：注册 Agent 1 节点，配置 PostgresSaver checkpointer | graph.compile() 成功 |
| 周四 | Agent 2 - 企业画像接口：`PUT/GET /company-profile` | API 测试通过，数据入库 |
| 周四 | Agent 2 - 资格评估 Prompt：结合企业画像，逐条评估 | 不同画像输入，结论有差异（非硬编码） |
| 周五 | Agent 2b - bid_abort_advisor：生成放弃建议 | 不建议投标时能输出有价值的放弃原因和建议 |
| 周五 | 条件边 1 配置：qualification_router 测试 | 不建议投标 → abort；其他 → continue |
| 周六下午 | 端到端测试 Agent 1→2，记录 LLM 输出质量问题 | — |

---

### 第 4 周：Agent 3/4/5 & 完整 Pipeline

**目标：五个 Agent 全部串通，能产出完整报告**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | Agent 3 - 策略分析 Prompt & Chain | 输出包含评分维度分析、策略建议、报价建议 |
| 周二 | Agent 4 - 方案大纲生成 Prompt & Chain | 生成章节结构合理，权重分配与评分标准对应 |
| 周三 | Agent 5 - 合规审查 Prompt & Chain | compliance_score 计算合理，missing_items 有参考价值 |
| 周三 | 条件边 2 配置：compliance_router + revision_count 递增测试 | 修订循环最多跑 2 次后正常结束 |
| 周四 | Redis pub/sub：各 Agent 节点完成后 publish 事件 | 每个 Agent 完成后推送 agent_output 事件 |
| 周四 | SSE 接口：`GET /tasks/{id}/stream`（含 Token 鉴权） | 前端能实时收到 Agent 进度 |
| 周五 | Celery 任务失败处理：更新 DB status + publish error 事件 | 强制抛异常测试，前端能收到 error 事件 |
| 周五 | `GET /tasks/{id}` 完整响应：聚合所有 Agent 结果返回 | Postman 能看到完整结构 |
| 周六下午 | 用 3 份招标文件跑完整流程，检查每步输出质量 | — |

---

### 第 5 周：RAG 增强（pgvector）

**目标：Agent 能参考历史相似项目，提升方案质量**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | 安装 pgvector，建 document_embeddings 表和 HNSW 索引 | `SELECT * FROM pg_extension WHERE extname='vector'` 成功 |
| 周一 | BGE-M3 嵌入：封装 embed_text() 函数（本地模型或 API） | 能对一段文本生成 1024 维向量 |
| 周二 | 文档入库流程：分析完成后将 chunk 和向量批量写入 | 分析完成后 embeddings 表有数据 |
| 周二 | 向量检索工具：search_similar_tenders() 函数 | 给定查询文本，能召回 top-5 相似 chunk |
| 周三 | 将 RAG 检索结果注入 Agent 3（策略分析）的上下文 | 策略分析 Prompt 包含"历史相似项目参考" |
| 周三 | 爬取或收集 10+ 份公开招标文件，建初始知识库 | 向量库里有真实数据可检索 |
| 周四 | 测试 RAG 效果：对比有/无历史参考的策略分析输出 | 有 RAG 时策略更具体，有数据支撑 |
| 周五 | 优化检索 Prompt，避免 RAG 引入噪音 | bad case 减少 |
| 周六下午 | 整理 RAG 优化记录，更新文档 | — |

---

### 第 6 周：前端核心页面

**目标：有可 demo 的完整前端界面**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | 企业画像填写页（表单）：连接 `PUT /company-profile` | 能填写并保存，下次刷新能回显 |
| 周一 | 文件上传组件：拖拽上传 + 进度条 + 去重提示 | 上传成功后跳转到分析页 |
| 周二 | 分析进度页（SSE 接收）：实时显示"当前执行到哪个 Agent" | Agent 步骤动画，类似打字机效果 |
| 周三 | 结果页 - 项目概况卡片 + 资格评估表格（✅❌风险色） | 视觉清晰，高风险项红色高亮 |
| 周三 | 结果页 - 评分雷达图（用 recharts 或 echarts） | 各评分维度可视化 |
| 周四 | 结果页 - 策略建议面板 + 方案大纲（树形结构/折叠列表） | 展示所有 Agent 4 输出 |
| 周四 | 结果页 - 合规审查报告：compliance_score 进度条 + missing_items 列表 | 视觉直观 |
| 周五 | 历史任务列表页（Dashboard）：分页、状态筛选、再次查看 | 能管理历史任务 |
| 周五 | 错误状态处理：任务失败时前端展示错误信息和重试按钮 | 不能让用户看到空白页 |
| 周六下午 | 整体走查 + 移动端适配检查 | — |

---

### 第 7 周：测试、Prompt 优化

**目标：用真实文件验证，输出质量达到可演示标准**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | 收集 10+ 份不同类型招标文件（IT类/工程类/服务类） | 文件多样性足够 |
| 周二-周三 | 逐份跑完整流程，记录：解析准确率、评估合理性、方案完整度 | 建立评测表格，每份文件打分 |
| 周三-周四 | 针对 bad case 迭代优化 Prompt（重点：Agent 1 和 Agent 5） | bad case 减少 50%以上 |
| 周四 | 并发测试：同时提交 3 个任务，验证 Celery 稳定性 | 3 个任务都能正常完成 |
| 周五 | Token 成本统计：记录每份文件的实际费用 | 平均每次分析成本 < 1元（合理目标） |
| 周六下午 | 边界情况测试：空文件/损坏PDF/纯图片PDF/超长文件 | 所有情况都有合理错误提示 |

---

### 第 8 周：部署上线 & 项目收尾

**目标：公网可访问，项目文档完整**

| 天 | 任务 | 完成标准 |
|----|------|---------|
| 周一 | 购买/配置服务器：阿里云ECS 或轻量服务器，安装 Docker | SSH 能连上，Docker 能跑 |
| 周一 | 配置环境变量：`.env.production`，不 commit 到 git | 敏感信息隔离 |
| 周二 | Let's Encrypt SSL 证书申请，Nginx HTTPS 配置 | 域名 https 访问正常 |
| 周二 | 生产环境部署：`docker compose -f docker-compose.prod.yml up -d` | 所有服务正常运行 |
| 周三 | 生产环境端到端测试：真实上传文件跑一遍完整流程 | 能正常出报告 |
| 周三 | 监控配置：Celery 任务状态监控（Flower），简单日志告警 | 任务失败时能感知 |
| 周四 | README 撰写：项目介绍、架构说明、本地运行指南、截图 | 别人 clone 后能跑起来 |
| 周五 | 录制 Demo 视频（3-5分钟）：上传文件 → 实时分析 → 查看报告 | 可用于简历投递和面试展示 |
| 周六 | 技术总结博客初稿：《用 LangGraph 构建招投标分析 Agent 的踩坑记录》 | 有技术深度，体现工程决策过程 |

---

## 附：关键决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 向量数据库 | pgvector | 无需额外组件，与 PostgreSQL 共用，MVP 阶段够用 |
| LLM 调度 | 统一 DeepSeek-V3 | 成本低，延迟稳定，MVP 阶段无需多模型调度复杂度 |
| 企业画像 | 表单 + 文本注入 Prompt | 企业 RAG 作为 v2 规划，降低 MVP 开发复杂度 |
| 检查点存储 | PostgresSaver | 避免 SqliteSaver 并发写锁问题 |
| 合规审查循环上限 | 2次 | 平衡质量和 Token 成本，避免死循环 |
