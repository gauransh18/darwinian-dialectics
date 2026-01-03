# 🧬 Darwinian Dialectics

**A recursive, self-optimizing reasoning engine built with LangGraph and DSPy.**

Most AI agents are "static"—they use the same prompt forever. Darwinian Dialectics is different. It implements an **evolutionary loop** where agents debate, critique, and rewrite their own logic until they converge on a high-confidence answer.

### 🧠 The Architecture

1.  **The Debate Loop (LangGraph):**
    * **Generator:** Drafts an answer using Chain-of-Thought.
    * **Critic:** Grades the answer (1-10) and provides specific feedback.
    * **Manager:** If Score < 8, the draft is rejected and sent back for revision.

2.  **The Brain (DSPy):**
    * Replaced brittle prompt strings with **DSPy Signatures** (`question -> answer`).
    * Uses **MIPRO/BootstrapFewShot** to "compile" the agents, optimizing their instructions based on training examples.

### 📊 Results

| Architecture | Attempts to Solve | Final Score |
| :--- | :---: | :---: |
| **Manual F-Strings** | 4+ (Failed) | 2/10 |
| **DSPy Signatures** | 1 (Instant) | 9/10 |
| **Evolved + Loop** | 2 (Self-Corrected) | **10/10** |

### 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt

you also need Ollama or another llm for system to work.