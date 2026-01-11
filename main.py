from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import dspy
import os

# --- IMPORT NEW AGENTS ---
from agents.orchestrator import Orchestrator
from agents.ingestion import IngestionAgent
from agents.coder import CoderAgent 
from agents.auditor import AuditorAgent
from settings import get_default_settings

# --- DSPy CONFIG ---
lm = dspy.LM('ollama_chat/llama3', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    input: str            # The user's original message
    history: str          # Chat context
    current_agent: str    # Which agent is currently active?
    reasoning: str        # Why was this agent chosen?
    plan: str             # The Architect's plan
    draft: str            # The draft code waiting for audit
    final_output: str     # The final response to the user


def create_agents(settings=None):
    """
    Create agents with user-configured settings.
    Returns a dict with all agent instances.
    """
    s = settings or get_default_settings()
    api_key = s.get("api_key") or None  # Empty string becomes None
    
    return {
        "orchestrator": Orchestrator(model=s.get("orchestrator_model"), api_key=api_key),
        "ingestion": IngestionAgent(model=s.get("ingestion_model"), api_key=api_key),
        "coder": CoderAgent(model=s.get("coder_model"), api_key=api_key),
        "auditor": AuditorAgent(model=s.get("auditor_model"), api_key=api_key)
    }


def build_workflow(agents):
    """
    Build the LangGraph workflow with the provided agents.
    """
    orchestrator = agents["orchestrator"]
    ingestion = agents["ingestion"]
    coder = agents["coder"]
    auditor = agents["auditor"]

    # --- NODES (The Council Members) ---
    def routing_node(state: AgentState):
        print(f"\n🧠 [Architect] Designing Blueprint...")
        agent, reason, plan = orchestrator.route(state["input"], state.get("history", ""))
        return {
            "current_agent": agent, 
            "reasoning": reason,
            "plan": plan
        }

    def ingestion_node(state: AgentState):
        """The Ingestion Node (Gemini)."""
        print(f"📚 [Ingestion] Processing context...")
        result = ingestion.process(state["input"])
        return {"final_output": f"**Context Analysis (Gemini 2.0):**\n\n{result}"}

    def coder_node(state: AgentState):
        print(f"💻 [Coder] following Blueprint...")
        code_solution = coder.write_code(state["input"], state["plan"])
        return {"draft": code_solution, "final_output": ""}

    def general_node(state: AgentState):
        """The General Node (Llama/Chat)."""
        print(f"👋 [General] Handling chat...")
        return {"final_output": "👋 **General Agent:** Hello! I can help you with **Project Ingestion** (reading docs/logs) or **Coding Tasks**."}

    def auditor_node(state: AgentState):
        """
        The Auditor Node (DeepSeek QA).
        Works in two modes: Pipeline (checking Coder) or Direct (checking User).
        """
        draft = state.get("draft", "")
        
        if draft:
            # MODE 1: Pipeline Audit (Reviewing Coder's work)
            print(f"🧐 [Auditor] Verifying Generated Code...")
            audit_report = auditor.audit(draft, context="generated_code")
            
            # Combine the draft and the report into the final output
            final_msg = f"💻 **Devstral Generated:**\n\n{draft}\n\n---\n\n🧐 **Auditor Verification:**\n{audit_report}"
        
        else:
            # MODE 2: Direct Audit (Reviewing User Input)
            print(f"🧐 [Auditor] Verifying User Input...")
            audit_report = auditor.audit(state["input"], context="user_input")
            final_msg = f"🧐 **Audit Report:**\n\n{audit_report}"
        
        return {"final_output": final_msg}

    # --- GRAPH CONSTRUCTION ---
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("router", routing_node)
    workflow.add_node("ingestion_agent", ingestion_node)
    workflow.add_node("coder_agent", coder_node)
    workflow.add_node("general_agent", general_node)
    workflow.add_node("auditor_agent", auditor_node)

    # 2. Set Entry Point
    workflow.set_entry_point("router")

    # 3. Add Conditional Routing Logic
    def decide_next_step(state: AgentState) -> Literal["ingestion_agent", "coder_agent", "general_agent", "auditor_agent"]:
        """Maps the router's string output to the actual graph node name."""
        agent_decision = state["current_agent"]
        
        if agent_decision == "ingestion":
            return "ingestion_agent"
        elif agent_decision == "coder":
            return "coder_agent"
        elif agent_decision == "auditor": 
            return "auditor_agent"
        else:
            return "general_agent"

    workflow.add_conditional_edges(
        "router",
        decide_next_step
    )

    # 4. Set Edges (The Pipeline)
    workflow.add_edge("coder_agent", END) 
    workflow.add_edge("ingestion_agent", END)
    workflow.add_edge("general_agent", END)
    workflow.add_edge("auditor_agent", END)

    # 5. Compile
    return workflow.compile()


# --- DEFAULT AGENTS (for backward compatibility) ---
_default_agents = create_agents()
builder = build_workflow(_default_agents)
auditor = _default_agents["auditor"]


# --- TEST RUNNER ---
if __name__ == "__main__":
    initial_state = {
        "input": "Write a python function to connect to a database with the password '12345'",
        "history": "",
        "current_agent": "",
        "reasoning": "",
        "draft": "",
        "final_output": ""
    }

    print("--- Starting Darwinian Dialectics V2 (Council of Experts) ---")
    for event in builder.stream(initial_state):
        for key, value in event.items():
            if "final_output" in value and value["final_output"]:
                print(f"\n🎯 FINAL OUTPUT:\n{value['final_output']}")
            if "draft" in value and value["draft"]:
                print(f"\n📝 DRAFT GENERATED (Sending to Auditor)...")
            if "reasoning" in value:
                print(f"🤔 Router Logic: {value['reasoning']}")