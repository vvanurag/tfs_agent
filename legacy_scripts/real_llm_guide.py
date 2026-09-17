"""
=============================================================================
ENTERPRISE LLM INTEGRATION GUIDE & CHEATSHEET
=============================================================================
This file demonstrates how to connect and interact with REAL Large Language 
Models in Python projects using both Zero-Egress Local Models (Ollama) and 
Cloud API Providers (Google Gemini, OpenAI, Anthropic).
=============================================================================
"""

import os
from pydantic import BaseModel, Field
from typing import List

# ---------------------------------------------------------------------------
# PATTERN 1: LOCAL ZERO-EGRESS LLM (OLLAMA / LLAMA 3)
# ---------------------------------------------------------------------------
# Best for: Air-gapped environments, strict privacy, zero cloud costs.
# Prerequisite: Install Ollama (https://ollama.ai) and run `ollama pull llama3`

from langchain_ollama import ChatOllama

def demo_local_ollama():
    print("\n" + "=" * 60)
    print("DEMO 1: REAL LOCAL LLM (Llama 3 via Ollama)")
    print("=" * 60)
    
    # 1. Initialize local LLM
    llm = ChatOllama(
        model="llama3",
        temperature=0.1  # Low temperature = deterministic/factual responses
    )
    
    # 2. Basic Invocation
    prompt = "Explain what a Two-Stage TFS Work Item retrieval architecture is in 2 sentences. Also tell me what colour Taj Mahal is"
    print(f"Prompt: {prompt}\n")
    
    response = llm.invoke(prompt)
    print(f"Llama 3 Output:\n{response.content}\n")


# ---------------------------------------------------------------------------
# PATTERN 2: STRUCTURED OUTPUT WITH PYDANTIC (Type-Safe LLM Responses)
# ---------------------------------------------------------------------------
# How to force any LLM to return valid, strongly-typed Python objects instead
# of unstructured text.

class WorkItemRemediation(BaseModel):
    ticket_id: int = Field(description="TFS Work item ID")
    title: str = Field(description="Brief title of the bug or task")
    severity: str = Field(description="Severity e.g., Critical, High, Medium")
    recommended_action: str = Field(description="Specific technical remediation steps")

def demo_structured_output():
    print("\n" + "=" * 60)
    print("DEMO 2: REAL LLM STRUCTURED OUTPUT (Pydantic Enforcement)")
    print("=" * 60)
    
    llm = ChatOllama(model="llama3", temperature=0.0)
    
    # Bind the Pydantic schema to the model
    structured_llm = llm.with_structured_output(WorkItemRemediation)
    
    raw_incident_text = """
    Incident 10241: Jane Doe reported that NTLM authentication to legacy Active 
    Directory timed out after 30 seconds. Domain controllers are experiencing 
    high load. Severity is Critical.
    """
    
    result = structured_llm.invoke(raw_incident_text)
    print("Pydantic Object Received from LLM:")
    print(f"  Ticket ID   : {result.ticket_id}")
    print(f"  Title       : {result.title}")
    print(f"  Severity    : {result.severity}")
    print(f"  Remediation : {result.recommended_action}")


# ---------------------------------------------------------------------------
# PATTERN 3: HOW TO SWITCH TO CLOUD LLMS (FOR NON-AIR-GAPPED PROJECTS)
# ---------------------------------------------------------------------------
# If you ever work on projects that permit cloud APIs, LangChain uses the 
# EXACT same .invoke() and .with_structured_output() interface across all providers:

def demo_cloud_llm_examples():
    """
    Working executable implementations for connecting to Google Gemini, 
    OpenAI ChatGPT, and Anthropic Claude via LangChain.
    
    Checks environment variables dynamically:
      - GOOGLE_API_KEY / GEMINI_API_KEY
      - OPENAI_API_KEY
      - ANTHROPIC_API_KEY
    """
    print("\n" + "=" * 60)
    print("DEMO 3: REAL CLOUD LLM PROVIDERS (LangChain Ecosystem)")
    print("=" * 60)

    test_prompt = "Explain in one sentence why API rate-limiting with exponential backoff is essential in production."

    # -----------------------------------------------------------------------
    # 1. Google Gemini (via langchain-google-genai)
    # -----------------------------------------------------------------------
    print("\n--- [Provider 1] Google Gemini ---")
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("  Connecting to Google Gemini (model='gemini-2.5-flash')...")
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key, 
                temperature=0.1
            )
            response = gemini_llm.invoke(test_prompt)
            print(f"  Gemini Response:\n    {response.content.strip()}\n")
            
            # Demonstrate Structured Output on Gemini
            structured_gemini = gemini_llm.with_structured_output(WorkItemRemediation)
            res_struct = structured_gemini.invoke("Bug 4010: Database SSL certificate expired on primary cluster. Critical severity.")
            print(f"  Gemini Structured Pydantic Output: Ticket #{res_struct.ticket_id} - {res_struct.title} ({res_struct.severity})")
        except Exception as e:
            print(f"  [ERROR] Gemini call failed: {e}")
    else:
        print("  [SKIPPED] GOOGLE_API_KEY not found in environment.")
        print("  To enable Gemini, run:")
        print("    export GOOGLE_API_KEY='your_api_key_here'")

    # -----------------------------------------------------------------------
    # 2. OpenAI ChatGPT (via langchain-openai)
    # -----------------------------------------------------------------------
    print("\n--- [Provider 2] OpenAI (GPT-4o) ---")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            print("  Connecting to OpenAI (model='gpt-4o')...")
            openai_llm = ChatOpenAI(
                model="gpt-4o", 
                api_key=openai_key, 
                temperature=0.1
            )
            response = openai_llm.invoke(test_prompt)
            print(f"  OpenAI Response:\n    {response.content.strip()}\n")
            
            # Demonstrate Structured Output on OpenAI
            structured_openai = openai_llm.with_structured_output(WorkItemRemediation)
            res_struct = structured_openai.invoke("Bug 4011: Redis cache connection refused on port 6379. High severity.")
            print(f"  OpenAI Structured Pydantic Output: Ticket #{res_struct.ticket_id} - {res_struct.title} ({res_struct.severity})")
        except Exception as e:
            print(f"  [ERROR] OpenAI call failed: {e}")
    else:
        print("  [SKIPPED] OPENAI_API_KEY not found in environment.")
        print("  To enable OpenAI, run:")
        print("    export OPENAI_API_KEY='your_api_key_here'")

    # -----------------------------------------------------------------------
    # 3. Anthropic Claude (via langchain-anthropic)
    # -----------------------------------------------------------------------
    print("\n--- [Provider 3] Anthropic Claude (Claude 3.5 Sonnet) ---")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            from langchain_anthropic import ChatAnthropic
            print("  Connecting to Anthropic (model='claude-3-5-sonnet-20240620')...")
            claude_llm = ChatAnthropic(
                model="claude-3-5-sonnet-20240620", 
                api_key=anthropic_key, 
                temperature=0.1
            )
            response = claude_llm.invoke(test_prompt)
            print(f"  Anthropic Response:\n    {response.content.strip()}\n")
            
            # Demonstrate Structured Output on Anthropic
            structured_claude = claude_llm.with_structured_output(WorkItemRemediation)
            res_struct = structured_claude.invoke("Bug 4012: Ingress controller routing loop detected on port 443. Critical severity.")
            print(f"  Anthropic Structured Pydantic Output: Ticket #{res_struct.ticket_id} - {res_struct.title} ({res_struct.severity})")
        except Exception as e:
            print(f"  [ERROR] Anthropic call failed: {e}")
    else:
        print("  [SKIPPED] ANTHROPIC_API_KEY not found in environment.")
        print("  To enable Anthropic Claude, run:")
        print("    export ANTHROPIC_API_KEY='your_api_key_here'")


if __name__ == "__main__":
    demo_local_ollama()
    demo_structured_output()
    demo_cloud_llm_examples()

