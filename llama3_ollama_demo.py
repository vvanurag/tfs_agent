"""
=============================================================================
🦙 MASTER GUIDE: USING LLAMA 3 VIA OLLAMA IN PYTHON
=============================================================================
This standalone script demonstrates 5 essential ways to use local Llama 3:
  1. Direct Chat (Official Ollama SDK)
  2. Real-Time Token Streaming (Word-by-word terminal output)
  3. Multi-Turn Conversation (Chat History / Memory)
  4. LangChain Integration (`ChatOllama`)
  5. Type-Safe Structured Output (Pydantic + Llama 3)
=============================================================================
"""

import sys
import ollama
from pydantic import BaseModel, Field
from typing import List
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


# ===========================================================================
# 1. DIRECT CHAT (Official Ollama Python SDK)
# ===========================================================================
def demo_1_basic_chat():
    print("\n" + "=" * 65)
    print("🔹 DEMO 1: BASIC CHAT (Official Ollama SDK)")
    print("=" * 65)
    
    response = ollama.chat(
        model="llama3",
        messages=[
            {"role": "system", "content": "You are a concise enterprise DevOps expert."},
            {"role": "user", "content": "What is Azure DevOps (TFS) and why do enterprises use it? (Answer in 2 sentences)"}
        ],
        options={
            "temperature": 0.2  # 0.0 = very factual/deterministic, 1.0 = creative
        }
    )
    
    print(f"Llama 3 Output:\n{response['message']['content']}\n")


# ===========================================================================
# 2. REAL-TIME STREAMING (Word-by-Word Output)
# ===========================================================================
def demo_2_streaming():
    print("=" * 65)
    print("🔹 DEMO 2: REAL-TIME STREAMING (Token-by-token)")
    print("=" * 65)
    print("Prompt: Write a 3-step checklist for troubleshooting network timeouts.\n")
    print("Streaming Response: ", end="", flush=True)

    # By setting stream=True, Ollama returns chunks as they are generated
    stream = ollama.chat(
        model="llama3",
        messages=[
            {"role": "user", "content": "Write a 3-step checklist for troubleshooting network timeouts."}
        ],
        stream=True,
    )

    for chunk in stream:
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        
    print("\n\n")


# ===========================================================================
# 3. MULTI-TURN CONVERSATION (Memory / Chat History)
# ===========================================================================
def demo_3_conversation_memory():
    print("=" * 65)
    print("🔹 DEMO 3: MULTI-TURN CONVERSATION (Chat History)")
    print("=" * 65)

    # Initialize a conversation history list
    messages = [
        {"role": "system", "content": "You are a helpful software engineering assistant."}
    ]

    # Turn 1
    user_turn_1 = "My project is named 'TFS Agent' and it handles Azure DevOps bugs."
    print(f"User: {user_turn_1}")
    messages.append({"role": "user", "content": user_turn_1})
    
    reply_1 = ollama.chat(model="llama3", messages=messages)["message"]["content"]
    print(f"Llama 3: {reply_1}\n")
    messages.append({"role": "assistant", "content": reply_1})

    # Turn 2 (Llama 3 remembers the context from Turn 1)
    user_turn_2 = "What is the name of my project and what does it do?"
    print(f"User: {user_turn_2}")
    messages.append({"role": "user", "content": user_turn_2})
    
    reply_2 = ollama.chat(model="llama3", messages=messages)["message"]["content"]
    print(f"Llama 3: {reply_2}\n")


# ===========================================================================
# 4. LANGCHAIN INTEGRATION (`ChatOllama`)
# ===========================================================================
def demo_4_langchain_integration():
    print("=" * 65)
    print("🔹 DEMO 4: LANGCHAIN INTEGRATION (ChatOllama)")
    print("=" * 65)

    # Create the LangChain ChatOllama instance
    llm = ChatOllama(
        model="llama3",
        temperature=0.1,
    )

    messages = [
        SystemMessage(content="You are an expert site reliability engineer."),
        HumanMessage(content="Explain what 'jittered exponential backoff' means in 2 bullet points.")
    ]

    response = llm.invoke(messages)
    print(f"LangChain Response:\n{response.content}\n")


# ===========================================================================
# 5. TYPE-SAFE STRUCTURED OUTPUT (Pydantic + Llama 3)
# ===========================================================================
class DevOpsTicketAnalysis(BaseModel):
    """Pydantic schema enforcing structured data from Llama 3."""
    ticket_id: int = Field(description="The numeric ID of the ticket")
    ticket_title: str = Field(description="Summary title of the issue")
    severity: str = Field(description="Severity: 'Critical', 'High', 'Medium', or 'Low'")
    root_cause: str = Field(description="Brief explanation of the suspected root cause")
    action_items: List[str] = Field(description="List of immediate action items to resolve the bug")

def demo_5_structured_output_pydantic():
    print("=" * 65)
    print("🔹 DEMO 5: STRUCTURED OUTPUT WITH PYDANTIC (Type-Safe JSON)")
    print("=" * 65)

    llm = ChatOllama(model="llama3", temperature=0.0)

    # Bind the Pydantic schema to Llama 3
    structured_llm = llm.with_structured_output(DevOpsTicketAnalysis)

    unstructured_log = """
    CRITICAL INCIDENT #10241:
    Engineer Jane Doe reported that the Adjudication Engine suffered a 30,000ms 
    connection timeout during NTLM handshake with legacy Active Directory. 
    Domain controllers are overloaded. Immediate mitigation requires setting up 
    retry backoff and upgrading to Kerberos v2.
    """

    print(f"Input Unstructured Log:\n{unstructured_log.strip()}\n")
    print("Extracting strongly-typed Pydantic object from Llama 3...")
    
    parsed_object = structured_llm.invoke(unstructured_log)

    print("\n✅ Successfully Parsed into Python Object:")
    print(f"  • Ticket ID    : {parsed_object.ticket_id}")
    print(f"  • Title        : {parsed_object.ticket_title}")
    print(f"  • Severity     : {parsed_object.severity}")
    print(f"  • Root Cause   : {parsed_object.root_cause}")
    print(f"  • Action Items :")
    for item in parsed_object.action_items:
        print(f"     - {item}")
    print("\n" + "=" * 65)


# ===========================================================================
# MAIN ENTRYPOINT
# ===========================================================================
if __name__ == "__main__":
    print("\n🦙 STARTING LOCAL LLAMA 3 VIA OLLAMA DEMONSTRATION")
    
    demo_1_basic_chat()
    demo_2_streaming()
    demo_3_conversation_memory()
    demo_4_langchain_integration()
    demo_5_structured_output_pydantic()
    
    print("🎉 All 5 Llama 3 demonstrations completed successfully!")
