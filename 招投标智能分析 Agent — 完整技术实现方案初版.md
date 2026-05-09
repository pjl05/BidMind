# 招投标智能分析 Agent — 完整技术实现方案

---

## 二、系统总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户浏览器                                  │
│  Next.js 前端 (App Router + RSC + Streaming UI)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / WebSocket (SSE for streaming)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx 反向代理 + SSL                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI 应用服务层                               │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ 认证模块  │  │ 文件管理  │  │ 任务调度  │  │  流式响应网关   │  │
│  │ JWT Auth │  │ Upload   │  │ Celery   │  │  SSE Gateway   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌────────────────┐ ┌──────────────┐ ┌─────────────────────────┐
│  PostgreSQL    │ │    Redis     │ │   LangGraph Agent 引擎   │
│  用户/任务/报告 │ │ 缓存/会话/锁 │ │                          │
│                │ │              │ │  ┌─────────────────────┐ │
│                │ │              │ │  │ StateGraph 编排      │ │
│                │ │              │ │  │                     │ │
│                │ │              │ │  │ Parser → Qualifier  │ │
│                │ │              │ │  │ → Strategist →      │ │
│                │ │              │ │  │ Drafter → Reviewer  │ │
│                │ │              │ │  └─────────────────────┘ │
│                │ │              │ │                          │
│                │ │              │ │  ┌─────────────────────┐ │
│                │ │              │ │  │ 工具层               │ │
│                │ │              │ │  │ PDF解析 / 向量检索   │ │
│                │ │              │ │  │ 代码执行 / 网页搜索  │ │
│                │ │              │ │  └─────────────────────┘ │
└────────────────┘ └──────────────┘ └────────────┬────────────┘
                                                  │
                                    ┌─────────────┼──────────────┐
                                    ▼             ▼              ▼
                              ┌──────────┐ ┌──────────┐  ┌──────────┐
                              │ DeepSeek │ │ Milvus   │  │ MinIO/OSS│
                              │ API      │ │ 向量数据库 │  │ 文件存储  │
                              └──────────┘ └──────────┘  └──────────┘
```

---

## 三、技术栈详细选型（附理由）

### 后端核心

| 技术          | 版本   | 选型理由                                                     |
| ------------- | ------ | ------------------------------------------------------------ |
| **Python**    | 3.11+  | AI/Agent 生态主力语言，LangGraph/LangChain 原生支持          |
| **FastAPI**   | 0.110+ | 异步高性能，原生支持 SSE 流式响应，自动生成 API 文档，面试高频技术 |
| **LangGraph** | 0.2+   | LangChain 官方 Agent 编排框架，状态图驱动，支持人机交互节点，2025年Agent开发事实标准 |
| **LangChain** | 0.3+   | LLM 抽象层，工具调用、Prompt 模板、输出解析的基础设施        |
| **Celery**    | 5.4+   | 异步任务队列，处理耗时的文档分析任务，避免阻塞 API 请求      |
| **Pydantic**  | 2.7+   | 数据校验 + 结构化输出，Agent 输出的类型安全保障              |

### LLM 选型

| 模型            | 用途                                 | 理由                                                         |
| --------------- | ------------------------------------ | ------------------------------------------------------------ |
| **DeepSeek-V3** | 主力模型（需求解析、代码生成、评估） | 中文能力强，性价比极高（约1元/百万token），支持 Function Calling |
| **Qwen2.5-72B** | 备选/对比                            | 阿里系，中文理解好，可通过阿里云DashScope调用                |
| **DeepSeek-R1** | 复杂推理场景（架构评估、合规审查）   | 推理能力接近 GPT-4，适合需要多步逻辑判断的任务               |

**面试时你能说：**"主力用 DeepSeek-V3 控制成本，对推理要求高的节点切换 R1，通过 LangGraph 的条件路由实现智能模型调度。" — 这展示了工程权衡能力。

### 文档解析层

| 技术                | 用途                                               |
| ------------------- | -------------------------------------------------- |
| **PyMuPDF (fitz)**  | PDF 文本提取，速度快，处理中文 PDF 表现好          |
| **Unstructured.io** | 复杂 PDF 结构化解析（表格、多栏、嵌套列表）        |
| **PaddleOCR**       | 处理扫描件/图片型 PDF 的 OCR（招标文件常见扫描件） |
| **pdfplumber**      | 精确提取 PDF 表格数据（评分标准表格）              |

### 向量数据库 & RAG

| 技术                           | 用途                                                   |
| ------------------------------ | ------------------------------------------------------ |
| **Milvus Lite**                | 向量存储和检索，支持百万级向量，单机可用也有分布式版本 |
| **BGE-M3**                     | 中文向量嵌入模型，开源免费，中文检索效果顶级           |
| **Reranker (BGE-Reranker-v2)** | 检索结果重排序，显著提升 RAG 精度                      |

### 前端

| 技术              | 版本             | 选型理由                                                   |
| ----------------- | ---------------- | ---------------------------------------------------------- |
| **Next.js**       | 14+ (App Router) | React 全栈框架，SSR + Streaming 原生支持，前端面试高频技术 |
| **TypeScript**    | 5.x              | 类型安全，展示工程素养                                     |
| **TailwindCSS**   | 3.4+             | 原子化 CSS，开发效率高                                     |
| **shadcn/ui**     | latest           | 高质量 React 组件库，可定制性强                            |
| **Framer Motion** | latest           | 动画库，提升产品视觉体验                                   |
| **Monaco Editor** | —                | VS Code 同款编辑器组件，展示代码片段用                     |

### 部署 & 基础设施

| 技术                        | 用途                                       |
| --------------------------- | ------------------------------------------ |
| **Docker + Docker Compose** | 容器化，一键部署，展示运维能力             |
| **Nginx**                   | 反向代理 + SSL 终止 + 静态资源服务         |
| **阿里云 ECS**              | 服务器（2核4G起步，够用）                  |
| **Supabase**                | PostgreSQL 托管（免费额度足够MVP阶段）     |
| **Vercel**                  | 前端部署（Next.js 官方推荐，免费额度充足） |
| **阿里云 OSS**              | 文件存储（招标文件PDF存储）                |

---

## 四、数据库设计

```sql
-- 用户表
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname      VARCHAR(100),
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- 分析任务表（核心表）
CREATE TABLE analysis_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    file_name       VARCHAR(500) NOT NULL,
    file_url        VARCHAR(1000) NOT NULL,      -- OSS文件地址
    file_size       INTEGER,                      -- 文件大小(bytes)
    page_count      INTEGER,                      -- PDF页数
    status          VARCHAR(20) DEFAULT 'pending',
    -- pending / parsing / analyzing / generating / completed / failed
    current_agent   VARCHAR(50),                  -- 当前执行的Agent节点
    progress        INTEGER DEFAULT 0,            -- 进度百分比
    error_message   TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    completed_at    TIMESTAMP
);

-- 结构化解析结果
CREATE TABLE parsed_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES analysis_tasks(id),
    -- 项目概况
    project_name    TEXT,
    project_budget  TEXT,
    bid_deadline    TEXT,
    bid_opening     TEXT,
    project_location TEXT,
    -- 结构化JSON存储
    qualification_requirements JSONB,  -- 资格条件列表
    scoring_criteria            JSONB,  -- 评分标准及权重
    technical_requirements      JSONB,  -- 技术参数要求
    key_risk_clauses            JSONB,  -- 风险条款
    raw_text                    TEXT,    -- 原始提取文本
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 资格评估结果
CREATE TABLE qualification_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES analysis_tasks(id),
    requirement     TEXT NOT NULL,        -- 招标要求原文
    category        VARCHAR(50),          -- 资质/业绩/人员/财务/其他
    is_met          BOOLEAN,              -- 是否满足
    evidence        TEXT,                 -- 满足依据
    risk_level      VARCHAR(10),          -- low/medium/high
    suggestion      TEXT,                 -- 建议
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 策略分析结果
CREATE TABLE strategy_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES analysis_tasks(id),
    scoring_analysis      JSONB,   -- 各评分维度分析
    competitive_strategy  JSONB,   -- 竞争策略建议
    risk_assessment       JSONB,   -- 风险评估
    recommended_actions   JSONB,   -- 推荐行动项
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 生成的投标方案大纲
CREATE TABLE proposal_outlines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES analysis_tasks(id),
    outline         JSONB NOT NULL,       -- 大纲结构
    content_draft   TEXT,                  -- 生成的草稿内容
    word_count      INTEGER,
    compliance_score FLOAT,               -- 合规评分
    missing_items   JSONB,               -- 遗漏项
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 用户历史记录索引
CREATE INDEX idx_tasks_user ON analysis_tasks(user_id, created_at DESC);
CREATE INDEX idx_tasks_status ON analysis_tasks(status);
CREATE INDEX idx_parsed_task ON parsed_results(task_id);
```

---

## 五、Agent 工作流详细设计（核心）

### LangGraph StateGraph 完整定义

```python
# ============================================================
# state.py — 定义全局状态
# ============================================================
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langgraph.graph import add_messages

class ProjectInfo(BaseModel):
    """项目基本信息"""
    project_name: str = ""
    project_code: str = ""
    budget: str = ""
    bid_deadline: str = ""
    bid_opening_time: str = ""
    project_location: str = ""
    purchaser: str = ""
    agent_contact: str = ""

class QualificationItem(BaseModel):
    """单项资格要求"""
    requirement: str
    category: str = Field(description="资质证书/业绩案例/人员配置/财务指标/其他")
    is_mandatory: bool = True
    risk_level: str = Field(default="low", description="low/medium/high")

class ScoringItem(BaseModel):
    """评分标准单项"""
    dimension: str
    max_score: float
    scoring_method: str
    weight: float = 0.0

class QualificationResult(BaseModel):
    """资格评估单项结果"""
    requirement: str
    category: str
    is_met: bool
    evidence: str = ""
    risk_level: str = "low"
    suggestion: str = ""

class AgentState(TypedDict):
    """LangGraph 全局状态"""
    # 输入
    task_id: str
    file_path: str
    raw_text: str

    # Agent 1: 文档解析输出
    project_info: ProjectInfo
    qualification_requirements: list[QualificationItem]
    scoring_criteria: list[ScoringItem]
    technical_requirements: list[str]
    risk_clauses: list[str]

    # Agent 2: 资格评估输出
    qualification_results: list[QualificationResult]
    overall_qualification: str  # "通过" / "有风险" / "不建议投标"

    # Agent 3: 策略分析输出
    scoring_analysis: dict
    competitive_strategy: list[str]
    recommended_actions: list[str]

    # Agent 4: 方案生成输出
    proposal_outline: dict
    proposal_draft: str

    # Agent 5: 合规审查输出
    compliance_score: float
    missing_items: list[str]
    revision_suggestions: list[str]

    # 控制流
    messages: Annotated[list, add_messages]
    current_step: str
    error: str
    needs_revision: bool
```

```python
# ============================================================
# agents.py — 五个Agent的具体实现
# ============================================================
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

llm_fast = ChatOpenAI(
    model="deepseek-chat",       # DeepSeek-V3
    base_url="https://api.deepseek.com",
    temperature=0.1,
    max_tokens=4096,
)

llm_reasoning = ChatOpenAI(
    model="deepseek-reasoner",   # DeepSeek-R1
    base_url="https://api.deepseek.com",
    temperature=0.0,
)


# ---- Agent 1: 文档结构化解析 ----
async def parse_document(state: AgentState) -> dict:
    """解析招标文件，提取结构化信息"""

    parser_project = PydanticOutputParser(pydantic_object=ProjectInfo)
    parser_qual = PydanticOutputParser(pydantic_object=QualificationItem)
    parser_score = PydanticOutputParser(pydantic_object=ScoringItem)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的招标文件分析专家。
请从以下招标文件内容中提取结构化信息。

{format_instructions}

注意：
1. 预算金额请保留原文格式（如"500万元"）
2. 时间请保留原文格式（如"2025年7月15日 09:30"）
3. 如果某项信息未找到，填写"未提及"
4. 资格条件要逐条拆分，不要合并"""),
        ("human", "招标文件内容：\n{document_text}")
    ])

    # 提取项目基本信息
    chain_project = prompt | llm_fast | parser_project
    project_info = await chain_project.ainvoke({
        "document_text": state["raw_text"][:8000],
        "format_instructions": parser_project.get_format_instructions()
    })

    # 提取资格要求（分段处理长文档）
    qual_prompt = ChatPromptTemplate.from_messages([
        ("system", """从以下招标文件片段中提取所有投标人资格条件要求。
输出为JSON数组，每个元素包含：
- requirement: 要求原文
- category: 分类(资质证书/业绩案例/人员配置/财务指标/其他)
- is_mandatory: 是否为必须满足的条件（否决性条件）

{format_instructions}"""),
        ("human", "文件内容：\n{chunk}")
    ])

    # 文档分块处理（避免超出上下文窗口）
    chunks = split_document(state["raw_text"], chunk_size=6000, overlap=500)
    all_qualifications = []
    for chunk in chunks:
        chain_qual = qual_prompt | llm_fast | parser_qual
        result = await chain_qual.ainvoke({
            "chunk": chunk,
            "format_instructions": parser_qual.get_format_instructions()
        })
        all_qualifications.append(result)

    # 去重合并
    qualifications = deduplicate_qualifications(all_qualifications)

    # 提取评分标准
    score_prompt = ChatPromptTemplate.from_messages([
        ("system", """从以下招标文件中提取评标标准/评分细则。
输出为JSON数组，每个元素包含：
- dimension: 评分维度名称
- max_score: 该维度满分
- scoring_method: 评分方法描述
- weight: 权重占比

{format_instructions}"""),
        ("human", "文件内容：\n{scoring_text}")
    ])

    scoring_text = extract_scoring_section(state["raw_text"])
    chain_score = score_prompt | llm_fast | parser_score
    scoring_criteria = await chain_score.ainvoke({
        "scoring_text": scoring_text,
        "format_instructions": parser_score.get_format_instructions()
    })

    return {
        "project_info": project_info,
        "qualification_requirements": qualifications,
        "scoring_criteria": scoring_criteria,
        "current_step": "document_parsed"
    }


# ---- Agent 2: 投标资格可行性评估 ----
async def check_qualification(state: AgentState) -> dict:
    """逐条评估企业资质是否满足招标要求"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个投标资格审核专家。
请逐条分析以下资格要求，给出评估结果。

对于每条要求，输出：
- requirement: 原始要求
- category: 分类
- is_met: 假设企业为一家中型科技公司，具备通用资质（系统集成资质、ISO认证、一般业绩）
- evidence: 满足/不满足的依据
- risk_level: low/medium/high
- suggestion: 如果不满足，给出建议

综合所有条件，给出 overall_qualification: "建议投标" / "有风险" / "不建议投标"

{format_instructions}"""),
        ("human", """资格要求列表：
{qualifications}

评分标准：
{scoring_criteria}""")
    ])

    parser = PydanticOutputParser(pydantic_object=QualificationResult)
    chain = prompt | llm_reasoning | parser

    results = await chain.ainvoke({
        "qualifications": format_list(state["qualification_requirements"]),
        "scoring_criteria": format_list(state["scoring_criteria"]),
        "format_instructions": parser.get_format_instructions()
    })

    # 计算整体评估
    high_risk_count = sum(1 for r in results if r.risk_level == "high")
    overall = ("不建议投标" if high_risk_count >= 3
               else "有风险" if high_risk_count >= 1
               else "建议投标")

    return {
        "qualification_results": results,
        "overall_qualification": overall,
        "current_step": "qualification_checked"
    }


# ---- Agent 3: 竞争策略分析 ----
async def analyze_strategy(state: AgentState) -> dict:
    """基于评分标准给出投标策略建议"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个资深投标策略顾问。
基于以下招标信息，给出详细的投标竞争策略。

分析维度：
1. 评分维度拆解：每个评分维度的得分策略
2. 重点突破方向：哪些维度性价比最高（投入产出比）
3. 风险规避建议
4. 技术方案亮点建议
5. 报价策略建议

输出JSON格式：
{{
    "scoring_analysis": [
        {{"dimension": "...", "max_score": ..., "strategy": "...", "difficulty": "...", "priority": "..."}}
    ],
    "competitive_strategy": ["策略1", "策略2", ...],
    "recommended_actions": ["行动1", "行动2", ...],
    "pricing_advice": "..."
}}"""),
        ("human", """项目信息：{project_info}

资格条件：{qualifications}

评分标准：{scoring_criteria}

技术要求：{technical_requirements}""")
    ])

    chain = prompt | llm_reasoning
    result = await chain.ainvoke({
        "project_info": state["project_info"].model_dump_json(),
        "qualifications": format_list(state["qualification_requirements"]),
        "scoring_criteria": format_list(state["scoring_criteria"]),
        "technical_requirements": "\n".join(state.get("technical_requirements", []))
    })

    parsed = parse_json_response(result.content)

    return {
        "scoring_analysis": parsed.get("scoring_analysis", {}),
        "competitive_strategy": parsed.get("competitive_strategy", []),
        "recommended_actions": parsed.get("recommended_actions", []),
        "current_step": "strategy_analyzed"
    }


# ---- Agent 4: 投标方案大纲生成 ----
async def generate_proposal(state: AgentState) -> dict:
    """根据评分权重自动生成投标方案大纲"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个投标方案撰写专家。
根据评分标准的权重，自动生成投标技术方案大纲。

规则：
1. 方案章节的篇幅分配应与评分权重成正比
2. 每个章节要对应具体的评分要求
3. 章节内容要包含：概述、详细方案、实施计划、保障措施
4. 输出结构化的JSON大纲

输出格式：
{{
    "outline": {{
        "title": "XXX项目投标技术方案",
        "chapters": [
            {{
                "chapter_num": "1",
                "title": "章节标题",
                "corresponding_score": "对应评分项",
                "allocated_weight": 0.25,
                "sections": [
                    {{"title": "小节标题", "key_points": ["要点1", "要点2"]}}
                ],
                "estimated_pages": 10
            }}
        ]
    }},
    "total_estimated_pages": 80,
    "draft_content": "各章节的详细内容草稿..."
}}"""),
        ("human", """项目名称：{project_name}
评分标准：{scoring_criteria}
技术要求：{technical_requirements}
策略建议：{strategy}""")
    ])

    chain = prompt | llm_fast
    result = await chain.ainvoke({
        "project_name": state["project_info"].project_name,
        "scoring_criteria": format_list(state["scoring_criteria"]),
        "technical_requirements": "\n".join(state.get("technical_requirements", [])),
        "strategy": json.dumps(state.get("competitive_strategy", []), ensure_ascii=False)
    })

    parsed = parse_json_response(result.content)

    return {
        "proposal_outline": parsed.get("outline", {}),
        "proposal_draft": parsed.get("draft_content", ""),
        "current_step": "proposal_generated"
    }


# ---- Agent 5: 合规审查 ----
async def compliance_review(state: AgentState) -> dict:
    """检查生成的方案是否覆盖所有招标要求"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个投标合规审查专家。
请检查以下投标方案大纲是否覆盖了招标文件的所有要求。

审查维度：
1. 是否所有否决性资格条件都有响应
2. 是否所有评分维度都有对应章节
3. 遗漏了哪些得分机会
4. 方案中是否有与招标要求矛盾的内容

输出JSON：
{{
    "compliance_score": 0.85,
    "covered_items": ["已覆盖项1", ...],
    "missing_items": ["遗漏项1", ...],
    "contradictions": ["矛盾项1", ...],
    "revision_suggestions": ["修改建议1", ...],
    "needs_revision": true/false
}}"""),
        ("human", """招标要求：
资格条件：{qualifications}
评分标准：{scoring_criteria}

投标方案大纲：
{proposal_outline}

方案草稿：
{proposal_draft}""")
    ])

    chain = prompt | llm_reasoning
    result = await chain.ainvoke({
        "qualifications": format_list(state["qualification_requirements"]),
        "scoring_criteria": format_list(state["scoring_criteria"]),
        "proposal_outline": json.dumps(state["proposal_outline"], ensure_ascii=False),
        "proposal_draft": state.get("proposal_draft", "")[:5000]
    })

    parsed = parse_json_response(result.content)

    return {
        "compliance_score": parsed.get("compliance_score", 0),
        "missing_items": parsed.get("missing_items", []),
        "revision_suggestions": parsed.get("revision_suggestions", []),
        "needs_revision": parsed.get("needs_revision", False),
        "current_step": "compliance_reviewed"
    }
```

```python
# ============================================================
# graph.py — LangGraph 工作流编排（核心中的核心）
# ============================================================
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

def build_tender_agent_graph() -> StateGraph:
    """构建招投标分析Agent工作流"""

    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("document_parser", parse_document)
    workflow.add_node("qualification_checker", check_qualification)
    workflow.add_node("strategy_analyzer", analyze_strategy)
    workflow.add_node("proposal_generator", generate_proposal)
    workflow.add_node("compliance_reviewer", compliance_review)

    # 定义边
    workflow.set_entry_point("document_parser")
    workflow.add_edge("document_parser", "qualification_checker")
    workflow.add_edge("qualification_checker", "strategy_analyzer")
    workflow.add_edge("strategy_analyzer", "proposal_generator")
    workflow.add_edge("proposal_generator", "compliance_reviewer")

    # 条件边：合规审查不通过则回到方案生成重新修改
    workflow.add_conditional_edges(
        "compliance_reviewer",
        lambda state: "revise" if state["needs_revision"] and state.get("_revision_count", 0) < 2 else "finish",
        {
            "revise": "proposal_generator",
            "finish": END
        }
    )

    # 编译（带检查点，支持断点续执行）
    memory = SqliteSaver.from_conn_string(":memory:")
    app = workflow.compile(checkpointer=memory)

    return app
```

```python
# ============================================================
# api.py — FastAPI 接口层（SSE流式响应）
# ============================================================
from fastapi import FastAPI, UploadFile, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio, json

app = FastAPI(title="招投标智能分析 Agent")

@app.post("/api/analysis/start")
async def start_analysis(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """上传招标文件，启动分析任务"""
    # 1. 保存文件到OSS
    file_url = await upload_to_oss(file)

    # 2. 创建任务记录
    task = await create_task(user_id=current_user.id, file_name=file.filename, file_url=file_url)

    # 3. 提交异步任务
    run_analysis_pipeline.delay(task.id, file_url)

    return {"task_id": task.id, "status": "pending"}


@app.get("/api/analysis/{task_id}/stream")
async def stream_analysis(task_id: str):
    """SSE流式返回分析进度和结果"""

    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"task:{task_id}:events")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield {
                        "event": data["event_type"],  # progress / agent_output / completed
                        "data": json.dumps(data["payload"], ensure_ascii=False)
                    }
                    if data["event_type"] == "completed":
                        break
        finally:
            await pubsub.unsubscribe()

    return EventSourceResponse(event_generator())
```

```python
# ============================================================
# tools.py — Agent可用的工具集
# ============================================================
from langchain_core.tools import tool

@tool
def extract_pdf_tables(file_path: str) -> str:
    """提取PDF中的所有表格，返回结构化数据"""
    import pdfplumber
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            tables.extend(page_tables)
    return json.dumps(tables, ensure_ascii=False, default=str)

@tool
def search_similar_tenders(query: str, top_k: int = 5) -> str:
    """在历史招标文件中搜索相似项目（向量检索）"""
    results = vector_store.similarity_search(query, k=top_k)
    return "\n---\n".join([doc.page_content for doc in results])

@tool
def calculate_score_distribution(scoring_criteria: str) -> str:
    """计算评分标准的权重分布，识别关键得分维度"""
    criteria = json.loads(scoring_criteria)
    total = sum(item["max_score"] for item in criteria)
    analysis = []
    for item in criteria:
        weight = item["max_score"] / total * 100
        analysis.append({
            "dimension": item["dimension"],
            "weight": f"{weight:.1f}%",
            "priority": "高" if weight > 20 else "中" if weight > 10 else "低"
        })
    return json.dumps(analysis, ensure_ascii=False)

@tool
def check_deadline_feasibility(deadline: str, project_complexity: str) -> str:
    """评估投标截止时间是否充足"""
    from datetime import datetime, timedelta
    # 解析截止日期，结合项目复杂度给出时间评估
    # ...
    return "时间充足/时间紧张/不建议投标"
```

---

## 六、前端页面设计

### 页面结构

```
/                         → 首页（产品介绍 + 上传入口）
/login                    → 登录
/register                 → 注册
/dashboard                → 用户仪表盘（历史任务列表）
/analysis/{task_id}       → 分析结果页（核心页面）
/history                  → 历史记录
```

### 核心页面：分析结果页

```tsx
// app/analysis/[taskId]/page.tsx — 核心分析结果页面
import { StreamingProgress } from '@/components/StreamingProgress'
import { ProjectOverview } from '@/components/ProjectOverview'
import { QualificationTable } from '@/components/QualificationTable'
import { ScoringRadar } from '@/components/ScoringRadar'
import { StrategyPanel } from '@/components/StrategyPanel'
import { ProposalOutline } from '@/components/ProposalOutline'
import { ComplianceReport } from '@/components/ComplianceReport'

export default async function AnalysisPage({ params }: { params: { taskId: string } }) {
  return (
    <div className="min-h-screen bg-background">
      {/* 顶部：项目概览卡片 */}
      <ProjectOverview taskId={params.taskId} />

      {/* 主体：五阶段分析结果 */}
      <div className="grid grid-cols-12 gap-6 p-6">

        {/* 左侧：资格评估 + 评分雷达图 */}
        <div className="col-span-4 space-y-6">
          <QualificationTable taskId={params.taskId} />
          <ScoringRadar taskId={params.taskId} />
        </div>

        {/* 右侧：策略分析 + 方案大纲 + 合规报告 */}
        <div className="col-span-8 space-y-6">
          <StrategyPanel taskId={params.taskId} />
          <ProposalOutline taskId={params.taskId} />
          <ComplianceReport taskId={params.taskId} />
        </div>
      </div>

      {/* 底部浮动：实时进度条（分析进行中时显示） */}
      <StreamingProgress taskId={params.taskId} />
    </div>
  )
}
```

---

## 七、部署方案

### Docker Compose 一键部署

```yaml
# docker-compose.yml
version: '3.9'

services:
  # ---- 后端 API ----
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/tender_agent
      - REDIS_URL=redis://redis:6379/0
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - MILVUS_HOST=milvus
    depends_on:
      - db
      - redis
      - milvus
    volumes:
      - ./uploads:/app/uploads

  # ---- Celery Worker（处理异步分析任务）----
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A tasks worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/tender_agent
      - REDIS_URL=redis://redis:6379/0
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - MILVUS_HOST=milvus
    depends_on:
      - db
      - redis
      - milvus

  # ---- 前端 ----
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000

  # ---- PostgreSQL ----
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: tender_agent
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # ---- Redis ----
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # ---- Milvus (向量数据库) ----
  milvus:
    image: milvusdb/milvus:v2.4-latest
    ports:
      - "19530:19530"
    environment:
      - ETCD_USE_EMBED=true
      - COMMON_STORAGETYPE=local
    volumes:
      - milvus_data:/var/lib/milvus

  # ---- Nginx 反向代理 ----
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  pgdata:
  milvus_data:
```

### Nginx 配置

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # API 请求转发到后端
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # SSE 流式响应需要的配置
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }

    # 其他请求转发到前端
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 服务器配置建议

```
阿里云 ECS 推荐配置（MVP阶段）：
├── 规格：2核4G（ecs.c7.large）
├── 系统盘：40G SSD
├── 带宽：5Mbps（够用，前端走Vercel可省带宽）
├── 操作系统：Ubuntu 22.04
├── 费用：约 ¥200-300/月（新用户有优惠）
└── 域名：¥50-100/年 + SSL证书（免费Let's Encrypt）

或者更省钱的方案：
├── 前端 → Vercel（免费）
├── 后端 → 阿里云ECS 轻量应用服务器（2核2G，¥60/月）
├── 数据库 → Supabase 免费额度
├── 向量库 → Milvus Lite 嵌入式模式（不需要单独部署）
└── 文件存储 → 阿里云OSS（按量付费，几乎免费）
```

---

## 八、开发排期（8周）

```
┌─────────────────────────────────────────────────────────────┐
│  第1周：基础搭建                                               │
│  ├── FastAPI 项目脚手架 + Docker 环境                          │
│  ├── PostgreSQL + Redis 初始化                                │
│  ├── 用户注册/登录（JWT）                                      │
│  ├── 文件上传接口（→ 本地存储，后续迁移OSS）                     │
│  └── Next.js 前端脚手架 + 登录/注册页面                         │
├─────────────────────────────────────────────────────────────┤
│  第2周：文档解析引擎                                            │
│  ├── PDF 文本提取（PyMuPDF）                                   │
│  ├── 复杂表格提取（pdfplumber + Unstructured）                 │
│  ├── 扫描件 OCR 支持（PaddleOCR）                             │
│  ├── Agent 1: 文档结构化解析（LLM + Pydantic输出）              │
│  └── 测试：用3-5份真实招标文件验证解析效果                       │
├─────────────────────────────────────────────────────────────┤
│  第3周：Agent核心Pipeline                                      │
│  ├── Agent 2: 投标资格评估                                     │
│  ├── Agent 3: 竞争策略分析                                     │
│  ├── LangGraph StateGraph 编排完整流程                         │
│  ├── Redis 发布/订阅 实时进度推送                               │
│  └── Celery 异步任务调度                                       │
├─────────────────────────────────────────────────────────────┤
│  第4周：Agent核心Pipeline（续）                                 │
│  ├── Agent 4: 投标方案大纲生成                                  │
│  ├── Agent 5: 合规审查 + 自动修订循环                           │
│  ├── 条件路由：不通过→重新生成（最多2次）                         │
│  └── 端到端集成测试                                             │
├─────────────────────────────────────────────────────────────┤
│  第5周：RAG增强                                                │
│  ├── 向量数据库搭建（Milvus Lite）                              │
│  ├── BGE-M3 嵌入模型部署                                      │
│  ├── 招标文件知识库构建（爬取公开招标文件）                       │
│  ├── RAG 检索增强Agent（历史相似项目参考）                       │
│  └── Reranker 精排优化                                         │
├─────────────────────────────────────────────────────────────┤
│  第6周：前端开发                                               │
│  ├── 分析结果页（项目概况 + 资格表格 + 评分雷达图）               │
│  ├── SSE 流式进度展示（Agent逐步输出动画）                       │
│  ├── 策略分析面板 + 投施方案大纲树形图                           │
│  ├── 历史任务列表 + 详情页                                     │
│  └── 响应式适配 + 动画打磨（Framer Motion）                     │
├─────────────────────────────────────────────────────────────┤
│  第7周：测试优化                                                │
│  ├── 10+ 份真实招标文件端到端测试                                │
│  ├── Agent 输出质量评估（准确率、完整度）                        │
│  ├── Prompt 优化迭代                                           │
│  ├── 性能优化（文档分块策略、并发控制）                           │
│  └── 错误处理 + 边界情况覆盖                                    │
├─────────────────────────────────────────────────────────────┤
│  第8周：部署上线 + 文档                                         │
│  ├── Docker Compose 打包                                       │
│  ├── 阿里云 ECS 部署 + 域名 + HTTPS                            │
│  ├── 生产环境测试                                              │
│  ├── README + 技术文档撰写                                     │
│  ├── 录制演示视频（备用）                                       │
│  └── 撰写技术博客："多Agent架构在招投标领域的实践"                │
└─────────────────────────────────────────────────────────────┘
```

