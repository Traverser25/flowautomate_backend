import os
from typing import Dict, List
from pinecone import Pinecone
from groq import Groq
# import asyncio 
from dotenv import load_dotenv
load_dotenv() 

# ---------------- Pinecone setup ----------------
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "automateflow")

pc = Pinecone(api_key=PINECONE_API_KEY)
dense_index = pc.Index(PINECONE_INDEX_NAME)

# ---------------- Groq setup ----------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

async def search_query_service(query: str, top_k_paragraphs: int = 5, top_k_tables: int = 10) -> Dict:
    """
    RAG flow:
    1. Search Pinecone index for top_k relevant paragraphs
    2. Search Pinecone index for top_k relevant tables
    3. Send retrieved documents and the query to Groq LLM
    4. LLM infers which source suits better
    5. Return the LLM result
    """

    # Search paragraphs
    para_response = dense_index.search(
        namespace="pdf-paragraphs",
        query={"top_k": top_k_paragraphs, "inputs": {"text": query}}
    )
    paragraphs = [hit['fields']['chunk_text'] for hit in para_response['result']['hits']]

    # Search tables
    table_response = dense_index.search(
        namespace="pdf-tables",
        query={"top_k": top_k_tables, "inputs": {"text": query}}
    )
    tables = [hit['fields']['chunk_text'] for hit in table_response['result']['hits']]

    # Construct detailed prompt
    prompt = (
        "You are an expert assistant. Carefully use the context documents provided below to answer the user's query. "
        "Do not fabricate information. If the answer is not contained in the context, respond with 'Information not available'.\n\n"
        f"Paragraphs:\n{paragraphs}\n\n"
        f"Tables:\n{tables}\n\n"
        f"User query:\n{query}\n\n"
        "Infer which source (paragraphs or tables) is most relevant and answer clearly and concisely "
        "based only on the provided context."
    )

    # Call Groq LLM using SDK
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )

    llm_result = completion.choices[0].message.content

    return {"result": llm_result}


# async def main():
#     query = ""
#     result = await search_users_service(query)
#     print(result["result"])

# asyncio.run(main())