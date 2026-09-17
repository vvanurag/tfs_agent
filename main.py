#!/usr/bin/env python3
"""
=============================================================================
🛡️ TFS AGENT: ZERO-EGRESS MULTI-AGENT DEVOPS PIPELINE
=============================================================================
Unified CLI & Entrypoint for all pipeline operations.
=============================================================================
"""

import sys
import argparse
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.emulator.seeder import seed_database
from src.emulator.server import start_server
from src.emulator.client import LocalTFSClient
from src.rag.indexer import build_vector_store
from src.rag.search import execute_rbac_search
from src.agents.orchestrator import run_orchestrator

def main():
    parser = argparse.ArgumentParser(
        description="TFS Agent: Zero-Egress Multi-Agent DevOps Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run-all            # Run complete pipeline end-to-end
  python main.py --seed               # Seed SQLite database & generate mock JSON
  python main.py --start-server       # Start local TFS FastAPI emulator (port 8000)
  python main.py --build-rag          # Ingest documents into ChromaDB with RBAC
  python main.py --test-client        # Test TFS client WIQL queries and pruning
  python main.py --test-rag           # Test ChromaDB RBAC similarity search
  python main.py --run-agent          # Execute LangGraph Multi-Agent Orchestrator
        """
    )
    
    parser.add_argument("--run-all", action="store_true", help="Execute complete pipeline end-to-end")
    parser.add_argument("--seed", action="store_true", help="Seed SQLite database from dataset")
    parser.add_argument("--start-server", action="store_true", help="Launch local FastAPI emulator")
    parser.add_argument("--build-rag", action="store_true", help="Build ChromaDB vector store")
    parser.add_argument("--test-client", action="store_true", help="Test TFS API client")
    parser.add_argument("--test-rag", action="store_true", help="Test ChromaDB RBAC search")
    parser.add_argument("--run-agent", action="store_true", help="Run multi-agent orchestrator")
    parser.add_argument("--clearance", type=int, default=2, help="Clearance level for agent / RAG (1, 2, or 3)")

    args = parser.parse_args()

    # If no flags provided, show help or run agent
    if len(sys.argv) == 1 or args.run_all:
        print("\n" + "=" * 65)
        print("🚀 RUNNING COMPLETE TFS AGENT PIPELINE END-TO-END")
        print("=" * 65)
        
        print("\n[1/3] Seeding Enterprise Database...")
        seed_database(verbose=True)
        
        print("\n[2/3] Building ChromaDB Vector Store with RBAC...")
        build_vector_store(verbose=True)
        
        print("\n[3/3] Executing LangGraph Multi-Agent Orchestrator (Real Llama 3)...")
        try:
            result = run_orchestrator(clearance=args.clearance)
            print("\n" + "=" * 65)
            print("🎯 FINAL SYNTHESIZED SPRINT REPORT:")
            print("=" * 65)
            output = result.get("final_report") or result.get("report_draft")
            if isinstance(output, dict):
                print(json.dumps(output, indent=2))
            else:
                print(output)
        except Exception as e:
            print(f"\n❌ Multi-Agent execution failed: {e}")
            print("Is the TFS server running (port 8000) and Ollama running with 'llama3'?")
        return

    if args.seed:
        seed_database(verbose=True)
        return

    if args.start_server:
        start_server()
        return

    if args.build_rag:
        build_vector_store(verbose=True)
        return

    if args.test_client:
        client = LocalTFSClient()
        bugs = client.query_active_bugs()
        print(f"Found {len(bugs)} active bugs from TFS API:")
        for bug in bugs:
            print(f" • [Bug #{bug.id}] (Priority {bug.priority}) {bug.title} -> Assigned: {bug.assigned_to}")
        return

    if args.test_rag:
        results = execute_rbac_search(
            query_text="What is the SLA retry policy for NTLM handshake timeouts?",
            user_clearance=args.clearance,
            verbose=True
        )
        return

    if args.run_agent:
        result = run_orchestrator(clearance=args.clearance)
        print("\n" + "=" * 65)
        print("FINAL SYNTHESIZED SPRINT REPORT:")
        print("=" * 65)
        output = result.get("final_report") or result.get("report_draft")
        if isinstance(output, dict):
            print(json.dumps(output, indent=2))
        else:
            print(output)
        return


if __name__ == "__main__":
    main()
