import sqlite3
import re
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import uvicorn
import os

DB_PATH = "local_tfs.db"

# 1. INITIALIZE FASTAPI APP
app = FastAPI(
    title="Local Azure DevOps (TFS) Emulator",
    description="Zero-Egress local emulator providing authentic Azure DevOps / TFS REST API endpoints.",
    version="2.0.0"
)

def get_db_connection():
    """Returns a SQLite connection with row factory for dictionary access."""
    if not os.path.exists(DB_PATH):
        # Auto-seed if database doesn't exist
        from seed_database import seed_database
        seed_database()
        
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 2. PYDANTIC MODELS FOR REQUESTS
class WIQLRequest(BaseModel):
    query: str

# 3. WIQL TO SQL TRANSLATOR
def parse_wiql_to_sql(wiql_query: str) -> tuple[str, list]:
    """
    Translates standard Azure DevOps WIQL syntax into SQLite SQL.
    Example:
      SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active' AND [System.WorkItemType] = 'Bug'
    """
    # Map TFS WIQL field names to SQLite column names
    field_mapping = {
        r"\[System\.Id\]": "id",
        r"\[System\.Title\]": "title",
        r"\[System\.WorkItemType\]": "work_item_type",
        r"\[System\.State\]": "state",
        r"\[System\.AssignedTo\]": "assigned_to",
        r"\[Microsoft\.VSTS\.Common\.Priority\]": "priority",
        r"\[Microsoft\.VSTS\.Common\.Severity\]": "severity",
        r"\[System\.AreaPath\]": "area_path",
        r"\[System\.IterationPath\]": "iteration_path",
        r"\[System\.Tags\]": "tags"
    }


    cleaned_query = wiql_query.strip()
    
    # Replace all TFS field brackets with table columns
    sql_query = cleaned_query
    for tfs_field, sql_col in field_mapping.items():
        sql_query = re.sub(tfs_field, sql_col, sql_query, flags=re.IGNORECASE)

    # If it's a basic query or cannot be safely transformed, ensure it targets the WorkItems table
    if "from workitems" not in sql_query.lower():
        # Fallback default: select active items
        return "SELECT id FROM WorkItems WHERE state = 'Active'", []

    # Make sure we select id for flat queries
    select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql_query, flags=re.IGNORECASE)
    if select_match:
        sql_query = re.sub(r"SELECT\s+.*?\s+FROM", "SELECT id FROM", sql_query, count=1, flags=re.IGNORECASE)

    return sql_query, []

# 4. API ENDPOINTS

@app.get("/")
def root():
    """Health check and emulator metadata."""
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM WorkItems").fetchone()[0]
    conn.close()
    return {
        "service": "Azure DevOps (TFS) Local Emulator",
        "status": "online",
        "zero_egress": True,
        "total_work_items": count
    }

@app.post("/_apis/wit/wiql")
def execute_wiql(payload: WIQLRequest):
    """
    STAGE 1: WIQL Execution
    Executes WIQL queries against local SQLite database and returns matching Work Item IDs.
    """
    print(f"[TFS Server] Received WIQL Query: {payload.query}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        sql_query, params = parse_wiql_to_sql(payload.query)
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        work_items = [{"id": row["id"]} for row in rows]
        print(f"[TFS Server] Found {len(work_items)} matching work items.")
    except Exception as e:
        print(f"[TFS Server] SQL Parse Error: {e}, falling back to active items.")
        cursor.execute("SELECT id FROM WorkItems WHERE state = 'Active'")
        rows = cursor.fetchall()
        work_items = [{"id": row["id"]} for row in rows]
    finally:
        conn.close()

    return {
        "queryType": "flat",
        "queryResultType": "workItem",
        "asOf": "2026-09-14T18:00:00Z",
        "workItems": work_items
    }

@app.get("/_apis/wit/workitems")
def get_workitems(ids: str = Query(..., description="Comma-separated list of work item IDs")):
    """
    STAGE 2: Batch Detail Lookup
    Returns authentic Azure DevOps bloated JSON payloads with system metadata.
    """
    print(f"[TFS Server] Batch Fetch for IDs: {ids}")
    
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs parameter must be comma-separated integers.")

    if not id_list:
        return {"count": 0, "value": []}

    placeholders = ",".join("?" * len(id_list))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM WorkItems WHERE id IN ({placeholders})", id_list)
    rows = cursor.fetchall()
    conn.close()

    values = []
    for row in rows:
        values.append({
            "id": row["id"],
            "rev": 3,
            "url": f"https://dev.azure.com/enterprise_org/_apis/wit/workItems/{row['id']}",
            "fields": {
                "System.Id": row["id"],
                "System.Title": row["title"],
                "System.WorkItemType": row["work_item_type"],
                "System.State": row["state"],
                "System.AssignedTo": {
                    "displayName": row["assigned_to"],
                    "id": f"guid-{row['id']}-user",
                    "uniqueName": row["assigned_to_email"] or f"{row['assigned_to'].replace(' ', '.').lower()}@enterprise.local"
                },
                "System.Description": row["description"] or "",
                "Microsoft.VSTS.Common.Priority": row["priority"],
                "Microsoft.VSTS.Common.Severity": row["severity"],
                "System.AreaPath": row["area_path"],
                "System.IterationPath": row["iteration_path"],
                "System.CreatedDate": row["created_date"],
                "System.Tags": row["tags"]
            }
        })

    return {"count": len(values), "value": values}

@app.get("/_apis/wit/workitems/{work_item_id}")
def get_single_workitem(work_item_id: int):
    """Fetch a single work item by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM WorkItems WHERE id = ?", (work_item_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Work item {work_item_id} not found.")

    return {
        "id": row["id"],
        "rev": 3,
        "url": f"https://dev.azure.com/enterprise_org/_apis/wit/workItems/{row['id']}",
        "fields": {
            "System.Id": row["id"],
            "System.Title": row["title"],
            "System.WorkItemType": row["work_item_type"],
            "System.State": row["state"],
            "System.AssignedTo": {
                "displayName": row["assigned_to"],
                "id": f"guid-{row['id']}-user",
                "uniqueName": row["assigned_to_email"]
            },
            "System.Description": row["description"],
            "Microsoft.VSTS.Common.Priority": row["priority"],
            "Microsoft.VSTS.Common.Severity": row["severity"],
            "System.AreaPath": row["area_path"],
            "System.IterationPath": row["iteration_path"],
            "System.CreatedDate": row["created_date"],
            "System.Tags": row["tags"]
        }
    }

# 5. SERVER RUNNER
if __name__ == "__main__":
    print("=" * 60)
    print("STARTING ENHANCED TFS FASTAPI EMULATOR (PORT 8000)")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)