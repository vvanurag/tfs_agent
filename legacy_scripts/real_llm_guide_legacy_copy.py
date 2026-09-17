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
    prompt = "Explain what a Two-Stage TFS Work Item retrieval architecture is in 2 sentences."
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
# EXACT same .invoke() interface across all providers:

def demo_cloud_llm_examples():
    """
    Code templates for connecting to Google Gemini, OpenAI, or Anthropic.
    (Requires corresponding API key set in environment variables).
    """
    # 1. Google Gemini
    # pip install langchain-google-genai
    # export GOOGLE_API_KEY="your-api-key"
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1)
    response = gemini_llm.invoke("Hello from Gemini!")
    """

    # 2. OpenAI ChatGPT
    # pip install langchain-openai
    # export OPENAI_API_KEY="your-api-key"
    """
    from langchain_openai import ChatOpenAI
    openai_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    response = openai_llm.invoke("Hello from GPT-4o!")
    """

    # 3. Anthropic Claude
    # pip install langchain-anthropic
    # export ANTHROPIC_API_KEY="your-api-key"
    """
    from langchain_anthropic import ChatAnthropic
    claude_llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0.1)
    response = claude_llm.invoke("Hello from Claude!")
    """


if __name__ == "__main__":
    demo_local_ollama()
    demo_structured_output()
