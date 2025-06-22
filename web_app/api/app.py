from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import uuid
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

# Path to the JSON data files (relative to the main Kettle directory)
KETTLE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'json')
KETTLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Path to the virtual environment Python interpreter
VENV_PYTHON = os.path.join(KETTLE_ROOT, 'kettle_env', 'bin', 'python3')

def load_json_file(filename: str) -> Dict[str, Any]:
    """Load JSON file from the Kettle data directory"""
    filepath = os.path.join(KETTLE_DATA_DIR, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json_file(filename: str, data: Dict[str, Any]) -> None:
    """Save JSON file to the Kettle data directory"""
    filepath = os.path.join(KETTLE_DATA_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def transform_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform task data to include required fields for the frontend"""
    # Generate a consistent ID based on task content if not present
    if 'id' not in task_data:
        task_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task_data.get('task', '')}{task_data.get('source', '')}"))
    else:
        task_id = task_data['id']
    
    return {
        'id': task_id,
        'task': task_data.get('task', ''),
        'source': task_data.get('source', ''),
        'phase': task_data.get('phase', 'feature_implementation'),
        'selectionStatus': task_data.get('selectionStatus', 'pending'),  # Changed from approvalStatus
        'createdAt': task_data.get('createdAt', datetime.now().isoformat()),
        'selectedAt': task_data.get('selectedAt'),
        'user': task_data.get('user')
    }

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get coding tasks from phased_tasks.json"""
    try:
        tasks_data = load_json_file('phased_tasks.json')
        
        # Transform the data to match frontend expectations
        tasks = []
        if isinstance(tasks_data, list):
            for task in tasks_data:
                # Only include coding tasks or tasks without category (backward compatibility)
                task_category = task.get('category', 'coding')  # Default to coding for backward compatibility
                if task_category == 'coding':
                    transformed_task = transform_task(task)
                    tasks.append(transformed_task)
        
        return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/select', methods=['POST'])
def select_task(task_id: str):
    """Update task selection status for coding tasks"""
    try:
        data = request.get_json()
        status = data.get('status', 'pending')  # 'selected', 'rejected', or 'pending'
        
        # Load current tasks
        tasks_data = load_json_file('phased_tasks.json')
        
        if isinstance(tasks_data, list):
            # Find and update the task (only coding tasks)
            task_found = False
            for task in tasks_data:
                # Only process coding tasks
                task_category = task.get('category', 'coding')
                if task_category != 'coding':
                    continue
                    
                # Check if this task matches the ID (either by existing ID or by generating one)
                task_check_id = task.get('id') or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task.get('task', '')}{task.get('source', '')}"))
                
                if task_check_id == task_id:
                    task['id'] = task_id  # Ensure ID is set
                    task['selectionStatus'] = status
                    if status in ['selected', 'rejected']:
                        task['selectedAt'] = datetime.now().isoformat()
                    task_found = True
                    break
            
            if not task_found:
                return jsonify({'error': 'Coding task not found'}), 404
            
            # Save updated tasks
            save_json_file('phased_tasks.json', tasks_data)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/dependencies', methods=['GET'])
def get_task_dependencies(task_id: str):
    """Get potential dependencies for a task using AI-generated dependency matrix"""
    try:
        # Load current tasks
        tasks_data = load_json_file('phased_tasks.json')
        
        if not isinstance(tasks_data, list):
            return jsonify({'error': 'No tasks found'}), 404
        
        # Find the target task
        target_task = None
        for task in tasks_data:
            task_check_id = task.get('id') or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task.get('task', '')}{task.get('source', '')}"))
            if task_check_id == task_id:
                target_task = task
                break
        
        if not target_task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Load dependency matrix
        try:
            dependency_matrix = load_json_file('dependency_matrix.json')
            dependencies_data = dependency_matrix.get('dependencies', {})
            explanations_data = dependency_matrix.get('explanations', {})
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to empty dependencies if matrix doesn't exist
            dependencies_data = {}
            explanations_data = {}
        
        # Find tasks that depend on the target task
        dependencies = []
        target_task_id = target_task.get('id')
        
        for task in tasks_data:
            task_id = task.get('id')
            if task_id and task_id != target_task_id:
                # Check if this task depends on the target task
                task_dependencies = dependencies_data.get(task_id, [])
                if target_task_id in task_dependencies:
                    dependencies.append({
                        'id': task_id,
                        'task': task.get('task'),
                        'phase': task.get('phase'),
                        'selectionStatus': task.get('selectionStatus', 'pending'),
                        'reason': explanations_data.get(task_id, f'Depends on {target_task.get("task", "")}')
                    })
        
        return jsonify({
            'task': target_task,
            'dependencies': dependencies,
            'warning': f'Rejecting this task may affect {len(dependencies)} other tasks' if dependencies else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-selected', methods=['POST'])
def execute_selected_tasks():
    """Execute all selected coding tasks in batch"""
    try:
        # Load current tasks
        tasks_data = load_json_file('phased_tasks.json')
        
        if not isinstance(tasks_data, list):
            return jsonify({'error': 'No tasks found'}), 404
        
        # Filter to only selected coding tasks
        selected_tasks = [task for task in tasks_data 
                         if task.get('selectionStatus') == 'selected' 
                         and task.get('category', 'coding') == 'coding']
        
        if not selected_tasks:
            return jsonify({'error': 'No coding tasks selected for execution'}), 400
        
        # Create a temporary file with only selected tasks for execution
        temp_tasks_file = os.path.join(KETTLE_DATA_DIR, 'temp_selected_tasks.json')
        with open(temp_tasks_file, 'w') as f:
            json.dump(selected_tasks, f, indent=2)
        
        try:
            # Change to Kettle root directory
            os.chdir(KETTLE_ROOT)
            
            # Execute the selected tasks using the virtual environment's Python interpreter
            result = subprocess.run([
                VENV_PYTHON, 'execute.py'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            # Check if files were actually created (success indicator)
            work_dir = os.path.expanduser("~/Desktop/Work")
            files_created = False
            if os.path.exists(work_dir):
                # Check if any new files were created in the last few minutes
                import time
                current_time = time.time()
                for root, dirs, files in os.walk(work_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) > current_time - 300:  # Files created in last 5 minutes
                            files_created = True
                            break
                    if files_created:
                        break
            
            # Consider it successful if files were created, even if return code is non-zero
            if result.returncode == 0 or files_created:
                # Mark selected coding tasks as executed
                for task in tasks_data:
                    if (task.get('selectionStatus') == 'selected' and 
                        task.get('category', 'coding') == 'coding'):
                        task['selectionStatus'] = 'executed'
                        task['executedAt'] = datetime.now().isoformat()
                
                # Save updated tasks
                save_json_file('phased_tasks.json', tasks_data)
                
                success_message = f'Successfully executed {len(selected_tasks)} selected coding tasks'
                if files_created and result.returncode != 0:
                    success_message += ' (files created despite script warnings)'
                
                return jsonify({
                    'success': True,
                    'message': success_message,
                    'output': result.stdout,
                    'stderr': result.stderr,
                    'returnCode': result.returncode,
                    'filesCreated': files_created,
                    'executedTasks': len(selected_tasks)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Task execution failed',
                    'output': result.stdout,
                    'stderr': result.stderr,
                    'returnCode': result.returncode,
                    'filesCreated': files_created
                }), 500
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_tasks_file):
                os.remove(temp_tasks_file)
                
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Task execution timed out (5 minutes)'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all messages from messages.json"""
    try:
        messages_data = load_json_file('messages.json')
        return jsonify(messages_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics for coding tasks"""
    try:
        tasks_data = load_json_file('phased_tasks.json')
        messages_data = load_json_file('messages.json')
        
        # Filter to only coding tasks
        all_tasks = tasks_data if isinstance(tasks_data, list) else []
        coding_tasks = [task for task in all_tasks if task.get('category', 'coding') == 'coding']
        
        messages = messages_data.get('messages', []) if isinstance(messages_data, dict) else []
        
        stats = {
            'totalTasks': len(coding_tasks),
            'selectedTasks': len([t for t in coding_tasks if t.get('selectionStatus') == 'selected']),
            'pendingSelection': len([t for t in coding_tasks if t.get('selectionStatus') == 'pending']),
            'executedTasks': len([t for t in coding_tasks if t.get('selectionStatus') == 'executed']),
            'totalMessages': len(messages)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'kettle-api'})

@app.route('/api/tasks', methods=['POST'])
def reset_tasks():
    """Reset all tasks"""
    try:
        # Clear the tasks file
        save_json_file('phased_tasks.json', [])
        return jsonify({'success': True, 'message': 'Tasks reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def reset_messages():
    """Reset all messages"""
    try:
        # Clear the messages file
        save_json_file('messages.json', {'messages': []})
        return jsonify({'success': True, 'message': 'Messages reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/media', methods=['POST'])
def reset_media():
    """Reset all media resources"""
    try:
        # Clear the media file with proper structure
        empty_media = {
            "research_topics": {},
            "summary": {
                "total_research_topics": 0,
                "total_media_resources": 0,
                "last_updated": ""
            }
        }
        save_json_file('media.json', empty_media)
        return jsonify({'success': True, 'message': 'Media resources reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-resources', methods=['GET'])
def get_research_resources():
    """Get all research resources from media.json"""
    try:
        media_data = load_json_file('media.json')
        # Return the research_topics dict as a flat list of resources
        resources = []
        if isinstance(media_data, dict) and 'research_topics' in media_data:
            for topic in media_data['research_topics'].values():
                for resource in topic.get('media_links', []):
                    # Attach the research_task/topic for context
                    resource['research_task'] = topic.get('research_task', '')
                    resources.append(resource)
        return jsonify(resources)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 