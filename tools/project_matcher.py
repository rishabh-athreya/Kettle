import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tools.mongodb_config import get_embedding_manager, get_mongodb_config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Compute embedding for messages using the sentence transformer model"""
    if isinstance(messages, str):
        messages = [messages]
    return model.encode([" ".join(messages)], normalize_embeddings=True)[0].tolist()

def save_project_embedding(folder, messages):
    """Save project embedding to MongoDB"""
    try:
        folder_name = os.path.basename(os.path.normpath(folder))
        
        # Get the embedding manager
        embedding_manager = get_embedding_manager()
        
        # Compute embedding
        embedding = compute_embedding(messages)
        
        # Infer project type from folder path and messages
        project_type = _infer_project_type(folder, messages)
        
        # Save to MongoDB
        success = embedding_manager.save_project_embedding(
            project_name=folder_name,
            folder_path=folder,
            messages=messages,
            embedding=embedding,
            project_type=project_type,
            metadata={
                "source": "project_matcher",
                "model": MODEL_NAME,
                "similarity_threshold": SIMILARITY_THRESHOLD
            }
        )
        
        if success:
            logger.info(f"✅ Saved embedding for project: {folder_name}")
        else:
            logger.warning(f"⚠️  Failed to save embedding for project: {folder_name}")
            
    except Exception as e:
        logger.error(f"❌ Error saving project embedding: {e}")
        # Fallback to JSON if MongoDB fails
        _save_to_json_fallback(folder, messages)

def _infer_project_type(folder_path, messages):
    """Infer project type from folder path and messages"""
    folder_lower = folder_path.lower()
    messages_text = " ".join(messages).lower()
    
    if any(keyword in folder_lower or keyword in messages_text for keyword in ["game", "pygame", "flappy", "tic-tac-toe"]):
        return "game"
    elif any(keyword in folder_lower or keyword in messages_text for keyword in ["web", "flask", "app", "website", "api"]):
        return "web_app"
    elif any(keyword in folder_lower or keyword in messages_text for keyword in ["script", "automation", "tool"]):
        return "script"
    elif any(keyword in folder_lower or keyword in messages_text for keyword in ["research", "analysis", "report"]):
        return "research"
    else:
        return "unknown"

def _save_to_json_fallback(folder, messages):
    """Fallback to JSON storage if MongoDB fails"""
    try:
        folder_name = os.path.basename(os.path.normpath(folder))
        embeddings_path = os.path.join("json", "project_embeddings.json")
        
        if os.path.exists(embeddings_path):
            with open(embeddings_path, "r") as f:
                data = json.load(f)
        else:
            data = {}
        
        # Compute embedding
        embedding = compute_embedding(messages)
        
        # Update or create the project entry
        data[folder_name] = {
            "embedding": embedding,
            "messages": messages,
            "folder": folder
        }
        
        with open(embeddings_path, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"✅ Fallback: Saved to JSON for project: {folder_name}")
        
    except Exception as e:
        logger.error(f"❌ Fallback JSON save also failed: {e}")

def load_all_project_embeddings():
    """Load all project embeddings from MongoDB (fallback to JSON if needed)"""
    try:
        embedding_manager = get_embedding_manager()
        projects = embedding_manager.get_all_projects()
        
        # Convert to the old format for backward compatibility
        result = {}
        for project in projects:
            result[project["project_name"]] = {
                "embedding": project["embedding"],
                "messages": project["messages"],
                "folder": project["folder_path"]
            }
        return result
        
    except Exception as e:
        logger.warning(f"⚠️  MongoDB failed, falling back to JSON: {e}")
        # Fallback to JSON
        embeddings_path = os.path.join("json", "project_embeddings.json")
        if os.path.exists(embeddings_path):
            with open(embeddings_path, "r") as f:
                return json.load(f)
        return {}

def find_closest_project(messages):
    """Find the closest project using MongoDB with fallback to JSON"""
    try:
        # Try MongoDB first
        embedding_manager = get_embedding_manager()
        query_embedding = compute_embedding(messages)
        
        # Find similar projects
        similar_projects = embedding_manager.find_similar_projects(
            query_embedding=query_embedding,
            limit=10,
            similarity_threshold=SIMILARITY_THRESHOLD
        )
        
        if similar_projects:
            best_match = similar_projects[0]
            logger.info(f"✅ Found similar project via MongoDB: {best_match['project_name']} (similarity: {best_match['similarity']:.4f})")
            return best_match["folder_path"], best_match["similarity"]
        else:
            logger.info("📭 No similar projects found in MongoDB")
            return None, 0.0
            
    except Exception as e:
        logger.warning(f"⚠️  MongoDB search failed, falling back to JSON: {e}")
        # Fallback to JSON-based search
        return _find_closest_project_json_fallback(messages)

def _find_closest_project_json_fallback(messages):
    """Fallback method using JSON file for finding closest project"""
    try:
        new_emb = np.array(compute_embedding(messages)).reshape(1, -1)
        all_projects = load_all_project_embeddings()
        
        if not all_projects:
            logger.info("📭 No projects found in JSON fallback")
            return None, 0.0
            
        best_project = None
        best_score = -1
        
        logger.info("[DEBUG] Embedding similarity scores (JSON fallback):")
        for name, info in all_projects.items():
            emb = np.array(info["embedding"]).reshape(1, -1)
            score = cosine_similarity(new_emb, emb)[0][0]
            logger.info(f"  - {name}: {score:.4f}")
            if score > best_score:
                best_score = score
                best_project = (name, info["folder"])
                
        if best_score >= SIMILARITY_THRESHOLD:
            logger.info(f"✅ Found similar project via JSON: {best_project[0]} (similarity: {best_score:.4f})")
            return best_project[1], best_score
        else:
            logger.info(f"❌ No similar project found (best similarity: {best_score:.4f})")
            return None, best_score
            
    except Exception as e:
        logger.error(f"❌ JSON fallback also failed: {e}")
        return None, 0.0

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
