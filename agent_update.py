import os
import requests
import json
from datetime import datetime

def run_agent():
    api_key = os.getenv("AI_AGENT_KEY")
    if not api_key:
        print("Error: AI_AGENT_KEY not found!")
        return

    print("Agent waking up (Gemini Version)...")
    
    # Gemini API Endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "You are a 2026 AI Agent. Write a 1-sentence futuristic trend for the year 2026. Be bold and tech-focused."}]
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    # Extract the text from Gemini response
    prediction = result['candidates'][0]['content']['parts'][0]['text']
    date_str = datetime.now().strftime("%B %d, %Y")

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Portfolio 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white font-sans p-10">
    <div class="max-w-3xl mx-auto border border-green-500 p-8 shadow-2xl shadow-green-500/20">
        <h1 class="text-3xl font-bold text-green-400 mb-4 tracking-tighter">SYSTEM: AUTONOMOUS PORTFOLIO 2026</h1>
        <p class="text-sm text-gray-500 mb-8 font-mono">Last Autonomous Update: {date_str}</p>
        
        <div class="mb-10">
            <h2 class="text-xl text-blue-400 font-mono mb-2">>> TODAY'S AI AGENT INSIGHT:</h2>
            <p class="text-2xl leading-relaxed italic text-gray-200">"{prediction.strip()}"</p>
        </div>

        <div class="grid grid-cols-2 gap-4 text-xs font-mono text-green-800">
            <div class="border border-green-900 p-2">AGENT_STATUS: ACTIVE</div>
            <div class="border border-green-900 p-2">MODEL: GEMINI_1.5_FLASH</div>
            <div class="border border-green-900 p-2">CREATIVITY_LOG: OPTIMIZED</div>
            <div class="border border-green-900 p-2">MODE: SELF_EVOLVING</div>
        </div>
    </div>
</body>
</html>
"""
    
    with open("index.html", "w") as f:
        f.write(html_content)
    print("Success! Website updated.")

if __name__ == "__main__":
    run_agent()
