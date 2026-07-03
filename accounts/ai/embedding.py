# embedding.py

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # loads once

def get_embedding(text):
    return model.encode(text)