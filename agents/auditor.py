from utils.openrouter_client import call_openrouter

class AuditorAgent:
    def __init__(self, model=None, api_key=None):
        self.model = model or "mistralai/devstral-2512:free"
        self.api_key = api_key

    def audit(self, content, context="user_input"):
        """
        context: 'user_input' (Auditing what the user sent) OR 'generated_code' (Auditing what Coder wrote)
        """
        print(f"🧐 Auditor is reviewing ({context})...")
        
        if context == "generated_code":
            system_prompt = """
            You are a Senior QA Engineer & Security Auditor.
            A junior developer (AI) has just generated the code below.
            
            YOUR TASK:
            1. Verify the code actually solves the user's request.
            2. Check for security holes (SQLi, XSS, etc.).
            3. If GOOD: Return the code as-is with a "✅ Verified" badge.
            4. If BAD: Rewrite the code with fixes and explain the error.
            """
        else:
            # Default: Auditing user input
            system_prompt = """
            You are a Lead Security Researcher.
            Review the user's provided code/text for logical fallacies, security risks, or bugs.
            Output: "✅ PASS" or "❌ FAIL" with a fix.
            """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTENT TO AUDIT:\n\n{content}"}
        ]
        
        response = call_openrouter(self.model, messages, api_key=self.api_key)
        
        if response:
            return response['choices'][0]['message']['content']
        return "⚠️ Error: Auditor failed to review."