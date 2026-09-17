import re
import html
import requests
from pydantic import BaseModel, Field
from typing import List, Optional

class WorkItemSummary(BaseModel):
    """
    Clean, normalized Pydantic model for LLM ingestion.
    Discards bloated internal GUIDs, URLs, and system revisions.
    """
    id: int
    title: str
    work_item_type: str = Field(alias="type")
    state: str
    assigned_to: str
    priority: int = 2
    severity: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str

    model_config = {
        "populate_by_name": True
    }

    @classmethod
    def clean_html(cls, raw_html: str) -> str:
        """Strips HTML tags and unescapes entities for clean LLM text."""
        if not raw_html:
            return ""
        text = re.sub(r'<(br|p|div)[^>]*>', ' ', raw_html, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()


class LocalTFSClient:
    """
    Two-Stage Client connecting to TFS / Azure DevOps REST API endpoints.
    Stage 1: Lightweight WIQL POST query to fetch matching IDs.
    Stage 2: Batch GET lookup with Pydantic payload pruning.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def stage_1_execute_wiql(self, query: str) -> List[int]:
        url = f"{self.base_url}/_apis/wit/wiql"
        response = requests.post(url, json={"query": query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [item["id"] for item in data.get("workItems", [])]

    def stage_2_fetch_details(self, ids: List[int]) -> List[WorkItemSummary]:
        if not ids:
            return []

        ids_str = ",".join(str(i) for i in ids)
        url = f"{self.base_url}/_apis/wit/workitems?ids={ids_str}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        raw_payload = response.json()
        clean_items = []
        
        for item in raw_payload.get("value", []):
            fields = item.get("fields", {})
            assigned_to_obj = fields.get("System.AssignedTo", {})
            
            assignee_name = (
                assigned_to_obj.get("displayName", "Unassigned")
                if isinstance(assigned_to_obj, dict)
                else str(assigned_to_obj) if assigned_to_obj else "Unassigned"
            )

            raw_desc = fields.get("System.Description", "")
            cleaned_desc = WorkItemSummary.clean_html(raw_desc)

            raw_tags = fields.get("System.Tags", "")
            tags_list = [t.strip() for t in raw_tags.split(";") if t.strip()] if raw_tags else []

            summary = WorkItemSummary(
                id=item.get("id"),
                title=fields.get("System.Title", "No Title"),
                type=fields.get("System.WorkItemType", "Unknown"),
                state=fields.get("System.State", "Unknown"),
                assigned_to=assignee_name,
                priority=fields.get("Microsoft.VSTS.Common.Priority", 2),
                severity=fields.get("Microsoft.VSTS.Common.Severity"),
                iteration_path=fields.get("System.IterationPath"),
                tags=tags_list,
                description=cleaned_desc
            )
            clean_items.append(summary)
            
        return clean_items

    def query_work_items(self, wiql_query: str) -> List[WorkItemSummary]:
        ids = self.stage_1_execute_wiql(wiql_query)
        return self.stage_2_fetch_details(ids)

    def query_active_bugs(self) -> List[WorkItemSummary]:
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'Active'"
        return self.query_work_items(query)

    def query_by_assignee(self, assignee_name: str) -> List[WorkItemSummary]:
        query = f"SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = '{assignee_name}'"
        return self.query_work_items(query)
