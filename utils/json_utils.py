#!/usr/bin/env python3
"""
Shared utility functions for JSON file management in KettleAI.
This module provides functions to clear and manage JSON files consistently.
"""

import os
import json

def clear_json_files():
    """Clear all .json and .txt files in json/ folder to their default states"""
    try:
        # Ensure json directory exists
        os.makedirs("json", exist_ok=True)
        
        # List all .json and .txt files in the json/ directory
        for filename in os.listdir("json"):
            filepath = os.path.join("json", filename)
            if not os.path.isfile(filepath):
                continue
            if filename == "media.json":
                # Reset media.json to default structure
                empty_media = {
                    "research_topics": {},
                    "summary": {
                        "total_research_topics": 0,
                        "total_media_resources": 0,
                        "last_updated": ""
                    }
                }
                with open(filepath, "w") as f:
                    json.dump(empty_media, f, indent=2)
            elif filename == "project_embeddings.json":
                # Clear project_embeddings.json to empty object
                with open(filepath, "w") as f:
                    f.write("{}")
            elif filename.endswith(".json"):
                # Clear all other .json files to empty object
                with open(filepath, "w") as f:
                    f.write("{}")
            elif filename.endswith(".txt"):
                # Clear all .txt files to empty string
                with open(filepath, "w") as f:
                    f.write("")
        # Remove session marker if exists
        session_marker = os.path.join("json", "session_active.txt")
        if os.path.exists(session_marker):
            os.remove(session_marker)
        print("🧹 Cleared all json/ files to default states")
        return True
    except Exception as e:
        print(f"❌ Error clearing json/ files: {e}")
        return False

def cleanup_project_embeddings():
    """Remove embeddings for projects that no longer exist in Work/ directory"""
    try:
        work_dir = os.path.expanduser("~/Desktop/Work")
        
        # Check if Work directory exists
        if not os.path.exists(work_dir):
            print("📁 Work directory doesn't exist, clearing all project embeddings")
            with open("json/project_embeddings.json", "w") as f:
                f.write("{}")
            # Also clear last_processed_ts.txt
            with open("json/last_processed_ts.txt", "w") as f:
                f.write("")
            return
        
        # Get list of existing project folders
        existing_projects = set()
        try:
            for item in os.listdir(work_dir):
                item_path = os.path.join(work_dir, item)
                if os.path.isdir(item_path):
                    existing_projects.add(item)
        except (OSError, PermissionError) as e:
            print(f"⚠️  Could not read Work directory: {e}")
            # If we can't read the directory, clear all embeddings
            with open("json/project_embeddings.json", "w") as f:
                f.write("{}")
            # Also clear last_processed_ts.txt
            with open("json/last_processed_ts.txt", "w") as f:
                f.write("")
            return
        
        print(f"📁 Found {len(existing_projects)} existing projects in Work/ directory")
        
        # If Work directory is empty, clear all embeddings
        if len(existing_projects) == 0:
            print("📁 Work directory is empty, clearing all project embeddings")
            with open("json/project_embeddings.json", "w") as f:
                f.write("{}")
            # Also clear last_processed_ts.txt
            with open("json/last_processed_ts.txt", "w") as f:
                f.write("")
            return
        
        # Load current embeddings
        if os.path.exists("json/project_embeddings.json"):
            try:
                with open("json/project_embeddings.json", "r") as f:
                    embeddings_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                embeddings_data = {}
        else:
            embeddings_data = {}
        
        # Filter embeddings to only include existing projects
        original_count = len(embeddings_data)
        cleaned_embeddings = {}
        
        for project_name, project_data in embeddings_data.items():
            if project_name in existing_projects:
                cleaned_embeddings[project_name] = project_data
            else:
                print(f"🗑️  Removing embedding for non-existent project: {project_name}")
        
        # Save cleaned embeddings
        with open("json/project_embeddings.json", "w") as f:
            json.dump(cleaned_embeddings, f, indent=2)
        
        removed_count = original_count - len(cleaned_embeddings)
        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} embeddings for non-existent projects")
        else:
            print("✅ All project embeddings are valid")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not cleanup project embeddings: {e}")
        # If cleanup fails, just clear the file
        try:
            with open("json/project_embeddings.json", "w") as f:
                f.write("{}")
        except:
            pass

def get_json_file_status():
    """Get the current status of all JSON files"""
    status = {}
    
    json_files = [
        "messages.json",
        "phased_tasks.json", 
        "last_processed_ts.txt",
        "last_task_processed_ts.txt",
        "task_dependencies.json",
        "dependency_matrix.json",
        "project_embeddings.json",
        "media.json",
        "session_active.txt"
    ]
    
    for filename in json_files:
        filepath = os.path.join("json", filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    content = f.read().strip()
                    if filename.endswith('.json'):
                        # Try to parse as JSON
                        try:
                            data = json.loads(content)
                            if isinstance(data, dict):
                                status[filename] = f"Object with {len(data)} keys"
                            elif isinstance(data, list):
                                status[filename] = f"Array with {len(data)} items"
                            else:
                                status[filename] = f"JSON data: {type(data).__name__}"
                        except json.JSONDecodeError:
                            status[filename] = f"Invalid JSON ({len(content)} chars)"
                    else:
                        # Text file
                        status[filename] = f"Text file ({len(content)} chars)"
            except Exception as e:
                status[filename] = f"Error reading: {e}"
        else:
            status[filename] = "File not found"
    
    return status

def print_json_status():
    """Print the current status of all JSON files"""
    print("📊 Current JSON Files Status:")
    print("=" * 50)
    
    status = get_json_file_status()
    for filename, file_status in status.items():
        print(f"  {filename}: {file_status}")
    
    print("=" * 50)

def clear_task_json_files():
    """Clear only the coding_tasks.json, research_tasks.json, and writing_tasks.json files (set to empty lists)"""
    try:
        os.makedirs("json", exist_ok=True)
        task_files = [
            "coding_tasks.json",
            "research_tasks.json",
            "writing_tasks.json"
        ]
        for filename in task_files:
            filepath = os.path.join("json", filename)
            with open(filepath, "w") as f:
                json.dump([], f, indent=2)
            print(f"✅ Cleared {filename}")
        return True
    except Exception as e:
        print(f"❌ Error clearing task json files: {e}")
        return False

if __name__ == "__main__":
    # Test the utility functions
    print("🧪 Testing JSON Utilities")
    print("=" * 30)
    
    print("\n1. Current status:")
    print_json_status()
    
    print("\n2. Clearing JSON files...")
    success = clear_json_files()
    
    if success:
        print("\n3. Status after clearing:")
        print_json_status()
    else:
        print("❌ Failed to clear JSON files") 