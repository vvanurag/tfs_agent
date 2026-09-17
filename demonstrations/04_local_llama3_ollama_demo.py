"""
=============================================================================
DEMO 4: LOCAL LLAMA 3 INVOCATION VIA OLLAMA
=============================================================================
Core Capability:
  - Invoking local Llama 3 via LangChain ChatOllama with system prompts.
  - Streaming tokens word-by-word in real time.
=============================================================================
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

def demonstrate_local_llama3():
    print("=" * 65)
    print("DEMO 4: LOCAL LLAMA 3 VIA OLLAMA")
    print("=" * 65)

    # 1. Initialize local LLM
    print("--> [Step 1] Connecting to local Ollama daemon (model='llama3')...")
    llm = ChatOllama(model="llama3", temperature=0.1)

    # 2. Standard Invocation
    print("\n--> [Step 2] Sending prompt with System & Human messages...")
    messages = [
        SystemMessage(content="You are a concise enterprise Site Reliability Engineer."),
        HumanMessage(content="What is a 'zero-egress' architecture and why is it important? (Answer in 2 sentences)")
    ]

    response = llm.invoke(messages)
    print(f"\nLlama 3 Response:\n{response.content}\n")

    # 3. Streaming Invocation
    print("--> [Step 3] Real-time Streaming Output (Token-by-Token):")
    print("Streaming: ", end="", flush=True)
    
    stream_prompt = "Provide 3 short bullet points on how to prevent database connection pool exhaustion."
    for chunk in llm.stream(stream_prompt):
        print(chunk.content, end="", flush=True)

    print("\n\n" + "=" * 65)

if __name__ == "__main__":
    demonstrate_local_llama3()
