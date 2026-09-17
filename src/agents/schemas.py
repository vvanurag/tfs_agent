from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field

class SprintReportSchema(BaseModel):
    """
    Strict data contract for the final sprint status synthesis report.
    Enforced by the Validation Agent and Self-Healing Loop.
    """
    sprint_id: str = Field(description="Name of current sprint, e.g., 'Sprint 12'")
    overall_status: str = Field(description="'On Track', 'At Risk', or 'Blocked'")
    active_bugs_count: int = Field(description="Total number of active bugs")
    critical_blockers: List[str] = Field(description="Key blocker titles and ticket IDs")
    architecture_remediations: List[str] = Field(description="Grounded remediation plans from RAG architecture specs")
    sla_risk_summary: str = Field(description="Executive summary of SLA compliance and operational risk")


class AgentState(TypedDict):
    """
    Tracks state throughout the multi-agent workflow.
    """
    messages: List[str]
    user_clearance: int
    tfs_items: List[dict]
    rag_context: str
    report_draft: str
    validation_errors: Optional[str]
    retry_count: int
    final_report: Optional[dict]
