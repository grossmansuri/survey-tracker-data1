import os
import requests
import json
from flask import Flask, redirect, request
from datetime import datetime
from base64 import b64encode, b64decode

app = Flask(__name__)

# GitHub Setup - REPLACE WITH YOUR DETAILS!
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "grossmansuri/survey-tracker-data1"  # Your GitHub repo
FILE_PATH = "data.json"                     # Your data file

def log_to_github(project_id, respondent_id, status):
    auth_codes = {
        "complete": 10,
        "terminate": 20,
        "overquota": 30,
        "security_terminate": 40
    }
    auth_code = auth_codes.get(status, 0)

    # Fetch existing data
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        file_data = response.json()
        current_content = json.loads(b64decode(file_data["content"]).decode()) if "content" in file_data else []
    except Exception as e:
        print(f"GitHub fetch error: {e}")
        current_content = []

    # Add new entry
    current_content.append({
        "project_id": project_id,
        "respondent_id": respondent_id,
        "status": status,
        "auth_code": auth_code,
        "timestamp": datetime.now().isoformat()
    })

    # Push update
    try:
        requests.put(
            url,
            headers=headers,
            json={
                "message": "Update survey data",
                "content": b64encode(json.dumps(current_content).encode()).decode(),
                "sha": file_data.get("sha", "")
            }
        )
    except Exception as e:
        print(f"GitHub push error: {e}")

    return auth_code

@app.route('/track/<project_id>/<status>/<respondent_id>')
def track(project_id, status, respondent_id):
    auth_code = log_to_github(project_id, respondent_id, status)
    
    # Custom redirects for BrainySampling
    if auth_code == 10:  # Complete
        return redirect(f"https://brainysampling.com/complete?rid={respondent_id}", code=302)
    elif auth_code == 20:  # Terminate
        return redirect(f"https://brainysampling.com/terminate?rid={respondent_id}", code=302)
    elif auth_code == 30:  # Overquota
        return redirect(f"https://brainysampling.com/overquota?rid={respondent_id}", code=302)
    else:  # Security terminate (40)
        return redirect(f"https://brainysampling.com/security_terminate?rid={respondent_id}", code=302)

if __name__ == '__main__':
    app.run()