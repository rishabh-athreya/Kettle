#!/usr/bin/env python3
"""
MongoDB configuration and connection management for Kettle AI.
Handles database connections, collections, and basic operations.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBConfig:
    """MongoDB configuration and connection manager"""
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "kettle_ai"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string (defaults to localhost)
            database_name: Name of the database to use
        """
        self.connection_string = connection_string or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connection timeout
                socketTimeoutMS=20000           # 20 second socket timeout
            )
            
            # Test the connection
            self.client.admin.command('ping')
            self.database = self.client[self.database_name]
            
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database"""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client is not None:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")

class ProjectEmbeddingManager:
    """Manager for project embeddings stored in MongoDB"""
    
    def __init__(self, mongodb_config: MongoDBConfig):
        self.config = mongodb_config
        self.collection = mongodb_config.get_collection("project_embeddings")
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # Index on project_name for fast lookups
            self.collection.create_index("project_name", unique=True)
            
            # Index on created_at for time-based queries
            self.collection.create_index("created_at")
            
            # Index on project_type for filtering
            self.collection.create_index("project_type")
            
            # Index on folder_path for path-based queries
            self.collection.create_index("folder_path")
            
            logger.info("✅ MongoDB indexes created/verified")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not create indexes: {e}")
    
    def save_project_embedding(self, 
                             project_name: str, 
                             folder_path: str, 
                             messages: List[str], 
                             embedding: List[float],
                             project_type: str = "unknown",
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save or update a project embedding
        
        Args:
            project_name: Name of the project
            folder_path: Path to the project folder
            messages: List of messages that generated this project
            embedding: Vector embedding of the project
            project_type: Type of project (e.g., "web_app", "game", "script")
            metadata: Additional metadata about the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare the document
            document = {
                "project_name": project_name,
                "folder_path": folder_path,
                "messages": messages,
                "embedding": embedding,
                "project_type": project_type,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "embedding_dimension": len(embedding)
            }
            
            # Use upsert to update existing or create new
            result = self.collection.replace_one(
                {"project_name": project_name},
                document,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Saved embedding for project: {project_name}")
                return True
            else:
                logger.warning(f"⚠️  No changes made for project: {project_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving embedding for {project_name}: {e}")
            return False
    
    def find_similar_projects(self, 
                            query_embedding: List[float], 
                            limit: int = 10,
                            similarity_threshold: float = 0.2,
                            project_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find similar projects using vector similarity
        
        Args:
            query_embedding: The embedding to search for
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            project_type_filter: Optional filter by project type
            
        Returns:
            List of similar projects with similarity scores
        """
        try:
            # Build query filter
            query_filter = {}
            if project_type_filter:
                query_filter["project_type"] = project_type_filter
            
            # Get all projects matching the filter
            projects = list(self.collection.find(query_filter))
            
            if not projects:
                logger.info("📭 No projects found in database")
                return []
            
            # Calculate similarities
            similarities = []
            for project in projects:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, project["embedding"])
                
                if similarity >= similarity_threshold:
                    similarities.append({
                        "project": project,
                        "similarity": similarity,
                        "project_name": project["project_name"],
                        "folder_path": project["folder_path"],
                        "project_type": project["project_type"],
                        "created_at": project["created_at"]
                    })
            
            # Sort by similarity (highest first) and limit results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error finding similar projects: {e}")
            return []
    
    def get_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by name"""
        try:
            return self.collection.find_one({"project_name": project_name})
        except Exception as e:
            logger.error(f"❌ Error getting project {project_name}: {e}")
            return None
    
    def delete_project(self, project_name: str) -> bool:
        """Delete a project from the database"""
        try:
            result = self.collection.delete_one({"project_name": project_name})
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted project: {project_name}")
                return True
            else:
                logger.warning(f"⚠️  Project not found: {project_name}")
                return False
        except Exception as e:
            logger.error(f"❌ Error deleting project {project_name}: {e}")
            return False
    
    def get_all_projects(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all projects in the database"""
        try:
            cursor = self.collection.find({})
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"❌ Error getting all projects: {e}")
            return []
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get statistics about stored projects"""
        try:
            total_projects = self.collection.count_documents({})
            
            # Count by project type
            pipeline = [
                {"$group": {"_id": "$project_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            type_counts = list(self.collection.aggregate(pipeline))
            
            # Get date range
            pipeline = [
                {"$group": {
                    "_id": None,
                    "earliest": {"$min": "$created_at"},
                    "latest": {"$max": "$created_at"}
                }}
            ]
            date_range = list(self.collection.aggregate(pipeline))
            
            return {
                "total_projects": total_projects,
                "project_types": type_counts,
                "date_range": date_range[0] if date_range else None
            }
        except Exception as e:
            logger.error(f"❌ Error getting project stats: {e}")
            return {"total_projects": 0, "project_types": [], "date_range": None}
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Convert to numpy arrays and reshape for sklearn
        vec1_array = np.array(vec1).reshape(1, -1)
        vec2_array = np.array(vec2).reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(vec1_array, vec2_array)[0][0]
        return float(similarity)
    
    def migrate_from_json(self, json_file_path: str) -> int:
        """
        Migrate existing JSON embeddings to MongoDB
        
        Args:
            json_file_path: Path to the existing project_embeddings.json file
            
        Returns:
            int: Number of projects migrated
        """
        try:
            if not os.path.exists(json_file_path):
                logger.warning(f"⚠️  JSON file not found: {json_file_path}")
                return 0
            
            with open(json_file_path, 'r') as f:
                json_data = json.load(f)
            
            migrated_count = 0
            
            for project_name, project_data in json_data.items():
                try:
                    # Extract data from JSON format
                    embedding = project_data.get("embedding", [])
                    messages = project_data.get("messages", [])
                    folder = project_data.get("folder", "")
                    
                    # Determine project type from folder path or messages
                    project_type = self._infer_project_type(folder, messages)
                    
                    # Save to MongoDB
                    success = self.save_project_embedding(
                        project_name=project_name,
                        folder_path=folder,
                        messages=messages,
                        embedding=embedding,
                        project_type=project_type,
                        metadata={"migrated_from_json": True}
                    )
                    
                    if success:
                        migrated_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error migrating project {project_name}: {e}")
                    continue
            
            logger.info(f"✅ Migrated {migrated_count} projects from JSON to MongoDB")
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            return 0
    
    def _infer_project_type(self, folder_path: str, messages: List[str]) -> str:
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

# Global instance for easy access
_mongodb_config = None
_embedding_manager = None

def get_mongodb_config() -> MongoDBConfig:
    """Get the global MongoDB configuration instance"""
    global _mongodb_config
    if _mongodb_config is None:
        _mongodb_config = MongoDBConfig()
    return _mongodb_config

def get_embedding_manager() -> ProjectEmbeddingManager:
    """Get the global embedding manager instance"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = ProjectEmbeddingManager(get_mongodb_config())
    return _embedding_manager

def cleanup_mongodb_connections():
    """Clean up MongoDB connections"""
    global _mongodb_config
    if _mongodb_config:
        _mongodb_config.close()
        _mongodb_config = None

if __name__ == "__main__":
    # Test the MongoDB connection and basic operations
    print("🧪 Testing MongoDB Integration")
    print("=" * 40)
    
    try:
        # Test connection
        config = get_mongodb_config()
        print("✅ MongoDB connection successful")
        
        # Test embedding manager
        manager = get_embedding_manager()
        print("✅ Embedding manager initialized")
        
        # Test stats
        stats = manager.get_project_stats()
        print(f"📊 Database stats: {stats}")
        
        # Test migration if JSON file exists
        json_path = "json/project_embeddings.json"
        if os.path.exists(json_path):
            print(f"🔄 Migrating from {json_path}...")
            migrated = manager.migrate_from_json(json_path)
            print(f"✅ Migrated {migrated} projects")
        
        print("✅ MongoDB integration test completed successfully")
        
    except Exception as e:
        print(f"❌ MongoDB integration test failed: {e}")
    finally:
        cleanup_mongodb_connections()
