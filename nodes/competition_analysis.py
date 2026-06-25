"""
深度竞争分析节点

基于 CompeteAI 理论框架，使用 LLM 进行深度竞争态势分析
"""

import json
from typing import Any, List, Optional
from .state import AgentState


class CompetitionAnalyzer:
    """
    竞争分析器
    
    基于 CompeteAI (ICML 2024) 理论框架，分析竞争态势
    """
    
    def __init__(self, llm: Any):
        self.llm = llm
    
    async def analyze_competition_dynamics(
        self,
        store_name: str,
        store_type: str,
        store_address: str,
        competitors: List[Any],
        business_env: Any
    ) -> dict:
        """
        分析竞争动态
        
        Args:
            store_name: 店铺名称
            store_type: 店铺类型
            store_address: 店铺地址
            competitors: 竞争对手列表
            business_env: 商业环境信息
            
        Returns:
            dict: 结构化的竞争分析结果
        """
        # 格式化竞争对手信息
        competitors_text = self._format_competitors(competitors)
        
        # 格式化商业环境信息
        env_text = self._format_business_env(business_env)
        
        # 构建分析 prompt
        prompt = f"""你是一位专业的商业分析师，请基于以下信息对店铺进行深度竞争分析。

## 店铺信息
- 名称: {store_name}
- 类型: {store_type}
- 地址: {store_address}

## 竞争对手信息
{competitors_text}

## 商业环境
{env_text}

请按照以下 JSON 格式输出分析结果（仅输出 JSON，不要其他内容）：

{{
    "competition_intensity": {{
        "level": "高/中/低",
        "score": 1-10,
        "description": "竞争强度说明"
    }},
    "market_position": {{
        "recommended": "建议的市场定位",
        "differentiation": "差异化方向",
        "target_segment": "目标客群"
    }},
    "competitive_advantages": [
        "优势1",
        "优势2"
    ],
    "competitive_threats": [
        {{
            "threat": "威胁描述",
            "source": "威胁来源",
            "severity": "高/中/低"
        }}
    ],
    "differentiation_opportunities": [
        {{
            "opportunity": "机会描述",
            "implementation": "实施建议"
        }}
    ],
    "pricing_strategy": {{
        "current_assessment": "当前定价评估",
        "recommendation": "定价建议"
    }},
    "scenario_analysis": {{
        "optimistic": "乐观情景预测",
        "baseline": "基准情景预测",
        "pessimistic": "悲观情景预测"
    }},
    "future_prediction": {{
        "short_term": "短期预测（1-3个月）",
        "medium_term": "中期预测（3-6个月）",
        "long_term": "长期预测（6-12个月）"
    }},
    "action_plan": [
        {{
            "priority": 1,
            "action": "行动描述",
            "timeline": "时间框架",
            "expected_roi": "预期回报"
        }}
    ]
}}"""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 尝试解析 JSON
            # 处理可能的 markdown 代码块包装
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败: {e}")
            return self._get_default_analysis()
        except Exception as e:
            print(f"⚠️ LLM 调用失败: {e}")
            return self._get_default_analysis()
    
    def _format_competitors(self, competitors: List[Any]) -> str:
        """格式化竞争对手信息"""
        if not competitors:
            return "暂无竞争对手数据"
        
        lines = []
        for i, comp in enumerate(competitors[:10], 1):
            if hasattr(comp, 'name'):
                # dataclass 对象
                name = comp.name
                distance = comp.distance
                rating = comp.rating or "无评分"
            elif isinstance(comp, dict):
                name = comp.get('name', '未知')
                distance = comp.get('distance', '?')
                rating = comp.get('rating', '无评分')
            else:
                continue
            lines.append(f"{i}. {name} - 距离{distance}米 - 评分{rating}")
        
        return "\n".join(lines) if lines else "暂无竞争对手数据"
    
    def _format_business_env(self, business_env: Any) -> str:
        """格式化商业环境信息"""
        if not business_env:
            return "暂无商业环境数据"
        
        # 处理 POIAnalysis dataclass
        if hasattr(business_env, 'poi_counts'):
            poi_counts = business_env.poi_counts
            poi_summary = business_env.poi_summary
            lines = [f"- {k}: {v}个" for k, v in poi_counts.items()]
            lines.append(f"\n总结: {poi_summary}")
            return "\n".join(lines)
        
        # 处理字典
        if isinstance(business_env, dict):
            poi_counts = business_env.get('poi_counts', {})
            if poi_counts:
                lines = [f"- {k}: {v}个" for k, v in poi_counts.items()]
                return "\n".join(lines)
            return str(business_env)
        
        return str(business_env)
    
    def _get_default_analysis(self) -> dict:
        """返回默认分析结果"""
        return {
            "competition_intensity": {
                "level": "中",
                "score": 5,
                "description": "竞争态势分析数据不足"
            },
            "market_position": {
                "recommended": "待定",
                "differentiation": "需要更多数据分析",
                "target_segment": "待定"
            },
            "competitive_advantages": [],
            "competitive_threats": [],
            "differentiation_opportunities": [],
            "pricing_strategy": {
                "current_assessment": "待分析",
                "recommendation": "建议收集更多市场数据"
            },
            "scenario_analysis": {
                "optimistic": "待分析",
                "baseline": "待分析",
                "pessimistic": "待分析"
            },
            "future_prediction": {
                "short_term": "待分析",
                "medium_term": "待分析",
                "long_term": "待分析"
            },
            "action_plan": []
        }


async def competition_analysis_node(state: AgentState, llm: Any = None) -> dict:
    """
    深度竞争分析节点
    
    使用 CompetitionAnalyzer 进行深度分析
    
    Args:
        state: 当前状态
        llm: LLM 实例
        
    Returns:
        dict: 包含深度分析结果的状态更新
    """
    print(f"🔬 正在进行深度竞争分析...")
    
    errors = list(state.get("errors", []))
    
    if not llm:
        errors.append("深度分析需要 LLM 支持")
        return {"competition_analysis": None, "errors": errors}
    
    try:
        analyzer = CompetitionAnalyzer(llm)
        
        analysis_result = await analyzer.analyze_competition_dynamics(
            store_name=state.get("store_name", ""),
            store_type=state.get("store_type", "餐厅"),
            store_address=state.get("store_address", ""),
            competitors=state.get("competitors", []),
            business_env=state.get("poi_analysis")
        )
        
        print(f"✓ 深度竞争分析完成")
        
        return {
            "competition_analysis": analysis_result,
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"深度分析异常: {str(e)}")
        print(f"❌ 深度竞争分析失败: {e}")
        return {"competition_analysis": None, "errors": errors}
