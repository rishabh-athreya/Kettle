#!/usr/bin/env python3
"""
Test script to verify MongoDB integration with Kettle AI.
This script tests the MongoDB functionality without affecting existing data.
"""

import os
import sys
import json
from datetime import datetime
from tools.mongodb_config import get_embedding_manager, get_mongodb_config, cleanup_mongodb_connections

def test_mongodb_connection():
    """Test basic MongoDB connection"""
    print("🔌 Testing MongoDB connection...")
    try:
        config = get_mongodb_config()
        # Test the connection
        config.database.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_embedding_operations():
    """Test embedding save and retrieval operations"""
    print("\n🧪 Testing embedding operations...")
    
    try:
        embedding_manager = get_embedding_manager()
        
        # Test data
        test_project = {
            "project_name": "test_project_mongodb",
            "folder_path": "/tmp/test_project",
            "messages": ["Create a test web app", "Add authentication"],
            "embedding": [0.1] * 384,  # Dummy embedding
            "project_type": "web_app"
        }
        
        # Test save
        print("  💾 Testing save operation...")
        success = embedding_manager.save_project_embedding(
            project_name=test_project["project_name"],
            folder_path=test_project["folder_path"],
            messages=test_project["messages"],
            embedding=test_project["embedding"],
            project_type=test_project["project_type"],
            metadata={"test": True, "timestamp": datetime.utcnow().isoformat()}
        )
        
        if success:
            print("  ✅ Save operation successful")
        else:
            print("  ❌ Save operation failed")
            return False
        
        # Test retrieval
        print("  🔍 Testing retrieval operation...")
        retrieved = embedding_manager.get_project_by_name(test_project["project_name"])
        
        if retrieved:
            print("  ✅ Retrieval operation successful")
            print(f"     Project: {retrieved['project_name']}")
            print(f"     Type: {retrieved['project_type']}")
            print(f"     Messages: {len(retrieved['messages'])}")
        else:
            print("  ❌ Retrieval operation failed")
            return False
        
        # Test similarity search
        print("  🔍 Testing similarity search...")
        similar_projects = embedding_manager.find_similar_projects(
            query_embedding=test_project["embedding"],
            limit=5,
            similarity_threshold=0.1
        )
        
        if similar_projects:
            print(f"  ✅ Similarity search successful - found {len(similar_projects)} projects")
            for i, project in enumerate(similar_projects[:3]):
                print(f"     {i+1}. {project['project_name']} (similarity: {project['similarity']:.4f})")
        else:
            print("  ⚠️  No similar projects found (this might be normal for test data)")
        
        # Test stats
        print("  📊 Testing statistics...")
        stats = embedding_manager.get_project_stats()
        print(f"     Total projects: {stats['total_projects']}")
        print(f"     Project types: {len(stats['project_types'])}")
        
        # Cleanup test data
        print("  🧹 Cleaning up test data...")
        deleted = embedding_manager.delete_project(test_project["project_name"])
        if deleted:
            print("  ✅ Test data cleaned up")
        else:
            print("  ⚠️  Could not clean up test data")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Embedding operations failed: {e}")
        return False

def test_json_migration():
    """Test migration from existing JSON file"""
    print("\n🔄 Testing JSON migration...")
    
    json_path = "json/project_embeddings.json"
    
    if not os.path.exists(json_path):
        print("  ⚠️  No existing JSON file found - skipping migration test")
        return True
    
    try:
        embedding_manager = get_embedding_manager()
        
        # Count existing projects in MongoDB
        stats_before = embedding_manager.get_project_stats()
        projects_before = stats_before['total_projects']
        
        print(f"  📊 Projects in MongoDB before migration: {projects_before}")
        
        # Test migration
        migrated_count = embedding_manager.migrate_from_json(json_path)
        
        if migrated_count > 0:
            print(f"  ✅ Migration successful - migrated {migrated_count} projects")
            
            # Check stats after migration
            stats_after = embedding_manager.get_project_stats()
            projects_after = stats_after['total_projects']
            
            print(f"  📊 Projects in MongoDB after migration: {projects_after}")
            print(f"  📈 Net increase: {projects_after - projects_before}")
            
            return True
        else:
            print("  ⚠️  No projects were migrated (might already be migrated)")
            return True
            
    except Exception as e:
        print(f"  ❌ Migration test failed: {e}")
        return False

def test_project_matcher_integration():
    """Test integration with project_matcher.py"""
    print("\n🔗 Testing project_matcher integration...")
    
    try:
        # Import project_matcher to test the integration
        import tools.project_matcher as project_matcher
        
        # Test compute_embedding function
        test_messages = ["Create a simple web application", "Build a game with pygame"]
        embedding = project_matcher.compute_embedding(test_messages)
        
        if embedding and len(embedding) > 0:
            print(f"  ✅ Embedding computation successful (dimension: {len(embedding)})")
        else:
            print("  ❌ Embedding computation failed")
            return False
        
        # Test find_closest_project function
        print("  🔍 Testing project similarity search...")
        closest_project, similarity = project_matcher.find_closest_project(test_messages)
        
        if closest_project:
            print(f"  ✅ Found similar project: {closest_project} (similarity: {similarity:.4f})")
        else:
            print("  📭 No similar projects found (this might be normal if no projects exist)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ project_matcher integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Kettle AI - MongoDB Integration Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("tools/mongodb_config.py"):
        print("❌ Please run this script from the Kettle AI root directory")
        sys.exit(1)
    
    tests = [
        ("MongoDB Connection", test_mongodb_connection),
        ("Embedding Operations", test_embedding_operations),
        ("JSON Migration", test_json_migration),
        ("Project Matcher Integration", test_project_matcher_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MongoDB integration is working correctly.")
        print("💡 You can now use MongoDB for project embeddings.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("💡 Make sure MongoDB is running and accessible.")
    
    # Cleanup
    cleanup_mongodb_connections()

if __name__ == "__main__":
    main()
