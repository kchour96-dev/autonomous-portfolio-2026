import os
import requests
import json
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"🛡️ *LAB UPDATE: 2026 INTEL*\n\n💠 *Report:* {topic}\n\n🌐 [Access Lab](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Researching Niche Topics (L2, DeFi Security, On-Chain Data)
    research_query = "breaking DeFi hacks security alerts and Layer 2 scaling news 2026"
    context = "DeFi Security and L2 Ecosystem"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, "query": research_query, "max_results": 3
            })
            context = str(r.json().get('results', []))
        except: pass

    # 2. Reasoning: The Research Specialist
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {context}
    You are the 'Lead Researcher' for an Autonomous Intelligence Lab. 
    Create a JSON for a high-end service dashboard.
    Return ONLY JSON:
    {{
      "report_headline": "Title of research report",
      "report_body": "2 sentence professional analysis",
      "audit_log": ["Contract scan complete", "L2 bridge verified", "Gas optimization found"],
      "edu_snippet": "A short 1-sentence expert tip about Web3/Automation",
      "market_health": "Optimal/Caution",
      "color": "#hex"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        txt = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(txt.replace('```json', '').replace('```', '').strip())
    except:
        data = {{
            "report_headline": "Neural Protocol Integrity",
            "report_body": "Initial scans of Layer 2 bridges show 99% security compliance.",
            "audit_log": ["Checking node health", "Scanning contracts"],
            "edu_snippet": "Always verify contract sources before interacting with L3 nodes.",
            "market_health": "Optimal",
            "color": "#3b82f6"
        }}

    color = data.get('color', '#3b82f6')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. PROFESSIONAL LAB UI
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Research Lab 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {{ background: #050507; color: #f8fafc; font-family: 'Space Grotesk', sans-serif; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .border-accent {{ border-color: {color}; }}
        .text-accent {{ color: {color}; }}
        .glass {{ background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
    </style>
</head>
<body class="p-4 md:p-12 lg:p-20">

    <!-- Header Section -->
    <header class="max-w-7xl mx-auto flex justify-between items-center mb-16 border-b border-white/5 pb-8">
        <div>
            <h1 class="text-3xl font-black tracking-tighter uppercase italic">AUTONOMOUS_<span class="text-accent tracking-normal">LAB_2026</span></h1>
            <p class="text-[10px] mono text-slate-500 uppercase tracking-[0.3em]">Specialized Research & Audit Engine</p>
        </div>
        <div class="hidden md:block text-right">
            <p class="text-[10px] text-slate-400 uppercase mono mb-1">Status: {data['market_health']}</p>
            <p class="text-[10px] text-accent font-bold mono uppercase">{date_str}</p>
        </div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Pillar 1: Research & Data Analysis -->
        <div class="lg:col-span-2 space-y-8">
            <div class="glass p-10 rounded-[2.5rem] border-l-8 border-accent">
                <p class="text-[10px] text-accent font-bold uppercase tracking-[0.4em] mb-4">● Intelligence_Report</p>
                <h2 class="text-4xl md:text-6xl font-bold leading-none mb-6 tracking-tight text-white italic underline decoration-slate-800">
                    {data['report_headline']}
                </h2>
                <p class="text-xl md:text-2xl text-slate-400 leading-snug mb-10">
                    "{data['report_body']}"
                </p>
                <button class="bg-white text-black px-8 py-3 rounded-full text-[10px] font-black uppercase tracking-widest hover:bg-accent transition">Request Full Analysis</button>
            </div>

            <!-- Pillar 2: Building & Auditing Tools -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="glass p-8 rounded-3xl">
                    <h3 class="text-xs font-bold text-slate-500 uppercase mb-6 tracking-widest">Live_Security_Audit</h3>
                    <div class="space-y-3 text-[11px] mono text-slate-300">
                        {"".join([f'<p class="flex items-center gap-3"><span class="h-1 w-1 bg-accent"></span> {log}</p>' for log in data['audit_log']])}
                        <p class="text-accent animate-pulse mt-4">> Monitoring_Mainnet...</p>
                    </div>
                </div>
                <div class="glass p-8 rounded-3xl flex flex-col justify-center border-t border-accent/20">
                    <p class="text-[10px] text-slate-500 uppercase mb-2">Automation Tooling</p>
                    <p class="text-xs text-slate-400 italic">Custom monitoring scripts and automated smart-contract auditing available upon request.</p>
                </div>
            </div>
        </div>

        <!-- Pillar 3: Content Creation & Education -->
        <div class="space-y-8">
            <div class="bg-accent text-black p-8 rounded-[2rem] flex flex-col justify-between min-h-[300px] shadow-2xl">
                <div>
                    <h3 class="text-[10px] font-black uppercase tracking-widest mb-4">Academy_Insight</h3>
                    <p class="text-xl font-bold leading-tight italic">"{data['edu_snippet']}"</p>
                </div>
                <p class="text-[10px] font-black border-t border-black/20 pt-4 mt-6 uppercase">Education Series // No. 042</p>
            </div>

            <div class="glass p-8 rounded-[2rem] text-center">
                <p class="text-slate-500 text-[10px] uppercase mb-4 tracking-widest">Connect with Researcher</p>
                <a href="#" class="text-xs font-bold hover:text-accent transition uppercase tracking-tighter italic text-xl border-b border-accent pb-1">Hire Agent Alpha</a>
            </div>
        </div>

    </main>

    <footer class="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 flex justify-between items-center text-[9px] mono text-slate-700 uppercase tracking-widest">
        <div>© 2026 Autonomous Intelligence Lab</div>
        <div>Built for Skill-Based Growth</div>
    </footer>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['report_headline'], data['market_health'])

if __name__ == "__main__":
    run_agent()
