import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

def search_pdf(query , k=3):
    index = faiss.read_index("faiss_index/index.faiss")

    with open("faiss_index/chunks.pkl" ,"rb") as f :
        chunks =pickle.load(f)

    query_embedding =    model.encode([query]).astype("float32")
    distances ,indices = index.search(query_embedding , k)
    results = []

    for i in indices[0]:
        results.append(chunks[i].page_content)

    return "\n\n".join(results)