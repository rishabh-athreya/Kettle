#!/usr/bin/env python3

import json
import os
from project_matcher import save_project_embedding, load_all_project_embeddings

def test_append_messages():
    """Test that save_project_embedding appends messages instead of replacing them"""
    
    # Test folder path
    test_folder = "/Users/rishabhathreya/Desktop/Work/flappy_bird"
    
    # First, let's see what's currently in the embeddings file
    print("=== Current state ===")
    current_data = load_all_project_embeddings()
    if "flappy_bird" in current_data:
        print(f"Current messages for flappy_bird: {current_data['flappy_bird']['messages']}")
    else:
        print("No flappy_bird project found")
    
    # Now let's simulate adding the original message
    original_message = "can you create a flappy bird game"
    print(f"\n=== Adding original message: '{original_message}' ===")
    
    save_project_embedding(test_folder, [original_message])
    
    # Check the result
    print("\n=== After adding original message ===")
    updated_data = load_all_project_embeddings()
    if "flappy_bird" in updated_data:
        print(f"Updated messages for flappy_bird: {updated_data['flappy_bird']['messages']}")
        print(f"Number of messages: {len(updated_data['flappy_bird']['messages'])}")
    else:
        print("flappy_bird project not found after update")

if __name__ == "__main__":
    test_append_messages() 