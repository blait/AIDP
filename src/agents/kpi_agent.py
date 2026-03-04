import csv
from pathlib import Path
from src.agents import AgentState
from src.utils.bedrock_client import invoke_llm
from src.utils.progress import notify

KPI_DIR = "bedrock-sample/3.KPI"

SYSTEM_PROMPT = """당신은 게임 KPI 분석 전문가입니다.
제공된 KPI 데이터를 분석하여 반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 포함하지 마세요.

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


def load_kpi_data() -> str:
    lines = []
    for f in Path(KPI_DIR).glob("*.csv"):
        notify(f"📂 [KPI Agent] {f.name} 로드")
        with open(f, encoding="utf-8", errors="ignore") as fh:
            reader = csv.reader(fh)
            for row in reader:
                lines.append(",".join(row))
    return "\n".join(lines)


def kpi_agent(state: AgentState) -> AgentState:
    notify("🔍 [KPI Agent] CSV 데이터 로드 중...")
    kpi_data = load_kpi_data()

    notify("🤖 [KPI Agent] Claude 분석 중...")
    messages = [{"role": "user", "content": f"다음 KPI 데이터를 분석해주세요:\n\n{kpi_data}\n\n분석 요청: {state['query']}"}]
    result = invoke_llm(messages, system=SYSTEM_PROMPT)
    notify("✅ [KPI Agent] 완료")

    return {**state, "kpi_analysis": result}
