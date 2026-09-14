import requests
from pydantic import BaseModel
from typing import List

# ---------------------------------------------------------
# 1. THE PYDANTIC SCHEMA (Data Contract)
# ---------------------------------------------------------
class WorkItemSummary(BaseModel):
    id: int
    title: str
    work_item_type: str
    state: str
    assigned_to: str
    description: str 

# ---------------------------------------------------------
# 2. THE LOCAL HTTP CLIENT
# ---------------------------------------------------------
class LocalTFSClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    def stage_1_execute_wiql(self, query: str) -> List[int]:
        """
        STAGE 1: Executing a real POST Request to our local emulator.
        """
        print(f"--> [STAGE 1] Executing POST Request: WIQL Query -> '{query}'")
        
        url = f"{self.base_url}/_apis/wit/wiql"
        payload = {"query": query}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Will throw an error if the server is down
        
        data = response.json()
        
        # Extract the list of IDs from the response
        ids = [item["id"] for item in data.get("workItems", [])]
        return ids

    def stage_2_fetch_details(self, ids: List[int]) -> List[WorkItemSummary]:
        """
        STAGE 2: Executing a real GET Request & applying the Pydantic filter.
        """
        print(f"--> [STAGE 2] Executing GET Request for IDs -> {ids}\n")
        
        # Convert list of ints to a comma-separated string
        ids_str = ",".join(str(i) for i in ids)
        url = f"{self.base_url}/_apis/wit/workitems?ids={ids_str}"
        
        response = requests.get(url)
        response.raise_for_status()
        
        raw_payload = response.json()
        clean_items = []
        
        # Filter the bloated JSON through our Pydantic model
        for item in raw_payload.get("value", []):
            #print(f"Raw Work Item JSON:\n{item}\n")
            fields = item.get("fields", {})
            assigned_to_obj = fields.get("System.AssignedTo", {})
            assignee_name = assigned_to_obj.get("displayName", "Unassigned")

            summary = WorkItemSummary(
                id=item.get("id"),
                title=fields.get("System.Title", "No Title"),
                work_item_type=fields.get("System.WorkItemType", "Unknown"),
                state=fields.get("System.State", "Unknown"),
                assigned_to=assignee_name,
                description=fields.get("System.Description", "")
            )
            clean_items.append(summary)
            
        return clean_items

# ---------------------------------------------------------
# 3. EXECUTE THE VERIFICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    client = LocalTFSClient()
    
    try:
        # Run Stage 1
        mock_ids = client.stage_1_execute_wiql("SELECT id FROM WorkItems WHERE state = 'Active'")
        
        # Run Stage 2
        pruned_work_items = client.stage_2_fetch_details(mock_ids)
        
        print("=" * 60)
        print("PYDANTIC PRUNED OUTPUT (Ready for LLM Ingestion)")
        print("=" * 60)
        for item in pruned_work_items:
            print(item.model_dump_json(indent=2))
            print("-" * 60)
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to the emulator. Is FastAPI running on port 8000?")
