#!/usr/bin/env python3
"""
Utility script to clear all JSON files in the json/ directory to their default states.
This is useful for starting fresh sessions or cleaning up after testing.
"""

import os
import json
import sys

def clear_json_files():
    """Clear all files in json/ folder to their default states"""
    try:
        # Ensure json directory exists
        os.makedirs("json", exist_ok=True)
        
        # Clear messages.json (empty object)
        with open("json/messages.json", "w") as f:
            f.write("{}")
        print("✅ Cleared messages.json")
        
        # Clear phased_tasks.json (empty array)
        with open("json/phased_tasks.json", "w") as f:
            f.write("[]")
        print("✅ Cleared phased_tasks.json")
        
        # Clear last_processed_ts.txt (empty string)
        with open("json/last_processed_ts.txt", "w") as f:
            f.write("")
        print("✅ Cleared last_processed_ts.txt")
        
        # Clear last_task_processed_ts.txt (empty string)
        with open("json/last_task_processed_ts.txt", "w") as f:
            f.write("")
        print("✅ Cleared last_task_processed_ts.txt")
        
        # Clear task_dependencies.json (empty object)
        with open("json/task_dependencies.json", "w") as f:
            f.write("{}")
        print("✅ Cleared task_dependencies.json")
        
        # Clear dependency_matrix.json (empty object)
        with open("json/dependency_matrix.json", "w") as f:
            f.write("{}")
        print("✅ Cleared dependency_matrix.json")
        
        # Clean up project_embeddings.json to only include existing projects
        cleanup_project_embeddings()
        
        print("\n🧹 Successfully cleared all json/ files to default states")
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
            print("✅ Cleared project_embeddings.json")
            return
        
        # Get list of existing project folders
        existing_projects = set()
        if os.path.exists(work_dir):
            for item in os.listdir(work_dir):
                item_path = os.path.join(work_dir, item)
                if os.path.isdir(item_path):
                    existing_projects.add(item)
        
        print(f"📁 Found {len(existing_projects)} existing projects in Work/ directory")
        
        # Load current embeddings
        if os.path.exists("json/project_embeddings.json"):
            with open("json/project_embeddings.json", "r") as f:
                embeddings_data = json.load(f)
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
        
        print("✅ Updated project_embeddings.json")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not cleanup project embeddings: {e}")
        # If cleanup fails, just clear the file
        try:
            with open("json/project_embeddings.json", "w") as f:
                f.write("{}")
            print("✅ Cleared project_embeddings.json (fallback)")
        except:
            print("❌ Failed to clear project_embeddings.json")

def main():
    """Main function to run the JSON clearing utility"""
    print("🧹 KettleAI JSON File Cleaner")
    print("=" * 40)
    
    # Check for confirmation if not running in non-interactive mode
    if "--force" not in sys.argv and "-f" not in sys.argv:
        print("This will clear all JSON files to their default empty states.")
        print("Project embeddings will be cleaned to only include existing projects.")
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return
    
    success = clear_json_files()
    
    if success:
        print("\n🎉 JSON files cleared successfully!")
        print("💡 You can now start a fresh session with the daemon or pipeline")
    else:
        print("\n❌ Failed to clear JSON files")
        sys.exit(1)

if __name__ == "__main__":
    main() 