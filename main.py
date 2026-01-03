from litellm import api_base
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
import re
import dspy
import os

lm = dspy.LM('ollama_chat/llama3', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)


class GenerateAnswer(dspy.Signature):
    question = dspy.InputField()
    previous_draft = dspy.InputField(desc = "The answer from the last attempt", optional=True)
    critique = dspy.InputField(desc="Feedback from the critic", optional=True)
    answer = dspy.OutputField(desc="The refined answer with clear math steps")


class CritiqueAnswer(dspy.Signature):
    question = dspy.InputField()
    draft = dspy.InputField()
    critique_text = dspy.OutputField(desc="Detailed feedback on what is wrong")
    score = dspy.OutputField(desc="The score value (e.g., 5)")
    

class AgentState(TypedDict):
    question: str
    draft: str
    critique: str
    revision_number: int
    score: int


def generator_node(state: AgentState):
    print(f"Generator (Revision {state['revision_number']})")

    generate_module = dspy.Predict(GenerateAnswer)

    #loading the evolved brain (if exists)
    if os.path.exists("evolved_agent.json"):
        generate_module.load("evolved_agent.json")
        print("Loaded Evolveed brain json file :)")

    pred = generate_module(
        question=state['question'],
        previous_draft=state.get('draft') or "",
        critique=state.get('critique') or ""
    )

    print(f"Generated length: {len(pred.answer)} chars")

    return {
        "draft": pred.answer,
        "revision_number": state['revision_number'] + 1
    }


def critic_node(state: AgentState):
    print("Critic")

    critic_module = dspy.Predict(CritiqueAnswer)

    pred = critic_module(
        question=state['question'],
        draft=state['draft']
    )

    score = 0

    try: 
        match = re.search(r"\d+", pred.score)
        if match: 
            score = int(match.group(0))
    except:
        print(f"Raw Score Output: {pred.score}")
        score = 0

    
    print(f"Critique: {pred.critique_text[:50]}...")
    print(f"Score: {score}/10")

    return {
        "critique": pred.critique_text,
        "score": score
    }



def should_continue(state: AgentState):
    current_score = state.get('score', 0)
    rev = state.get('revision_number', 0)

    if current_score >= 8:
        print(f"DECISION: GOOD SCORE ({current_score}). Ending Early. ---")
        return END
    
    if rev > 3:
        print("DECISION: Too many revisions. Ending. ---")
        return END
    
    print(f"DECISION: Score {current_score} is too low. Retrying ---")
    return "critic"

builder = StateGraph(AgentState)
builder.add_node("generator", generator_node)
builder.add_node("critic", critic_node)
builder.set_entry_point("generator")

builder.add_edge("generator", "critic")
builder.add_conditional_edges("critic", should_continue, {
    "critic": "generator",
    END: END
})

graph = builder.compile()

if __name__ == "__main__":

   
    initial_state = {
        "question": "I have 3 apples. I eat 2. Then I buy 5 more. I give 3 to my friend. How many apples do I have?",
        "draft": None,
        "critique": None,
        "revision_number": 0,
        "score": 0
    }

    print("Starting Darwinian Dialectics (DSPy Powered)...")
    final_state = initial_state.copy()

    for event in graph.stream(initial_state, recursion_limit=15):
        for key, value in event.items():
            final_state.update(value)

    print("\n--- FINAL OUTPUT ---")
    print(f"Final Score: {final_state.get('score')}/10")
    print(f"Final Answer: \n{final_state.get('draft')}")