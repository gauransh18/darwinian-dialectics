import chainlit as cl
from main import builder  # Importing the V2 Graph
from vector_memory import save_memory, get_relevant_examples
import dspy

# --- CONFIG ---
class Repair(dspy.Signature):
    """
    You are a correction engine.
    Input: An original (flawed) draft and user feedback.
    Task: Completely rewrite the draft to satisfy the feedback.
    
    CRITICAL RULES:
    1. If the user suggests a specific phrase (e.g., "Say 'Hello'"), USE IT EXACTLY.
    2. Do NOT merge the old draft with the new one if the old one was wrong.
    3. Output ONLY the final, polished response. No 'Here is the fixed version:' meta-talk.
    """
    original_draft = dspy.InputField()
    user_feedback = dspy.InputField()
    corrected_draft = dspy.OutputField(desc="The final, perfected answer string.")

user_session = {"last_question": None, "last_output": None}

@cl.on_chat_start
async def start():
    await cl.Message(content="🧠 **Darwinian V2 (Council of Experts) Ready.**\nI will route your request to the best expert (Gemini, Coder, or General).").send()

@cl.on_message
async def main(message: cl.Message):
    # 1. Memory Recall
    past_lessons = get_relevant_examples(message.content)
    augmented_input = message.content
    
    if past_lessons:
        augmented_input += f"\n\n[MEMORY: Consider these past lessons]\n{past_lessons}"
        await cl.Message(content=f"💡 *Recalled past lessons...*", author="System").send()

    # 2. V2 State Initialization
    initial_state = {
        "input": augmented_input,
        "history": "",
        "current_agent": "",
        "reasoning": "",
        "final_output": ""
    }

    final_response = ""

    # 3. Run the V2 Graph
    async with cl.Step(name="Council of Experts", type="run") as parent_step:
        
        async for event in builder.astream(initial_state, limit={"recursion_limit": 15}):
            
            for node_name, state in event.items():
                
                # -- HANDLER: ROUTER --
                if node_name == "router":
                    reasoning = state.get("reasoning", "No reasoning provided.")
                    agent_name = state.get("current_agent", "Unknown")
                    
                    async with cl.Step(name=f"Orchestrator (MiMo)", type="tool") as step:
                        # FIX: Use initial_state["input"] instead of state["input"]
                        step.input = initial_state["input"]  
                        step.output = f"👉 Decision: {agent_name.upper()}\n💭 Logic: {reasoning}"

                # -- HANDLER: AGENTS --
                elif "final_output" in state:
                    final_response = state["final_output"]
                    
                    async with cl.Step(name=f"Agent: {node_name}", type="llm") as step:
                        step.output = final_response

        parent_step.output = "Cycle Complete."

    # 4. Store for Feedback Loop
    user_session["last_question"] = message.content 
    user_session["last_output"] = final_response

    # 5. Show Result with Actions
    actions = [
        cl.Action(name="good", payload={"value": "good"}, label="✅ Good"),
        cl.Action(name="bad", payload={"value": "bad"}, label="❌ Bad (Fix it)")
    ]
    
    if final_response:
        await cl.Message(content=final_response, actions=actions).send()
    else:
        await cl.Message(content="⚠️ Error: No agent produced an output.", actions=actions).send()

# --- FEEDBACK HANDLERS ---

@cl.action_callback("good")
async def on_good(action: cl.Action):
    count = save_memory(user_session["last_question"], user_session["last_output"])
    await cl.Message(content=f"💾 **Reinforced!** Logic saved. (Total Memories: {count})").send()

@cl.action_callback("bad")
async def on_bad(action: cl.Action):
    res = await cl.AskUserMessage(content="My apologies! 😔 **What did I get wrong?** (Just give me a hint, and I'll fix the answer)").send()
    
    if res:
        feedback = res['output']
        await cl.Message(content="🔧 **Repairing...** Applying your feedback...").send()
        
        repair_module = dspy.Predict(Repair)
        pred = repair_module(original_draft=user_session["last_output"], user_feedback=feedback)
        fixed_answer = pred.corrected_draft
        
        count = save_memory(user_session["last_question"], fixed_answer)
        
        await cl.Message(content=f"🎓 **Learned!** I have saved this corrected version for next time:\n\n> {fixed_answer}").send()