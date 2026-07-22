import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key= os.getenv("GROQ_API_KEY")

)

def generate_answer(question , context):
    prompt = f"""
You are a helpful AI assistant.

If the PDF context contains the answer, use it.

If the PDF context is empty or doesn't contain the answer,
answer using your own knowledge.
If the user asks in Hindi, answer in only Hindi.
If the user asks in English, answer in only English.
pdf Context:
            

{context}

Question:
{question}

"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
            "role":"user",
            "content":prompt
            }
        ], temperature=0.3
    )

    return response.choices[0].message.content