import os
import requests
import json
from datetime import datetime

def run_agent():
    api_key = os.getenv("AI_AGENT_KEY")
    if not api_key:
        print("ERROR: AI_AGENT_KEY is missing in GitHub Secrets!")
        exit(1)

    print("Checking API connection...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Write a 1-sentence tech trend for 2026."}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"API Response Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API ERROR: {response.text}")
            exit(1)

        result = response.json()
        prediction = result['candidates'][0]['content']['parts'][0]['text']
        print(f"AI Success: {prediction}")

        # HTML Generation
        date_str = datetime.now().strftime("%B %d, %Y")
        html_content = f"""<!DOCTYPE html><html><body style="background:black;color:green;font-family:monospace;padding:50px;"><h1>AUTONOMOUS PORTFOLIO 2026</h1><p>UPDATED: {date_str}</p><hr><p>INSIGHT: {prediction}</p></body></html>"""
        
        with open("index.html", "w") as f:
            f.write(html_content)
            
    except Exception as e:
        print(f"SCRIPT CRASHED: {str(e)}")
        exit(1)

if __name__ == "__main__":
    run_agent()
