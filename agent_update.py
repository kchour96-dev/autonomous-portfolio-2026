import os
import requests
import json
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"🚀 *DASHBOARD SYNC COMPLETE*\n\n🔥 *Top Intel:* {topic}\n\n🌐 [Enter Mission Control](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Advanced Research (Multiple Topics)
    research_context = "Breaking tech 2026: AI, Robotics, Neurotech, Space"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "hottest technology trends may 2026", 
                "max_results": 5
            })
            research_context = str(r.json().get('results', []))
        except: pass

    # 2. Complex Prompt for a FULL DASHBOARD
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {research_context}
    You are an advanced AI Dashboard Architect in 2026. Generate a COMPLEX JSON for a full mission control website.
    Return ONLY JSON:
    {{
      "main_headline": "The biggest news story today",
      "main_analysis": "3 sentence deep dive",
      "sub_news": ["News 1", "News 2", "News 3"],
      "metrics": {{"compute": "98%", "sync": "100%", "evolution": "+2.4%"}},
      "agent_status": "A specific mood (e.g. Analytical, Aggressive, Optimizing)",
      "color": "A vibrant hex code (e.g. #00ff00)"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        txt = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(txt.replace('```json', '').replace('```', '').strip())
    except:
        data = {
            "main_headline": "Neural Network Expansion",
            "main_analysis": "The autonomous grid is expanding across all sectors.",
            "sub_news": ["Compute rising", "Agent active", "Data clear"],
            "metrics": {"compute": "80%", "sync": "90%", "evolution": "1%"},
            "agent_status": "Idle",
            "color": "#3b82f6"
        }

    color = data.get('color', '#3b82f6')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. THE NEW DASHBOARD HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mission Control 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;800&display=swap" rel="stylesheet">
    <style>
        body {{ background: #000; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .border-accent {{ border-color: {color}; }}
        .text-accent {{ color: {color}; }}
        .bg-accent {{ background-color: {color}; }}
        .glow {{ text-shadow: 0 0 10px {color}; }}
        .glass {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); }}
    </style>
</head>
<body class="p-4 md:p-8">
    <!-- Top Bar -->
    <nav class="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
        <div class="text-xl font-black italic tracking-tighter">AUTONOMOUS_HUB <span class="text-accent">2026</span></div>
        <div class="hidden md:flex gap-6 text-[10px] text-gray-500 uppercase tracking-widest">
            <span>Uptime: 99.9%</span>
            <span>Agent: {data['agent_status']}</span>
            <span class="text-accent">{date_str}</span>
        </div>
    </nav>

    <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        <!-- Left: Metrics Column -->
        <div class="md:col-span-3 space-y-6">
            <div class="glass p-6 rounded-2xl">
                <p class="text-[10px] text-gray-500 mb-4 tracking-[0.3em]">SYSTEM_METRICS</p>
                <div class="space-y-4">
                    <div>
                        <div class="flex justify-between text-xs mb-1"><span>COMPUTE</span><span>{data['metrics']['compute']}</span></div>
                        <div class="h-1 bg-white/10 rounded-full"><div class="h-1 bg-accent rounded-full" style="width: {data['metrics']['compute']}"></div></div>
                    </div>
                    <div>
                        <div class="flex justify-between text-xs mb-1"><span>SYNC</span><span>{data['metrics']['sync']}</span></div>
                        <div class="h-1 bg-white/10 rounded-full"><div class="h-1 bg-accent rounded-full" style="width: {data['metrics']['sync']}"></div></div>
                    </div>
                    <div>
                        <div class="flex justify-between text-xs mb-1"><span>EVOLVE</span><span>{data['metrics']['evolution']}</span></div>
                        <div class="h-1 bg-white/10 rounded-full"><div class="h-1 bg-accent rounded-full" style="width: 50%"></div></div>
                    </div>
                </div>
            </div>

            <div class="glass p-6 rounded-2xl">
                <p class="text-[10px] text-gray-500 mb-4 tracking-[0.3em]">RELEVANT_FEEDS</p>
                <ul class="text-[11px] space-y-3 leading-tight">
                    {"".join([f"<li class='border-b border-white/5 pb-2'>» {item}</li>" for item in data['sub_news']])}
                </ul>
            </div>
        </div>

        <!-- Center: The Big Story -->
        <div class="md:col-span-6 space-y-6">
            <div class="glass p-8 rounded-[2rem] border-t-4 border-accent relative overflow-hidden h-full">
                <div class="absolute top-0 right-0 p-8 opacity-5 text-9xl font-black italic">26</div>
                <p class="text-accent text-[10px] mb-4 font-bold tracking-widest">● PRIORITY_ONE_INTEL</p>
                <h1 class="text-4xl md:text-6xl font-black uppercase mb-6 leading-[0.9] glow italic">
                    {data['main_headline']}
                </h1>
                <p class="text-lg md:text-xl text-gray-400 mb-8 leading-relaxed">
                    "{data['main_analysis']}"
                </p>
                <div class="flex gap-4">
                    <button class="bg-accent text-black text-[10px] px-6 py-2 rounded-full font-bold uppercase tracking-widest">Archive Intel</button>
                    <button class="border border-white/20 text-[10px] px-6 py-2 rounded-full font-bold uppercase tracking-widest hover:bg-white/5">Analyze Trace</button>
                </div>
            </div>
        </div>

        <!-- Right: Activity Terminal -->
        <div class="md:col-span-3">
            <div class="glass p-6 rounded-2xl h-full font-mono">
                <p class="text-[10px] text-gray-500 mb-4 tracking-[0.3em]">LIVE_TERMINAL</p>
                <div class="text-[10px] space-y-2 text-green-500/80">
                    <p>> initializing search query...</p>
                    <p>> tavily research complete.</p>
                    <p>> parsing content strings...</p>
                    <p>> gemini flash logic engaged.</p>
                    <p>> building dynamic grid...</p>
                    <p>> deploying to github main.</p>
                    <p>> system optimized.</p>
                    <p class="animate-pulse">> _</p>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-12 pt-6 border-t border-white/5 text-center text-[10px] text-gray-600 tracking-[0.5em] uppercase italic">
        The Portfolio of a Decentralized Intelligence Entity
    </footer>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['main_headline'], data['main_analysis'])

if __name__ == "__main__":
    run_agent()
