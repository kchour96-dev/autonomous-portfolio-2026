import os
import requests
import json
from datetime import datetime

def run_agent():
    # 1. Setup Keys
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")
    if not g_key:
        print("CRITICAL ERROR: GEMINI Secret is missing!")
        return

    # 2. Advanced Research (Web3 & AI 2026)
    context = "2026 tech trends and crypto market"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, "query": "breaking crypto web3 and ai news 2026", "max_results": 3
            }, timeout=10)
            if r.status_code == 200:
                context = str(r.json().get('results', []))
        except: print("Tavily search failed, using backup logic.")

    # 3. Brain (Gemini Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research Data: {context}
    You are a Systems Engineer for a 2026 Command Center. Create a JSON for a Professional Dashboard.
    Return ONLY PURE JSON:
    {{
      "alert": "Headline news event",
      "forecast": "2 sentence professional analysis",
      "trend": [40, 55, 45, 70, 85, 80, 95],
      "sectors": [{{"name": "DeFi", "status": "Stable", "val": "94%"}}, {{"name": "Compute", "status": "Warning", "val": "72%"}}],
      "action": "Immediate Action Item",
      "logs": ["Network scan complete", "Node rebalanced"]
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(raw_text.replace('```json', '').replace('```', '').strip())
    except Exception as e:
        print(f"Gemini Error: {e}. Using Default Safety Data.")
        data = {
            "alert": "System Neural Sync", "forecast": "Autonomous nodes are rebalancing across the global grid.",
            "trend": [50, 55, 52, 60, 65, 70, 75], "sectors": [{"name": "Global Sync", "status": "Stable", "val": "100%"}],
            "action": "Initiate Diagnostics", "logs": ["Node 1-A Active", "Database Secure"]
        }

    # 4. Generate UI Components
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    
    sector_html = ""
    for s in data.get('sectors', []):
        color = "bg-green-500 shadow-[0_0_8px_#22c55e]" if s['status'] == "Stable" else "bg-yellow-500 animate-pulse"
        sector_html += f'''
        <div class="flex justify-between items-center mb-6">
            <div><p class="text-xs font-bold font-mono">{s['name']}</p><p class="text-[9px] text-slate-500 uppercase italic">{s['status']}</p></div>
            <div class="flex items-center gap-3"><span class="text-sm font-black">{s['val']}</span><div class="h-2 w-2 rounded-full {color}"></div></div>
        </div>'''

    log_html = "".join([f'<p class="border-l border-slate-700 pl-3 mb-2">> {log}</p>' for log in data.get('logs', [])])

    # 5. Build Final HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Command Center 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background: #020203; color: #f8fafc; font-family: sans-serif; }}
        .glass {{ background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); backdrop-filter: blur(12px); }}
    </style>
</head>
<body class="p-4 md:p-10 lg:p-16">
    <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
        <div class="flex items-center gap-4">
            <div class="h-10 w-10 bg-cyan-400 rounded flex items-center justify-center font-black text-black italic">CC</div>
            <h1 class="text-xl font-black uppercase tracking-tighter">Command_Center <span class="text-cyan-400 font-mono">2026</span></h1>
        </div>
        <div class="text-[10px] text-slate-500 uppercase font-mono tracking-widest">Last_Sync: {date_str}</div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div class="lg:col-span-3 space-y-4">
            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase mb-6 italic tracking-widest">Sector_Status</h3>
                {sector_html}
            </div>
            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase mb-4 italic tracking-widest">Agent_Ops</h3>
                <div class="text-[9px] font-mono text-slate-400">{log_html}</div>
            </div>
        </div>

        <div class="lg:col-span-6">
            <div class="glass p-8 rounded-2xl relative overflow-hidden">
                <p class="text-[10px] text-cyan-400 uppercase font-bold mb-2 tracking-[0.3em]">Priority_Analysis</p>
                <h1 class="text-4xl font-black mb-6 uppercase tracking-tighter italic">{data['alert']}</h1>
                <div class="h-48 mb-8"><canvas id="trendChart"></canvas></div>
                <div class="flex justify-between items-center pt-6 border-t border-slate-800">
                    <p class="text-[9px] text-slate-500 uppercase font-mono italic">Source: Neural_Node_Alpha</p>
                    <button class="bg-white text-black px-6 py-2 rounded text-[10px] font-black uppercase hover:bg-cyan-400 transition">{data['action']}</button>
                </div>
            </div>
        </div>

        <div class="lg:col-span-3 space-y-6">
            <div class="bg-cyan-400 text-black p-6 rounded-xl shadow-[0_0_20px_rgba(34,211,238,0.2)]">
                <p class="text-[10px] font-black uppercase mb-2 tracking-widest">Oracle_Brief</p>
                <p class="text-sm font-bold italic leading-tight">"{data['forecast']}"</p>
            </div>
            <div class="p-6 border border-red-900/30 rounded-xl bg-red-950/10 text-[9px] text-red-400/70 leading-relaxed uppercase font-mono">
                Disclaimer: Operational data is simulated for 2026 forecast. Not financial advice.
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
                    borderColor: '#22d3ee',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0,
                    fill: true,
                    backgroundColor: 'rgba(34, 211, 238, 0.05)'
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ display: false }}, y: {{ display: false }} }} }}
        }});
    </script>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    # Send Telegram
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHANNEL_ID")
    if token and chat:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat, "text": f"🛰️ COMMAND SYNC: {data['alert']}"})
        except: print("Telegram failed.")

if __name__ == "__main__":
    run_agent()
