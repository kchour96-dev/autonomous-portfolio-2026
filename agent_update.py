import os
import requests
import json
from datetime import datetime

def run_agent():
    # 1. Get Keys
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")
    if not g_key:
        print("ERROR: GEMINI key missing")
        return

    # 2. Research
    context = "Web3 and AI market trends 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, "query": "2026 tech and crypto market status", "max_results": 2
            }, timeout=10)
            context = str(r.json().get('results', []))
        except: print("Search failed, using backup.")

    # 3. Brain (Gemini)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {context}
    You are a Systems Engineer in 2026. Create a Command Center JSON. 
    Return ONLY JSON:
    {{
      "alert": "Headline news",
      "analysis": "2 sentence forecast",
      "trend": [40, 50, 45, 60, 70, 85, 90],
      "sectors": [{{"n": "DeFi", "s": "Stable", "v": "92%"}}],
      "logs": ["Task 1", "Task 2"],
      "action": "Next Step"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        raw = resp.json()['candidates'][0]['content']['parts'][0]['text']
        clean = raw.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean)
    except Exception as e:
        print(f"AI Error: {e}")
        data = {
            "alert": "System Rebalancing", "analysis": "Neural nodes are syncing.", 
            "trend": [50, 52, 48, 55, 60, 58, 65],
            "sectors": [{"n": "Global Sync", "s": "Stable", "v": "100%"}],
            "logs": ["Internal check", "Node refresh"], "action": "Standby"
        }

    # 4. PRE-PROCESS HTML BLOCKS (Fixes the syntax error)
    sector_html = ""
    for s in data.get('sectors', []):
        dot_color = "bg-green-500 shadow-[0_0_8px_#22c55e]" if s['s'] == "Stable" else "bg-yellow-500 animate-pulse"
        sector_html += f'''
        <div class="flex justify-between items-center mb-6">
            <div><p class="text-xs font-bold">{s['n']}</p><p class="text-[9px] text-slate-500 uppercase italic">{s['s']}</p></div>
            <div class="flex items-center gap-3"><span class="text-sm font-black">{s['v']}</span><div class="h-2 w-2 rounded-full {dot_color}"></div></div>
        </div>'''

    log_html = "".join([f'<p class="border-l border-slate-700 pl-3 mb-2">> {l}</p>' for l in data.get('logs', [])])
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 5. FINAL HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background: #020203; color: #f8fafc; font-family: sans-serif; }}
        .glass {{ background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); backdrop-filter: blur(12px); }}
    </style>
</head>
<body class="p-4 md:p-12">
    <header class="max-w-7xl mx-auto flex justify-between items-center mb-10">
        <h1 class="text-xl font-black uppercase tracking-tighter">Command_Center <span class="text-cyan-400">2026</span></h1>
        <div class="text-[10px] text-slate-400 text-right uppercase font-mono">Sync: {date_str}</div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div class="lg:col-span-3 space-y-4">
            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase mb-6 italic">Sector_Status</h3>
                {sector_html}
            </div>
            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase mb-4 italic">Agent_Operations</h3>
                <div class="text-[10px] font-mono text-slate-400">{log_html}</div>
            </div>
        </div>

        <div class="lg:col-span-6">
            <div class="glass p-8 rounded-2xl">
                <p class="text-[10px] text-cyan-400 uppercase font-bold mb-2">Priority_Analysis</p>
                <h1 class="text-4xl font-black mb-6 uppercase tracking-tighter">{data['alert']}</h1>
                <div class="h-48 mb-8"><canvas id="trendChart"></canvas></div>
                <div class="flex justify-between items-center pt-6 border-t border-slate-800">
                    <p class="text-[9px] text-slate-500 uppercase">Src: Neural_Sync_v4</p>
                    <button class="bg-white text-black px-6 py-2 rounded text-[10px] font-black uppercase hover:bg-cyan-400 transition">{data['action']}</button>
                </div>
            </div>
        </div>

        <div class="lg:col-span-3 space-y-6">
            <div class="bg-cyan-500 text-black p-6 rounded-xl"><p class="text-sm font-bold italic">"{data['analysis']}"</p></div>
            <div class="p-6 border border-red-900/30 rounded-xl bg-red-950/10 text-[9px] text-red-400 leading-relaxed uppercase">
                Risk: Simulated data for 2026 forecast. Not financial advice.
            </div>
        </div>
    </main>

    <script>
        const ctx = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
                datasets: [{{
                    data: {data['trend']},
                    borderColor: '#00f2ff',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                    backgroundColor: 'rgba(0, 242, 255, 0.05)'
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ display: false }}, y: {{ display: false }} }} }}
        }});
    </script>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    # Telegram
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHANNEL_ID")
    if token and chat:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": f"🛰️ COMMAND UPDATE: {data['alert']}"})

if __name__ == "__main__":
    run_agent()
