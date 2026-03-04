from src.agents import AgentState
from src.utils.bedrock_client import invoke_llm
from src.agents.athena_agent import run_athena_query
from src.utils.progress import notify
import json

SYSTEM_PROMPT = """당신은 게임 KPI 분석 전문가입니다.
제공된 KPI 데이터를 바탕으로 다음을 분석하여 반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 포함하지 마세요.

```json
{
  "period": "분석 기간",
  "highlights": [
    {
      "metric": "지표명",
      "finding": "발견 사항 1문장",
      "trend": "up|down|stable",
      "severity": "critical|high|medium|low"
    }
  ],
  "anomalies": [
    {
      "date": "날짜",
      "metric": "지표명",
      "description": "이상 징후 설명 1문장"
    }
  ],
  "risk_factors": ["위험요소1", "위험요소2", "위험요소3"],
  "summary": "전체 KPI 동향 3-4문장 요약",
  "recommendation": "핵심 권고사항 2-3문장"
}
```

highlights는 최대 5개, anomalies는 최대 3개로 제한하세요."""


def kpi_agent(state: AgentState) -> AgentState:
    notify("🔍 [KPI Agent] Athena Agent에게 KPI 데이터 요청 중...")

    athena_result = run_athena_query("kpi 테이블에서 전체 기간 일별 dau, nu, pu, pur, daily_sales, daily_arppu, daily_arpdau를 날짜순으로 조회해줘")

    kpi_data = json.dumps(athena_result.get("results", [])[:50], default=str) if athena_result.get("results") else "데이터 없음"
    notify(f"📊 [KPI Agent] {len(athena_result.get('results', []))}행 수신")

    notify("🤖 [KPI Agent] Claude 분석 중...")
    messages = [{"role": "user", "content": f"다음 KPI 데이터를 분석해주세요:\n\n{kpi_data}\n\n분석 요청: {state['query']}"}]
    result = invoke_llm(messages, system=SYSTEM_PROMPT)
    notify("✅ [KPI Agent] 완료")

    return {**state, "kpi_analysis": result}
