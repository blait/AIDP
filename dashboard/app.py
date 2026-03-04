import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import re
import streamlit as st
import pandas as pd
from pathlib import Path

from src.agents.supervisor import run_analysis
from src.utils.progress import set_progress_callback
from src.utils.chatbot import chat

st.set_page_config(page_title="NAIDP - 게임 인사이트 분석", layout="wide")
st.title("🎮 NAIDP - 게임 인사이트 분석 플랫폼")


def parse_json(text: str) -> dict | None:
    try:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(text)
    except:
        return None


@st.cache_data
def load_kpi():
    kpi_dir = Path("bedrock-sample/3.KPI")
    dfs = [pd.read_csv(f, parse_dates=["log_date"]) for f in kpi_dir.glob("*.csv")]
    df = pd.concat(dfs).sort_values("log_date").reset_index(drop=True)
    df["daily_sales_억"] = df["daily_sales"] / 1e8
    df["weekly_avg_dau"] = df["dau"].rolling(7).mean()
    df["weekly_avg_sales"] = df["daily_sales_억"].rolling(7).mean()
    return df


df_kpi = load_kpi()

SEVERITY_COLORS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
TREND_ICONS = {"up": "📈", "down": "📉", "stable": "➡️"}
STATUS_ICONS = {"positive": "✅", "neutral": "➖", "negative": "❌"}
STATUS_COLORS = {"critical": "🔴", "warning": "🟠", "stable": "🟡", "good": "🟢"}
PROB_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}

DEFAULT_QUERY = "DK모바일 리본 게임의 주요 VOC 이슈와 KPI 현황을 종합 분석해줘"

# 세션 초기화
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("🔍 AI 분석")
    if st.button("🚀 분석 시작", type="primary", use_container_width=True):
        status = st.status("분석 진행 중...", expanded=True)
        logs = []
        placeholder = status.empty()

        def on_progress(msg):
            logs.append(msg)
            placeholder.markdown("\n\n".join(logs))

        set_progress_callback(on_progress)
        result = run_analysis(DEFAULT_QUERY)
        status.update(label="✅ 분석 완료!", state="complete")
        st.session_state["result"] = result

    if "result" in st.session_state:
        st.success("분석 완료! 각 탭에서 확인하세요.")


# ============================================================
# 메인 탭
from src.agents.athena_agent import run_athena_query

# ============================================================
tab_kpi, tab_voc, tab_content, tab_report, tab_athena = st.tabs(
    ["📊 KPI 대시보드", "📢 VOC 분석", "📝 콘텐츠 분석", "📋 종합 리포트", "🔍 Athena 분석"]
)

# TAB 1: KPI
with tab_kpi:
    st.subheader("핵심 지표 현황")
    recent = df_kpi.tail(7)
    prev = df_kpi.iloc[-14:-7]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v, p = int(recent["dau"].mean()), int(prev["dau"].mean())
        st.metric("평균 DAU", f"{v:,}", delta=f"{v-p:,}")
    with col2:
        v, p = recent["daily_sales_억"].mean(), prev["daily_sales_억"].mean()
        st.metric("일 평균 매출", f"{v:.1f}억", delta=f"{v-p:.1f}억")
    with col3:
        v, p = int(recent["pu"].mean()), int(prev["pu"].mean())
        st.metric("평균 PU", f"{v:,}", delta=f"{v-p:,}")
    with col4:
        v, p = int(recent["daily_arppu"].mean()), int(prev["daily_arppu"].mean())
        st.metric("평균 ARPPU", f"{v:,}원", delta=f"{v-p:,}원")

    st.divider()
    st.subheader("📈 DAU 트렌드")
    st.line_chart(
        df_kpi.set_index("log_date")[["dau", "weekly_avg_dau"]].rename(
            columns={"dau": "일별 DAU", "weekly_avg_dau": "7일 이동평균"}
        ), height=350
    )
    st.subheader("💰 매출 트렌드 (억원)")
    st.line_chart(
        df_kpi.set_index("log_date")[["daily_sales_억", "weekly_avg_sales"]].rename(
            columns={"daily_sales_억": "일별 매출", "weekly_avg_sales": "7일 이동평균"}
        ), height=350
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("👤 PU & 신규유저")
        st.line_chart(
            df_kpi.set_index("log_date")[["pu", "nu"]].rename(
                columns={"pu": "결제유저(PU)", "nu": "신규유저(NU)"}
            ), height=300
        )
    with col_b:
        st.subheader("💎 ARPPU & ARPDAU")
        st.line_chart(
            df_kpi.set_index("log_date")[["daily_arppu", "daily_arpdau"]].rename(
                columns={"daily_arppu": "ARPPU", "daily_arpdau": "ARPDAU"}
            ), height=300
        )
    with st.expander("📄 원본 데이터"):
        st.dataframe(df_kpi, use_container_width=True)

# TAB 2: VOC
with tab_voc:
    if "result" not in st.session_state:
        st.info("👈 사이드바에서 분석을 먼저 실행해주세요.")
    else:
        voc_data = parse_json(st.session_state["result"].get("voc_analysis", ""))
        if voc_data:
            risk = voc_data.get("risk_level", "medium")
            st.markdown(f"### 전체 위험도: {SEVERITY_COLORS.get(risk, '⚪')} {risk.upper()}")

            st.subheader("😊 감정 분포")
            sentiment = voc_data.get("sentiment", {})
            if sentiment:
                col1, col2 = st.columns([1, 2])
                with col1:
                    for label, val in sentiment.items():
                        emoji = {"긍정": "😊", "중립": "😐", "부정": "😠"}.get(label, "")
                        st.metric(f"{emoji} {label}", f"{val}%")
                with col2:
                    sent_df = pd.DataFrame([sentiment]).T.rename(columns={0: "비율(%)"})
                    st.bar_chart(sent_df, height=250)

            st.divider()
            st.subheader("🔥 핵심 이슈 TOP 5")
            for issue in voc_data.get("top_issues", []):
                sev = issue.get("severity", "medium")
                icon = SEVERITY_COLORS.get(sev, "⚪")
                with st.container(border=True):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        st.markdown(f"#### {icon} {issue.get('title', '')}")
                    with col2:
                        st.caption(f"카테고리: **{issue.get('category', '')}**")
                    with col3:
                        views = issue.get("views", 0)
                        if views:
                            st.caption(f"조회수: **{views:,}**")
                    st.write(issue.get("description", ""))
                    st.info(f"💬 유저 반응: {issue.get('user_reaction', '')}")

            st.divider()
            keywords = voc_data.get("key_keywords", [])
            if keywords:
                st.subheader("🏷️ 핵심 키워드")
                st.markdown(" ".join([f"`{kw}`" for kw in keywords]))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📝 요약")
                st.write(voc_data.get("summary", ""))
            with col2:
                st.subheader("💡 권고사항")
                st.write(voc_data.get("recommendation", ""))
        else:
            st.markdown(st.session_state["result"].get("voc_analysis", ""))

# TAB 3: 콘텐츠
with tab_content:
    if "result" not in st.session_state:
        st.info("👈 사이드바에서 분석을 먼저 실행해주세요.")
    else:
        content_data = parse_json(st.session_state["result"].get("content_analysis", ""))
        if content_data:
            health = content_data.get("content_health", {})
            if health:
                st.subheader("🏥 콘텐츠 건강도")
                col1, col2, col3 = st.columns(3)
                with col1:
                    score = health.get("quality_score", 0)
                    st.metric("품질 점수", f"{score}/10")
                    st.progress(score / 10)
                with col2:
                    st.metric("업데이트 빈도", health.get("update_frequency", ""))
                with col3:
                    st.metric("유저 만족도", health.get("user_satisfaction", ""))

            st.divider()
            updates = content_data.get("updates", [])
            if updates:
                st.subheader("📦 업데이트 현황")
                for u in updates:
                    status_icon = STATUS_ICONS.get(u.get("status", ""), "")
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{status_icon} {u.get('title', '')}**")
                            st.write(u.get("description", ""))
                        with col2:
                            st.caption(f"카테고리: **{u.get('category', '')}**")
                        if u.get("user_feedback"):
                            st.info(f"💬 {u['user_feedback']}")

            st.divider()
            gaps = content_data.get("gap_analysis", [])
            if gaps:
                st.subheader("⚖️ 기획 의도 vs 실제 반응")
                gap_rows = []
                for g in gaps:
                    gap_rows.append({
                        "영역": g.get("area", ""),
                        "기획 의도": g.get("planned", ""),
                        "실제 반응": g.get("actual", ""),
                        "괴리도": SEVERITY_COLORS.get(g.get("gap_level", ""), "") + " " + g.get("gap_level", "").upper()
                    })
                st.dataframe(pd.DataFrame(gap_rows), use_container_width=True, hide_index=True)

            recs = content_data.get("recommendations", [])
            if recs:
                st.subheader("💡 권고사항")
                for i, r in enumerate(recs, 1):
                    st.markdown(f"**{i}.** {r}")

            st.divider()
            st.subheader("📝 요약")
            st.write(content_data.get("summary", ""))
        else:
            st.markdown(st.session_state["result"].get("content_analysis", ""))

# TAB 4: 종합 리포트
with tab_report:
    if "result" not in st.session_state:
        st.info("👈 사이드바에서 분석을 먼저 실행해주세요.")
    else:
        report_data = parse_json(st.session_state["result"].get("final_report", ""))
        if report_data:
            exec_sum = report_data.get("executive_summary", {})
            if exec_sum:
                risk = exec_sum.get("overall_risk", "medium")
                score = exec_sum.get("overall_score", 0)
                st.subheader("🎯 Executive Summary")
                st.markdown(f"### {SEVERITY_COLORS.get(risk, '')} {exec_sum.get('one_line', '')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("종합 위험도", risk.upper())
                with col2:
                    st.metric("종합 점수", f"{score}/10")
                    st.progress(score / 10)
                findings = exec_sum.get("key_findings", [])
                if findings:
                    st.markdown("**🔑 핵심 발견:**")
                    for f in findings:
                        st.markdown(f"- {f}")

            st.divider()
            scorecard = report_data.get("scorecard", [])
            if scorecard:
                st.subheader("📊 영역별 스코어카드")
                cols = st.columns(min(len(scorecard), 6))
                for i, item in enumerate(scorecard):
                    with cols[i % len(cols)]:
                        status = item.get("status", "stable")
                        sc = item.get("score", 0)
                        with st.container(border=True):
                            st.markdown(f"**{item.get('area', '')}**")
                            st.markdown(f"### {STATUS_COLORS.get(status, '')} {sc}/10")
                            st.progress(sc / 10)
                            st.caption(item.get("comment", ""))

            st.divider()
            cross = report_data.get("cross_insights", [])
            if cross:
                st.subheader("🔗 교차 인사이트")
                for c in cross:
                    impact = c.get("impact", "medium")
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{c.get('title', '')}**")
                            st.write(c.get("description", ""))
                            areas = c.get("related_areas", [])
                            if areas:
                                st.markdown(" ".join([f"`{a}`" for a in areas]))
                        with col2:
                            st.markdown(f"{SEVERITY_COLORS.get(impact, '')} **{impact.upper()}**")

            st.divider()
            actions = report_data.get("action_items", [])
            if actions:
                st.subheader("✅ 액션 아이템")
                action_rows = []
                for a in actions:
                    action_rows.append({
                        "우선순위": f"#{a.get('priority', '')}",
                        "액션": a.get("action", ""),
                        "담당": a.get("owner", ""),
                        "기한": a.get("timeline", ""),
                        "기대 효과": a.get("expected_impact", ""),
                    })
                st.dataframe(pd.DataFrame(action_rows), use_container_width=True, hide_index=True)

            st.divider()
            risks = report_data.get("risk_scenarios", [])
            if risks:
                st.subheader("⚠️ 리스크 시나리오")
                for r in risks:
                    prob = PROB_ICONS.get(r.get("probability", ""), "")
                    imp = PROB_ICONS.get(r.get("impact", ""), "")
                    with st.container(border=True):
                        st.markdown(f"**{r.get('scenario', '')}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"발생 확률: {prob} {r.get('probability', '').upper()}")
                        with col2:
                            st.markdown(f"영향도: {imp} {r.get('impact', '').upper()}")
                        with col3:
                            st.markdown(f"💡 {r.get('mitigation', '')}")

            st.divider()
            st.download_button(
                "📥 리포트 다운로드 (JSON)",
                data=json.dumps(report_data, ensure_ascii=False, indent=2),
                file_name="insight_report.json",
                mime="application/json",
            )
        else:
            st.markdown(st.session_state["result"].get("final_report", ""))
# ============================================================
# TAB 5: Athena 분석
# ============================================================
with tab_athena:
    st.subheader("🔍 Athena Text-to-SQL 분석")
    st.caption("자연어로 질문하면 SQL을 자동 생성하여 Athena에서 실행합니다.")

    athena_query = st.text_input("질문을 입력하세요", placeholder="예: 최근 30일 DAU 트렌드를 보여줘", key="athena_input")

    if st.button("🚀 쿼리 실행", key="athena_btn") and athena_query:
        status = st.status("Athena 분석 진행 중...", expanded=True)
        logs = []
        placeholder = status.empty()

        def on_athena_progress(msg):
            logs.append(msg)
            placeholder.markdown("\n\n".join(logs))

        set_progress_callback(on_athena_progress)

        result = run_athena_query(athena_query)
        status.update(label="✅ 완료!", state="complete")
        st.session_state["athena_result"] = result

    if "athena_result" in st.session_state:
        r = st.session_state["athena_result"]

        # SQL 표시
        if r.get("sql"):
            with st.expander("📝 생성된 SQL", expanded=False):
                st.code(r["sql"], language="sql")

        # 결과 테이블
        if r.get("results"):
            st.subheader("📊 쿼리 결과")
            result_df = pd.DataFrame(r["results"])

            # 숫자 컬럼 변환
            for col in result_df.columns:
                try:
                    result_df[col] = pd.to_numeric(result_df[col])
                except (ValueError, TypeError):
                    pass

            st.dataframe(result_df, use_container_width=True, hide_index=True)

            # 자동 차트: 날짜 컬럼 + 숫자 컬럼이 있으면 라인 차트
            date_cols = [c for c in result_df.columns if "date" in c.lower()]
            num_cols = result_df.select_dtypes(include="number").columns.tolist()
            if date_cols and num_cols:
                st.subheader("📈 차트")
                chart_df = result_df.set_index(date_cols[0])[num_cols]
                st.line_chart(chart_df)

        # 인사이트
        if r.get("insights"):
            st.subheader("💡 인사이트")
            st.markdown(r["insights"])

# ============================================================
# 하단 고정 챗봇
# ============================================================
st.markdown("""
<style>
.chat-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--background-color, #0e1117);
    border-top: 2px solid #333;
    z-index: 999;
    padding: 0.5rem 1rem;
}
.main .block-container { padding-bottom: 200px; }
</style>
""", unsafe_allow_html=True)

st.divider()
chat_col1, chat_col2 = st.columns([1, 20])
with chat_col1:
    st.markdown("💬")
with chat_col2:
    st.markdown("**추가 질문** — 분석 결과와 RAG 문서를 참조하여 답변합니다")

# 최근 대화 표시 (최근 3턴만)
if st.session_state["chat_history"]:
    with st.container(height=250):
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if st.button("🗑️ 대화 초기화", key="clear_chat"):
        st.session_state["chat_history"] = []
        st.rerun()

if "result" in st.session_state:
    if user_input := st.chat_input("분석 결과에 대해 질문하세요"):
        st.session_state["chat_history"].append({"role": "user", "content": user_input})

        with st.spinner("답변 생성 중..."):
            response = chat(
                user_input,
                st.session_state["chat_history"],
                st.session_state["result"],
            )
        st.session_state["chat_history"].append({"role": "assistant", "content": response})
        st.rerun()
else:
    st.chat_input("분석을 먼저 실행해주세요", disabled=True)
