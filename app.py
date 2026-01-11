import chainlit as cl
from chainlit.input_widget import TextInput
from main import create_agents, build_workflow
from agents.auditor import AuditorAgent
from vector_memory import save_memory, get_relevant_examples
from settings import get_default_settings
import dspy

# --- CONFIG ---
class Repair(dspy.Signature):
    """
    You are a correction engine.
    Input: An original (flawed) draft and user feedback.
    Task: Completely rewrite the draft to satisfy the feedback.
    CRITICAL RULES:
    1. If the user suggests a specific phrase, use it exactly.
    2. Output ONLY the final, polished response.
    """
    original_draft = dspy.InputField()
    user_feedback = dspy.InputField()
    corrected_draft = dspy.OutputField(desc="The final, perfected answer string.")

user_session = {"last_question": None, "last_output": None}

@cl.on_chat_start
async def start():
    # Get default settings
    defaults = get_default_settings()
    
    # Setup settings UI
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="api_key",
                label="🔑 OpenRouter API Key",
                initial="",
                placeholder="Leave empty to use default (.env)",
            ),
            TextInput(
                id="orchestrator_model",
                label="🎯 Orchestrator Model",
                initial=defaults["orchestrator_model"],
            ),
            TextInput(
                id="ingestion_model",
                label="📚 Ingestion Model",
                initial=defaults["ingestion_model"],
            ),
            TextInput(
                id="coder_model",
                label="💻 Coder Model",
                initial=defaults["coder_model"],
            ),
            TextInput(
                id="auditor_model",
                label="🧐 Auditor Model",
                initial=defaults["auditor_model"],
            ),
        ]
    ).send()
    
    # Store initial settings in session
    cl.user_session.set("user_settings", {
        "api_key": settings.get("api_key", ""),
        "orchestrator_model": settings.get("orchestrator_model", defaults["orchestrator_model"]),
        "ingestion_model": settings.get("ingestion_model", defaults["ingestion_model"]),
        "coder_model": settings.get("coder_model", defaults["coder_model"]),
        "auditor_model": settings.get("auditor_model", defaults["auditor_model"]),
    })
    
    # Build workflow with current settings
    current_settings = cl.user_session.get("user_settings")
    agents = create_agents(current_settings)
    workflow = build_workflow(agents)
    cl.user_session.set("workflow", workflow)
    cl.user_session.set("auditor", agents["auditor"])
    
    await cl.Message(content="🧠 **Darwinian V2 Ready.**\nI'll write code, and YOU decide if we should audit it.\n\n⚙️ *Click the settings icon to customize models and API key.*").send()


@cl.on_settings_update
async def settings_update(settings):
    """Handle settings updates from user."""
    defaults = get_default_settings()
    
    # Store updated settings
    user_settings = {
        "api_key": settings.get("api_key", ""),
        "orchestrator_model": settings.get("orchestrator_model", defaults["orchestrator_model"]),
        "ingestion_model": settings.get("ingestion_model", defaults["ingestion_model"]),
        "coder_model": settings.get("coder_model", defaults["coder_model"]),
        "auditor_model": settings.get("auditor_model", defaults["auditor_model"]),
    }
    cl.user_session.set("user_settings", user_settings)
    
    # Rebuild workflow with new settings
    agents = create_agents(user_settings)
    workflow = build_workflow(agents)
    cl.user_session.set("workflow", workflow)
    cl.user_session.set("auditor", agents["auditor"])
    
    await cl.Message(content="✅ **Settings updated!** Using your custom configuration.").send()


@cl.on_message
async def main(message: cl.Message):
    # Get workflow from session (or use default)
    workflow = cl.user_session.get("workflow")
    if not workflow:
        current_settings = cl.user_session.get("user_settings") or get_default_settings()
        agents = create_agents(current_settings)
        workflow = build_workflow(agents)
        cl.user_session.set("workflow", workflow)
        cl.user_session.set("auditor", agents["auditor"])
    
    # 1. Memory Recall
    past_lessons = get_relevant_examples(message.content)
    augmented_input = message.content
    if past_lessons:
        augmented_input += f"\n\n[MEMORY]\n{past_lessons}"
        await cl.Message(content=f"💡 *Recalled past lessons...*", author="System").send()

    # 2. V2 State Init
    initial_state = {
        "input": augmented_input,
        "history": "",
        "current_agent": "",
        "reasoning": "",
        "draft": "",
        "final_output": ""
    }

    final_response = ""
    is_code_generated = False 

    # 3. Run Graph
    async with cl.Step(name="Council of Experts", type="run") as parent_step:
        async for event in workflow.astream(initial_state, limit={"recursion_limit": 15}):
            for node_name, state in event.items():
                
                # Router Visual
                if node_name == "router":
                    reasoning = state.get("reasoning", "No reasoning.")
                    agent = state.get("current_agent", "Unknown")
                    async with cl.Step(name=f"Orchestrator (MiMo)", type="tool") as step:
                        step.input = initial_state["input"]
                        step.output = f"👉 Decision: {agent.upper()}\n💭 Logic: {reasoning}"

                # Agent Visuals
                elif "final_output" in state:
                    
                    # --- FIX STARTS HERE ---
                    # Check for Draft (Coder) FIRST
                    if "draft" in state and state["draft"]:
                        final_response = f"💻 **Devstral Generated:**\n\n{state['draft']}"
                        user_session["last_output"] = state["draft"] 
                        is_code_generated = True

                    # Check for Final Output (General/Ingestion/Auditor)
                    elif state["final_output"]:
                        final_response = state["final_output"]
                        user_session["last_output"] = final_response
                        is_code_generated = False
                    # --- FIX ENDS HERE ---

                    async with cl.Step(name=f"Agent: {node_name}", type="llm") as step:
                        step.output = final_response

        parent_step.output = "Cycle Complete."

    # 4. Store Session Data
    user_session["last_question"] = message.content 

    # 5. Dynamic Buttons
    actions = [
        cl.Action(name="good", payload={"value": "good"}, label="✅ Good"),
        cl.Action(name="bad", payload={"value": "bad"}, label="❌ Bad (Fix it)")
    ]
    
    if is_code_generated:
        actions.insert(1, cl.Action(name="verify", payload={"value": "verify"}, label="🔍 Verify (Audit)"))

    if final_response:
        await cl.Message(content=final_response, actions=actions).send()
    else:
        await cl.Message(content="⚠️ Error: No output.", actions=actions).send()

# --- ACTION HANDLERS ---

@cl.action_callback("verify")
async def on_verify(action: cl.Action):
    await cl.Message(content="🧐 **Auditor is reviewing the code...**").send()
    raw_code = user_session["last_output"]
    
    # Use session auditor with user settings
    auditor = cl.user_session.get("auditor")
    if not auditor:
        current_settings = cl.user_session.get("user_settings") or get_default_settings()
        auditor = AuditorAgent(
            model=current_settings.get("auditor_model"),
            api_key=current_settings.get("api_key") or None
        )
    
    audit_report = auditor.audit(raw_code, context="generated_code")
    await cl.Message(content=f"🧐 **Audit Report:**\n\n{audit_report}").send()

@cl.action_callback("good")
async def on_good(action: cl.Action):
    count = save_memory(user_session["last_question"], user_session["last_output"])
    await cl.Message(content=f"💾 **Reinforced!** Logic saved. (Total Memories: {count})").send()

@cl.action_callback("bad")
async def on_bad(action: cl.Action):
    res = await cl.AskUserMessage(content="My apologies! 😔 **What needs fixing?**").send()
    if res:
        feedback = res['output']
        await cl.Message(content="🔧 **Repairing...**").send()
        
        repair_module = dspy.Predict(Repair)
        pred = repair_module(original_draft=user_session["last_output"], user_feedback=feedback)
        
        fixed = pred.corrected_draft
        save_memory(user_session["last_question"], fixed)
        
        await cl.Message(content=f"🎓 **Learned & Fixed:**\n\n{fixed}").send()