import os
import requests
import json
from flask import Flask, redirect, request
from datetime import datetime
from base64 import b64encode, b64decode
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "your-github-username/survey-tracker"  # Replace this!
FILE_PATH = "data.json"

def log_to_github(project_id, respondent_id, status):
    auth_codes = {
        "complete": 10,
        "terminate": 20,
        "overquota": 30,
        "security_terminate": 40
    }
    auth_code = auth_codes.get(status, 0)

    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    file_data = response.json()
    current_content = json.loads(
        b64decode(file_data["content"]).decode()) if "content" in file_data else []

    current_content.append({
        "project_id": project_id,
        "respondent_id": respondent_id,
        "status": status,
        "auth_code": auth_code,
        "timestamp": datetime.now().isoformat()
    })

    requests.put(
        url,
        headers=headers,
        json={
            "message": "Update survey data",
            "content": b64encode(json.dumps(current_content).encode()).decode(),
            "sha": file_data.get("sha", "")
        }
    )
    return auth_code

@app.route('/track/<project_id>/<status>/<respondent_id>')
def track(project_id, status, respondent_id):
    auth_code = log_to_github(project_id, respondent_id, status)
    return redirect(f"https://www.brainysampling.com/thanks/Index?auth={auth_code}&rid={respondent_id}", code=302)


if __name__ == '__main__':
    app.run(debug=True)
