from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import dspy
import os

# --- IMPORT NEW AGENTS ---
from agents.orchestrator import Orchestrator
from agents.ingestion import IngestionAgent
from agents.coder import CoderAgent  #

# Initialize the "Brains"
orchestrator = Orchestrator()
ingestion = IngestionAgent()
coder = CoderAgent()

# --- DSPy CONFIG (Keep existing config if needed for other modules) ---
lm = dspy.LM('ollama_chat/llama3', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    input: str            # The user's original message
    history: str          # Chat context
    current_agent: str    # Which agent is currently active?
    reasoning: str        # Why was this agent chosen?
    final_output: str     # The final response to the user

# --- NODES (The Council Members) ---

def routing_node(state: AgentState):
    """
    The Orchestrator Node.
    Analyzes the input and decides which expert to call.
    """
    print(f"\n🧠 [Router] Analyzing request: {state['input'][:50]}...")
    
    # Call the Orchestrator (MiMo) to decide
    agent, reason = orchestrator.route(state["input"], state.get("history", ""))
    
    return {
        "current_agent": agent, 
        "reasoning": reason
    }

def ingestion_node(state: AgentState):
    """
    The Ingestion Node (Gemini).
    Handles large context, logs, and documentation.
    """
    print(f"📚 [Ingestion] Processing context...")
    
    # Call the Gemini Ingestion Agent
    result = ingestion.process(state["input"])
    
    return {"final_output": f"**Context Analysis (Gemini 2.0):**\n\n{result}"}

def coder_node(state: AgentState):
    """
    The Coder Node (Devstral/DeepSeek).
    """
    print(f"💻 [Coder] Engineering solution...")
    
    # This calls the REAL DeepSeek agent now!
    code_solution = coder.write_code(state["input"])
    
    return {"final_output": f"💻 **Devstral Generated:**\n\n{code_solution}"}

def general_node(state: AgentState):
    """
    The General Node (Llama/Chat).
    Handles greetings and simple queries.
    """
    print(f"👋 [General] Handling chat...")
    return {"final_output": "👋 **General Agent:** Hello! I can help you with **Project Ingestion** (reading docs/logs) or **Coding Tasks**."}

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("router", routing_node)
workflow.add_node("ingestion_agent", ingestion_node)
workflow.add_node("coder_agent", coder_node)
workflow.add_node("general_agent", general_node)

# 2. Set Entry Point
workflow.set_entry_point("router")

# 3. Add Conditional Routing Logic
def decide_next_step(state: AgentState) -> Literal["ingestion_agent", "coder_agent", "general_agent"]:
    """Maps the router's string output to the actual graph node name."""
    agent_decision = state["current_agent"]
    
    if agent_decision == "ingestion":
        return "ingestion_agent"
    elif agent_decision == "coder":
        return "coder_agent"
    elif agent_decision == "auditor": 
        # For V2 MVP, route Auditor requests to General or Coder (or add explicit node later)
        return "general_agent"
    else:
        return "general_agent"

workflow.add_conditional_edges(
    "router",
    decide_next_step
)

# 4. Set End Points (All agents finish after one turn for now)
workflow.add_edge("ingestion_agent", END)
workflow.add_edge("coder_agent", END)
workflow.add_edge("general_agent", END)

# 5. Compile
builder = workflow.compile() 
# Renaming to 'builder' to maintain compatibility if app.py imports it as 'builder'
# If app.py imports 'graph', rename this variable to 'graph'

# --- TEST RUNNER (If run directly) ---
if __name__ == "__main__":
    initial_state = {
        "input": "Here is a massive log file from my server: [Error: 500]...",
        "history": "",
        "current_agent": "",
        "reasoning": "",
        "final_output": ""
    }

    print("--- Starting Darwinian Dialectics V2 (Council of Experts) ---")
    for event in builder.stream(initial_state):
        for key, value in event.items():
            if "final_output" in value:
                print(f"\n🎯 FINAL OUTPUT:\n{value['final_output']}")
            if "reasoning" in value:
                print(f"🤔 Router Logic: {value['reasoning']}")