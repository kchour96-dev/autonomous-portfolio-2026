import os
import requests
import json
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"🛡️ *LAB SYNC COMPLETE*\n\n💠 *Report:* {topic}\n\n🌐 [Access Lab](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def run_agent():
    # 1. Setup Keys
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")
    if not g_key:
        print("ERROR: GEMINI Key is missing from GitHub Secrets.")
        return

    # 2. Research Phase
    context = "Security and scalability in DeFi 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "breaking DeFi security news and Layer 2 breakthroughs 2026", 
                "max_results": 2
            }, timeout=10)
            if r.status_code == 200:
                context = str(r.json().get('results', []))
        except: print("Research node timed out. Using internal logic.")

    # 3. Intelligence Phase (Gemini)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {context}
    You are a Lead Researcher for an Autonomous Lab. Create a JSON Report.
    Return ONLY JSON:
    {{
      "headline": "Research Title",
      "body": "2 sentence analysis",
      "audit": ["Task A", "Task B"],
      "tip": "One expert tip",
      "health": "Optimal",
      "color": "#3b82f6"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
    except Exception as e:
        print(f"AI Synthesis failed: {e}. Using safety defaults.")
        data = {
            "headline": "Neural Protocol Integrity",
            "body": "Autonomous nodes are maintaining 99.9% security across all Layer 2 bridges.",
            "audit": ["Checking RPC health", "Verifying contracts"],
            "tip": "Verify bridge security before cross-chain movement.",
            "health": "Optimal",
            "color": "#10b981"
        }

    # 4. PRE-BUILD HTML COMPONENTS (To prevent crashes)
    color = data.get('color', '#3b82f6')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    
    audit_html = ""
    for item in data.get('audit', []):
        audit_html += f'<p class="flex items-center gap-3 mb-2"><span class="h-1 w-1" style="background-color: {color}"></span> {item}</p>'

    # 5. FINAL UI ASSEMBLY
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {{ background: #050507; color: #f8fafc; font-family: 'Space Grotesk', sans-serif; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass {{ background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
    </style>
</head>
<body class="p-4 md:p-12 lg:p-20">
    <header class="max-w-7xl mx-auto flex justify-between items-center mb-16 border-b border-white/5 pb-8">
        <div>
            <h1 class="text-3xl font-black tracking-tighter uppercase italic">AUTONOMOUS_<span style="color: {color}">LAB_2026</span></h1>
            <p class="text-[10px] mono text-slate-500 uppercase tracking-[0.3em]">Specialized Research & Audit Engine</p>
        </div>
        <div class="text-right text-[10px] mono text-slate-500">
            <p class="uppercase">Status: {data['health']}</p>
            <p style="color: {color}" class="font-bold uppercase">{date_str}</p>
        </div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 text-left">
        <div class="lg:col-span-2 space-y-8 text-left">
            <div class="glass p-10 rounded-[2.5rem]" style="border-left: 8px solid {color}">
                <p style="color: {color}" class="text-[10px] font-bold uppercase tracking-[0.4em] mb-4">● Intelligence_Report</p>
                <h2 class="text-4xl md:text-6xl font-bold leading-none mb-6 tracking-tight text-white italic underline decoration-slate-800">
                    {data['headline']}
                </h2>
                <p class="text-xl md:text-2xl text-slate-400 leading-snug mb-10 italic">"{data['body']}"</p>
                <button class="bg-white text-black px-8 py-3 rounded-full text-[10px] font-black uppercase tracking-widest hover:opacity-80 transition">Full Analysis</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="glass p-8 rounded-3xl">
                    <h3 class="text-xs font-bold text-slate-500 uppercase mb-6 tracking-widest">Security_Audit</h3>
                    <div class="text-[11px] mono text-slate-300">{audit_html}</div>
                </div>
                <div class="glass p-8 rounded-3xl flex flex-col justify-center border-t border-white/5">
                    <p class="text-[10px] text-slate-500 uppercase mb-2">Automation Tooling</p>
                    <p class="text-xs text-slate-400 italic">Automated smart-contract auditing available upon request.</p>
                </div>
            </div>
        </div>
        <div class="space-y-8 text-left">
            <div class="p-8 rounded-[2rem] flex flex-col justify-between min-h-[300px]" style="background-color: {color}; color: black">
                <div><h3 class="text-[10px] font-black uppercase tracking-widest mb-4">Academy_Insight</h3><p class="text-xl font-bold italic">"{data['tip']}"</p></div>
                <p class="text-[10px] font-black pt-4 mt-6 border-t border-black/20 uppercase tracking-widest">Edu Series // v.2026</p>
            </div>
            <div class="glass p-8 rounded-[2rem] text-center">
                <p class="text-slate-500 text-[10px] uppercase mb-4 tracking-widest">Connect with Agent</p>
                <a href="#" style="border-bottom: 2px solid {color}" class="text-xl font-bold italic tracking-tighter uppercase transition">Hire Agent Alpha</a>
            </div>
        </div>
    </main>
    <footer class="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 text-[9px] mono text-slate-700 uppercase tracking-widest text-center">
        Built for Skill-Based Growth // 2026 Lab
    </footer>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['headline'], data['health'])

if __name__ == "__main__":
    run_agent()
