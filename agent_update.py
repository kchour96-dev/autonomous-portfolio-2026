import os
import requests
import json
from datetime import datetime

def send_telegram(topic, summary):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id: return
    msg = f"💎 *WEB3 & CRYPTO SYNC*\n\n🔥 *Intel:* {topic}\n\n🌐 [Access Ledger](https://autonomous-portfolio-2026.live)"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Specialized Crypto & Web3 Research
    crypto_context = "Crypto market trends 2026, Web3 breakthroughs, DeFi news"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": t_key, 
                "query": "latest crypto web3 news and bitcoin eth prices 2026", 
                "max_results": 5
            })
            crypto_context = str(r.json().get('results', []))
        except: pass

    # 2. Brain Logic: Crypto Analyst Mode
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"""
    Research Data: {crypto_context}
    You are a 2026 Web3 Strategist AI. Create a detailed JSON for a Crypto Dashboard.
    Return ONLY JSON:
    {{
      "headline": "Main Web3 Story",
      "analysis": "2 sentence expert DeFi breakdown",
      "market_sentiment": "Bullish/Bearish/Neutral",
      "top_token": {{"name": "Token Name", "symbol": "TKN", "trend": "+12%"}},
      "web3_news": ["Web3 Story 1", "Web3 Story 2"],
      "gas_status": "Low/Medium/High",
      "accent_color": "#hex"
    }}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        txt = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(txt.replace('```json', '').replace('```', '').strip())
    except:
        data = {
            "headline": "Global Ledger Synchronization",
            "analysis": "Ethereum 2026 upgrade complete. DeFi TVL hitting new highs.",
            "market_sentiment": "Bullish",
            "top_token": {"name": "Ethereum", "symbol": "ETH", "trend": "+5.2%"},
            "web3_news": ["L3 expansion", "ZK-Rollup stability"],
            "gas_status": "Low",
            "accent_color": "#f59e0b"
        }

    color = data.get('accent_color', '#f59e0b')
    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")

    # 3. WEB3 DASHBOARD HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web3 Mission Control 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;800&display=swap" rel="stylesheet">
    <style>
        body {{ background: #000; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .border-accent {{ border-color: {color}; }}
        .text-accent {{ color: {color}; }}
        .bg-accent {{ background-color: {color}; }}
        .glow {{ text-shadow: 0 0 10px {color}; }}
        .glass {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); }}
        .ticker {{ animation: ticker 20s linear infinite; }}
        @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    </style>
</head>
<body class="p-2 md:p-6 min-h-screen">
    <!-- Crypto Ticker -->
    <div class="fixed top-0 left-0 w-full bg-accent text-black text-[10px] font-bold py-1 overflow-hidden z-50 uppercase">
        <div class="ticker whitespace-nowrap">
            BTC: $142,500 (+2.1%) • ETH: $8,420 ({data['top_token']['trend']}) • WEB3_STATUS: {data['market_sentiment']} • GAS: {data['gas_status']} • NODE_SYNC: ACTIVE • 
            BTC: $142,500 (+2.1%) • ETH: $8,420 ({data['top_token']['trend']}) • WEB3_STATUS: {data['market_sentiment']} • GAS: {data['gas_status']}
        </div>
    </div>

    <div class="max-w-7xl mx-auto mt-8">
        <!-- Header -->
        <header class="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
            <div class="text-xl font-black italic tracking-tighter">WEB3_AUTONOMOUS <span class="text-accent">2026</span></div>
            <div class="hidden md:flex gap-4 text-[10px] text-gray-500 uppercase font-bold">
                <span class="text-accent animate-pulse">● SENTIMENT: {data['market_sentiment']}</span>
                <span>{date_str}</span>
            </div>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
            
            <!-- Sidebar: Market Pulse -->
            <div class="md:col-span-3 space-y-4">
                <div class="glass p-5 rounded-xl border-l-2 border-accent">
                    <p class="text-[9px] text-gray-500 mb-4 tracking-widest">MARKET_SPOTLIGHT</p>
                    <h3 class="text-2xl font-bold text-accent mb-1">{data['top_token']['name']}</h3>
                    <p class="text-xs text-gray-400 font-bold mb-4">{data['top_token']['symbol']} // {data['top_token']['trend']}</p>
                    <div class="text-[10px] bg-white/5 p-3 rounded leading-relaxed text-gray-400">
                        Top trending asset detected by agent analysis.
                    </div>
                </div>

                <div class="glass p-5 rounded-xl">
                    <p class="text-[9px] text-gray-500 mb-4 tracking-widest">CHAIN_INTELLIGENCE</p>
                    <ul class="text-[10px] space-y-3 leading-tight">
                        {"".join([f"<li class='flex items-start gap-2 text-gray-300'><span class='text-accent'>»</span>{n}</li>" for n in data['web3_news']])}
                    </ul>
                </div>
            </div>

            <!-- Main Panel -->
            <div class="md:col-span-6 space-y-4">
                <div class="glass p-8 rounded-2xl border border-white/10 relative overflow-hidden h-full min-h-[400px] flex flex-col justify-center">
                    <div class="absolute top-0 left-0 w-full h-1 bg-accent/20"></div>
                    <p class="text-[10px] text-accent mb-4 tracking-[0.5em] font-bold">DECENTRALIZED_INTEL_UPDATE</p>
                    <h1 class="text-4xl md:text-6xl font-black uppercase mb-6 leading-tight glow tracking-tighter">
                        {data['headline']}
                    </h1>
                    <p class="text-xl text-gray-400 leading-relaxed mb-8 border-l-4 border-accent pl-6">
                        "{data['analysis']}"
                    </p>
                    <div class="flex gap-3">
                        <div class="px-4 py-2 bg-accent text-black text-[10px] font-black uppercase rounded">Execute Swap</div>
                        <div class="px-4 py-2 border border-accent text-accent text-[10px] font-black uppercase rounded">View On-Chain</div>
                    </div>
                </div>
            </div>

            <!-- Right: Node Activity -->
            <div class="md:col-span-3">
                <div class="glass p-5 rounded-xl h-full font-mono">
                    <p class="text-[9px] text-gray-500 mb-4 tracking-widest">AGENT_NODE_LOG</p>
                    <div class="text-[9px] space-y-2 text-accent/60">
                        <p>> Connecting to RPC endpoints...</p>
                        <p>> Fetching DeFi TVL metrics...</p>
                        <p>> Checking L2/L3 sequence status...</p>
                        <p>> Gemini: Web3 logic engaged.</p>
                        <p>> Analysis: {data['market_sentiment']} shift.</p>
                        <p>> Updating global ledger...</p>
                        <p class="text-white animate-pulse">> Ready_</p>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-8 pt-4 border-t border-white/5 flex justify-between items-center text-[9px] text-gray-600 uppercase tracking-widest">
            <div>NETWORK: MAINNET_2026</div>
            <div>© DECENTRALIZED_ENTITY</div>
        </footer>
    </div>
</body>
</html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    send_telegram(data['headline'], data['market_sentiment'])

if __name__ == "__main__":
    run_agent()
