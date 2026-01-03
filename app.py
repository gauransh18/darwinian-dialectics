import chainlit as cl
from main import builder  # Importing your existing Graph
from vector_memory import save_memory, get_relevant_examples
import dspy

# --- GLOBAL STATE ---
user_session = {"last_question": None, "last_draft": None}

# --- REPAIR MODULE (New!) ---
# This allows the AI to fix itself based on your hint
class Repair(dspy.Signature):
    """Rewrite the draft based on the user's feedback/correction."""
    original_draft = dspy.InputField()
    user_feedback = dspy.InputField()
    corrected_draft = dspy.OutputField(desc="The corrected text, ready to be saved as the ground truth.")

@cl.on_chat_start
async def start():
    await cl.Message(content="🧠 **Darwinian Agent Ready.**\nI learn from my mistakes. If I'm wrong, just give me a hint!").send()

@cl.on_message
async def main(message: cl.Message):
    # 1. RETRIEVE MEMORY
    past_lessons = get_relevant_examples(message.content)
    
    # 2. AUGMENT PROMPT
    augmented_question = message.content
    if past_lessons:
        augmented_question += f"\n\n[IMPORTANT: Use these past lessons to guide your answer]\n{past_lessons}"
        await cl.Message(content=f"💡 *Recalled past lessons...*", author="System").send()

    # 3. PREPARE STATE
    initial_state = {
        "question": augmented_question,
        "revision_number": 0,
        "max_revisions": 2, 
        "draft": "",
        "critique": ""
    }

    # 4. RUN LANGGRAPH
    final_draft = ""
    async with cl.Step(name="Thinking Process...", type="run") as parent_step:
        async for event in builder.compile().astream(initial_state, limit={"recursion_limit": 15}):
            
            if "generator" in event:
                state = event["generator"]
                draft = state["draft"]
                rev = state["revision_number"]
                final_draft = draft 
                async with cl.Step(name=f"Generator (Rev {rev})", type="run") as step:
                    step.output = draft

            elif "critic" in event:
                state = event["critic"]
                score = state["score"]
                icon = "✅" if score >= 8 else "❌"
                async with cl.Step(name=f"Critic (Score: {score}) {icon}", type="tool") as step:
                    step.output = state["critique"]
        parent_step.output = "Done."

    # 5. SAVE CONTEXT
    user_session["last_question"] = message.content 
    user_session["last_draft"] = final_draft

    # 6. SHOW RESULT
    actions = [
        cl.Action(name="good", payload={"value": "good"}, label="✅ Good"),
        cl.Action(name="bad", payload={"value": "bad"}, label="❌ Bad (Fix it)")
    ]
    await cl.Message(content=f"{final_draft}", actions=actions).send()

@cl.action_callback("good")
async def on_good(action: cl.Action):
    count = save_memory(user_session["last_question"], user_session["last_draft"])
    await cl.Message(content=f"💾 **Reinforced!** Logic saved. (Total Memories: {count})").send()

@cl.action_callback("bad")
async def on_bad(action: cl.Action):
    # 1. Ask for the hint (Low effort for user)
    res = await cl.AskUserMessage(content="My apologies! 😔 **What did I get wrong?** (Just give me a hint, and I'll fix the answer)").send()
    
    if res:
        feedback = res['output']
        
        # 2. Run the Repair Module (The AI does the heavy lifting)
        await cl.Message(content="🔧 **Repairing...** Applying your feedback...").send()
        
        repair_module = dspy.Predict(Repair)
        pred = repair_module(original_draft=user_session["last_draft"], user_feedback=feedback)
        fixed_answer = pred.corrected_draft
        
        # 3. Save the FIXED version to memory
        count = save_memory(user_session["last_question"], fixed_answer)
        
        # 4. Show the user what we saved
        await cl.Message(content=f"🎓 **Learned!** I have saved this corrected version for next time:\n\n> {fixed_answer}").send()