import sqlite3
import re
from typing import List
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from pathlib import Path

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "local_tfs.db"

app = FastAPI(
    title="Local Azure DevOps (TFS) Emulator",
    description="Zero-Egress local emulator providing authentic Azure DevOps / TFS REST API endpoints.",
    version="2.0.0"
)

def get_db_connection():
    """Returns a SQLite connection with row factory for dictionary access."""
    if not DB_PATH.exists():
        from .seeder import seed_database
        seed_database(verbose=False)
        
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

class WIQLRequest(BaseModel):
    query: str

def parse_wiql_to_sql(wiql_query: str) -> tuple[str, list]:
    """Translates Azure DevOps WIQL syntax into SQLite SQL."""
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
    sql_query = cleaned_query
    for tfs_field, sql_col in field_mapping.items():
        sql_query = re.sub(tfs_field, sql_col, sql_query, flags=re.IGNORECASE)

    if "from workitems" not in sql_query.lower():
        return "SELECT id FROM WorkItems WHERE state = 'Active'", []

    select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql_query, flags=re.IGNORECASE)
    if select_match:
        sql_query = re.sub(r"SELECT\s+.*?\s+FROM", "SELECT id FROM", sql_query, count=1, flags=re.IGNORECASE)

    return sql_query, []

@app.get("/")
def root():
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
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql_query, params = parse_wiql_to_sql(payload.query)
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        work_items = [{"id": row["id"]} for row in rows]
    except Exception as e:
        cursor.execute("SELECT id FROM WorkItems WHERE state = 'Active'")
        rows = cursor.fetchall()
        work_items = [{"id": row["id"]} for row in rows]
    finally:
        conn.close()

    return {
        "queryType": "flat",
        "queryResultType": "workItem",
        "asOf": "2026-09-17T09:00:00Z",
        "workItems": work_items
    }

@app.get("/_apis/wit/workitems")
def get_workitems(ids: str = Query(..., description="Comma-separated list of work item IDs")):
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

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the uvicorn ASGI server."""
    print("=" * 60)
    print(f"STARTING ENHANCED TFS FASTAPI EMULATOR (PORT {port})")
    print("=" * 60)
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
