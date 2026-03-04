from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    query: str
    voc_analysis: str
    kpi_analysis: str
    content_analysis: str
    final_report: str
    messages: Annotated[list, operator.add]
