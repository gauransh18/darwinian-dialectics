import chainlit as cl
from main import builder, auditor 
from vector_memory import save_memory, get_relevant_examples
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
    await cl.Message(content="🧠 **Darwinian V2 Ready.**\nI'll write code, and YOU decide if we should audit it.").send()

@cl.on_message
async def main(message: cl.Message):
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
        async for event in builder.astream(initial_state, limit={"recursion_limit": 15}):
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