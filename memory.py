import json
import os

MEMORY_FILE = "user_memory.json"

def load_memory():
    """Loads the user's training data from disk."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# THIS was likely the broken function. It needs 'question' and 'answer' arguments.
def save_memory(question, answer):
    """Teaches the AI a new lesson. Returns total memories count."""
    memory = load_memory()
    
    # Simple check to avoid exact duplicates
    for item in memory:
        if item["question"] == question and item["answer"] == answer:
            return len(memory)
            
    memory.append({"question": question, "answer": answer})
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)
    return len(memory)

def get_relevant_examples(current_question, k=2):
    """
    Retrieves the most relevant past lessons.
    """
    memory = load_memory()
    if not memory:
        return ""
    
    # Get last k examples
    selected = memory[-k:] 
    
    formatted = "\n".join([
        f"- Q: {m['question']}\n  A: {m['answer']}"
        for m in selected
    ])
    return formatted