import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np

SUPPORTED_EXTS = [".py", ".js", ".ts", ".html", ".css", ".md", ".txt"]
CHUNK_SIZE = 20  # lines per chunk
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class EmbeddingIndex:
    def __init__(self, project_folder, index_path=None):
        self.project_folder = project_folder
        self.index_path = index_path or os.path.join(project_folder, ".kettle_index.json")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = []
        if os.path.exists(self.index_path):
            self.load()

    def build(self):
        self.index = []
        for root, _, files in os.walk(self.project_folder):
            for fname in files:
                if any(fname.endswith(ext) for ext in SUPPORTED_EXTS):
                    self._index_file(os.path.join(root, fname))
        self.save()

    def _index_file(self, filepath):
        rel_path = os.path.relpath(filepath, self.project_folder)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for i in range(0, len(lines), CHUNK_SIZE):
            chunk_lines = lines[i:i+CHUNK_SIZE]
            chunk_text = "".join(chunk_lines)
            if chunk_text.strip():
                embedding = self.model.encode(chunk_text)
                self.index.append({
                    "file": rel_path,
                    "start": i+1,
                    "end": i+len(chunk_lines),
                    "text": chunk_text,
                    "embedding": embedding.tolist()
                })

    def save(self):
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)

    def load(self):
        with open(self.index_path, "r") as f:
            self.index = json.load(f)

    def query(self, query_text, top_k=5):
        query_emb = self.model.encode(query_text)
        scores = []
        for chunk in self.index:
            emb = np.array(chunk["embedding"])
            sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
            scores.append(sim)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [self.index[i] for i in top_indices]

# Example usage:
# idx = EmbeddingIndex("/path/to/project")
# idx.build()
# results = idx.query("add a logs feature to the tic tac toe game")
# for r in results:
#     print(r["file"], r["start"], r["end"], r["text"]) 