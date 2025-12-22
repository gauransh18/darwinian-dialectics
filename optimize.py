import dspy
from dspy.teleprompt import BootstrapFewShot
from main import GenerateAnswer

lm = dspy.LM('ollama_chat/llama3', api_base='http://localhost:11434', api_key='')
dspy.configure(lm=lm)

trainset = [
    dspy.Example(
        question="I have 3 apples. I eat 2. Buy 5. Give 3. How many?", 
        answer="I start with 3. Eat 2 leaves 1. Buy 5 makes 6. Give 3 leaves 3. Answer: 3"
    ).with_inputs('question'),
    
    dspy.Example(
        question="Sally has 3 brothers. Each brother has 2 sisters. How many sisters does Sally have?", 
        answer="The brothers are siblings. They share the same sisters. Sally is one sister. If there is another, they have 2. Assuming Sally is the only girl mentioned, the answer is 1."
    ).with_inputs('question'),

    dspy.Example(
        question="If you pass the person in 2nd place in a race, what place are you in?", 
        answer="If I pass the 2nd person, I take their spot. I am now in 2nd place."
    ).with_inputs('question'),
]

def validate_answer(example, pred, trace=None):
    return example.answer.lower() in pred.answer.lower()


print("Starting Evolution (TIME TAKING 2-3 minutes)")

teleprompter = BootstrapFewShot(metric=validate_answer, max_bootstrapped_demos=4, max_labeled_demos=4)

compiled_generator = teleprompter.compile(dspy.Predict(GenerateAnswer), trainset=trainset)

print("EVOLUTION COMPLETE :)")

q = "The date before yesterday was three days after Saturday. WHat day is it today?"

pred = compiled_generator(question=q)

print(f"Question: {q}")
print(f"Evolved Answer: {pred.answer}")

compiled_generator.save("evolved_agent.json")
print("savved evolved logic to 'evolvled_agent.json' :)")
print("end end")