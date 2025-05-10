import os
import requests
import json
from flask import Flask, redirect
from datetime import datetime
from base64 import b64encode, b64decode

app = Flask(__name__)

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "grossmansuri/survey-tracker-data1"  # Your repository
FILE_PATH = "data.json"                     # Your data file
MAX_RETRIES = 3                             # Retry failed GitHub updates

def log_to_github(project_id, respondent_id, status):
    auth_codes = {
        "complete": 10,
        "terminate": 20,
        "overquota": 30,
        "security_terminate": 40
    }
    auth_code = auth_codes.get(status, 0)

    # Fetch existing data with retry logic
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    for attempt in range(MAX_RETRIES):
        try:
            # 1. Get current file content
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            file_data = response.json()
            current_content = json.loads(b64decode(file_data["content"]).decode()) if "content" in file_data else []

            # 2. Add new entry
            current_content.append({
                "project_id": project_id,
                "respondent_id": respondent_id,
                "status": status,
                "auth_code": auth_code,
                "timestamp": datetime.now().isoformat()
            })

            # 3. Push update
            update_response = requests.put(
                url,
                headers=headers,
                json={
                    "message": f"Survey {status}: {respondent_id}",
                    "content": b64encode(json.dumps(current_content).encode()).decode(),
                    "sha": file_data.get("sha", "")
                },
                timeout=15
            )
            update_response.raise_for_status()
            print(f"GitHub update succeeded (attempt {attempt + 1})")
            return auth_code

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                print("Max retries reached. Logging failed.")
                return auth_code  # Still return auth_code for redirect

@app.route('/track/<project_id>/<status>/<respondent_id>')
def track(project_id, status, respondent_id):
    auth_code = log_to_github(project_id, respondent_id, status)
    
    # Custom redirects
    base_url = "https://brainysampling.com"
    if auth_code == 10:    # Complete
        return redirect(f"{base_url}/complete?rid={respondent_id}", code=302)
    elif auth_code == 20:  # Terminate
        return redirect(f"{base_url}/terminate?rid={respondent_id}", code=302)
    elif auth_code == 30:  # Overquota
        return redirect(f"{base_url}/overquota?rid={respondent_id}", code=302)
    else:                  # Security terminate (40)
        return redirect(f"{base_url}/security_terminate?rid={respondent_id}", code=302)

if __name__ == '__main__':
    app.run()
