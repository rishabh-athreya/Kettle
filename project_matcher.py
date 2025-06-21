import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDINGS_PATH = os.path.join("json", "project_embeddings.json")
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.2

model = SentenceTransformer(MODEL_NAME)

def load_codebase(project_folder):
    """Load existing codebase from a project folder for LLM input"""
    codebase = {}
    
    if not os.path.exists(project_folder):
        return codebase
    
    # Common file extensions to include
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.json', '.yaml', '.yml', '.md', '.txt'}
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'env', '.env', 'dist', 'build', '.pytest_cache'}
    
    for root, dirs, files in os.walk(project_folder):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_folder)
            
            # Only include code files and important config files
            if any(file.endswith(ext) for ext in code_extensions) or file in {'requirements.txt', 'package.json', 'Dockerfile', 'docker-compose.yml'}:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    codebase[rel_path] = content
                except Exception as e:
                    print(f"Warning: Could not read {rel_path}: {e}")
    
    return codebase

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

def main():
    # Read messages from json/messages.json
    try:
        with open("json/messages.json", "r") as f:
            data = json.load(f)
            messages = [msg.get("text", "") for msg in data.get("messages", [])]
    except FileNotFoundError:
        print("Warning: json/messages.json not found.")
        return None, 0.0
    
    print(f"🔍 Looking for similar projects for: {messages}")
    closest_project, similarity = find_closest_project(messages)
    
    if closest_project:
        print(f"✅ Found similar project: {closest_project} (similarity: {similarity:.4f})")
        return closest_project, similarity
    else:
        print(f"❌ No similar project found (best similarity: {similarity:.4f})")
        return None, similarity

if __name__ == "__main__":
    main() 