import chainlit as cl
from main import builder  # Importing your existing Graph
from memory import save_memory, get_relevant_examples

# Global state to track the current conversation for "Teaching Mode"
user_session = {"last_question": None, "last_draft": None}

@cl.on_chat_start
async def start():
    await cl.Message(content="🧠 **Darwinian Agent Ready.**\nI learn from my mistakes. If I get something wrong, click 'Bad' to teach me.").send()

@cl.on_message
async def main(message: cl.Message):
    # 1. RETRIEVE MEMORY
    past_lessons = get_relevant_examples(message.content)
    
    # 2. AUGMENT PROMPT
    augmented_question = message.content
    if past_lessons:
        augmented_question += f"\n\n[IMPORTANT: Use these past lessons to guide your answer]\n{past_lessons}"
        # Send a quiet notification that memory was used
        await cl.Message(content=f"💡 *Recalled past lessons...*", author="System").send()

    # 3. PREPARE STATE
    initial_state = {
        "question": augmented_question,
        "revision_number": 0,
        "max_revisions": 2, 
        "draft": "",
        "critique": ""
    }

    # 4. RUN LANGGRAPH (With Clean UI)
    final_draft = ""
    
    # Create a parent step to group the "Thinking" logs
    # We remove 'collapsed=True' to prevent the crash. 
    # The parent step will naturally contain the noise.
    async with cl.Step(name="Thinking Process...", type="run") as parent_step:
        
        async for event in builder.compile().astream(initial_state, limit={"recursion_limit": 15}):
            
            # Visualize Generator
            if "generator" in event:
                state = event["generator"]
                draft = state["draft"]
                rev = state["revision_number"]
                final_draft = draft 
                
                async with cl.Step(name=f"Generator (Rev {rev})", type="run") as step:
                    step.output = draft

            # Visualize Critic
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

    # 6. SHOW RESULT WITH ACTIONS
    actions = [
        cl.Action(name="good", payload={"value": "good"}, label="✅ Good"),
        cl.Action(name="bad", payload={"value": "bad"}, label="❌ Bad (Teach Me)")
    ]
    
    # This is the "Direct Response" you wanted
    await cl.Message(content=f"{final_draft}", actions=actions).send()

@cl.action_callback("good")
async def on_good(action: cl.Action):
    count = save_memory(user_session["last_question"], user_session["last_draft"])
    await cl.Message(content=f"💾 **Reinforced!** Logic saved. (Total Memories: {count})").send()

@cl.action_callback("bad")
async def on_bad(action: cl.Action):
    res = await cl.AskUserMessage(content="I'm sorry! 😔 Please type the **Correct Answer** so I can learn.").send()
    if res:
        count = save_memory(user_session["last_question"], res['output'])
        await cl.Message(content=f"🎓 **Learned!** Brain updated. (Total Memories: {count})").send()