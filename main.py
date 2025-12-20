from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import re

# --- 1. DEFINE THE STATE ---
class AgentState(TypedDict):
    question: str
    draft: str
    critique: str
    revision_number: int
    score: int  #score so we can track quality

# --- 2. INITIALIZE MODEL ---
llm = ChatOllama(model="llama3", temperature=0)

# --- 3. DEFINE NODES ---

def generator_node(state: AgentState):
    print(f"\n--- GENERATOR (Revision {state['revision_number']}) ---")

    question = state['question']
    critique = state.get('critique')
    draft = state.get('draft')

    if not draft: 
        prompt = (f"Question: {question}\n"
                  "Answer cleanly and logically. You MUST show your step-by-step math. "
                  "State the final answer clearly at the end.")
    else:
        prompt = (f"Original question: '{question}'\n"
                  f"Previous draft: '{draft}'\n"
                  f"Critique: '{critique}'\n"
                  "Refine the answer. You MUST show the math steps to prove your answer is correct. "
                  "Do NOT use conversational filler. Just the math and the answer.")
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "draft": response.content,
        "revision_number": state['revision_number'] + 1
    }

def critic_node(state: AgentState):
    print("\n--- CRITIC ---")

    draft = state['draft']
    question = state['question']
    
    prompt = (f"Question: {question}\n"
              f"Draft Answer: {draft}\n"
              "Critique this answer. Be extremely harsh. If there is even a slight error, give a low score.\n"
              "If the reasoning is vague, give a score below 5.\n"
              "IMPORTANT: After your text critique, give a score from 1-10.\n"
              "Format your last line exactly like this: SCORE: 10")
              
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content
    
    # print(f"Critique text: {content}")
   
    score = 0
    match = re.search(r"SCORE:\D*(\d+)", content)
    if match:
        score = int(match.group(1))
        print(f"Detected Score: {score}/10")
    else:
        print("Could not find score in output.")

    return {
        "critique": content, 
        "score": score
    }
# --- 4. THE LOGIC (Learning Task 3) ---

def should_continue(state: AgentState):
    '''
    Decides if we stop or loop back based on SCORE or ITERATIONS
    '''
    current_score = state.get('score', 0)
    rev = state.get('revision_number', 0)

    # ### FIXED: The Logic
    if current_score >= 8:
        print(f"--- DECISION: Good score ({current_score}). Ending early. ---")
        return END
    
    if rev > 3:
        print("--- DECISION: Too many revisions. Ending. ---")
        return END
        
    print(f"--- DECISION: Score {current_score} is too low. Retrying... ---")
    return "critic" 


# --- 5. BUILD GRAPH ---

builder = StateGraph(AgentState)

builder.add_node("generator", generator_node)
builder.add_node("critic", critic_node)

builder.set_entry_point("generator")

# LOGIC FLOW:
# Generator -> Critic -> Decision -> (Loop back to Generator OR End)

builder.add_edge("generator", "critic") 
builder.add_conditional_edges("critic", should_continue, {
    "critic": "generator",
    END: END
})

graph = builder.compile()

# --- 6. RUN IT ---

initial_state = {
   "question": "I have 3 apples. I eat 2. Then I buy 5 more. I give 3 to my friend. How many apples do I have?",
    "draft": None,
    "critique": None,
    "revision_number": 0,
    "score": 0
}

print("Starting Darwinian Dialectics...")

final_state = initial_state.copy()

for event in graph.stream(initial_state, recursion_limit=10):
    # event is like {'generator': {'draft': '...'}} or {'critic': {'score': ...}}
    for key, value in event.items():
     
        final_state.update(value) 

print("\n--- FINAL OUTPUT ---")
print(f"Final Score: {final_state.get('score')}/10")
print(f"Final Answer: {final_state.get('draft')}")
print(f"Total Revisions: {final_state.get('revision_number')}")