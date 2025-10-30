#!/usr/bin/env python3
"""
MongoDB Status Checker for Kettle AI
Check the current state of your MongoDB database anytime.
"""

import sys
from datetime import datetime
from tools.mongodb_config import get_embedding_manager, get_mongodb_config, cleanup_mongodb_connections

def check_mongodb_connection():
    """Check if MongoDB is accessible"""
    try:
        config = get_mongodb_config()
        # Test the connection
        config.database.command('ping')
        print("MongoDB connection successful")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Make sure MongoDB is running: brew services start mongodb/brew/mongodb-community")
        return False

def show_database_stats():
    """Show comprehensive database statistics"""
    try:
        embedding_manager = get_embedding_manager()
        
        print("Database Statistics")
        print("=" * 40)
        
        # Get basic stats
        stats = embedding_manager.get_project_stats()
        print(f"Total projects: {stats['total_projects']}")
        
        if stats['project_types']:
            print("\nProject types:")
            for project_type in stats['project_types']:
                print(f"  {project_type['_id']}: {project_type['count']} projects")
        else:
            print("No project types found")
        
        if stats['date_range'] and stats['date_range'].get('earliest'):
            print(f"\nDate range:")
            print(f"  Earliest: {stats['date_range']['earliest']}")
            print(f"  Latest: {stats['date_range']['latest']}")
        
        return True
        
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return False

def list_recent_projects(limit=10):
    """List recent projects"""
    try:
        embedding_manager = get_embedding_manager()
        
        print(f"Recent Projects (last {limit})")
        print("=" * 40)
        
        projects = embedding_manager.get_all_projects(limit=limit)
        
        if not projects:
            print("No projects found in database")
            return True
        
        for i, project in enumerate(projects, 1):
            created_at = project.get('created_at', 'Unknown')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"{i:2d}. {project['project_name']}")
            print(f"    Type: {project.get('project_type', 'unknown')}")
            print(f"    Path: {project.get('folder_path', 'unknown')}")
            print(f"    Created: {created_at}")
            print(f"    Messages: {len(project.get('messages', []))}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error listing projects: {e}")
        return False

def search_projects(query=None, project_type=None):
    """Search for specific projects"""
    try:
        embedding_manager = get_embedding_manager()
        
        print(f"Project Search")
        print("=" * 40)
        
        if query:
            print(f"Searching for: '{query}'")
            # Simple text search in project names and messages
            projects = embedding_manager.get_all_projects()
            matching_projects = []
            
            for project in projects:
                project_name = project.get('project_name', '').lower()
                messages_text = ' '.join(project.get('messages', [])).lower()
                
                if query.lower() in project_name or query.lower() in messages_text:
                    matching_projects.append(project)
            
            print(f"Found {len(matching_projects)} matching projects:")
            for project in matching_projects[:10]:  # Show first 10
                print(f"  • {project['project_name']} ({project.get('project_type', 'unknown')})")
        
        if project_type:
            print(f"Filtering by type: '{project_type}'")
            projects = embedding_manager.get_all_projects()
            filtered_projects = [p for p in projects if p.get('project_type') == project_type]
            print(f"Found {len(filtered_projects)} projects of type '{project_type}':")
            for project in filtered_projects[:10]:  # Show first 10
                print(f"  • {project['project_name']}")
        
        return True
        
    except Exception as e:
        print(f"Error searching projects: {e}")
        return False

def show_database_info():
    """Show database connection and configuration info"""
    try:
        config = get_mongodb_config()
        
        print("\nDatabase Configuration")
        print("=" * 40)
        print(f"Connection string: {config.connection_string}")
        print(f"Database name: {config.database_name}")
        print(f"Client connected: {config.client is not None}")
        print(f"Database object: {config.database is not None}")
        
        return True
        
    except Exception as e:
        print(f"Error getting database info: {e}")
        return False

def main():
    """Main status check function"""
    print("Kettle AI - MongoDB Status Checker")
    print("=" * 50)
    
    # Check connection
    if not check_mongodb_connection():
        sys.exit(1)
    
    # Show database info
    show_database_info()
    
    # Show statistics
    show_database_stats()
    
    # List recent projects
    list_recent_projects(limit=5)
    
    # Interactive search if arguments provided
    if len(sys.argv) > 1:
        query = sys.argv[1]
        search_projects(query=query)
    
    if len(sys.argv) > 2:
        project_type = sys.argv[2]
        search_projects(project_type=project_type)
    
    print("Status check complete!")
    print("Use 'python tools/check_mongodb_status.py [search_term] [project_type]' for searches")
    
    # Cleanup
    cleanup_mongodb_connections()

if __name__ == "__main__":
    main()
