import os
import requests
import json
from datetime import datetime

def run_agent():
    api_key = os.getenv("AI_AGENT_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # We tell the AI to focus on "HOT TOPICS" that people search for
    prompt = """
    You are an AI SEO Expert and Tech Forecaster in 2026. 
    1. Identify a HOT TREND for 2026 (e.g., Humanoid Robots, Space Travel, AI-Bio Integration, or Decentralized Energy).
    2. Provide a JSON response:
       - "title": A catchy, SEO-friendly headline.
       - "insight": A 2-sentence deep-dive into this hot topic.
       - "keywords": 5 trending keywords separated by commas.
       - "thought1": 'Scanning global tech news for high-volume search trends...'
       - "thought2": 'Synthesizing 2026 forecast data...'
       - "thought3": 'Optimizing metadata for Google indexing...'
    Return ONLY JSON.
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=data)
    raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
    clean_json = raw_text.replace('```json', '').replace('```', '').strip()
    ai_data = json.loads(clean_json)

    date_now = datetime.now().strftime("%d %b %Y")

    # This HTML now includes SEO META TAGS so people can find you on Google
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ai_data['title']} | Autonomous Portfolio 2026</title>
    <meta name="description" content="{ai_data['insight']}">
    <meta name="keywords" content="{ai_data['keywords']}">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');
        body {{ font-family: 'Inter', sans-serif; background: #000; color: #fff; }}
        .cyber-font {{ font-family: 'Orbitron', sans-serif; }}
        .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
        .gradient-text {{ background: linear-gradient(90deg, #4ade80, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="p-6 md:p-20">
    <div class="max-w-5xl mx-auto">
        <nav class="flex justify-between items-center mb-16">
            <div class="cyber-font text-xl font-bold tracking-widest text-green-500">AUTONOMOUS_2026</div>
            <div class="text-[10px] text-gray-500 uppercase tracking-widest">System Status: Optimal</div>
        </nav>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-12">
            <div class="md:col-span-8">
                <p class="text-green-500 cyber-font text-sm mb-4">>> TREND_ANALYSIS_LIVE</p>
                <h1 class="text-5xl md:text-7xl font-bold mb-8 leading-tight">{ai_data['title']}</h1>
                <p class="text-xl text-gray-400 leading-relaxed mb-12">"{ai_data['insight']}"</p>
                
                <div class="flex gap-4">
                    <div class="glass p-4 rounded-xl">
                        <p class="text-[10px] text-gray-500 uppercase mb-1">Search Keywords</p>
                        <p class="text-xs text-green-400 italic">{ai_data['keywords']}</p>
                    </div>
                </div>
            </div>

            <div class="md:col-span-4">
                <div class="glass p-6 rounded-2xl border-l-4 border-green-500">
                    <h3 class="cyber-font text-xs mb-6 text-gray-400">Agent Thought Process</h3>
                    <ul class="space-y-6 text-xs font-light tracking-wide text-gray-300">
                        <li class="flex gap-3"><span class="text-green-500">01</span> {ai_data['thought1']}</li>
                        <li class="flex gap-3"><span class="text-green-500">02</span> {ai_data['thought2']}</li>
                        <li class="flex gap-3"><span class="text-green-500">03</span> {ai_data['thought3']}</li>
                    </ul>
                </div>
            </div>
        </div>

        <footer class="mt-32 pt-8 border-t border-white/10 flex justify-between items-center text-[10px] text-gray-600 tracking-widest uppercase">
            <div>Last Updated: {date_now}</div>
            <div>© 2026 Autonomous Agent Systems</div>
        </footer>
    </div>
</body>
</html>
    """

    with open("index.html", "w") as f:
        f.write(html_template)

if __name__ == "__main__":
    run_agent()
