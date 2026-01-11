import json
from utils.openrouter_client import call_openrouter

class Orchestrator:
    def __init__(self):
        self.model = "xiaomi/mimo-v2-flash:free"

    def route(self, user_input, chat_history=""):
        print(f"🤔 MiMo is thinking about: {user_input[:50]}...")
        
        system_prompt = """
        You are the Chief Architect (Router) of a software development system.
        
        Your Goal: Analyze the user's request and route it to the correct specialized agent.
        
        AVAILABLE AGENTS:
        1. 'ingestion': Use ONLY if the user provides a large block of text, documentation, logs, or context history to remember.
        2. 'coder': Use if the user wants to write code, refactor, fix bugs, or design software architecture.
        3. 'auditor': Use if the user specifically asks to review, critique, or verify existing logic/code.
        4. 'general': For greetings, simple questions, or small talk.
        
        OUTPUT FORMAT:
        You must return valid JSON only. No markdown.
        {
            "next_agent": "ingestion" | "coder" | "auditor" | "general",
            "reasoning": "Brief explanation of why you chose this agent."
        }
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"History: {chat_history}\n\nCurrent Request: {user_input}"}
        ]

        response = call_openrouter(self.model, messages, enable_reasoning=True)
        
        if not response:
            return "general", "API Error, defaulting to general."

        content = response['choices'][0]['message']['content']
        
        try:
            cleaned = content.replace("```json", "").replace("```", "").strip()
            decision = json.loads(cleaned)
            
            agent = decision.get("next_agent", "general")
            reason = decision.get("reasoning", "No reasoning provided.")
            
            print(f"👉 MiMo Decided: {agent.upper()}")
            print(f"   (Internal Thought: {reason})")
            
            return agent, reason
            
        except json.JSONDecodeError:
            print(f"⚠️ JSON Parse Error. Raw content: {content}")
            return "general", "Failed to parse router decision."