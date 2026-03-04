from langgraph.graph import StateGraph, END
from src.agents import AgentState
from src.agents.voc_agent import voc_agent
from src.agents.kpi_agent import kpi_agent
from src.agents.content_agent import content_agent
from src.agents.report_agent import report_agent


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("voc_agent", voc_agent)
    graph.add_node("kpi_agent", kpi_agent)
    graph.add_node("content_agent", content_agent)
    graph.add_node("report_agent", report_agent)

    graph.set_entry_point("voc_agent")
    graph.add_edge("voc_agent", "kpi_agent")
    graph.add_edge("kpi_agent", "content_agent")
    graph.add_edge("content_agent", "report_agent")
    graph.add_edge("report_agent", END)

    return graph.compile()


def run_analysis(query: str) -> dict:
    app = build_graph()
    initial_state = AgentState(
        query=query,
        voc_analysis="",
        kpi_analysis="",
        content_analysis="",
        final_report="",
        messages=[],
    )
    return app.invoke(initial_state)
