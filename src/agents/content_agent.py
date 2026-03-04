from src.agents import AgentState
from src.rag.retriever import retrieve, format_context
from src.utils.bedrock_client import invoke_llm
from src.utils.progress import notify

SYSTEM_PROMPT = """당신은 게임 콘텐츠 기획 분석 전문가입니다.
제공된 기획서와 업데이트 내역을 분석하여 반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 포함하지 마세요.

```json
{
  "updates": [
    {
      "title": "업데이트 항목명",
      "category": "콘텐츠|밸런스|버그수정|이벤트|시스템",
      "status": "positive|neutral|negative",
      "description": "1-2문장 설명",
      "user_feedback": "유저 반응 요약 1문장"
    }
  ],
  "content_health": {
    "quality_score": 1~10 숫자,
    "update_frequency": "적절|부족|과다",
    "user_satisfaction": "높음|보통|낮음"
  },
  "gap_analysis": [
    {
      "area": "영역명",
      "planned": "기획 의도",
      "actual": "실제 유저 반응",
      "gap_level": "high|medium|low"
    }
  ],
  "recommendations": ["권고사항1", "권고사항2", "권고사항3"],
  "summary": "전체 콘텐츠 현황 3-4문장 요약"
}
```

updates는 최대 5개, gap_analysis는 최대 3개로 제한하세요."""


def content_agent(state: AgentState) -> AgentState:
    notify("🔍 [Content Agent] 문서 검색 중...")
    query = state["query"]
    docs = retrieve(f"콘텐츠 기획서 업데이트 패치노트 {query}", top_k=5)
    context = format_context(docs)

    notify("🤖 [Content Agent] Claude 분석 중...")
    messages = [{"role": "user", "content": f"다음 기획서 및 업데이트 내역을 분석해주세요:\n\n{context}\n\n분석 요청: {query}"}]
    result = invoke_llm(messages, system=SYSTEM_PROMPT)
    notify("✅ [Content Agent] 완료")

    return {**state, "content_analysis": result}
