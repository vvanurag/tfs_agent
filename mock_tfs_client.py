import json
from pydantic import BaseModel

# ---------------------------------------------------------
# 1. THE PYDANTIC SCHEMA (Data Contract)
# This acts as our filter. Any data from the massive JSON 
# payload that is NOT listed here gets immediately discarded.
# ---------------------------------------------------------
class WorkItemSummary(BaseModel):
    id: int
    title: str
    work_item_type: str
    state: str
    assigned_to: str
    # We keep the description, but in a real pipeline we might 
    # run a regex here to strip HTML tags like <div> and <b>.
    description: str 

# ---------------------------------------------------------
# 2. THE MOCK CLIENT (Simulating the Enterprise Server)
# ---------------------------------------------------------
class MockTFSClient:
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path

    def stage_1_execute_wiql(self, query: str) -> list[int]:
        """
        EMULATE THE POST REQUEST: 
        Instead of calling the server, we print the query and 
        return the hardcoded IDs we know exist in our mock JSON.
        """
        print(f"--> [STAGE 1] Executing POST Request: WIQL Query -> '{query}'")
        # Simulating the server returning just a lightweight list of IDs
        return [10241, 10242]

    def stage_2_fetch_details(self, ids: list[int]) -> list[WorkItemSummary]:
        """
        EMULATE THE GET REQUEST & APPLY PYDANTIC FILTER:
        Reads the bloated JSON file and parses it through Pydantic.
        """
        print(f"--> [STAGE 2] Executing GET Request: Fetching massive JSON payload for IDs -> {ids}\n")
        
        # Simulate the server returning the massive JSON payload
        with open(self.json_file_path, "r") as file:
            raw_payload = json.load(file)
        
        clean_items = []
        
        # Loop through the bloated JSON and extract exactly what we need
        for item in raw_payload.get("value", []):
            fields = item.get("fields", {})
            
            # The "AssignedTo" field in the raw JSON is a deeply nested dictionary.
            # We dig into it here to extract just the simple string we need.
            assigned_to_obj = fields.get("System.AssignedTo", {})
            assignee_name = assigned_to_obj.get("displayName", "Unassigned")

            # Feed the extracted data into our strict Pydantic model
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
# 3. EXECUTE THE SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    # Initialize our mock client
    client = MockTFSClient("mock_tfs_response.json")
    
    # Run Stage 1
    mock_ids = client.stage_1_execute_wiql("SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'")
    
    # Run Stage 2
    pruned_work_items = client.stage_2_fetch_details(mock_ids)
    
    # Output the final, pruned payload ready for an LLM
    print("=" * 60)
    print("PYDANTIC PRUNED OUTPUT (Ready for LLM Ingestion)")
    print("=" * 60)
    for item in pruned_work_items:
        # .model_dump_json() outputs our clean, strictly enforced JSON string
        print(item.model_dump_json(indent=2))
        print("-" * 60)