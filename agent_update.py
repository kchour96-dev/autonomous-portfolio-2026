import os
import requests
import json
from datetime import datetime

def run_elite_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. DEEP RESEARCH (The Scout)
    research_data = "Global tech and web3 shifts May 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "most controversial and high-growth tech trends 2026", 
                "max_results": 5
            })
            research_data = str(r.json().get('results', []))
        except: pass

    # 2. THE DUAL-AGENT REASONING (The Brain)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {research_data}
    
    Task: Act as two separate AI entities: 'The Scout' (Optimist) and 'The Critic' (Skeptic).
    1. The Scout identifies a massive 2026 trend.
    2. The Critic finds one fatal flaw or risk in it.
    3. You (The System) provide the 'Final Oracle Decision'.

    Return ONLY JSON:
    {{
      "trend_title": "Headline",
      "scout_view": "One sentence optimistic view",
      "critic_view": "One sentence skeptical view",
      "oracle_decision": "The final 2-sentence synthesis",
      "confidence_score": 0-100,
      "market_impact": "High/Critical",
      "accent_color": "#hex"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        data = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip())
    except:
        data = {"trend_title": "Neural Linkage", "scout_view": "Total connectivity.", "critic_view": "Privacy collapse.", "oracle_decision": "Proceed with caution.", "confidence_score": 85, "market_impact": "High", "accent_color": "#00ff00"}

    color = data.get('accent_color', '#00ff00')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. THE ELITE SWISS-TERMINAL HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ORACLE_2026 | {data['trend_title']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;900&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        body {{ background: #050505; color: #fff; font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .text-accent {{ color: {color}; }}
        .bg-accent {{ background-color: {color}; }}
        .border-accent {{ border-color: {color}; }}
        .glow {{ text-shadow: 0 0 20px {color}66; }}
        @keyframes pulse-slow {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
        .animate-flicker {{ animation: pulse-slow 3s infinite; }}
    </style>
</head>
<body class="p-6 md:p-16 lg:p-24 min-h-screen border-t-8 border-accent">
    
    <header class="max-w-6xl mx-auto flex justify-between items-start mb-24">
        <div class="space-y-1">
            <h1 class="text-xs font-black tracking-[0.5em] uppercase text-gray-500">Autonomous_Portfolio_v.4</h1>
            <div class="text-2xl font-black italic italic tracking-tighter uppercase">Oracle<span class="text-accent">_2026</span></div>
        </div>
        <div class="text-right mono text-[10px] text-gray-600 uppercase space-y-1">
            <p class="text-accent animate-flicker font-bold">● System_Live</p>
            <p>{date_str}</p>
        </div>
    </header>

    <main class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16">
        
        <!-- Section 1: The Reason Chain -->
        <div class="lg:col-span-4 space-y-12">
            <div class="space-y-4">
                <p class="mono text-[10px] font-bold text-accent uppercase tracking-widest">[01] The_Scout</p>
                <p class="text-gray-400 text-sm leading-relaxed border-l border-gray-800 pl-4 italic">"{data['scout_view']}"</p>
            </div>
            <div class="space-y-4">
                <p class="mono text-[10px] font-bold text-red-500 uppercase tracking-widest">[02] The_Critic</p>
                <p class="text-gray-400 text-sm leading-relaxed border-l border-red-900/30 pl-4 italic">"{data['critic_view']}"</p>
            </div>
            <div class="pt-8">
                <div class="mono text-[10px] text-gray-500 mb-2 uppercase">Confidence_Index</div>
                <div class="text-5xl font-black text-white glow italic tracking-tighter">{data['confidence_score']}%</div>
            </div>
        </div>

        <!-- Section 2: The Core Decision -->
        <div class="lg:col-span-8 flex flex-col justify-center border-t border-gray-900 pt-12 lg:pt-0 lg:border-t-0">
            <p class="mono text-[10px] text-accent mb-6 uppercase tracking-[0.4em] font-bold">● Oracle_Decision_Output</p>
            <h2 class="text-6xl md:text-8xl font-black uppercase leading-[0.85] tracking-tighter mb-10">
                {data['trend_title']}
            </h2>
            <p class="text-2xl md:text-4xl font-light text-gray-300 leading-tight mb-12">
                "{data['oracle_decision']}"
            </p>
            
            <div class="flex gap-6 items-center">
                <div class="px-8 py-3 bg-white text-black text-[10px] font-black uppercase tracking-widest hover:bg-accent transition cursor-pointer">Export Intel</div>
                <div class="mono text-[10px] text-gray-600 uppercase">Impact_Rating: <span class="text-white font-bold">{data['market_impact']}</span></div>
            </div>
        </div>
    </main>

    <footer class="max-w-6xl mx-auto mt-32 pt-12 border-t border-gray-900">
        <div class="flex flex-col md:flex-row justify-between gap-8 items-center text-[9px] mono text-gray-700 uppercase tracking-widest">
            <p>Built with Gemini_Flash_1.5 + Tavily_Search</p>
            <p>Verification_Hash: 0x2026_AGENT_AUTONOMOUS_LEDGER</p>
            <p>© 2026 Decentralized Portfolio System</p>
        </div>
    </footer>

</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    # Telegram Notification
    t_token, t_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHANNEL_ID")
    if t_token and t_id:
        msg = f"🔮 *ORACLE 2026 SYNC*\n\n*Intel:* {data['trend_title']}\n*Confidence:* {data['confidence_score']}%\n\n🔗 [Access System](https://autonomous-portfolio-2026.live)"
        requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", data={"chat_id": t_id, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    run_elite_agent()
