import json
import requests
import os
from keys import ANTHROPIC_API_KEY
import uuid

# Use the modern messages endpoint
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def create_dependency_analysis_prompt(tasks):
    """Create a prompt for Claude to analyze task dependencies"""
    
    task_list = "\n".join([f"{i+1}. {task.get('task', '')}" for i, task in enumerate(tasks)])
    
    prompt = f"""
You are a software project dependency analyzer. Analyze the following tasks and create a dependency matrix showing which tasks depend on others.

TASKS TO ANALYZE:
{task_list}

ANALYSIS INSTRUCTIONS:
1. For each task, identify which other tasks it depends on (prerequisites)
2. Consider technical dependencies, logical order, and implementation requirements
3. Be conservative - only mark dependencies that are clearly necessary
4. Consider both direct dependencies (Task A directly needs Task B) and logical dependencies (Task A makes more sense after Task B)

RESPONSE FORMAT:
Return ONLY a JSON object with this exact structure:
{{
  "dependencies": {{
    "task_id_1": ["task_id_2", "task_id_3"],
    "task_id_2": ["task_id_4"],
    "task_id_3": [],
    ...
  }},
  "explanations": {{
    "task_id_1": "This task depends on task_id_2 because... and task_id_3 because...",
    "task_id_2": "This task depends on task_id_4 because...",
    ...
  }}
}}

Where task_id_X corresponds to the task number (1, 2, 3, etc.) from the list above.

EXAMPLE:
If Task 1 is "Set up project structure" and Task 2 is "Install dependencies", then Task 2 might depend on Task 1:
{{
  "dependencies": {{
    "1": [],
    "2": ["1"]
  }},
  "explanations": {{
    "1": "No dependencies - this is a foundational task",
    "2": "Depends on task 1 because dependencies should be installed after project structure is set up"
  }}
}}

Analyze the tasks and provide the dependency matrix:
"""
    
    return prompt

def call_claude_for_dependencies(prompt_text: str) -> str:
    """Call Claude to analyze task dependencies"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    system_message = (
        "You are a dependency analysis assistant. You must respond with ONLY valid JSON in the exact format specified. "
        "Do not include any explanatory text, markdown formatting, or additional commentary.\n\n"
        "RESPONSE FORMAT:\n"
        "Return a JSON object with 'dependencies' and 'explanations' fields as specified in the prompt.\n\n"
        "CRITICAL: Only include dependencies that are clearly necessary. Be conservative in your analysis."
    )

    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "system": system_message,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.1
    }

    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    
    if resp.status_code != 200:
        print(f"Error calling Claude: {resp.status_code}")
        print(f"Response: {resp.text}")
        resp.raise_for_status()

    return resp.json()["content"][0]["text"].strip()

def parse_dependency_response(response: str):
    """Parse Claude's dependency analysis response"""
    try:
        data = json.loads(response)
        return data
    except json.JSONDecodeError as e:
        print(f"Failed to parse dependency JSON: {e}")
        print(f"Response was: {response}")
        return {"dependencies": {}, "explanations": {}}

def create_dependency_matrix(tasks):
    """Create a dependency matrix for all tasks using Claude"""
    if not tasks:
        print("No tasks to analyze for dependencies")
        return {}
    
    print(f"🔍 Analyzing dependencies for {len(tasks)} tasks...")
    
    # Create prompt for Claude
    prompt = create_dependency_analysis_prompt(tasks)
    
    # Call Claude
    try:
        response = call_claude_for_dependencies(prompt)
        dependency_data = parse_dependency_response(response)
        
        # Create a mapping from task numbers to actual task IDs
        task_id_map = {}
        for i, task in enumerate(tasks):
            task_num = str(i + 1)
            # Use existing ID or generate one
            task_id = task.get('id')
            if not task_id:
                # Generate a consistent ID based on task content
                task_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task.get('task', '')}{task.get('source', '')}"))
                # Update the task with the generated ID
                task['id'] = task_id
            task_id_map[task_num] = task_id
        
        # Transform the dependency data to use actual task IDs
        transformed_dependencies = {}
        transformed_explanations = {}
        
        for task_num, deps in dependency_data.get('dependencies', {}).items():
            if task_num in task_id_map:
                actual_task_id = task_id_map[task_num]
                actual_deps = [task_id_map.get(dep, dep) for dep in deps if dep in task_id_map]
                transformed_dependencies[actual_task_id] = actual_deps
                
                if task_num in dependency_data.get('explanations', {}):
                    transformed_explanations[actual_task_id] = dependency_data['explanations'][task_num]
        
        # Save the dependency matrix
        dependency_matrix = {
            "dependencies": transformed_dependencies,
            "explanations": transformed_explanations,
            "analyzed_at": "2024-01-01T00:00:00Z"  # You could add actual timestamp here
        }
        
        os.makedirs("json", exist_ok=True)
        with open("json/dependency_matrix.json", "w") as f:
            json.dump(dependency_matrix, f, indent=2)
        
        print(f"✅ Dependency matrix created with {len(transformed_dependencies)} task relationships")
        return dependency_matrix
        
    except Exception as e:
        print(f"❌ Error creating dependency matrix: {e}")
        return {}

def main():
    """Main function to analyze dependencies for existing tasks"""
    try:
        # Load existing tasks
        with open("json/phased_tasks.json", "r") as f:
            tasks = json.load(f)
        
        # Create dependency matrix
        dependency_matrix = create_dependency_matrix(tasks)
        
        if dependency_matrix:
            print("✅ Dependency analysis complete")
        else:
            print("❌ Dependency analysis failed")
            
    except FileNotFoundError:
        print("No tasks found. Run task extraction first.")
    except Exception as e:
        print(f"Error in dependency analysis: {e}")

if __name__ == "__main__":
    main() 