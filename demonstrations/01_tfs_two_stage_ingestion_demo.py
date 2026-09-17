"""
=============================================================================
DEMO 1: TWO-STAGE TFS / AZURE DEVOPS INGESTION & PYDANTIC PRUNING
=============================================================================
Core Capability:
  Stage 1: Lightweight WIQL POST query to get matching Work Item IDs.
  Stage 2: Batch GET lookup + Pydantic v2 payload pruning & HTML tag stripping.
=============================================================================
"""

import re
import html
import requests
from pydantic import BaseModel, Field
from typing import List, Optional

# ---------------------------------------------------------------------------
# 1. THE DATA CONTRACT (Pydantic Schema)
# ---------------------------------------------------------------------------
class WorkItemSummary(BaseModel):
    """
    Clean, normalized data model for LLM ingestion.
    Discards bloated internal GUIDs, URLs, and revision history.
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

    model_config = {"populate_by_name": True}

    @classmethod
    def clean_html(cls, raw_html: str) -> str:
        """Strips HTML formatting and unescapes entities for clean LLM text."""
        if not raw_html:
            return ""
        text = re.sub(r'<(br|p|div)[^>]*>', ' ', raw_html, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()


# ---------------------------------------------------------------------------
# 2. TWO-STAGE RETRIEVAL LOGIC
# ---------------------------------------------------------------------------
def demonstrate_two_stage_ingestion():
    base_url = "http://127.0.0.1:8000"
    
    print("=" * 65)
    print("DEMO 1: TWO-STAGE TFS WORK ITEM INGESTION")
    print("=" * 65)

    # Stage 1: WIQL Metadata Query
    print("\n--> [Stage 1] Executing WIQL POST query to get active bug IDs...")
    wiql_query = "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'Active'"
    
    try:
        stage1_resp = requests.post(f"{base_url}/_apis/wit/wiql", json={"query": wiql_query}, timeout=5)
        stage1_resp.raise_for_status()
        matching_ids = [item["id"] for item in stage1_resp.json().get("workItems", [])]
        print(f"    [Stage 1 Result] Matching Work Item IDs: {matching_ids}")
    except Exception as e:
        print(f"    [!] Error connecting to TFS emulator ({e}). Using sample IDs [10241, 10243, 10245].")
        matching_ids = [10241, 10243, 10245]

    # Stage 2: Batch GET Lookup + Pydantic Pruning
    print(f"\n--> [Stage 2] Executing Batch GET request for IDs -> {matching_ids}...")
    ids_param = ",".join(str(i) for i in matching_ids)
    
    try:
        stage2_resp = requests.get(f"{base_url}/_apis/wit/workitems?ids={ids_param}", timeout=5)
        stage2_resp.raise_for_status()
        raw_items = stage2_resp.json().get("value", [])
        
        pruned_objects: List[WorkItemSummary] = []
        for raw in raw_items:
            fields = raw.get("fields", {})
            assignee_obj = fields.get("System.AssignedTo", {})
            assignee = assignee_obj.get("displayName", "Unassigned") if isinstance(assignee_obj, dict) else str(assignee_obj)
            
            cleaned_summary = WorkItemSummary(
                id=raw.get("id"),
                title=fields.get("System.Title", "No Title"),
                type=fields.get("System.WorkItemType", "Unknown"),
                state=fields.get("System.State", "Unknown"),
                assigned_to=assignee,
                priority=fields.get("Microsoft.VSTS.Common.Priority", 2),
                severity=fields.get("Microsoft.VSTS.Common.Severity"),
                iteration_path=fields.get("System.IterationPath"),
                tags=[t.strip() for t in fields.get("System.Tags", "").split(";") if t.strip()],
                description=WorkItemSummary.clean_html(fields.get("System.Description", ""))
            )
            pruned_objects.append(cleaned_summary)

        print(f"    [Stage 2 Result] Successfully pruned {len(pruned_objects)} work items into Pydantic models.\n")
        print("Sample Pruned Work Item (Ready for LLM):")
        print(pruned_objects[0].model_dump_json(indent=2))

    except Exception as e:
        print(f"    [!] Batch lookup failed: {e}")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    demonstrate_two_stage_ingestion()
