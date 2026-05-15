import os
import requests
import json
from datetime import datetime

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Research for Web3 & Market Conditions
    context = "Web3 trends and crypto prices May 2026"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "current crypto market sentiment and top gainers 2026", 
                "max_results": 4
            })
            context = str(r.json().get('results', []))
        except: pass

    # 2. Intelligence Logic
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research: {context}
    You are the CEO of an Autonomous AI Fund in 2026. Generate a JSON Dashboard.
    Return ONLY JSON:
    {{
      "headline": "Main Portfolio Move",
      "strategy": "Why you are making this move in 2 sentences",
      "risk_score": 0-100,
      "portfolio": [
        {{"asset": "AI Tokens", "percent": 40}},
        {{"asset": "DeFi L3", "percent": 30}},
        {{"asset": "Real World Assets", "percent": 30}}
      ],
      "market_vibe": "Bullish/Bearish",
      "color": "#hex"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        data = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip())
    except:
        data = {
            "headline": "Liquidity Rebalancing",
            "strategy": "Shifting assets to high-yield L3 protocols.",
            "risk_score": 65,
            "portfolio": [{"asset": "BTC", "percent": 50}, {"asset": "ETH", "percent": 50}],
            "market_vibe": "Neutral",
            "color": "#00ffcc"
        }

    color = data.get('color', '#00ffcc')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. ADVANCED DATA DASHBOARD HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;800&display=swap" rel="stylesheet">
    <style>
        body {{ background: #000; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .text-accent {{ color: {color}; }}
        .bg-accent {{ background-color: {color}; }}
        .border-accent {{ border-color: {color}; }}
        .glass {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); }}
        @keyframes slide {{ from {{ transform: translateX(100%); }} to {{ transform: translateX(-100%); }} }}
        .ticker {{ animation: slide 15s linear infinite; }}
    </style>
</head>
<body class="p-4 md:p-10">
    <div class="fixed top-0 left-0 w-full bg-accent text-black text-[9px] py-1 font-bold z-50">
        <div class="ticker whitespace-nowrap uppercase">
            AGENT_STATUS: {data['market_vibe']} • RISK_LEVEL: {data['risk_score']}% • SYNC_TIME: {date_str} • TOTAL_AUM: $42.8M (SIMULATED) • DEFI_GAS: LOW • 
        </div>
    </div>

    <main class="max-w-6xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-12 gap-6">
        
        <!-- Column 1: Asset Allocation -->
        <div class="md:col-span-4 space-y-6">
            <div class="glass p-6 rounded-3xl">
                <p class="text-[10px] text-gray-500 mb-6 tracking-widest uppercase">Treasury_Allocation</p>
                <div class="space-y-6">
                    {"".join([f'''
                    <div>
                        <div class="flex justify-between text-xs mb-2"><span>{p['asset']}</span><span>{p['percent']}%</span></div>
                        <div class="h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div class="h-full bg-accent" style="width: {p['percent']}%"></div>
                        </div>
                    </div>
                    ''' for p in data['portfolio']])}
                </div>
            </div>

            <div class="glass p-6 rounded-3xl flex items-center justify-between">
                <span class="text-[10px] text-gray-500 tracking-widest uppercase">System_Risk</span>
                <div class="text-3xl font-black text-accent">{data['risk_score']}%</div>
            </div>
        </div>

        <!-- Column 2: Strategy Core -->
        <div class="md:col-span-8">
            <div class="glass p-10 rounded-[3rem] border-t-8 border-accent h-full relative overflow-hidden">
                <div class="absolute -top-10 -right-10 opacity-5 text-[15rem] font-black italic">26</div>
                <p class="text-accent text-xs mb-6 font-bold tracking-[0.4em]">● CORE_STRATEGY_SYNC</p>
                <h1 class="text-5xl md:text-7xl font-black uppercase mb-8 leading-[0.9] tracking-tighter italic">
                    {data['headline']}
                </h1>
                <p class="text-xl md:text-2xl text-gray-400 mb-10 leading-tight">
                    "{data['strategy']}"
                </p>
                <div class="flex gap-4">
                    <div class="h-12 w-12 rounded-full border border-accent flex items-center justify-center animate-spin-slow text-accent">◈</div>
                    <div class="flex flex-col justify-center">
                        <p class="text-[10px] text-gray-500">SIGNATURE_HASH</p>
                        <p class="text-[10px] text-accent font-bold">0xAI_AGENT_2026_CORE_v2</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <div class="max-w-6xl mx-auto mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="glass p-4 rounded-2xl text-[10px] text-gray-500 flex justify-between uppercase">
            <span>Network: Ethereum L3</span>
            <span class="text-green-500">Active</span>
        </div>
        <div class="glass p-4 rounded-2xl text-[10px] text-gray-500 flex justify-between uppercase">
            <span>Uptime: 1420 Hours</span>
            <span class="text-green-500">100%</span>
        </div>
        <div class="glass p-4 rounded-2xl text-[10px] text-gray-500 flex justify-between uppercase">
            <span>Mode: Autonomous</span>
            <span class="text-accent">Enabled</span>
        </div>
    </div>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    # Send simplified telegram
    msg = f"🏦 *STRATEGY UPDATE*\n\n{data['headline']}\n\n📈 Risk: {data['risk_score']}%"
    t_token = os.getenv("TELEGRAM_BOT_TOKEN")
    t_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if t_token and t_id:
        requests.post(f"https://api.telegram.org/bot{t_token}/sendMessage", data={"chat_id": t_id, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    run_agent()
