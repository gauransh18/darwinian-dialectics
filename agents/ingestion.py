from utils.openrouter_client import call_openrouter

class IngestionAgent:
    def __init__(self):
        # Gemini 2.0 Flash - The Context King (1M Token Window)
        self.model = "google/gemini-2.0-flash-exp:free"

    def process(self, user_input):
        print("📚 Gemini is reading...")
        
        system_prompt = """
        You are the 'Deep Context' agent. 
        Your job is to ingest information (logs, docs, history) and summarize the critical intent.
        Do not just repeat the text; analyze the *intent* and *constraints*.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = call_openrouter(self.model, messages)
        
        if response:
            return response['choices'][0]['message']['content']
        return "Error processing context."