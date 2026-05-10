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
