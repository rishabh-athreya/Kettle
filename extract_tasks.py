import json
import requests
import os
from datetime import datetime
from keys import ANTHROPIC_API_KEY
from prompts import extract_tasks_prompt
import time
from dependency_analyzer import *
from research_processor import *

# Use the modern messages endpoint
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def call_claude_for_summary(prompt_text: str) -> str:
    """Call Claude for generating readable summaries (returns plain text, not JSON)"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2000,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7
    }
    
    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    
    if resp.status_code != 200:
        print(f"Debug: Status code: {resp.status_code}")
        print(f"Debug: Response text: {resp.text}")
        resp.raise_for_status()

    # The `content` field contains the assistant's response
    return resp.json()["content"][0]["text"].strip()

def extract_main_objective(messages):
    """Extract the main objective from the messages using LLM."""
    if len(messages) == 1:
        # For single messages, create a task description based on the message content
        message = messages[0].lower()
        if "report" in message or "analysis" in message:
            return f"Write {messages[0]}"
        elif "game" in message or "app" in message or "implement" in message:
            return f"Create {messages[0]}"
        else:
            return f"Complete {messages[0]}"
    else:
        # For multiple messages, extract a combined objective
        prompt = f"""From these Slack messages, extract the single high-level objective that summarizes the overall goal. Return only a short string, not a list.

Messages:
{chr(10).join(f'- {msg}' for msg in messages)}"""
        try:
            raw_response = call_claude(prompt)
            main_objective = extract_valid_tasks_json(raw_response)
            if isinstance(main_objective, list):
                return str(main_objective[0])
            return str(main_objective)
        except Exception as e:
            print(f"Error extracting main objective: {e}")
            return "Project"

def extract_subtasks_from_messages(messages):
    """Extract all subtasks from the messages (each as a string)."""
    if len(messages) == 1:
        # For single messages, create subtasks based on the message content
        message = messages[0].lower()
        subtasks = []
        
        if "report" in message or "analysis" in message:
            # For reports/analysis, create research and writing subtasks
            if "ev" in message or "charging" in message:
                subtasks = [
                    "Research current EV charging infrastructure",
                    "Analyze major EV charger manufacturers", 
                    "Compile market size and growth data",
                    "Write industry trends section"
                ]
            else:
                subtasks = [
                    "Research topic",
                    "Analyze data",
                    "Compile findings",
                    "Write report"
                ]
        elif "game" in message:
            # For games, create development subtasks
            if "flappy" in message or "bird" in message:
                subtasks = [
                    "Set up game development environment",
                    "Install game development libraries",
                    "Create game assets and sprites",
                    "Implement bird physics and controls",
                    "Add obstacle generation and collision",
                    "Implement scoring system"
                ]
            else:
                subtasks = [
                    "Set up development environment",
                    "Install required libraries",
                    "Create game assets",
                    "Implement core game mechanics",
                    "Add user interface",
                    "Test and debug"
                ]
        elif "app" in message or "website" in message:
            # For apps/websites, create development subtasks
            subtasks = [
                "Set up project structure",
                "Install dependencies",
                "Create basic framework",
                "Implement core features",
                "Add user interface",
                "Test functionality"
            ]
        else:
            # Default subtasks
            subtasks = [
                "Plan the project",
                "Set up environment",
                "Implement core functionality",
                "Test and refine"
            ]
        
        return subtasks
    else:
        # For multiple messages, extract combined subtasks
        prompt = f"""From these Slack messages, extract all major subtasks (steps, phases, or deliverables) needed to accomplish the main objective. Return a JSON array of short strings, one for each subtask.

Messages:
{chr(10).join(f'- {msg}' for msg in messages)}"""
        try:
            raw_response = call_claude(prompt)
            subtasks = extract_valid_tasks_json(raw_response)
            if isinstance(subtasks, list):
                return [str(task) for task in subtasks]
            return []
        except Exception as e:
            print(f"Error extracting subtasks: {e}")
            return []

def create_subtasks_for_subtask(subtask, source_message):
    """Create ordered subtasks (coding, research, writing) for a subtask"""
    subtask_str = str(subtask).lower()
    source_str = str(source_message).lower()
    
    # Improved keyword detection
    coding_keywords = [
        "code", "program", "script", "app", "application", "website", "web app", 
        "api", "database", "server", "client", "frontend", "backend", "game",
        "function", "class", "module", "package", "library", "framework",
        "install", "setup", "configure", "deploy", "build", "compile",
        "test", "debug", "fix", "bug", "error", "exception", "implement",
        "create", "develop", "build", "make"
    ]
    
    research_keywords = [
        "research", "find", "search", "look up", "investigate", "explore",
        "study", "analyze", "examine", "review", "survey", "gather",
        "collect", "discover", "learn about", "understand", "explore",
        "market research", "competitor analysis", "user research", "embedding",
        "models", "algorithms", "techniques", "methods", "approaches"
    ]
    
    writing_keywords = [
        "write", "document", "report", "analysis", "summary", "review",
        "proposal", "plan", "strategy", "documentation", "manual",
        "guide", "tutorial", "article", "blog", "content", "copy",
        "draft", "create document", "prepare report"
    ]
    
    # Score each category
    coding_score = sum(1 for keyword in coding_keywords if keyword in subtask_str or keyword in source_str)
    research_score = sum(1 for keyword in research_keywords if keyword in subtask_str or keyword in source_str)
    writing_score = sum(1 for keyword in writing_keywords if keyword in subtask_str or keyword in source_str)
    
    # Create subtasks based on scores
    subtasks = {"coding": [], "research": [], "writing": []}
    
    # If research keywords are found, prioritize research
    if research_score > 0:
        subtasks["research"] = [f"Research {subtask}"]
        # If there are also coding keywords, add coding task
        if coding_score > 0:
            subtasks["coding"] = [f"Implement {subtask}"]
        # If there are also writing keywords, add writing task
        if writing_score > 0:
            subtasks["writing"] = [f"Write {subtask}"]
    # If coding keywords are found, prioritize coding
    elif coding_score > 0:
        subtasks["coding"] = [f"Implement {subtask}"]
        # If there are also writing keywords, add writing task
        if writing_score > 0:
            subtasks["writing"] = [f"Write {subtask}"]
    # If writing keywords are found, prioritize writing
    elif writing_score > 0:
        subtasks["writing"] = [f"Write {subtask}"]
        # Research is often needed for writing
        subtasks["research"] = [f"Research for {subtask}"]
    # Default fallback - if no clear category, assume it's a general task that needs research
    else:
        # For general tasks, start with research
        subtasks["research"] = [f"Research {subtask}"]
        subtasks["coding"] = [f"Implement {subtask}"]
    
    return subtasks

def create_hierarchical_tasks(messages):
    """Create hierarchical task structure with separate main objectives for each message."""
    hierarchical_tasks = {}
    
    for i, message in enumerate(messages):
        # Extract main objective from this specific message
        main_objective = extract_main_objective([message])
        
        # Extract subtasks from this specific message
        subtasks = extract_subtasks_from_messages([message])
        
        # Create subtask objects for this message
        hierarchical_subtasks = []
        for subtask in subtasks:
            subtask_obj = create_subtasks_for_subtask(subtask, message)
            hierarchical_subtasks.append(subtask_obj)
        
        # Add this message's tasks to the hierarchical structure
        hierarchical_tasks[main_objective] = hierarchical_subtasks
    
    return hierarchical_tasks

def save_hierarchical_tasks(hierarchical_tasks):
    """Save tasks as {main_task: [subtasks...]} where each subtask has a phase."""
    os.makedirs("json", exist_ok=True)
    
    structured_tasks = {}
    all_coding_tasks = []
    all_research_tasks = []
    all_writing_tasks = []
    
    for main_task, subtask_objs in hierarchical_tasks.items():
        main_task_lower = main_task.lower()
        subtasks = []
        # Research task: just one subtask
        if any(keyword in main_task_lower for keyword in ["research", "study", "analyze", "investigate", "embedding", "models"]):
            subtasks = [{"task": main_task, "phase": "research"}]
            all_research_tasks.append({
                "task": main_task,
                "source": main_task,
                "phase": "research",
                "category": "research"
            })
        # Writing task: research + writing
        elif any(keyword in main_task_lower for keyword in ["write", "document", "report", "analysis", "summary"]):
            subtasks = [
                {"task": f"Research {main_task}", "phase": "research"},
                {"task": f"Write LaTeX document for {main_task}", "phase": "writing"}
            ]
            all_writing_tasks.append({
                "task": main_task,
                "source": main_task,
                "phase": "writing",
                "category": "writing"
            })
        # Coding task: all coding subtasks with phase
        else:
            for subtask in subtask_objs:
                for coding_task in subtask.get("coding", []):
                    task_lower = coding_task.lower()
                    if any(keyword in task_lower for keyword in ["setup", "create", "initialize", "project"]):
                        phase = "project_setup"
                    elif any(keyword in task_lower for keyword in ["install", "dependency", "library", "package"]):
                        phase = "dependency_installation"
                    else:
                        phase = "feature_implementation"
                    subtasks.append({"task": coding_task, "phase": phase})
                    all_coding_tasks.append({
                        "task": coding_task,
                        "source": main_task,
                        "phase": phase,
                        "category": "coding"
                    })
        structured_tasks[main_task] = subtasks
    # Save the new structure
    with open("json/phased_tasks.json", "w") as f:
        json.dump(structured_tasks, f, indent=2)
    # Save categorized tasks for backward compatibility
    with open("json/coding_tasks.json", "w") as f:
        json.dump(all_coding_tasks, f, indent=2)
    with open("json/research_tasks.json", "w") as f:
        json.dump(all_research_tasks, f, indent=2)
    with open("json/writing_tasks.json", "w") as f:
        json.dump(all_writing_tasks, f, indent=2)
    print(f"✅ Saved tasks to json/phased_tasks.json (main task as key, subtasks as array)")
    print(f"✅ Saved {len(all_coding_tasks)} coding tasks to json/coding_tasks.json")
    print(f"✅ Saved {len(all_research_tasks)} research tasks to json/research_tasks.json")
    print(f"✅ Saved {len(all_writing_tasks)} writing tasks to json/writing_tasks.json")

def categorize_tasks_by_type(tasks):
    """Categorize tasks into coding, research, and writing types"""
    categorized_tasks = {
        "coding": [],
        "research": [],
        "writing": []
    }
    
    for task in tasks:
        task_text = task.get("task", "").lower()
        source_text = task.get("source", "").lower()
        
        # Keywords for each category
        coding_keywords = [
            "code", "program", "script", "app", "application", "website", "web app", 
            "api", "database", "server", "client", "frontend", "backend", "game",
            "function", "class", "module", "package", "library", "framework",
            "install", "setup", "configure", "deploy", "build", "compile",
            "test", "debug", "fix", "bug", "error", "exception"
        ]
        
        research_keywords = [
            "research", "find", "search", "look up", "investigate", "explore",
            "study", "analyze", "examine", "review", "survey", "gather",
            "collect", "discover", "learn about", "understand", "explore",
            "market research", "competitor analysis", "user research"
        ]
        
        writing_keywords = [
            "write", "document", "report", "analysis", "summary", "review",
            "proposal", "plan", "strategy", "documentation", "manual",
            "guide", "tutorial", "article", "blog", "content", "copy",
            "draft", "create document", "prepare report"
        ]
        
        # Score each category
        coding_score = sum(1 for keyword in coding_keywords if keyword in task_text or keyword in source_text)
        research_score = sum(1 for keyword in research_keywords if keyword in task_text or keyword in source_text)
        writing_score = sum(1 for keyword in writing_keywords if keyword in task_text or keyword in source_text)
        
        # Determine the best category
        scores = {
            "coding": coding_score,
            "research": research_score,
            "writing": writing_score
        }
        
        best_category = max(scores, key=scores.get)
        
        # Only categorize if there's a clear winner (score > 0)
        if scores[best_category] > 0:
            # Add category to the task
            task["category"] = best_category
            categorized_tasks[best_category].append(task)
        else:
            # Default to coding if no clear category (legacy behavior)
            task["category"] = "coding"
            categorized_tasks["coding"].append(task)
    
    return categorized_tasks

def save_categorized_tasks(categorized_tasks):
    """Save categorized tasks to separate files and update main tasks file"""
    os.makedirs("json", exist_ok=True)
    
    # Save each category to its own file
    for category, tasks in categorized_tasks.items():
        filename = f"json/{category}_tasks.json"
        with open(filename, "w") as f:
            json.dump(tasks, f, indent=2)
        print(f"✅ Saved {len(tasks)} {category} tasks to {filename}")
    
    # Combine all tasks for the main phased_tasks.json file
    all_tasks = []
    for category, tasks in categorized_tasks.items():
        all_tasks.extend(tasks)
    
    # Save to main tasks file
    with open("json/phased_tasks.json", "w") as f:
        json.dump(all_tasks, f, indent=2)
    print(f"✅ Saved {len(all_tasks)} total tasks to json/phased_tasks.json")

# Parse out a clean JSON array of task objects
def extract_valid_tasks_json(response: str):
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "tasks" in data:
            return data["tasks"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Unexpected JSON structure")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}\nResponse was: {response}")
        return []

# Real Slack fetch - read from saved messages
def fetch_messages():
    try:
        with open("json/messages.json", "r") as f:
            data = json.load(f)
            messages = data.get("messages", [])
            
        # Get the last processed timestamp for tasks
        last_task_ts = 0
        try:
            with open("json/last_task_processed_ts.txt", "r") as f:
                last_task_ts = float(f.read().strip())
        except (FileNotFoundError, ValueError):
            pass
        
        # Check if we have any existing tasks
        try:
            with open("json/phased_tasks.json", "r") as f:
                existing_tasks = json.load(f)
                has_existing_tasks = len(existing_tasks) > 0
        except (FileNotFoundError, json.JSONDecodeError):
            has_existing_tasks = False
        
        # Check if the latest message is a modification request
        is_modification_request = False
        if messages:
            latest_message = messages[0].get("text", "").lower()
            modification_keywords = [
                "modify", "update", "change", "add to", "enhance", "improve", 
                "fix", "adjust", "tweak", "refactor", "extend", "expand"
            ]
            is_modification_request = any(keyword in latest_message for keyword in modification_keywords)
        
        # If no existing tasks, process all messages
        if not has_existing_tasks:
            print(f"Processing all {len(messages)} messages for initial task extraction")
            # Update the timestamp to the latest message processed
            if messages:
                latest_ts = max(float(msg.get("ts", 0)) for msg in messages)
                with open("json/last_task_processed_ts.txt", "w") as f:
                    f.write(str(latest_ts))
            return [msg.get("text", "") for msg in messages if msg.get("text", "").strip()]
        
        # If it's a modification request, process all recent messages (last 5)
        if is_modification_request:
            print(f"🔧 Modification request detected! Processing recent messages for task updates")
            recent_messages = messages[:5]  # Get last 5 messages
            message_texts = [msg.get("text", "") for msg in recent_messages if msg.get("text", "").strip()]
            
            # Clear existing tasks to make room for new modification tasks
            print("🗑️  Clearing existing tasks for modification...")
            with open("json/phased_tasks.json", "w") as f:
                json.dump([], f, indent=2)
            
            # Update the timestamp to the latest message processed
            if messages:
                latest_ts = max(float(msg.get("ts", 0)) for msg in messages)
                with open("json/last_task_processed_ts.txt", "w") as f:
                    f.write(str(latest_ts))
            
            return message_texts
        
        # Only process messages newer than the last task extraction (normal flow)
        new_messages = []
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts > last_task_ts:
                new_messages.append(msg.get("text", ""))
        
        if new_messages:
            print(f"Processing {len(new_messages)} new messages for task extraction")
            # Update the timestamp to the latest message processed
            latest_ts = max(float(msg.get("ts", 0)) for msg in messages)
            with open("json/last_task_processed_ts.txt", "w") as f:
                f.write(str(latest_ts))
            return new_messages
        else:
            print("No new messages for task extraction")
            return []
            
    except FileNotFoundError:
        print("Warning: json/messages.json not found. Using dummy message.")
        return ["Create a simple tic tac toe game to run on localhost"]
    except Exception as e:
        print(f"Error reading messages: {e}")
        return ["Create a simple tic tac toe game to run on localhost"]

# Call Claude via /v1/messages to enforce JSON output
def call_claude(prompt_text: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    # Build a system message that enforces JSON output
    system_message = (
        "You are a task extraction assistant. You must respond with ONLY valid JSON in the exact format specified. "
        "Do not include any explanatory text, markdown formatting, or additional commentary.\n\n"
        "RESPONSE FORMAT:\n"
        "Return a JSON array of task objects, where each task has:\n"
        "- \"task\": string\n"
        "- \"source\": string\n"
        "- \"phase\": string (project_setup, dependency_installation, feature_implementation)\n\n"
        "EXAMPLE RESPONSE:\n"
        "[\n"
        "  {\"task\": \"Create project directory structure\", \"source\": \"Create a web app\", \"phase\": \"project_setup\"},\n"
        "  {\"task\": \"Install Flask framework\", \"source\": \"Create a web app\", \"phase\": \"dependency_installation\"}\n"
        "]"
    )

    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8000,
        "system": system_message,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.1
    }

    print(f"Debug: Sending request to {ANTHROPIC_API_URL}")
    print(f"Debug: Headers: {headers}")
    print(f"Debug: Body keys: {list(body.keys())}")
    
    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
    
    if resp.status_code != 200:
        print(f"Debug: Status code: {resp.status_code}")
        print(f"Debug: Response text: {resp.text}")
        resp.raise_for_status()

    # The `content` field contains the assistant's response
    return resp.json()["content"][0]["text"].strip()


def main():
    messages = fetch_messages()
    
    # Don't process tasks if there are no messages
    if not messages:
        print("No messages to process for task extraction")
        return
    
    # Check if this is a modification request
    is_modification = any(keyword in " ".join(messages).lower() for keyword in [
        "modify", "update", "change", "add to", "enhance", "improve", 
        "fix", "adjust", "tweak", "refactor", "extend", "expand"
    ])
    
    if is_modification:
        print("🔧 Processing modification request...")
        print(f"📝 Messages: {messages}")
    else:
        print("🆕 Processing new project request...")
    
    # Create hierarchical tasks (like Desktop/Kettle)
    print("🔍 Creating hierarchical tasks...")
    hierarchical_tasks = create_hierarchical_tasks(messages)
    
    # Save hierarchical tasks in the correct structure
    save_hierarchical_tasks(hierarchical_tasks)
    
    if is_modification:
        print("✅ Modification tasks extracted and ready for execution")
    else:
        print("✅ Task extraction and categorization complete")
    
    # Automatically process research tasks to generate media resources
    if research_tasks and len(research_tasks) > 0:
        print("🔍 Research tasks detected - generating media resources...")
        try:
            main(auto_mode=True)
            print("✅ Research media generation complete")
        except Exception as e:
            print(f"⚠️  Could not generate research media: {e}")
    else:
        print("📝 No research tasks found - skipping media generation")
    
    if is_modification:
        print("✅ Modification processing complete - new tasks ready in dashboard")
    else:
        print("✅ Task extraction, categorization, dependency analysis, and research processing complete")


if __name__ == "__main__":
    main()
