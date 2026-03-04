import json
import logging
from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, END
from src.utils.bedrock_client import invoke_llm
from src.utils.athena_client import get_table_schema, execute_query, validate_query
from src.utils.progress import notify

logger = logging.getLogger(__name__)
MAX_RETRIES = 5


class AthenaState(TypedDict):
    user_request: str
    sql: Optional[str]
    is_valid: Optional[bool]
    results: Optional[List[Dict]]
    execution_successful: Optional[bool]
    verification_passed: Optional[bool]
    insights: Optional[str]
    error_feedback: Optional[str]
    retry_count: Optional[int]


def generate_sql(state: AthenaState) -> AthenaState:
    notify(f"🔧 [Athena] SQL 생성 중... (시도 {state.get('retry_count', 0) + 1})")
    schema = get_table_schema()
    error_feedback = state.get("error_feedback", "")

    prompt = f"""당신은 Amazon Athena SQL 전문가입니다.
스키마 정보:
{schema}

중요: kpi 테이블의 log_date는 varchar 타입이며 '2025-04-18' ~ '2026-02-18' 범위입니다.
날짜 필터링 시 CURRENT_DATE 대신 실제 데이터 범위를 고려하세요.
예: 최근 7일 → log_date >= (SELECT MAX(log_date) FROM naidp.kpi) - interval '7' day 대신
    ORDER BY log_date DESC LIMIT 7 을 사용하세요.

사용자 요청: {state['user_request']}

{f'이전 오류: {error_feedback}' if error_feedback else ''}

Athena(Presto) SQL 문법으로 쿼리를 작성하세요. SQL만 반환하세요."""

    result = invoke_llm([{"role": "user", "content": prompt}])
    sql = result.strip().replace("```sql", "").replace("```", "").strip()

    return {**state, "sql": sql, "retry_count": state.get("retry_count", 0) + 1}


def validate_sql_node(state: AthenaState) -> AthenaState:
    notify("✅ [Athena] SQL 검증 중...")
    sql = state.get("sql")
    if not sql:
        return {**state, "is_valid": False, "error_feedback": "SQL이 생성되지 않았습니다."}

    is_valid, msg = validate_query(sql)
    if is_valid:
        return {**state, "is_valid": True}
    return {**state, "is_valid": False, "error_feedback": f"SQL 검증 실패: {msg}"}


def execute_sql_node(state: AthenaState) -> AthenaState:
    notify("🚀 [Athena] SQL 실행 중...")
    try:
        df = execute_query(state["sql"])
        results = df.to_dict(orient="records") if df is not None else []
        notify(f"📊 [Athena] {len(results)}행 반환")
        return {**state, "results": results, "execution_successful": True}
    except Exception as e:
        return {**state, "execution_successful": False, "error_feedback": f"실행 실패: {e}"}


def verify_results(state: AthenaState) -> AthenaState:
    notify("🔍 [Athena] 결과 검증 중...")
    if not state.get("results"):
        return {**state, "verification_passed": False, "error_feedback": "결과가 비어있습니다."}

    prompt = f"""SQL 결과가 사용자 요청을 충족하는지 판단하세요.
사용자 요청: {state['user_request']}
SQL: {state['sql']}
결과 (상위 5행): {json.dumps(state['results'][:5], default=str)}

VERIFIED 또는 NOT_VERIFIED로 시작하여 답하세요."""

    result = invoke_llm([{"role": "user", "content": prompt}])
    passed = result.strip().startswith("VERIFIED")

    if passed:
        return {**state, "verification_passed": True}
    return {**state, "verification_passed": False, "error_feedback": f"검증 실패: {result}"}


def generate_insights(state: AthenaState) -> AthenaState:
    notify("💡 [Athena] 인사이트 생성 중...")
    prompt = f"""데이터 분석 전문가로서 결과를 분석하고 인사이트를 제공하세요.
사용자 요청: {state['user_request']}
SQL: {state['sql']}
결과: {json.dumps(state['results'][:50], default=str)}

한국어로 핵심 인사이트, 트렌드, 권장사항을 제공하세요."""

    result = invoke_llm([{"role": "user", "content": prompt}])
    notify("✅ [Athena] 완료")
    return {**state, "insights": result}


def route_validation(state: AthenaState) -> str:
    if state.get("is_valid") or state.get("retry_count", 0) >= MAX_RETRIES:
        return "valid"
    return "invalid"


def route_execution(state: AthenaState) -> str:
    if state.get("execution_successful") or state.get("retry_count", 0) >= MAX_RETRIES:
        return "success"
    return "failure"


def route_verification(state: AthenaState) -> str:
    if state.get("verification_passed") or state.get("retry_count", 0) >= MAX_RETRIES:
        return "verified"
    return "not_verified"


def build_athena_graph():
    graph = StateGraph(AthenaState)

    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("verify_results", verify_results)
    graph.add_node("generate_insights", generate_insights)

    graph.set_entry_point("generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_conditional_edges("validate_sql", route_validation, {"valid": "execute_sql", "invalid": "generate_sql"})
    graph.add_conditional_edges("execute_sql", route_execution, {"success": "verify_results", "failure": "generate_sql"})
    graph.add_conditional_edges("verify_results", route_verification, {"verified": "generate_insights", "not_verified": "generate_sql"})
    graph.add_edge("generate_insights", END)

    return graph.compile()


def run_athena_query(user_request: str) -> dict:
    app = build_athena_graph()
    result = app.invoke({"user_request": user_request, "retry_count": 0}, {"recursion_limit": MAX_RETRIES * 4})
    return result
