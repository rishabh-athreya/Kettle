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
    return {
        'id': str(uuid.uuid4()),  # Generate unique ID if not present
        'task': task_data.get('task', ''),
        'source': task_data.get('source', ''),
        'phase': task_data.get('phase', 'feature_implementation'),
        'approvalStatus': task_data.get('approvalStatus', 'pending'),
        'createdAt': task_data.get('createdAt', datetime.now().isoformat()),
        'completedAt': task_data.get('completedAt'),
        'user': task_data.get('user')
    }

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks from phased_tasks.json"""
    try:
        tasks_data = load_json_file('phased_tasks.json')
        
        # Transform the data to match frontend expectations
        tasks = []
        if isinstance(tasks_data, list):
            for task in tasks_data:
                transformed_task = transform_task(task)
                tasks.append(transformed_task)
        
        return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/approve', methods=['POST'])
def approve_task(task_id: str):
    """Update task approval status"""
    try:
        data = request.get_json()
        status = data.get('status', 'pending')
        
        # Load current tasks
        tasks_data = load_json_file('phased_tasks.json')
        
        if isinstance(tasks_data, list):
            # Find and update the task
            for task in tasks_data:
                if task.get('id') == task_id:
                    task['approvalStatus'] = status
                    if status in ['approved', 'rejected']:
                        task['completedAt'] = datetime.now().isoformat()
                    break
            
            # Save updated tasks
            save_json_file('phased_tasks.json', tasks_data)
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    """Get dashboard statistics"""
    try:
        tasks_data = load_json_file('phased_tasks.json')
        messages_data = load_json_file('messages.json')
        
        tasks = tasks_data if isinstance(tasks_data, list) else []
        messages = messages_data.get('messages', []) if isinstance(messages_data, dict) else []
        
        stats = {
            'totalTasks': len(tasks),
            'completedTasks': len([t for t in tasks if t.get('approvalStatus') == 'approved']),
            'pendingApproval': len([t for t in tasks if t.get('approvalStatus') == 'pending']),
            'totalMessages': len(messages)
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually trigger Slack fetch and task extraction"""
    try:
        # Change to Kettle root directory
        os.chdir(KETTLE_ROOT)
        
        # Run the master pipeline to fetch new data
        result = subprocess.run([
            sys.executable, 'master_pipeline.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return jsonify({
                'success': True, 
                'message': 'Data refreshed successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to refresh data',
                'output': result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False, 
            'error': 'Refresh timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'kettle-api'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 