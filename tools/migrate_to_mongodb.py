#!/usr/bin/env python3
"""
Migration script to move project embeddings from JSON to MongoDB.
This script helps transition from the old JSON-based storage to MongoDB.
"""

import os
import json
import sys
from datetime import datetime
from tools.mongodb_config import get_embedding_manager, get_mongodb_config, cleanup_mongodb_connections

def check_mongodb_connection():
    """Check if MongoDB is available and accessible"""
    try:
        config = get_mongodb_config()
        # Test the connection
        config.database.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("💡 Make sure MongoDB is running and accessible")
        return False

def backup_json_file(json_path):
    """Create a backup of the existing JSON file"""
    if not os.path.exists(json_path):
        print(f"⚠️  JSON file not found: {json_path}")
        return None
    
    backup_path = f"{json_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(json_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
        return None

def migrate_embeddings():
    """Migrate project embeddings from JSON to MongoDB"""
    json_path = "json/project_embeddings.json"
    
    print("🔄 Starting migration from JSON to MongoDB")
    print("=" * 50)
    
    # Check if JSON file exists
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        print("💡 No migration needed - starting fresh with MongoDB")
        return True
    
    # Check MongoDB connection
    if not check_mongodb_connection():
        return False
    
    # Create backup
    backup_path = backup_json_file(json_path)
    
    try:
        # Get embedding manager
        embedding_manager = get_embedding_manager()
        
        # Migrate data
        print("📦 Migrating project embeddings...")
        migrated_count = embedding_manager.migrate_from_json(json_path)
        
        if migrated_count > 0:
            print(f"✅ Successfully migrated {migrated_count} projects to MongoDB")
            
            # Show stats
            stats = embedding_manager.get_project_stats()
            print(f"📊 Database now contains {stats['total_projects']} projects")
            
            # Ask if user wants to remove JSON file
            if backup_path:
                response = input(f"\n🗑️  Remove original JSON file? (y/N): ").strip().lower()
                if response == 'y':
                    try:
                        os.remove(json_path)
                        print(f"✅ Removed {json_path}")
                        print(f"💾 Backup available at: {backup_path}")
                    except Exception as e:
                        print(f"⚠️  Could not remove JSON file: {e}")
                else:
                    print(f"📁 Original JSON file kept: {json_path}")
                    print(f"💾 Backup available at: {backup_path}")
            
            return True
        else:
            print("⚠️  No projects were migrated")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    try:
        embedding_manager = get_embedding_manager()
        
        print("\n🔍 Verifying migration...")
        
        # Get all projects
        projects = embedding_manager.get_all_projects()
        print(f"📊 Found {len(projects)} projects in MongoDB")
        
        if projects:
            print("\n📋 Sample projects:")
            for i, project in enumerate(projects[:5]):  # Show first 5
                print(f"  {i+1}. {project['project_name']} ({project['project_type']})")
                print(f"     Path: {project['folder_path']}")
                print(f"     Messages: {len(project['messages'])}")
                print(f"     Created: {project['created_at']}")
                print()
            
            if len(projects) > 5:
                print(f"  ... and {len(projects) - 5} more projects")
        
        # Test similarity search
        print("🧪 Testing similarity search...")
        test_messages = ["Create a simple web app", "Build a game", "Make a script"]
        
        # Note: this is a smoke check; production similarity lives in tools.project_matcher
        similar = embedding_manager.find_similar_projects(
            query_embedding=projects[0]["embedding"] if projects else [0.0] * 384,
            limit=3,
            similarity_threshold=0.1
        )
        print(f"  Similarity search returned {len(similar)} candidates")
        
        print("✅ Migration verification completed")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_mongodb_info():
    """Show information about MongoDB setup"""
    print("\n📚 MongoDB Setup Information")
    print("=" * 40)
    print("🔧 To use MongoDB with Kettle AI:")
    print("1. Install MongoDB: https://www.mongodb.com/try/download/community")
    print("2. Start MongoDB service")
    print("3. Run this migration script")
    print("4. Update your environment variables if needed:")
    print("   export MONGODB_URI='mongodb://localhost:27017/'")
    print("   export MONGODB_DATABASE='kettle_ai'")
    print("\n💡 Benefits of MongoDB:")
    print("  • Faster similarity searches")
    print("  • Better scalability")
    print("  • Rich querying capabilities")
    print("  • Concurrent access support")
    print("  • Automatic indexing")

def main():
    """Main migration function"""
    print("🚀 Kettle AI - MongoDB Migration Tool")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("json") or not os.path.exists("tools/project_matcher.py"):
        print("❌ Please run this script from the Kettle AI root directory")
        sys.exit(1)
    
    # Show MongoDB info
    show_mongodb_info()
    
    # Ask user if they want to proceed
    response = input("\n🤔 Do you want to proceed with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("👋 Migration cancelled")
        return
    
    # Perform migration
    success = migrate_embeddings()
    
    if success:
        # Verify migration
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("💡 You can now use MongoDB for project embeddings")
    else:
        print("\n❌ Migration failed")
        print("💡 Check the error messages above and try again")
    
    # Cleanup
    cleanup_mongodb_connections()

if __name__ == "__main__":
    main()
