from utils.openrouter_client import call_openrouter


class GeneralAgent:
    def __init__(self, model=None, api_key=None):
        self.model = model or "arcee-ai/trinity-large-preview:free"
        self.api_key = api_key

    def chat(self, user_input, chat_history=""):
        system_prompt = """
        You are a helpful, friendly assistant.
        Respond directly to the user. Keep it concise unless asked for detail.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"History: {chat_history}\n\nUser: {user_input}"}
        ]

        response = call_openrouter(self.model, messages, api_key=self.api_key)
        if response:
            return response["choices"][0]["message"]["content"]
        return "👋 Hi! How can I help?"
