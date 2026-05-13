import os
import requests
import json
from datetime import datetime

def run_advanced_agent():
    gemini_key = os.getenv("AI_AGENT_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    print("Step 1: Agent 'Researcher' is browsing the web...")
    
    # --- TAVILY SEARCH ---
    search_url = "https://api.tavily.com/search"
    search_data = {
        "api_key": tavily_key,
        "query": "latest tech breakthroughs and future trends 2026",
        "search_depth": "advanced",
        "max_results": 3
    }
    search_response = requests.post(search_url, json=search_data)
    search_results = search_response.json().get('results', [])
    
    # Format search results for Gemini
    context = ""
    for res in search_results:
        context += f"Source: {res['title']} - {res['content']}\n"

    print("Step 2: Agent 'Architect' is synthesizing data...")

    # --- GEMINI ANALYSIS & CODING ---
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    You are a Lead AI Architect. Based on this REAL-TIME RESEARCH:
    {context}
    
    Create a 2026 forecast for a website. Provide JSON:
    1. "hot_topic": The main trend name.
    2. "analysis": A 2-sentence expert forecast.
    3. "source_url": Use the most interesting URL from the research.
    4. "thought_log": A list of 3 things you did (searching, analyzing, coding).
    Return ONLY JSON.
    """
    
    gemini_data = {"contents": [{"parts": [{"text": prompt}]}]}
    gemini_response = requests.post(gemini_url, json=gemini_data)
    
    raw_text = gemini_response.json()['candidates'][0]['content']['parts'][0]['text']
    ai_data = json.loads(raw_text.replace('```json', '').replace('```', '').strip())

    # --- GENERATE HTML ---
    date_str = datetime.now().strftime("%B %d, %Y")
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>Autonomous 2026 | {ai_data['hot_topic']}</title>
</head>
<body class="bg-[#0a0a0a] text-gray-100 min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-4xl w-full border border-white/10 bg-white/5 p-8 rounded-3xl backdrop-blur-xl">
        <div class="flex justify-between items-start mb-12">
            <div class="bg-green-500 text-black px-3 py-1 text-[10px] font-bold rounded-full uppercase tracking-widest">Live Research Feed</div>
            <div class="text-[10px] text-gray-500 font-mono">Date: {date_str}</div>
        </div>

        <h1 class="text-6xl font-black mb-6 tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 italic">
            {ai_data['hot_topic'].upper()}
        </h1>
        
        <p class="text-2xl text-gray-400 mb-10 leading-snug">"{ai_data['analysis']}"</p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <div class="p-4 border border-white/5 bg-white/5 rounded-2xl">
                <p class="text-[10px] text-gray-500 uppercase mb-4">Internal Thought Logs</p>
                <ul class="text-xs space-y-2 font-mono text-blue-300">
                    { "".join([f"<li>> {t}</li>" for t in ai_data['thought_log']]) }
                </ul>
            </div>
            <div class="p-4 border border-white/5 bg-white/5 rounded-2xl flex flex-col justify-between">
                <p class="text-[10px] text-gray-500 uppercase mb-4">Primary Source</p>
                <a href="{ai_data['source_url']}" target="_blank" class="text-xs text-green-400 break-all underline hover:text-white transition">
                    {ai_data['source_url']}
                </a>
            </div>
        </div>

        <div class="text-center text-[10px] text-gray-600 uppercase tracking-widest">
            This site was autonomously built using Tavily Research + Gemini Flash 1.5
        </div>
    </div>
</body>
</html>
    """
    
    with open("index.html", "w") as f:
        f.write(html_content)

if __name__ == "__main__":
    run_advanced_agent()
