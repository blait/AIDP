from src.agents import AgentState
from src.utils.bedrock_client import invoke_llm
from src.utils.progress import notify

SYSTEM_PROMPT = """당신은 게임 인사이트 리포트 작성 전문가입니다.
VOC 분석, KPI 분석, 콘텐츠 분석 결과를 종합하여 반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 포함하지 마세요.

```json
{
  "executive_summary": {
    "one_line": "한 줄 진단",
    "overall_risk": "critical|high|medium|low",
    "overall_score": 1~10 숫자,
    "key_findings": ["핵심 발견1", "핵심 발견2", "핵심 발견3"]
  },
  "scorecard": [
    {"area": "영역명", "score": 1~10, "status": "critical|warning|stable|good", "comment": "한 줄 코멘트"}
  ],
  "cross_insights": [
    {
      "title": "교차 인사이트 제목",
      "description": "VOC/KPI/콘텐츠를 연결한 인사이트 2-3문장",
      "impact": "high|medium|low",
      "related_areas": ["VOC", "KPI", "콘텐츠"] 
    }
  ],
  "action_items": [
    {
      "priority": 1,
      "action": "액션 아이템 설명",
      "owner": "담당 부서",
      "timeline": "기한",
      "expected_impact": "기대 효과 1문장"
    }
  ],
  "risk_scenarios": [
    {
      "scenario": "시나리오 설명",
      "probability": "high|medium|low",
      "impact": "high|medium|low",
      "mitigation": "대응 방안 1문장"
    }
  ]
}
```

scorecard는 5-6개 영역, cross_insights는 3-4개, action_items는 5개 이내, risk_scenarios는 3개 이내로 제한하세요."""


def report_agent(state: AgentState) -> AgentState:
    notify("🤖 [Report Agent] 종합 리포트 작성 중...")
    combined = f"""
## VOC 분석 결과
{state.get("voc_analysis", "데이터 없음")}

## KPI 분석 결과
{state.get("kpi_analysis", "데이터 없음")}

## 콘텐츠 분석 결과
{state.get("content_analysis", "데이터 없음")}
"""
    messages = [{"role": "user", "content": f"다음 분석 결과를 종합하여 인사이트 리포트를 작성해주세요:\n{combined}"}]
    result = invoke_llm(messages, system=SYSTEM_PROMPT)
    notify("✅ [Report Agent] 완료")

    return {**state, "final_report": result}
