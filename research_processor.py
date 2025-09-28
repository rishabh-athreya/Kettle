import json
import requests
import os
import sys
import webbrowser
import subprocess
import time
from utils.keys import ANTHROPIC_API_KEY

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def call_claude(prompt):
    """Call Claude API with the given prompt"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def generate_media_search_prompt(research_task):
    """Generate a prompt for Claude to search for relevant media"""
    return f"""You are a research assistant that finds high-quality educational videos and articles for learning about specific topics.

For the research task: "{research_task}"

Please search for and return a JSON array of relevant educational resources. Each resource should have:
- "title": The title of the video/article
- "url": The direct URL to the resource
- "type": Either "video" or "article"
- "source": The platform/source (e.g., "YouTube", "Medium", "Stack Overflow", "GitHub", "Documentation")
- "description": A brief description of what the resource covers
- "relevance_score": A number from 1-10 indicating how relevant it is to the research task

Focus on:
- High-quality educational content
- Recent and up-to-date resources
- Well-known platforms and sources
- Content that would help someone learn about the topic

Return ONLY valid JSON in this exact format:
[
  {{
    "title": "Example Video Title",
    "url": "https://example.com/video",
    "type": "video",
    "source": "YouTube",
    "description": "This video covers the basics of the topic",
    "relevance_score": 9
  }}
]

Find 5-10 high-quality resources that would be most helpful for learning about this topic."""

def extract_media_links(research_task):
    """Extract media links for a research task using Claude"""
    print(f"🔍 Searching for media resources for: {research_task}")
    
    prompt = generate_media_search_prompt(research_task)
    response = call_claude(prompt)
    
    if not response:
        print("❌ Failed to get response from Claude")
        return []
    
    try:
        # Try to extract JSON from the response
        # Look for JSON blocks in the response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].strip()
        else:
            json_str = response.strip()
        
        # Parse the JSON
        media_links = json.loads(json_str)
        
        if isinstance(media_links, list):
            print(f"✅ Found {len(media_links)} media resources")
            return media_links
        else:
            print("❌ Response is not a list")
            return []
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        print(f"Response was: {response}")
        return []
    except Exception as e:
        print(f"❌ Error processing response: {e}")
        return []

def open_media_links_in_browser(media_links):
    """Open all media URLs in new browser tabs (videos/articles)"""
    if not media_links:
        print("No media links to open.")
        return
    urls = [item.get('url') for item in media_links if item.get('url')]
    if not urls:
        print("No valid URLs found in media links.")
        return
    print(f"\n🌐 Ready to open {len(urls)} media resources in your browser.")
    confirm = input("Open all links in new browser tabs? [y/N]: ").strip().lower()
    if confirm == 'y':
        for url in urls:
            webbrowser.open_new_tab(url)
        print(f"✅ Opened {len(urls)} tabs in your browser.")
    else:
        print("❌ Skipped opening browser tabs.")

def display_media_links(media_links, research_task="", open_in_browser=False):
    """Display media links in a formatted terminal output and optionally open in browser"""
    if not media_links:
        print("📺 No media resources found.")
        return
    
    print(f"\n{'='*80}")
    if research_task:
        print(f"📺 MEDIA RESOURCES FOR: {research_task}")
    else:
        print(f"📺 MEDIA RESOURCES")
    print(f"{'='*80}")
    
    # Sort by relevance score (highest first)
    sorted_links = sorted(media_links, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    for i, resource in enumerate(sorted_links, 1):
        title = resource.get('title', 'No title')
        url = resource.get('url', 'No URL')
        resource_type = resource.get('type', 'Unknown')
        source = resource.get('source', 'Unknown')
        description = resource.get('description', 'No description')
        relevance = resource.get('relevance_score', 'Unknown')
        
        # Type icon
        type_icon = "🎥" if resource_type.lower() == "video" else "📄"
        
        # Source color coding
        source_icons = {
            "YouTube": "📺",
            "Medium": "📝",
            "Stack Overflow": "💻",
            "GitHub": "🐙",
            "Documentation": "📚",
            "Udemy": "🎓",
            "Stanford University": "🎓",
            "Google Developers": "🔍",
            "O'Reilly": "📖"
        }
        source_icon = source_icons.get(source, "🔗")
        
        print(f"\n{i:2d}. {type_icon} {title}")
        print(f"    {source_icon} {source} | Relevance: {relevance}/10")
        print(f"    🔗 {url}")
        print(f"    📝 {description}")
        
        if i < len(sorted_links):
            print(f"    {'─'*70}")
    
    if open_in_browser:
        open_media_links_in_browser(sorted_links)

def save_media_links(research_task, media_links):
    """Save media links to a single media.json file, updating existing entries"""
    filename = "json/media.json"
    
    # Create json directory if it doesn't exist
    os.makedirs("json", exist_ok=True)
    
    # Load existing media data or create new structure
    existing_data = {}
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}
    
    # Ensure the structure exists
    if "research_topics" not in existing_data:
        existing_data["research_topics"] = {}
    
    # Create a key for this research task (sanitized)
    task_key = research_task.replace(' ', '_').lower()[:50]
    # Remove any special characters that might cause issues
    task_key = ''.join(c for c in task_key if c.isalnum() or c == '_')
    
    # Add timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update or add the research task data
    existing_data["research_topics"][task_key] = {
        "research_task": research_task,
        "media_links": media_links,
        "timestamp": timestamp,
        "total_resources": len(media_links)
    }
    
    # Update summary statistics
    total_topics = len(existing_data["research_topics"])
    total_resources = sum(topic.get("total_resources", 0) for topic in existing_data["research_topics"].values())
    
    existing_data["summary"] = {
        "total_research_topics": total_topics,
        "total_media_resources": total_resources,
        "last_updated": timestamp
    }
    
    try:
        with open(filename, "w") as f:
            json.dump(existing_data, f, indent=2)
        print(f"💾 Updated media.json with {len(media_links)} resources for '{research_task}'")
        print(f"   📊 Total topics: {total_topics}, Total resources: {total_resources}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save media links: {e}")
        return None

def process_research_tasks(auto_mode=False):
    """Process all research tasks and generate media links"""
    try:
        # Load research tasks
        with open("json/research_tasks.json", "r") as f:
            research_tasks = json.load(f)
        
        if not research_tasks:
            print("📝 No research tasks found in json/research_tasks.json")
            return
        
        print(f"🔍 Processing {len(research_tasks)} research tasks...")
        
        processed_count = 0
        
        for task in research_tasks:
            task_text = task.get("task", "")
            if task_text:
                print(f"\n📋 Processing research task: {task_text}")
                
                # Generate media links for this task
                media_links = extract_media_links(task_text)
                
                if media_links:
                    # Display the media links and offer to open in browser (only if not in auto mode)
                    display_media_links(media_links, task_text, open_in_browser=not auto_mode)
                    
                    # Save to single media.json file
                    save_media_links(task_text, media_links)
                    processed_count += 1
        
        # Display summary
        print(f"\n{'='*80}")
        print(f"📊 MEDIA GENERATION SUMMARY")
        print(f"{'='*80}")
        print(f"📋 Research tasks processed: {processed_count}")
        print(f"💾 All results saved to json/media.json")
        
        # Show final summary from the file
        try:
            with open("json/media.json", "r") as f:
                final_data = json.load(f)
                summary = final_data.get("summary", {})
                print(f"📊 Total research topics: {summary.get('total_research_topics', 0)}")
                print(f"📺 Total media resources: {summary.get('total_media_resources', 0)}")
                print(f"🕒 Last updated: {summary.get('last_updated', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Could not read final summary: {e}")
        
    except FileNotFoundError:
        print("📝 json/research_tasks.json not found")
    except Exception as e:
        print(f"❌ Error processing research tasks: {e}")

def generate_latex_report(writing_task, research_summary=None):
    """Generate a LaTeX report for the writing task and save it to json/writing/"""
    os.makedirs("json/writing", exist_ok=True)
    title = writing_task.get("task", "AI Report")
    content = research_summary or "This is an auto-generated report."
    latex = f"""
\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\title{{{title}}}
\\begin{{document}}
\\maketitle
\\section*{{Summary}}
{content}
\\end{{document}}
"""
    # Use a filename based on the task
    safe_title = title.replace(" ", "_").replace("/", "_")[:40]
    filename = f"json/writing/{safe_title}.tex"
    with open(filename, "w") as f:
        f.write(latex)
    return filename

def process_writing_tasks():
    """Generate LaTeX reports for all writing tasks and update their entries with report_path."""
    try:
        with open("json/writing_tasks.json", "r") as f:
            writing_tasks = json.load(f)
        updated_tasks = []
        for task in writing_tasks:
            # Optionally, you could summarize research here
            report_path = generate_latex_report(task)
            task["report_path"] = report_path
            updated_tasks.append(task)
        with open("json/writing_tasks.json", "w") as f:
            json.dump(updated_tasks, f, indent=2)
        print(f"✅ Generated LaTeX reports for {len(updated_tasks)} writing tasks.")
    except Exception as e:
        print(f"❌ Error generating LaTeX reports: {e}")

def main(auto_mode=False):
    """Main function to run research processing"""
    print("🎬 Starting research processing...")
    process_research_tasks(auto_mode=auto_mode)
    print("✅ Research processing complete!")
    process_writing_tasks()

if __name__ == "__main__":
    main() 