import sqlite3
from fastapi import FastAPI, Query
from pydantic import BaseModel
import uvicorn

# 1. INITIALIZE FASTAPI APP
app = FastAPI(title="Local Azure DevOps (TFS) Emulator")

# 2. DATABASE SETUP
def setup_database():
    """Creates a local SQLite file and populates it with mock data."""
    conn = sqlite3.connect("local_tfs.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Create the WorkItems table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS WorkItems (
            id INTEGER PRIMARY KEY,
            title TEXT,
            work_item_type TEXT,
            state TEXT,
            assigned_to TEXT,
            description TEXT
        )
    """)
    
    # Clear old data and insert the specific IDs we know from our mocks (10241, 10242)
    cursor.execute("DELETE FROM WorkItems")
    
    sample_data = [
        (10241, "NTLM Handshake Timeout Exception", "Bug", "Active", "Jane Doe", "<div><b>Error:</b> Connection timed out after 30000ms.</div>"),
        (10242, "Update RBAC Clearance Cache", "Task", "Active", "John Smith", "Ensure metadata filters apply cleanly to ChromaDB queries.")
    ]
    
    cursor.executemany(
        "INSERT INTO WorkItems (id, title, work_item_type, state, assigned_to, description) VALUES (?, ?, ?, ?, ?, ?)", 
        sample_data
    )
    conn.commit()
    return conn

# Connect to DB on startup
db_conn = setup_database()

# 3. PYDANTIC MODELS FOR REQUESTS
class WIQLRequest(BaseModel):
    query: str

# 4. API ENDPOINTS

@app.post("/_apis/wit/wiql")
def execute_wiql(payload: WIQLRequest):
    """
    STAGE 1: WIQL Execution
    Simulates the POST request. Instead of full SQL parsing, we simply return 
    the IDs of all 'Active' work items to mimic the lightweight metadata search.
    """
    print(f"[Server] Received WIQL POST Request: {payload.query}")
    
    cursor = db_conn.cursor()
    # Simple simulation: just fetching Active IDs
    cursor.execute("SELECT id FROM WorkItems WHERE state = 'Active'")
    rows = cursor.fetchall()
    
    # Format the response to mimic Azure DevOps JSON structure
    work_items = [{"id": row[0]} for row in rows]
    return {"queryType": "flat", "workItems": work_items}

@app.get("/_apis/wit/workitems")
def get_workitems(ids: str = Query(...)):
    """
    STAGE 2: Batch Detail Lookup
    Simulates the GET request. Returns the bloated payload with internal GUIDs
    and nested fields that your client will need to prune.
    """
    print(f"[Server] Received GET Request for IDs: {ids}")
    
    id_list = [int(i.strip()) for i in ids.split(",")]
    placeholders = ",".join("?" * len(id_list))
    
    cursor = db_conn.cursor()
    cursor.execute(f"SELECT * FROM WorkItems WHERE id IN ({placeholders})", id_list)
    rows = cursor.fetchall()
    
    # Reconstruct the "bloated" payload structure seen in your mock JSON
    values = []
    for row in rows:
        values.append({
            "id": row[0],
            "rev": 3,
            "url": f"https://dev.azure.com/localorg/_apis/wit/workItems/{row[0]}",
            "fields": {
                "System.Title": row[1],
                "System.WorkItemType": row[2],
                "System.State": row[3],
                "System.AssignedTo": {
                    "displayName": row[4],
                    "id": "mock-guid-1234",
                    "uniqueName": f"{row[4].replace(' ', '.').lower()}@local.com"
                },
                "System.Description": row[5]
            }
        })
        
    return {"count": len(values), "value": values}

# 5. SERVER EXECUTION
if __name__ == "__main__":
    print("=" * 60)
    print("STARTING LOCAL TFS FASTAPI EMULATOR")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)