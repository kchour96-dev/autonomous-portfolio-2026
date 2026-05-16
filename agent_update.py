import os
import requests
import json
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if token and chat_id:
        msg = f"🛰️ *LAB UPDATE: {topic}*\n\n{summary}\n\n🔗 https://autonomous-portfolio-2026.live"
        try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
        except: pass

def run_master_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")
    
    # 1. Research Step
    context = "Web3 security and AI breakthroughs 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={"api_key": t_key, "query": "latest DeFi hacks, Web3 security risks and L2 scaling news June 2026", "max_results": 4}, timeout=10)
            context = str(r.json().get('results', []))
        except: pass

    # 2. Reasoning Step
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {context}
    You are a Senior Security Architect. Create a deep-dive technical JSON.
    RULES: 'report' must be 4 long paragraphs of expert analysis.
    JSON Format:
    {{
      "title": "Professional Headline",
      "summary": "2 sentence executive brief",
      "report": "4 long paragraphs of deep technical analysis",
      "threat_level": "Low/Medium/High/Critical",
      "steps": ["Step 1", "Step 2", "Step 3"],
      "tip": "One expert skill-building tip",
      "color": "#hex_accent_color"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(raw_text.replace('```json', '').replace('```', '').strip())
    except Exception as e:
        data = {"title": "Neural Protocol Sync", "summary": "System rebalancing.", "report": "Standard maintenance in progress.", "threat_level": "Low", "steps": ["Check Nodes"], "tip": "Always verify hash.", "color": "#3b82f6"}

    # 3. Archive Logic (Preserve old posts)
    history_html = ""
    try:
        if os.path.exists("index.html"):
            with open("index.html", "r") as f:
                content = f.read()
                if "<!-- HIST_S -->" in content:
                    history_html = content.split("<!-- HIST_S -->")[1].split("<!-- HIST_E -->")[0]
    except: pass
    
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_archive = f"<div class='mb-4 border-l border-white/10 pl-4'><p class='text-[10px] opacity-50'>{date_str}</p><p class='text-[11px] font-bold'>{data['title']}</p></div>"
    final_history = (new_archive + history_html)[:3000]

    # 4. Final UI Assembly
    color = data.get('color', '#3b82f6')
    steps_html = "".join([f'<p class="mb-2">> {s}</p>' for s in data['steps']])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Research Lab</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {{ background: #020203; color: #f8fafc; font-family: 'Space Grotesk', sans-serif; text-align: left; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass {{ background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(12px); }}
        #reportSection {{ display: none; }}
    </style>
</head>
<body class="p-4 md:p-12 lg:p-20">
    <header class="max-w-7xl mx-auto flex justify-between items-center mb-16 border-b border-white/5 pb-8">
        <div>
            <h1 class="text-3xl font-black italic tracking-tighter uppercase">AUTONOMOUS_<span style="color: {color}">LAB_2026</span></h1>
            <p class="text-[10px] mono text-slate-500 uppercase tracking-widest italic">Node Status: {data['threat_level']}</p>
        </div>
        <div class="text-right text-[10px] mono text-slate-500 uppercase font-bold">
            <p style="color: {color}">{date_str}</p>
        </div>
    </header>

    <main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div class="lg:col-span-8 space-y-12">
            <section class="glass p-10 rounded-[3rem]" style="border-left: 8px solid {color}">
                <p style="color: {color}" class="text-[10px] font-black uppercase tracking-[0.4em] mb-4">● Intelligence_Report</p>
                <h2 class="text-4xl md:text-7xl font-bold mb-6 tracking-tighter leading-none text-white italic">{data['title']}</h2>
                <p class="text-xl md:text-2xl text-slate-400 mb-10 leading-tight italic">"{data['summary']}"</p>
                <button onclick="toggle()" id="btn" class="bg-white text-black px-10 py-4 rounded-full text-[11px] font-black uppercase tracking-widest hover:opacity-80 transition">Read Full Analysis ↓</button>
                <div id="reportSection" class="mt-12 pt-12 border-t border-white/10">
                    <div class="text-lg text-slate-300 leading-relaxed space-y-6 whitespace-pre-line">{data['report']}</div>
                </div>
            </section>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="glass p-8 rounded-3xl"><h3 class="text-xs font-bold text-slate-500 uppercase mb-6 tracking-widest">Audit_Log</h3><div class="text-[10px] mono text-slate-400 uppercase">{steps_html}</div></div>
                <div class="glass p-8 rounded-3xl" style="background: {color}22"><h3 class="text-xs font-bold text-slate-500 uppercase mb-4 tracking-widest tracking-widest">Skill_Sync</h3><p class="text-sm font-bold italic leading-snug">"{data['tip']}"</p></div>
            </div>
        </div>
        <aside class="lg:col-span-4">
            <div class="glass p-8 rounded-[2.5rem]">
                <h3 class="text-xs font-bold text-slate-500 uppercase mb-8 tracking-[0.3em] italic">Intelligence_Archive</h3>
                <div class="mono"><!-- HIST_S -->{final_history}<!-- HIST_E --></div>
            </div>
        </aside>
    </main>
    <script>
        function toggle() {{
            var x = document.getElementById("reportSection");
            var b = document.getElementById("btn");
            if (x.style.display === "none" || x.style.display === "") {{ x.style.display = "block"; b.innerHTML = "Close Report ↑"; }}
            else {{ x.style.display = "none"; b.innerHTML = "Read Full Analysis ↓"; }}
        }}
    </script>
</body>
</html>"""
    with open("index.html", "w") as f: f.write(html)
    send_telegram(data['title'], data['summary'])

if __name__ == "__main__": run_master_agent()
