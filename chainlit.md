# 🧬 Darwinian Dialectics v2

**A self-correcting, lifelong-learning AI agent.**

This is not a standard chatbot. It is a **Recursive Reasoning Engine** that thinks, critiques itself, and learns from you in real-time.

---

### 🧠 How it Works

1.  **The Debate Loop (LangGraph)**
    * **Generator:** Drafts an initial answer.
    * **Critic:** Reviews the answer for logic, tone, and accuracy (Score 0-10).
    * **Manager:** If the score is low (< 8/10), it forces the Generator to revise the answer.

2.  **Lifelong Learning (Vector Memory)**
    * The agent has a persistent **ChromaDB** brain.
    * It remembers past corrections.
    * **Semantic Search:** It understands concepts (e.g., "Lunar" matches "Moon") to recall relevant lessons.

---

### 🎮 How to Use

1.  **Ask a Question:** Try something tricky or creative.
2.  **Watch it Think:** Expand the "Thinking Process" to see the Agent and Critic arguing.
3.  **Teach It:**
    * ✅ **Good:** Click this to reinforce the logic.
    * ❌ **Bad (Teach Me):** Click this to provide the *correct* answer. The agent will embed this lesson and use it forever.

---

### 🛠️ Tech Stack
* **Orchestrator:** LangGraph
* **Optimization:** DSPy
* **Memory:** ChromaDB + Sentence-Transformers
* **LLM:** Llama-3 (Local)