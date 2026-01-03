import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path='./chroma_db')

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = client.get_or_create_collection(
    name="agent_memory",
    embedding_function=sentence_transformer_ef
)

def save_memory(question, answer):
    collection.upsert(
        documents=[question], 
        metadatas=[{"answer": answer}],
        ids=[question]
    )

    return collection.count()

def get_relevant_examples(query_text, k=2):
    results = collection.query(
        query_texts=[query_text],
        n_results=k
    )

    if not results['documents'][0]:
        return ""
    
    formatted_memories = []

    for i in range(len(results['documents'][0])):
        past_question = results['documents'][0][i]
        past_answer = results['metadatas'][0][i]['answer']

        formatted_memories.append(f"- Context: When asked '{past_question}', the answer was: '{past_answer}'")
        
    return "\n".join(formatted_memories)