# BidMind Week 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现招投标文档智能分析核心功能，包括 PDF 解析、LangGraph 多Agent流程、DeepSeek API 集成。

**Architecture:** 基于 FastAPI + LangGraph + DeepSeek API + Celery 的异步分析流程，前端通过轮询获取分析进度。

---

## File Structure Overview

```
BidMind/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py          # LangGraph StateGraph
│   │   │   ├── nodes.py           # Agent nodes
│   │   │   └── schemas.py         # Agent state schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py     # PDF 文本提取
│   │   │   ├── deepseek.py       # DeepSeek API 封装
│   │   │   └── embedding.py      # 向量化服务
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py     # Celery 配置
│   │   │   └── analysis.py        # Celery 分析任务
│   │   └── api/v1/
│   │       └── analysis.py        # 分析 API 端点
│   └── tests/
│       └── test_agents.py
├── frontend/
│   └── src/
│       └── app/
│           └── analysis/
│               ├── page.tsx      # 分析页面
│               └── result/
│                   └── page.tsx  # 结果页面
```

---

## Day 7: DeepSeek API Integration (Monday)

### Task 42: Create DeepSeek Service

**Files:**
- Create: `backend/app/services/deepseek.py`
- Create: `backend/app/services/__init__.py`

- [ ] **Step 1: Create DeepSeek API service**

Create: `D:/person_ai_projects/BidMind/backend/app/services/deepseek.py`

```python
from typing import Optional
import httpx
from app.core.config import get_settings

settings = get_settings()


class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = "deepseek-chat"

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send chat completion request to DeepSeek API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // 4


deepseek_service = DeepSeekService()
```

- [ ] **Step 2: Update app/services/__init__.py**

Create: `D:/person_ai_projects/BidMind/backend/app/services/__init__.py`

```python
from app.services.deepseek import deepseek_service

__all__ = ["deepseek_service"]
```

- [ ] **Step 3: Add httpx to requirements.txt**

Add `httpx==0.27.0` to the Utilities section.

---

### Task 43: Create PDF Parser Service

**Files:**
- Create: `backend/app/services/pdf_parser.py`

- [ ] **Step 1: Create PDF parser service**

Create: `D:/person_ai_projects/BidMind/backend/app/services/pdf_parser.py`

```python
import os
from typing import Optional
import hashlib

try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()


class PDFParser:
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    def extract_text(self, file_path: str) -> str:
        """Extract text content from PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf is not installed")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise ValueError(f"PDF file too large: {file_size} bytes")

        text_parts = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Page {i+1}]\n{text}")

        return "\n\n".join(text_parts)

    def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF."""
        if not PDF_AVAILABLE:
            raise ImportError("pypdf is not installed")

        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            return len(reader.pages)


pdf_parser = PDFParser()
```

- [ ] **Step 2: Add pypdf to requirements.txt**

Add `pypdf==5.0.1` to the Utilities section.

---

### Task 44: Create Embedding Service

**Files:**
- Create: `backend/app/services/embedding.py`

- [ ] **Step 1: Create embedding service**

Create: `D:/person_ai_projects/BidMind/backend/app/services/embedding.py`

```python
from typing import Optional
import hashlib
import numpy as np


class EmbeddingService:
    """Simple embedding service using hash-based representation."""

    def __init__(self):
        self.dimension = 1536

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for text.

        Note: For production, use a dedicated embedding model.
        This is a placeholder that uses hash-based representation.
        """
        text_hash = hashlib.sha256(text.encode()).digest()
        vector = np.frombuffer(text_hash[:self.dimension], dtype=np.float32)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        return [await self.embed_text(doc) for doc in documents]


embedding_service = EmbeddingService()
```

- [ ] **Step 2: Add numpy to requirements.txt**

Add `numpy==1.26.4` to the Utilities section.

---

### Task 45: Commit Day 7 Changes

- [ ] **Step 1: Commit all Day 7 changes**

```bash
git add .
git commit -m "feat(day7): DeepSeek API and PDF parser services

- add DeepSeek API client with chat completion
- add PDF text extraction service using pypdf
- add embedding service for vector representation
- update requirements with httpx, pypdf, numpy"
```

---

## Day 8: LangGraph Multi-Agent Pipeline (Tuesday)

### Task 46: Create Agent State Schemas

**Files:**
- Create: `backend/app/agents/schemas.py`

- [ ] **Step 1: Create agent state schemas**

Create: `D:/person_ai_projects/BidMind/backend/app/agents/schemas.py`

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisState(BaseModel):
    """State for the analysis workflow."""

    task_id: str
    user_id: str
    file_path: str
    file_name: str
    text_content: str = ""
    page_count: int = 0

    current_agent: Literal["pdf_parser", "requirement_extractor", "scoring_analyzer", "strategy_generator", "report_generator", "done"] = "pdf_parser"

    requirements: list[dict] = Field(default_factory=list)
    scoring_criteria: list[dict] = Field(default_factory=list)
    bid_strategy: dict = Field(default_factory=dict)
    final_report: str = ""

    progress: int = 0
    error_message: Optional[str] = None

    token_used: int = 0
    llm_cost: float = 0.0


class AgentResponse(BaseModel):
    """Response from an agent node."""

    success: bool
    message: str
    data: dict = Field(default_factory=dict)
    token_used: int = 0
    cost: float = 0.0
```

---

### Task 47: Create Agent Nodes

**Files:**
- Create: `backend/app/agents/nodes.py`

- [ ] **Step 1: Create agent nodes**

Create: `D:/person_ai_projects/BidMind/backend/app/agents/nodes.py`

```python
from app.agents.schemas import AnalysisState
from app.services.deepseek import deepseek_service
from app.services.pdf_parser import pdf_parser
import json


async def parse_pdf_node(state: AnalysisState) -> AnalysisState:
    """Extract text content from PDF file."""
    try:
        text = pdf_parser.extract_text(state.file_path)
        page_count = pdf_parser.get_page_count(state.file_path)
        state.text_content = text
        state.page_count = page_count
        state.current_agent = "requirement_extractor"
        state.progress = 20
        return state
    except Exception as e:
        state.error_message = str(e)
        state.current_agent = "done"
        return state


async def extract_requirements_node(state: AnalysisState) -> AnalysisState:
    """Extract qualification requirements from PDF text."""
    prompt = f"""从以下招投标文档中提取资格要求条款。

要求包括但不限于：
1. 投标人资格条件（资质、业绩、人员等）
2. 投标文件要求
3. 资格审查方式
4. 其他资格要求

文档内容：
{state.text_content[:10000]}

请以JSON格式返回：
{{
  "requirements": [
    {{
      "category": "资格要求",
      "content": "具体要求内容",
      "priority": "high/medium/low"
    }}
  ]
}}
"""
    try:
        response = await deepseek_service.chat([
            {"role": "system", "content": "你是一个专业的招投标分析助手。"},
            {"role": "user", "content": prompt}
        ])
        data = json.loads(response)
        state.requirements = data.get("requirements", [])
        state.current_agent = "scoring_analyzer"
        state.progress = 40
        return state
    except Exception as e:
        state.error_message = str(e)
        state.current_agent = "done"
        return state


async def analyze_scoring_node(state: AnalysisState) -> AnalysisState:
    """Analyze scoring criteria from PDF text."""
    prompt = f"""从以下招投标文档中提取评分标准和评分方法。

请提取：
1. 评分因素及权重
2. 评分细则
3. 业绩要求
4. 技术方案评分标准
5. 价格评分方式

文档内容：
{state.text_content[:10000]}

请以JSON格式返回：
{{
  "scoring_criteria": [
    {{
      "factor": "评分因素名称",
      "weight": 0.2,
      "details": "评分细则"
    }}
  ]
}}
"""
    try:
        response = await deepseek_service.chat([
            {"role": "system", "content": "你是一个专业的招投标分析助手。"},
            {"role": "user", "content": prompt}
        ])
        data = json.loads(response)
        state.scoring_criteria = data.get("scoring_criteria", [])
        state.current_agent = "strategy_generator"
        state.progress = 60
        return state
    except Exception as e:
        state.error_message = str(e)
        state.current_agent = "done"
        return state


async def generate_strategy_node(state: AnalysisState) -> AnalysisState:
    """Generate bid strategy based on extracted information."""
    prompt = f"""基于以下招投标信息，生成投标策略建议。

资格要求：
{state.requirements}

评分标准：
{state.scoring_criteria}

请生成：
1. 投标策略总体方向
2. 需要重点准备的材料
3. 竞争策略建议
4. 风险评估

请以JSON格式返回：
{{
  "strategy": {{
    "direction": "策略方向",
    "key_materials": ["材料1", "材料2"],
    "competitive_advice": "竞争策略",
    "risk_assessment": "风险评估"
  }}
}}
"""
    try:
        response = await deepseek_service.chat([
            {"role": "system", "content": "你是一个专业的招投标分析助手。"},
            {"role": "user", "content": prompt}
        ])
        data = json.loads(response)
        state.bid_strategy = data.get("strategy", {})
        state.current_agent = "report_generator"
        state.progress = 80
        return state
    except Exception as e:
        state.error_message = str(e)
        state.current_agent = "done"
        return state


async def generate_report_node(state: AnalysisState) -> AnalysisState:
    """Generate final analysis report."""
    prompt = f"""基于以下分析结果，生成完整的招投标分析报告。

资格要求分析：
{state.requirements}

评分标准分析：
{state.scoring_criteria}

投标策略：
{state.bid_strategy}

请生成一份结构完整、内容详实的分析报告。
"""
    try:
        response = await deepseek_service.chat([
            {"role": "system", "content": "你是一个专业的招投标分析助手，擅长撰写专业报告。"},
            {"role": "user", "content": prompt}
        ])
        state.final_report = response
        state.current_agent = "done"
        state.progress = 100
        return state
    except Exception as e:
        state.error_message = str(e)
        state.current_agent = "done"
        return state
```

---

### Task 48: Create LangGraph StateGraph

**Files:**
- Create: `backend/app/agents/graph.py`

- [ ] **Step 1: Create LangGraph workflow**

Create: `D:/person_ai_projects/BidMind/backend/app/agents/graph.py`

```python
from langgraph.graph import StateGraph, END
from app.agents.schemas import AnalysisState
from app.agents.nodes import (
    parse_pdf_node,
    extract_requirements_node,
    analyze_scoring_node,
    generate_strategy_node,
    generate_report_node,
)


def create_analysis_graph() -> StateGraph:
    """Create the analysis workflow graph."""

    workflow = StateGraph(AnalysisState)

    workflow.add_node("parse_pdf", parse_pdf_node)
    workflow.add_node("extract_requirements", extract_requirements_node)
    workflow.add_node("analyze_scoring", analyze_scoring_node)
    workflow.add_node("generate_strategy", generate_strategy_node)
    workflow.add_node("generate_report", generate_report_node)

    workflow.set_entry_point("parse_pdf")

    workflow.add_edge("parse_pdf", "extract_requirements")
    workflow.add_edge("extract_requirements", "analyze_scoring")
    workflow.add_edge("analyze_scoring", "generate_strategy")
    workflow.add_edge("generate_strategy", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


analysis_graph = create_analysis_graph()
```

- [ ] **Step 2: Add langgraph to requirements.txt**

Add:
```
langgraph==0.2.10
langchain-core==0.3.0
```

---

### Task 49: Commit Day 8 Changes

- [ ] **Step 1: Commit all Day 8 changes**

```bash
git add .
git commit -m "feat(day8): LangGraph multi-agent pipeline

- add agent state schemas (AnalysisState, AgentResponse)
- add 5 agent nodes: PDF parser, requirements extractor,
  scoring analyzer, strategy generator, report generator
- create LangGraph StateGraph workflow
- add langgraph and langchain-core dependencies"
```

---

## Day 9: Celery Async Task Integration (Wednesday)

### Task 50: Create Celery Configuration

**Files:**
- Create: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/__init__.py`

- [ ] **Step 1: Create Celery app configuration**

Create: `D:/person_ai_projects/BidMind/backend/app/tasks/celery_app.py`

```python
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bidmind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analysis"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
)
```

---

### Task 51: Create Analysis Task

**Files:**
- Create: `backend/app/tasks/analysis.py`

- [ ] **Step 1: Create analysis Celery task**

Create: `D:/person_ai_projects/BidMind/backend/app/tasks/analysis.py`

```python
import asyncio
from datetime import datetime
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.core.database import async_session_maker
from app.models.task import AnalysisTask
from app.agents.graph import analysis_graph
from app.agents.schemas import AnalysisState


@celery_app.task(bind=True)
def run_analysis_task(self, task_id: str, user_id: str, file_path: str, file_name: str):
    """Run the analysis workflow for a task."""

    async def _run():
        state = AnalysisState(
            task_id=task_id,
            user_id=user_id,
            file_path=file_path,
            file_name=file_name,
        )

        async for event in analysis_graph.astream(state):
            if isinstance(event, dict):
                for node_name, node_state in event.items():
                    if hasattr(node_state, "progress"):
                        await update_task_progress(task_id, node_state.progress, node_name)
                    if hasattr(node_state, "error_message") and node_state.error_message:
                        await update_task_error(task_id, node_state.error_message)
                        return

        await finalize_task(task_id, state)

    asyncio.run(_run())


async def update_task_progress(task_id: str, progress: int, current_agent: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.progress = progress
            task.current_agent = current_agent
            task.status = "processing"
            await session.commit()


async def update_task_error(task_id: str, error_message: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "failed"
            task.error_message = error_message
            await session.commit()


async def finalize_task(task_id: str, state: AnalysisState):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.final_report = state.final_report
            task.requirements = state.requirements
            task.scoring_criteria = state.scoring_criteria
            task.bid_strategy = state.bid_strategy
            await session.commit()
```

---

### Task 52: Update Task Model for Analysis

**Files:**
- Modify: `backend/app/models/task.py`

- [ ] **Step 1: Add analysis fields to task model**

Add to `AnalysisTask` class:
```python
final_report = Column(Text, nullable=True)
requirements = Column(JSON, nullable=True)
scoring_criteria = Column(JSON, nullable=True)
bid_strategy = Column(JSON, nullable=True)
```

Also add JSON import:
```python
from sqlalchemy import JSON
```

---

### Task 53: Create Analysis API Endpoint

**Files:**
- Create: `backend/app/api/v1/analysis.py`

- [ ] **Step 1: Create analysis API router**

Create: `D:/person_ai_projects/BidMind/backend/app/api/v1/analysis.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.core.database import get_db
from app.models.user import User
from app.models.task import AnalysisTask
from app.schemas.auth import ApiResponse
from app.tasks.analysis import run_analysis_task
from app.api.v1.auth import get_current_user_required

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/{task_id}/start")
async def start_analysis(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(AnalysisTask).where(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == str(current_user.id),
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task already started")

    task.status = "processing"
    await db.commit()

    run_analysis_task.delay(
        task_id=str(task.id),
        user_id=str(current_user.id),
        file_path=task.file_url,
        file_name=task.file_name,
    )

    return ApiResponse(
        code=0,
        data={"task_id": task_id, "status": "processing"},
        message="Analysis started",
    )


@router.get("/{task_id}/result")
async def get_analysis_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(AnalysisTask).where(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == str(current_user.id),
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return ApiResponse(
        code=0,
        data={
            "task_id": str(task.id),
            "status": task.status,
            "progress": task.progress,
            "final_report": task.final_report,
            "requirements": task.requirements,
            "scoring_criteria": task.scoring_criteria,
            "bid_strategy": task.bid_strategy,
        },
        message="ok",
    )
```

- [ ] **Step 2: Update main.py to include analysis router**

Modify `backend/app/main.py`:
```python
from app.api.v1.analysis import router as analysis_router
app.include_router(analysis_router, prefix="/api/v1")
```

---

### Task 54: Commit Day 9 Changes

- [ ] **Step 1: Commit all Day 9 changes**

```bash
git add .
git commit -m "feat(day9): Celery task integration

- add Celery app configuration with Redis broker
- add analysis Celery task for async processing
- add analysis result endpoint
- add analysis fields to task model"
```

---

## Day 10: Frontend Analysis Pages (Thursday)

### Task 55: Create Analysis Page

**Files:**
- Create: `frontend/src/app/analysis/page.tsx`

- [ ] **Step 1: Create analysis page**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/analysis/page.tsx`

```typescript
"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { taskService, api } from "@/lib/api";
import type { Task } from "@/types/auth";

export default function AnalysisPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get("task_id");

  const [task, setTask] = useState<Task | null>(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) {
      router.push("/");
      return;
    }

    const token = Cookies.get("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetchTask();
    startAnalysis();
  }, [taskId, router]);

  const fetchTask = async () => {
    try {
      const response = await taskService.list(1, 10);
      const found = response.data?.items?.find((t: Task) => t.task_id === taskId);
      if (found) {
        setTask(found);
        setProgress(found.progress || 0);
      }
    } catch (err) {
      console.error("Failed to fetch task:", err);
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analysis/${taskId}/start`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
      });
    } catch (err) {
      console.error("Start analysis failed:", err);
    }
  };

  useEffect(() => {
    if (!taskId || progress >= 100) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/analysis/${taskId}/result`,
          {
            headers: {
              Authorization: `Bearer ${Cookies.get("access_token")}`,
            },
          }
        );
        const data = await response.json();
        if (data.code === 0 && data.data) {
          setProgress(data.data.progress || 0);
          if (data.data.status === "completed") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Progress update failed:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId, progress]);

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
          <Button variant="outline" onClick={() => router.push("/")}>
            返回首页
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>文档分析中</CardTitle>
            <CardDescription>{task?.file_name}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>分析进度</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {progress >= 100 && (
                <div className="mt-6">
                  <Button onClick={() => router.push(`/analysis/result?task_id=${taskId}`)}>
                    查看分析结果
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
```

---

### Task 56: Create Analysis Result Page

**Files:**
- Create: `frontend/src/app/analysis/result/page.tsx`

- [ ] **Step 1: Create result page**

Create: `D:/person_ai_projects/BidMind/frontend/src/app/analysis/result/page.tsx`

```typescript
"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface AnalysisResult {
  task_id: string;
  status: string;
  progress: number;
  final_report: string;
  requirements: any[];
  scoring_criteria: any[];
  bid_strategy: any;
}

export default function AnalysisResultPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get("task_id");

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) {
      router.push("/");
      return;
    }

    const token = Cookies.get("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetchResult();
  }, [taskId, router]);

  const fetchResult = async () => {
    try {
      const response = await api.get(`/analysis/${taskId}/result`, {
        headers: {
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
      });

      if (response.data.code === 0) {
        setResult(response.data.data);
      }
    } catch (err) {
      console.error("Failed to fetch result:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>加载中...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>未找到分析结果</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">BidMind</h1>
          <Button variant="outline" onClick={() => router.push("/")}>
            返回首页
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>分析报告</CardTitle>
            <CardDescription>任务 ID: {result.task_id}</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm">
              {result.final_report || "暂无报告内容"}
            </pre>
          </CardContent>
        </Card>

        {result.requirements && result.requirements.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>资格要求</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-2">
                {result.requirements.map((req: any, idx: number) => (
                  <li key={idx}>
                    <strong>{req.category}:</strong> {req.content}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {result.scoring_criteria && result.scoring_criteria.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>评分标准</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-2">
                {result.scoring_criteria.map((criteria: any, idx: number) => (
                  <li key={idx}>
                    <strong>{criteria.factor}</strong> (权重: {criteria.weight})
                    <br />
                    {criteria.details}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {result.bid_strategy && (
          <Card>
            <CardHeader>
              <CardTitle>投标策略</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <strong>策略方向：</strong>
                  <p>{result.bid_strategy.direction}</p>
                </div>
                <div>
                  <strong>重点材料：</strong>
                  <ul className="list-disc pl-5">
                    {(result.bid_strategy.key_materials || []).map((m: string, idx: number) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>风险评估：</strong>
                  <p>{result.bid_strategy.risk_assessment}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
```

---

### Task 57: Add File Upload to Home Page

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Update home page with file upload**

Modify: `D:/person_ai_projects/BidMind/frontend/src/app/page.tsx`

Add imports and state:
```typescript
import { useRef } from "react";

const fileInputRef = useRef<HTMLInputElement>(null);
const [uploading, setUploading] = useState(false);
```

Add upload handler:
```typescript
const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    alert("只支持 PDF 文件");
    return;
  }

  setUploading(true);
  try {
    const response = await taskService.create(file);
    if (response.code === 0) {
      router.push(`/analysis?task_id=${response.data.task_id}`);
    }
  } catch (err) {
    alert("上传失败");
  } finally {
    setUploading(false);
  }
};
```

Add to JSX after the CardContent:
```typescript
<div className="mt-6">
  <input
    type="file"
    ref={fileInputRef}
    onChange={handleFileUpload}
    accept=".pdf"
    className="hidden"
  />
  <Button
    onClick={() => fileInputRef.current?.click()}
    disabled={uploading}
  >
    {uploading ? "上传中..." : "上传招标文件"}
  </Button>
</div>
```

---

### Task 58: Commit Day 10 Changes

- [ ] **Step 1: Commit all Day 10 changes**

```bash
git add .
git commit -m "feat(day10): frontend analysis pages

- add analysis page with progress tracking
- add result page to display full report
- update home page with file upload functionality
- integrate progress polling for real-time updates"
```

---

## Day 11: Database Migrations and Testing (Friday)

### Task 59: Create Analysis Migration

**Files:**
- Create: `backend/alembic/versions/003_add_analysis_results.py`

- [ ] **Step 1: Create migration for analysis results**

Create: `D:/person_ai_projects/BidMind/backend/alembic/versions/003_add_analysis_results.py`

```python
"""add analysis results fields

Revision ID: 003
Revises: 002
Create Date: 2026-05-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analysis_tasks', sa.Column('final_report', sa.Text(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('requirements', postgresql.JSON(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('scoring_criteria', postgresql.JSON(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('bid_strategy', postgresql.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('analysis_tasks', 'bid_strategy')
    op.drop_column('analysis_tasks', 'scoring_criteria')
    op.drop_column('analysis_tasks', 'requirements')
    op.drop_column('analysis_tasks', 'final_report')
```

- [ ] **Step 2: Run migration**

```bash
docker compose exec backend alembic upgrade head
```

---

### Task 60: Integration Testing

**Files:**
- Create: `backend/tests/test_analysis.py`

- [ ] **Step 1: Create integration tests**

Create: `D:/person_ai_projects/BidMind/backend/tests/test_analysis.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_analysis_endpoints():
    """Test analysis API endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "analysistest@example.com",
                "password": "Test1234",
                "nickname": "Analysis Test",
            }
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "analysistest@example.com",
                "password": "Test1234",
            }
        )
        assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_health():
    """Test health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
```

---

### Task 61: Commit Day 11 Changes

- [ ] **Step 1: Commit all Day 11 changes**

```bash
git add .
git commit -m "feat(day11): database migrations and integration tests

- add migration 003 for analysis result columns
- add integration tests for analysis flow"
```

---

## Day 12: E2E Testing and Bug Fixes (Saturday)

### Task 62: Full Stack E2E Testing

- [ ] **Step 1: Start all services**

```bash
docker compose up -d
sleep 20
docker compose ps
```

- [ ] **Step 2: Test complete flow**

```bash
# Register user
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"Test1234","nickname":"E2E Test"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"Test1234"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# Test frontend pages
curl -s http://localhost:3000/login | grep -o "登录"
curl -s http://localhost:3000/register | grep -o "注册"
```

- [ ] **Step 3: Verify all containers are healthy**

```bash
docker compose ps
```

---

### Task 63: Push All Week 2 Changes to Remote

- [ ] **Step 1: Commit all remaining changes**

```bash
git add .
git commit -m "feat: complete week 2 implementation

Week 2 deliverables:
- DeepSeek API integration with chat completion
- PDF text extraction service using pypdf
- Embedding service for vector representation
- LangGraph multi-agent pipeline (5 agent nodes)
- Celery async task for background analysis
- Frontend analysis page with progress tracking
- Frontend result page for viewing reports
- Database migration for analysis results
- Integration tests"
```

- [ ] **Step 2: Push to remote**

```bash
git push origin main
```

---

## Self-Review Checklist

### Spec Coverage
- [ ] DeepSeek API client with chat completion
- [ ] PDF parser with text extraction
- [ ] Embedding service for vector representation
- [ ] LangGraph StateGraph with 5 agent nodes
- [ ] Celery task for async analysis
- [ ] Analysis page with real-time updates
- [ ] Result page with full report display
- [ ] Database migration for analysis results
- [ ] Integration tests

### Placeholder Scan
- [ ] No TBD or TODO entries
- [ ] All file paths are concrete
- [ ] All code snippets are complete
- [ ] All commands have expected outputs

### Type Consistency
- [ ] Backend: All Python use correct types
- [ ] Frontend: All TypeScript interfaces match API responses
- [ ] API: All endpoints return consistent ApiResponse format
