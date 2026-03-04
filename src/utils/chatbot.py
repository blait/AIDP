import json
from src.utils.bedrock_client import invoke_llm
from src.rag.retriever import retrieve, format_context

SYSTEM_PROMPT = """당신은 게임 인사이트 분석 어시스턴트입니다.
사용자가 게임 분석 결과에 대해 추가 질문을 합니다.

아래 분석 결과를 참조하여 답변하세요:
{analysis_context}

추가로 RAG에서 검색된 관련 문서:
{rag_context}

규칙:
- 분석 결과에 있는 데이터를 우선 활용하세요
- 분석 결과에 없는 내용은 RAG 검색 결과를 참조하세요
- 둘 다 없으면 솔직히 "해당 데이터가 없습니다"라고 답하세요
- 한국어로 답변하세요
- 간결하고 실용적으로 답변하세요"""


def build_analysis_context(result: dict) -> str:
    parts = []
    for key, label in [("voc_analysis", "VOC 분석"), ("kpi_analysis", "KPI 분석"),
                        ("content_analysis", "콘텐츠 분석"), ("final_report", "종합 리포트")]:
        val = result.get(key, "")
        if val:
            parts.append(f"[{label}]\n{val[:3000]}")
    return "\n\n".join(parts)


def chat(question: str, history: list, analysis_result: dict) -> str:
    # 분석 결과 컨텍스트
    analysis_ctx = build_analysis_context(analysis_result) if analysis_result else "분석 결과 없음"

    # RAG 검색 (VOC + Content 양쪽에서 검색)
    voc_docs = retrieve(question, index_type="voc", top_k=2)
    content_docs = retrieve(question, index_type="content", top_k=2)
    rag_ctx = format_context(voc_docs + content_docs) if (voc_docs or content_docs) else "관련 문서 없음"

    system = SYSTEM_PROMPT.format(analysis_context=analysis_ctx, rag_context=rag_ctx)

    # 대화 히스토리 + 현재 질문
    messages = []
    for msg in history[-6:]:  # 최근 3턴만
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    return invoke_llm(messages, system=system)
