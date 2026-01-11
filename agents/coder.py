from utils.openrouter_client import call_openrouter

class CoderAgent:
    def __init__(self, model=None, api_key=None):
        self.model = model or "deepseek/deepseek-v3.2"
        self.api_key = api_key

    def write_code(self, user_request, plan):
        print(f"💻 DeepSeek is Engineering based on Plan...")
        
        system_prompt = f"""
        You are an Elite Software Engineer (Devstral Profile).
        
        You have received a TECHNICAL BLUEPRINT from the Chief Architect.
        
        ARCHITECT'S PLAN:
        {plan}
        
        YOUR TASK:
        Execute this plan perfectly. Write clean, efficient code.
        - Output ONLY code inside markdown blocks (```python ... ```).
        - Follow the Architect's library recommendations.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Request: {user_request}"}
        ]
        
        response = call_openrouter(self.model, messages, api_key=self.api_key)
        
        if response:
            return response['choices'][0]['message']['content']
        return "⚠️ Error: Coder Agent failed."