import json
import sqlite3
import os

DB_PATH = "local_tfs.db"
DATASET_PATH = "tfs_dataset.json"
MOCK_RESPONSE_PATH = "mock_tfs_response.json"

def seed_database():
    """Initializes SQLite database and populates it with the enterprise TFS dataset."""
    print("=" * 60)
    print("SEEDING LOCAL TFS SQLITE DATABASE")
    print("=" * 60)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset file '{DATASET_PATH}' not found.")

    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table with comprehensive fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS WorkItems (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            work_item_type TEXT NOT NULL,
            state TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            assigned_to_email TEXT,
            priority INTEGER,
            severity TEXT,
            area_path TEXT,
            iteration_path TEXT,
            created_date TEXT,
            tags TEXT,
            description TEXT
        )
    """)

    # Clear existing entries
    cursor.execute("DELETE FROM WorkItems")

    rows = []
    for item in dataset:
        rows.append((
            item["id"],
            item["title"],
            item["work_item_type"],
            item["state"],
            item["assigned_to"],
            item.get("assigned_to_email", ""),
            item.get("priority", 2),
            item.get("severity", "3 - Medium"),
            item.get("area_path", ""),
            item.get("iteration_path", "Sprint 12"),
            item.get("created_date", ""),
            item.get("tags", ""),
            item.get("description", "")
        ))

    cursor.executemany("""
        INSERT INTO WorkItems (
            id, title, work_item_type, state, assigned_to, assigned_to_email,
            priority, severity, area_path, iteration_path, created_date, tags, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM WorkItems").fetchone()[0]
    conn.close()

    print(f" Successfully inserted {count} enterprise work items into '{DB_PATH}'.")

    # Also generate mock_tfs_response.json for offline testing
    mock_payload = {
        "count": len(dataset),
        "value": [
            {
                "id": item["id"],
                "rev": 3,
                "url": f"https://dev.azure.com/enterprise_org/_apis/wit/workItems/{item['id']}",
                "fields": {
                    "System.Id": item["id"],
                    "System.Title": item["title"],
                    "System.WorkItemType": item["work_item_type"],
                    "System.State": item["state"],
                    "System.AssignedTo": {
                        "displayName": item["assigned_to"],
                        "id": f"guid-{item['id']}",
                        "uniqueName": item.get("assigned_to_email", "")
                    },
                    "System.Description": item.get("description", ""),
                    "Microsoft.VSTS.Common.Priority": item.get("priority", 2),
                    "Microsoft.VSTS.Common.Severity": item.get("severity", "3 - Medium"),
                    "System.AreaPath": item.get("area_path", ""),
                    "System.IterationPath": item.get("iteration_path", "Sprint 12"),
                    "System.CreatedDate": item.get("created_date", ""),
                    "System.Tags": item.get("tags", "")
                }
            }
            for item in dataset
        ]
    }

    with open(MOCK_RESPONSE_PATH, "w") as f:
        json.dump(mock_payload, f, indent=2)

    print(f" Generated '{MOCK_RESPONSE_PATH}' for offline mock clients.")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
