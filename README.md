# Darwinian Dialectics V2: Multi-Model Neural Operating System

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Status](https://img.shields.io/badge/status-active-success.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![LangGraph](https://img.shields.io/badge/LangGraph-Powered-orange.svg)

> **"Survival of the Fittest Code."**
> A self-correcting, router-based AI architecture that evolves solution quality by dispatching tasks to specialized "Expert Models" rather than relying on a single generalist LLM.

---

## 🧬 The Evolution (Phase 4: Specialization)

Most AI agents are monolithic—they ask one model to plan, code, and review. This leads to mediocrity and hallucinations.

**Darwinian Dialectics V2** implements a **"Council of Experts"** architecture. Instead of a single brain, a central "Architect" analyzes user intent and routes tasks to the absolute best model for that specific cognitive domain.

### The Council of Experts (Jan 2026 Stack)

| Role | Agent Name | Model Used | Specialization |
| :--- | :--- | :--- | :--- |
| 🧠 **The Architect** | `Orchestrator` | **Xiaomi MiMo-V2** | High-level reasoning, planning, and intent classification. Does not write code; writes the *blueprint*. |
| 💻 **The Engineer** | `Coder` | **DeepSeek-V3** | SOTA Code generation. Follows the Architect's blueprint to implement production-ready modules. |
| 🧐 **The Auditor** | `Critic` | **Mistral Devstral** | Architecture-level analysis. Reviews code for security risks, SOLID principles, and logic flaws. |
| 📚 **The Librarian** | `Ingestion` | **Gemini 2.0 Flash** | 1M+ Token Context Window. Ingests massive logs, documentation, and repo history in a single pass. |

---

## 🏗️ Architecture

The system uses **LangGraph** to manage the state and control flow between these independent "brains."

1.  **Input:** User provides a request (e.g., "Build a scraper").
2.  **Router (MiMo):** Analyzes intent. Decides this is a *Coding Task*. Generates a technical **Blueprint** (JSON).
3.  **Engineer (DeepSeek):** Receives the Blueprint. Generates the Python implementation.
4.  **Human-in-the-Loop:** User sees the draft and clicks **"🔍 Verify"**.
5.  **Auditor (Devstral):** Reviews the draft against security standards and outputs a pass/fail report.
6.  **Memory (ChromaDB):** Successful patterns are stored in Vector Memory for future reinforcement.

---

## 🚀 Key Features

* **Architectural Routing:** The system doesn't just guess; it plans. MiMo generates a multi-step execution plan before a single line of code is written.
* **Dynamic Compute Allocation:** Lightweight requests go to fast models; heavy context tasks are automatically diverted to Gemini 2.0 (1M context).
* **Dual-Mode Auditing:** The Auditor can review *generated code* (Pipeline Mode) or *user logic* (Direct Mode).
* **Darwinian Memory:** A "Lifelong Learning" layer using RAG. If you correct the agent once, it saves the correction to ChromaDB and never makes that mistake again.

---

## 🛠️ Installation & Usage

### Prerequisites
* Python 3.10+
* An [OpenRouter](https://openrouter.ai/) API Key

### Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/darwinian-dialectics.git](https://github.com/yourusername/darwinian-dialectics.git)
    cd darwinian-dialectics
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```env
    OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
    ```

4.  **Run the Neural OS**
    ```bash
    chainlit run app.py -w
    ```

---

## 🧪 Example Workflow

**User:** *"Write a Python script to scrape a website using BeautifulSoup."*

> **🧠 [Architect] MiMo:** "Intent detected: Coding. Plan: Use `requests` for fetching and `bs4` for parsing. Handle HTTP errors. Route to -> Coder."
>
> **💻 [Engineer] DeepSeek:** *Generates a robust, commented Python script with error handling.*
>
> **User:** *Clicks [🔍 Verify]*
>
> **🧐 [Auditor] Devstral:** "✅ VERIFIED. Code handles exceptions correctly and uses User-Agent headers to avoid blocking."

---

## 📜 History

* **V1 (Dec 2025):** Single-loop agent using Llama-3 and DSPy for prompt optimization.
* **V2 (Jan 2026):** "Council of Experts" architecture. Shift to LangGraph + Multi-Model Routing (MiMo/DeepSeek/Gemini/Devstral).

## 📄 License

MIT License. Free to fork and evolve.