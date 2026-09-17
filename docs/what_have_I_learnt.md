# What is an API? Here which code referes to API running?
1. What is an API?
API stands for Application Programming Interface.

In simple terms, an API is a bridge and a rulebook that allows two different software programs to talk to each other and exchange data.

The Restaurant Analogy:
You (The Client / Python script): You are sitting at a table looking at a menu. You want food (data), but you can't just walk into the kitchen and grab raw ingredients.
The Waiter (The API): The waiter takes your order, brings it to the kitchen in a standardized format, and brings back your prepared meal.
The Kitchen & Pantry (The Database / SQLite): Where the raw data is stored and processed.
In a web/REST API:

Request: A client sends an HTTP message (like a GET request or POST request) to a specific URL (called an endpoint).
Response: The server processes the request and sends back structured data (usually in JSON format).
2. Which Code Refers to the API Running?
In 

local_tfs_emulator.py
, there are three key parts that make up the API:

Part A: Creating the API Instance
Lines 12–16 create the FastAPI application instance:

python
# 1. INITIALIZE FASTAPI APP
app = FastAPI(
    title="Local Azure DevOps (TFS) Emulator",
    description="Zero-Egress local emulator providing authentic Azure DevOps / TFS REST API endpoints.",
    version="2.0.0"
)
FastAPI is the Python web framework that defines and routes web requests.
Part B: Defining the API Endpoints (The "Menu")
These decorators (@app.get and @app.post) tell the server what URLs to listen for and what to do when someone visits them:

Health Check API (GET /)

python
@app.get("/")
def root():
    ...
WIQL Query API (POST /_apis/wit/wiql) — Stage 1:

python
@app.post("/_apis/wit/wiql")
def execute_wiql(payload: WIQLRequest):
    ...
When a client sends a WIQL query here, the server queries SQLite and returns matching Work Item IDs.
Work Items Batch API (GET /_apis/wit/workitems) — Stage 2:

python
@app.get("/_apis/wit/workitems")
def get_workitems(ids: str = Query(...)):
    ...
When a client asks for specific IDs (e.g., ?ids=10241,10242), the server returns the full details.
Part C: The Code That Actually Starts & Runs the Server
At the bottom of 

local_tfs_emulator.py
:

python
# 5. SERVER RUNNER
if __name__ == "__main__":
    print("=" * 60)
    print("STARTING ENHANCED TFS FASTAPI EMULATOR (PORT 8000)")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
uvicorn.run(app, host="127.0.0.1", port=8000) is the engine that actually boots up the web server and listens on port 8000.
Once this line executes, your computer opens a local web server at http://127.0.0.1:8000 waiting to receive requests.
3. How the Client Calls This Running API
In 

real_local_tfs_client.py
, you can see the client sending requests across the network to that running API:

python
# The client talks to the API running on port 8000:
response = requests.post("http://127.0.0.1:8000/_apis/wit/wiql", json={"query": "..."})
response = requests.get("http://127.0.0.1:8000/_apis/wit/workitems?ids=10241,10242")
