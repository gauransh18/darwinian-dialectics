# File: agents/coder.py
from utils.openrouter_client import call_openrouter

class CoderAgent:
    def __init__(self):
        self.model = "deepseek/deepseek-v3.2" 

    def write_code(self, user_request):
        print(f"💻 DeepSeek is engineering: {user_request[:50]}...")
        
        system_prompt = """
        You are an Elite Software Engineer (Devstral Profile).
        
        YOUR TASK:
        Write clean, efficient, and well-commented code based on the user's request.
        
        GUIDELINES:
        - Output ONLY code inside markdown blocks (```python ... ```).
        - Provide a brief explanation *after* the code.
        - If the request is ambiguous, make a reasonable architectural assumption and state it.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request}
        ]
        
        response = call_openrouter(self.model, messages)
        
        if response:
            return response['choices'][0]['message']['content']
        return "⚠️ Error: Coder Agent failed to generate a response."