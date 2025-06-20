import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDINGS_PATH = os.path.join("json", "project_embeddings.json")
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.2

model = SentenceTransformer(MODEL_NAME)

def compute_embedding(messages):
    if isinstance(messages, str):
        messages = [messages]
    return model.encode([" ".join(messages)], normalize_embeddings=True)[0].tolist()

def save_project_embedding(folder, messages):
    embedding = compute_embedding(messages)
    if os.path.exists(EMBEDDINGS_PATH):
        with open(EMBEDDINGS_PATH, "r") as f:
            data = json.load(f)
    else:
        data = {}
    folder_name = os.path.basename(os.path.normpath(folder))
    data[folder_name] = {
        "embedding": embedding,
        "messages": messages,
        "folder": folder
    }
    with open(EMBEDDINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_all_project_embeddings():
    if not os.path.exists(EMBEDDINGS_PATH):
        return {}
    with open(EMBEDDINGS_PATH, "r") as f:
        return json.load(f)

def find_closest_project(messages):
    new_emb = np.array(compute_embedding(messages)).reshape(1, -1)
    all_projects = load_all_project_embeddings()
    if not all_projects:
        return None, 0.0
    best_project = None
    best_score = -1
    print("[DEBUG] Embedding similarity scores:")
    for name, info in all_projects.items():
        emb = np.array(info["embedding"]).reshape(1, -1)
        score = cosine_similarity(new_emb, emb)[0][0]
        print(f"  - {name}: {score:.4f}")
        if score > best_score:
            best_score = score
            best_project = (name, info["folder"])
    if best_score >= SIMILARITY_THRESHOLD:
        return best_project[1], best_score
    return None, best_score 