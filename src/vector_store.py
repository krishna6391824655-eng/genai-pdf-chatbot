import faiss 
import numpy as np
import pickle
import os

def create_vector_store(chunks , embeddings):
    embeddings = np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    if not os.path.exists("faiss_index"):
        os.makedirs("faiss_index")

    faiss.write_index(index , "faiss_index/index.faiss")    
    with open("faiss_index/chunks.pkl" , "wb") as f:
        pickle.dump(chunks,f)
    return index      