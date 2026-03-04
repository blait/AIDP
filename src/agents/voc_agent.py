from src.agents import AgentState
from src.rag.retriever import retrieve, format_context
from src.utils.bedrock_client import invoke_llm
from src.utils.progress import notify

SYSTEM_PROMPT = """당신은 게임 VOC(고객의 소리) 분석 전문가입니다.
제공된 VOC 문서를 분석하여 반드시 아래 JSON 형식으로만 응답하세요. JSON 외의 텍스트는 포함하지 마세요.

```json
{
  "sentiment": {"긍정": 숫자, "중립": 숫자, "부정": 숫자},
  "top_issues": [
    {
      "title": "이슈 제목",
      "severity": "critical|high|medium|low",
      "category": "운영|콘텐츠|기술|경제|세력",
      "description": "2-3문장 설명",
      "user_reaction": "유저 반응 요약",
      "views": 대표 조회수(숫자)
    }
  ],
  "key_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "summary": "전체 VOC 동향 3-4문장 요약",
  "risk_level": "critical|high|medium|low",
  "recommendation": "핵심 권고사항 2-3문장"
}
```

top_issues는 최대 5개, severity 기준 내림차순으로 정렬하세요."""


def voc_agent(state: AgentState) -> AgentState:
    notify("🔍 [VOC Agent] 문서 검색 중...")
    query = state["query"]
    docs = retrieve(f"VOC 고객 불만 피드백 {query}", top_k=5)
    context = format_context(docs)

    notify("🤖 [VOC Agent] Claude 분석 중...")
    messages = [{"role": "user", "content": f"다음 VOC 데이터를 분석해주세요:\n\n{context}\n\n분석 요청: {query}"}]
    result = invoke_llm(messages, system=SYSTEM_PROMPT)
    notify("✅ [VOC Agent] 완료")

    return {**state, "voc_analysis": result}
