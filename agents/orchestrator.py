import json
import re
from utils.openrouter_client import call_openrouter

class Orchestrator:
    def __init__(self, model=None, api_key=None):
        self.model = model or "z-ai/glm-4.5-air:free"
        self.api_key = api_key

    def route(self, user_input, chat_history=""):
        print(f"🤔 Architect is routing: {user_input[:50]}...")
        
        system_prompt = """
        You are the Chief Technical Architect.
        
        YOUR GOAL:
        1. Analyze the user's request.
        2. Create a high-level technical plan (blueprint).
        3. Assign the task to the best specialist.

        AGENTS:
        - 'ingestion': For reading docs, logs, or huge context.
        - 'coder': For writing code, fixing bugs, or building apps.
        - 'auditor': For reviewing code logic/security.
        - 'general': For small talk.

        OUTPUT FORMAT (JSON ONLY):
        {
            "next_agent": "ingestion" | "coder" | "auditor" | "general",
            "reasoning": "Why you chose this agent.",
            "plan": "Step-by-step technical instructions for the agent. Be specific. If coding, suggest libraries and logic flow."
        }
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"History: {chat_history}\n\nCurrent Request: {user_input}"}
        ]

        # Enable reasoning to let the architect think through the architecture first
        response = call_openrouter(
            self.model,
            messages,
            enable_reasoning=True,
            api_key=self.api_key,
            response_format={"type": "json_object"},
            plugins=["response-healing"],
        )
        
        if not response:
            return "general", "Error", "No plan."

        content = response['choices'][0]['message']['content']
        
        try:
            cleaned = content.replace("```json", "").replace("```", "").strip()
            decision = json.loads(cleaned)
            
            agent = decision.get("next_agent", "general")
            reason = decision.get("reasoning", "No reasoning.")
            plan = decision.get("plan", "Proceed with standard execution.") # <--- NEW FIELD
            
            print(f"👉 Architect's Plan: {plan[:100]}...")
            return agent, reason, plan
            
        except json.JSONDecodeError:
            # Fallback: extract the first JSON object if the model wrapped it.
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    decision = json.loads(match.group(0))
                    agent = decision.get("next_agent", "general")
                    reason = decision.get("reasoning", "No reasoning.")
                    plan = decision.get("plan", "Proceed with standard execution.")
                    print(f"👉 Architect's Plan (extracted): {plan[:100]}...")
                    return agent, reason, plan
                except json.JSONDecodeError:
                    pass
            return "general", "JSON Error", "Failed to parse plan."
