import os
import requests
import json
from datetime import datetime

def send_telegram(topic, insight):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"🌅 *PORTFOLIO 2026 UPDATE*\n\n🔥 *Hot Topic:* {topic}\n\n🔮 *Forecast:* {insight}\n\n🌐 [View Live Site](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Smarter Research (Search for NEW breaking tech)
    context = "Future technology 2026"
    if t_key:
        try:
            # We ask for the latest hour's news to keep it fresh
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "breaking technology news robotics AI space 2026", 
                "search_depth": "advanced",
                "max_results": 3
            })
            results = r.json().get('results', [])
            context = "\n".join([f"{res['title']}: {res['content']}" for res in results])
        except: print("Search failed.")

    # 2. Executive Prompt
    # We tell the AI to NEVER repeat itself and to pick the most exciting news
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    RESEARCH DATA: {context}
    
    ROLE: You are the Chief AI Editor of 'Autonomous Portfolio 2026'. 
    TASK: Pick the MOST EXCITING news from the research and create a futuristic report.
    RULES: 
    1. Do not be boring. 
    2. Focus on how this news changes the year 2026.
    3. Use a high-tech, futuristic tone.
    
    Return ONLY a JSON object: 
    {{"topic": "Headline", "analysis": "2 sentence expert forecast", "color_theme": "hex code for accent color"}}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        txt = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(txt.replace('```json', '').replace('```', '').strip())
    except:
        data = {"topic": "Neural Network Sync", "analysis": "The 2026 core is rebalancing for optimal data flow.", "color_theme": "#22c55e"}

    # 3. New Dynamic Design (The background changes color based on the topic!)
    color = data.get('color_theme', '#22c55e')
    date_str = datetime.now().strftime("%B %d, %Y | %H:%M %p")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: #000; color: #fff; font-family: ui-monospace, monospace; }}
        .accent-border {{ border-color: {color}; }}
        .accent-text {{ color: {color}; }}
        .glow {{ text-shadow: 0 0 15px {color}; }}
    </style>
</head>
<body class="p-4 md:p-20 min-h-screen flex items-center justify-center">
    <div class="max-w-3xl w-full border-2 accent-border p-10 rounded-[3rem] bg-gradient-to-br from-gray-900 to-black shadow-2xl">
        <div class="flex justify-between items-center mb-12 text-[10px] tracking-[0.3em] accent-text font-bold">
            <span class="animate-pulse">● CORE_STABLE</span>
            <span>LAST UPDATE: {date_str}</span>
        </div>
        
        <p class="text-xs uppercase tracking-widest text-gray-500 mb-2">Current Intelligence Focus:</p>
        <h1 class="text-5xl md:text-7xl font-black mb-8 leading-none glow tracking-tighter uppercase italic">
            {data['topic']}
        </h1>
        
        <div class="space-y-6 border-l-2 accent-border pl-6 mb-12">
            <p class="text-xl md:text-2xl text-gray-300 leading-tight">
                "{data['analysis']}"
            </p>
        </div>

        <div class="flex justify-between items-end">
            <div class="text-[9px] text-gray-700 leading-tight">
                AUTONOMOUS SYSTEM 2026<br>
                RESEARCH_NODE: TAVILY_AI<br>
                BRAIN_NODE: GEMINI_1.5_FLASH
            </div>
            <a href="https://autonomous-portfolio-2026.live" class="accent-text text-xs font-bold underline hover:opacity-50 transition">REFRESH_NODE</a>
        </div>
    </div>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['topic'], data['analysis'])
    print("AUTONOMOUS UPDATE COMPLETE.")

if __name__ == "__main__":
    run_agent()
