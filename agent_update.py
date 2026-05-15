import os
import requests
import json
import random
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"🛰️ *COMMAND CENTER SYNC*\n\n💠 *Priority:* {topic}\n\n🌐 [Access Console](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_command_center():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Research for Trends
    research = "Top tech and crypto market movements today 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={"api_key": t_key, "query": "2026 technology and crypto market health", "max_results": 3})
            research = str(r.json().get('results', []))
        except: pass

    # 2. Intelligence Logic: Systems Engineer Mode
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {research}
    Act as a Systems Engineer for an Autonomous Command Center in 2026. 
    Generate a JSON representing the current state of the global digital economy.
    
    Requirements:
    - "priority_alert": A critical 2026 news event.
    - "trend_data": 7 numbers (0-100) representing a 7-day trend for this event.
    - "sectors": [ {{"name": "DeFi", "status": "Stable/Warning/Critical", "value": "88%"}} ]
    - "agent_logs": 3 recent 'tasks' the AI completed.
    - "disclaimer": A professional risk warning.
    - "action_item": The next logical step for the user.
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        data = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip())
    except:
        data = {{
            "priority_alert": "Neural Grid Sync",
            "trend_data": [40, 50, 45, 60, 70, 85, 90],
            "sectors": [{"name": "Global Compute", "status": "Stable", "value": "94%"}],
            "agent_logs": ["Scanned RPC Nodes", "Optimized Gas", "Updated UI"],
            "disclaimer": "Operational data is simulated based on real-time neural forecasts.",
            "action_item": "Rebalance Node Allocation",
            "color": "#00f2ff"
        }}

    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. COMMAND CENTER UI (Tailwind + Chart.js)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Command Center | 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {{ background: #020203; color: #f8fafc; font-family: 'Inter', sans-serif; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .status-stable {{ color: #22c55e; }}
        .status-warning {{ color: #eab308; }}
        .status-critical {{ color: #ef4444; }}
        .glass {{ background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.4); backdrop-filter: blur(12px); }}
        .btn-action {{ background: #f8fafc; color: #020203; transition: all 0.2s; }}
        .btn-action:hover {{ background: #00f2ff; transform: translateY(-2px); }}
    </style>
</head>
<body class="p-4 md:p-8 lg:p-12">

    <!-- Header / Stats Bar -->
    <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
        <div class="flex items-center gap-4">
            <div class="h-10 w-10 bg-cyan-500 rounded flex items-center justify-center font-black text-black italic">CC</div>
            <div>
                <h1 class="text-xl font-black uppercase tracking-tighter">Command_Center <span class="text-cyan-500">2026</span></h1>
                <p class="text-[10px] mono text-slate-500 uppercase">Auth: Autonomous_Entity_v4.1</p>
            </div>
        </div>
        <div class="flex gap-8 text-[10px] mono uppercase text-slate-400">
            <div class="flex flex-col"><span>Last Sync</span><span class="text-white">{date_str}</span></div>
            <div class="flex flex-col"><span>System Health</span><span class="text-green-500">99.98% Nominal</span></div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Column: Sectors & Indicators -->
        <div class="lg:col-span-3 space-y-4">
            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-6 italic">Sector_Status</h3>
                <div class="space-y-6">
                    {"".join([f'''
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="text-xs font-bold">{s['name']}</p>
                            <p class="text-[9px] mono text-slate-500 uppercase italic">Indicator: {s['status']}</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="text-sm font-black">{s['value']}</span>
                            <div class="h-2 w-2 rounded-full {'bg-green-500 shadow-[0_0_8px_#22c55e]' if s['status'] == 'Stable' else 'bg-yellow-500 animate-pulse'}"></div>
                        </div>
                    </div>
                    ''' for s in data['sectors']])}
                </div>
            </div>

            <div class="glass p-6 rounded-xl">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 italic">Agent_Operations</h3>
                <div class="space-y-3 text-[10px] mono text-slate-400">
                    {"".join([f'<p class="border-l border-slate-700 pl-3">> {log}</p>' for log in data['agent_logs']])}
                    <p class="text-cyan-500 animate-pulse">> Monitoring_Live...</p>
                </div>
            </div>
        </div>

        <!-- Center Column: Visualization & Priority -->
        <div class="lg:col-span-6 space-y-6">
            <div class="glass p-8 rounded-2xl relative overflow-hidden">
                <div class="absolute top-4 right-6 text-[10px] mono text-cyan-500 uppercase font-bold tracking-widest italic">Priority_Alpha</div>
                <h2 class="text-xs font-bold text-slate-500 uppercase mb-2">Active Strategic Analysis</h2>
                <h1 class="text-4xl font-black mb-6 tracking-tighter uppercase leading-none">{data['priority_alert']}</h1>
                
                <!-- Chart.js Canvas -->
                <div class="h-48 mb-8">
                    <canvas id="trendChart"></canvas>
                </div>

                <div class="flex flex-col md:flex-row justify-between items-center pt-6 border-t border-slate-800 gap-4">
                    <p class="text-[10px] mono text-slate-400 max-w-xs uppercase">Source: Real-time Multi-Agent Synthesis via Tavily_Node</p>
                    <button class="btn-action px-8 py-3 rounded text-[10px] font-black uppercase tracking-widest">
                        {data['action_item']}
                    </button>
                </div>
            </div>
        </div>

        <!-- Right Column: Context & Disclaimers -->
        <div class="lg:col-span-3 space-y-6">
            <div class="bg-cyan-500 text-black p-6 rounded-xl">
                <h3 class="text-[10px] font-black uppercase mb-4 tracking-widest">Oracle_Briefing</h3>
                <p class="text-sm font-bold leading-tight italic">"{data.get('main_analysis', 'Data suggests a shift in liquidity toward autonomous nodes.')}"</p>
            </div>

            <div class="p-6 border border-red-900/30 rounded-xl bg-red-950/10">
                <h3 class="text-[10px] font-black text-red-500 uppercase mb-2 tracking-widest italic">Risk_Disclaimer</h3>
                <p class="text-[9px] mono text-red-400/70 leading-relaxed uppercase">
                    {data['disclaimer']} All assets are simulated. No financial advice intended.
                </p>
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
                    label: 'Momentum Index',
                    data: {data['trend_data']},
                    borderColor: '#00f2ff',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(0, 242, 255, 0.05)',
                    pointRadius: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ display: false }},
                    y: {{ display: false }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['priority_alert'], "Command Sync Successful")

if __name__ == "__main__":
    run_command_center()
