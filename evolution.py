import dspy


lm = dspy.LM('ollama_chat/llama3', api_base='http://localhost:11434', api_key='')

dspy.configure(lm=lm)

class GenerateAnswer(dspy.Signature):
    question = dspy.InputField()
    answer = dspy.OutputField(desc="The reasoned answer with math steps")




generator = dspy.Predict(GenerateAnswer)

print("Asking DSPy")
response = generator(question="I have 3 apples. Eat 2. Buy 5. Give 3. How many?")

print("DSPy output: ")
print(response.answer)

