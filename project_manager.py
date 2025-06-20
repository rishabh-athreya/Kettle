import os
import json
from datetime import datetime

PROJECTS_PATH = os.path.join("json", "projects.json")

class ProjectManager:
    def __init__(self, path=PROJECTS_PATH):
        self.path = path
        self.projects = self._load_projects()

    def _load_projects(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                return json.load(f)
        return []

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.projects, f, indent=2)

    def find_project(self, name_or_context):
        # Simple name or keyword match (case-insensitive)
        for project in self.projects:
            if name_or_context.lower() in project["project_name"].lower():
                return project
            if any(name_or_context.lower() in kw.lower() for kw in project.get("keywords", [])):
                return project
        return None

    def register_project(self, project_name, folder, keywords=None, embedding_index_path=None):
        now = datetime.utcnow().isoformat() + "Z"
        project = {
            "project_name": project_name,
            "folder": folder,
            "last_active": now,
            "keywords": keywords or [],
            "embedding_index_path": embedding_index_path or os.path.join(folder, ".kettle_index.json")
        }
        self.projects.append(project)
        self.save()
        return project

    def update_last_active(self, project_name):
        for project in self.projects:
            if project["project_name"] == project_name:
                project["last_active"] = datetime.utcnow().isoformat() + "Z"
                self.save()
                return

    def get_project_folder(self, project_name):
        for project in self.projects:
            if project["project_name"] == project_name:
                return project["folder"]
        return None

# Example usage:
# pm = ProjectManager()
# project = pm.find_project("tic tac toe")
# if not project:
#     pm.register_project("tic_tac_toe", "tic_tac_toe", keywords=["tic tac toe", "game"]) 