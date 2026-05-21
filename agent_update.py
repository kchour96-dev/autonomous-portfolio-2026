import os
import requests
import json
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

# ─────────────────────────────────────────────
# LAYER 1: RSS — Real world news (Hardened Parsing)
# ─────────────────────────────────────────────
def get_rss_context():
    feeds = [
        "https://feeds.feedburner.com/TheHackersNews",
        "https://krebsonsecurity.com/feed/",
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed"
    ]
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for url in feeds:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            
            # Use native XML parsing to avoid RegEx failures on unexpected tags
            root = ET.fromstring(r.content)
            channel = root.find('channel')
            if channel is not None:
                count = 0
                for item in channel.findall('item'):
                    title = item.find('title')
                    if title is not None and title.text:
                        clean_title = title.text.replace("<![CDATA[", "").replace("]]>", "").strip()
                        if clean_title:
                            items.append(clean_title)
                            count += 1
                            if count >= 2:  # Keep top 2 items from each feed
                                break
        except Exception as e:
            print(f"Warning: RSS parse failed for {url} -> {e}")
            
    result = " | ".join(items[:8]) if items else "Crypto markets and Web3 security threat vectors"
    print(f"RSS Context Compiled: {result[:120]}...")
    return result

# ─────────────────────────────────────────────
# LAYER 2: Tavily — Deep background research
# ─────────────────────────────────────────────
def get_research(rss_context, t_key):
    if not t_key:
        print("Tavily API key missing. Running in Direct Context mode.")
        return rss_context
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": t_key,
                "query": f"latest crypto web3 exploit breach market news {rss_context[:120]} 2026",
                "max_results": 3
            },
            timeout=12
        )
        r.raise_for_status()
        results = r.json().get('results', [])
        if results:
            combined = " ".join([res.get('content', '') for res in results])[:2500]
            print(f"Tavily ground research loaded successfully ({len(combined)} chars)")
            return combined
    except Exception as e:
        print(f"Warning: Tavily research API call failed -> {e}")
    return rss_context

# ─────────────────────────────────────────────
# LAYER 3: Core LLM Synthesis & Fallback Channels
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_groq(prompt, groq_key):
    if not groq_key:
        raise ValueError("GROQ API key unavailable")
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.6
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

def get_gemini_data(research_context, g_key):
    prompt = f"""You are an elite, autonomous AI cybersecurity researcher and Web3 risk analyst.
Evaluate this intelligence data: {research_context}

Output exactly a raw JSON block. No wrapping, no markdown backticks, no preface.
JSON structure to generate:
{{
  "title": "A highly punchy 4-6 word alert header summarizing today's key dynamic",
  "news_bullets": [
    "First crucial summary sentence highlighting specific players, targets, or protocols",
    "Second sentence adding deep mechanical context or technical exploit details",
    "Third sentence detailing immediate ecosystem-wide operational fallout"
  ],
  "threat": "One dense, clear sentence analyzing the precise systemic risk factor to look out for",
  "opportunity": "One forward-looking sentence about tactical, defensive positions or protocols that benefit",
  "threat_score": 8,
  "opportunity_score": 6,
  "threat_level": "High",
  "deep_analysis": "Three analytical, expert paragraphs detailing the mechanical root causes, supply-chain impacts, and mid-term architecture predictions. Separate paragraphs with a single newline.",
  "tokens_to_watch": ["SYM1", "SYM2", "SYM3"],
  "critic": "One highly analytical, contrarian statement challenging why the opportunity might prove premature, unscalable, or risky.",
  "color": "#8B0000"
}}

Rules for 'tokens_to_watch': Do not print generic Bitcoin (BTC) or Ethereum (ETH). Choose targeted protocol assets directly associated with the vulnerability.
Rules for 'threat_level': Choose strictly from 'Critical', 'High', 'Medium', or 'Low'."""

    # Robust multi-engine fallback matrix
    attempts = [
        ("gemini-2.5-flash",   "gemini",  g_key),
        ("groq-llama-3.3-70b", "groq",    os.getenv("GROQ")),
        ("gemini-1.5-flash",   "gemini",  g_key),
    ]

    for model_name, provider, key in attempts:
        try:
            print(f"Triggering pipeline request via: {model_name}...")
            if provider == "groq" and not key:
                print("Skipping Groq: No local credential set in environment.")
                continue
            
            raw = call_groq(prompt, key) if provider == "groq" else call_gemini(prompt, key, model_name)
            
            # Sanitize responses dynamically using dynamic string constructors to avoid nesting errors
            cleaned_text = raw.strip()
            backticks = chr(96) * 3
            if backticks in cleaned_text:
                cleaned_text = re.sub(rf'^{backticks}(?:json)?\s*|\s*{backticks}$', '', cleaned_text, flags=re.MULTILINE)
            
            match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if not match:
                raise ValueError("JSON matching brackets not found in raw response.")
                
            parsed_data = json.loads(match.group(0))
            print(f"Pipeline SUCCESS via {model_name}!")
            return parsed_data
            
        except Exception as e:
            print(f"Engine failure [{model_name}]: {e}")
            continue
            
    return None

# ─────────────────────────────────────────────
# LAYER 4: Notification & Automation Integration
# ─────────────────────────────────────────────
def send_telegram(title, threat, opportunity, threat_score, opp_score):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        print("Telegram configuration absent. Skipping dispatch.")
        return
    msg = (
        f"🧠 *AUTONOMOUS LAB UPDATE*\n\n"
        f"*{title}*\n\n"
        f"⚠️ *Threat [{threat_score}/10]:* {threat}\n\n"
        f"💡 *Opportunity [{opp_score}/10]:* {opportunity}\n\n"
        f"🔗 https://autonomous-portfolio-2026.live"
    )
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        r.raise_for_status()
        print("Telegram alert successfully sent!")
    except Exception as e:
        print(f"Telegram dispatch failed: {e}")

def post_to_devto(data):
    key = os.getenv("DEV")
    if not key:
        print("Dev.to publishing credentials (DEV) absent. Skipping step.")
        return
        
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])])
    body = (
        f"> 🔗 Live Dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n"
        f"> 📢 Telegram Feed: [t.me/AII2026futher](https://t.me/AII2026futher)\n\n"
        f"## Live Headlines\n\n{bullets}\n\n"
        f"## ⚠️ Systemic Risk Assessment [{data.get('threat_score','?')}/10]\n\n{data.get('threat','')}\n\n"
        f"## 💡 Market Catalyst Assessment [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity','')}\n\n"
        f"## 🪙 Tokens Under Watch\n\n{', '.join(data.get('tokens_to_watch', []))}\n\n"
        f"## 📊 Deep Core Analysis\n\n{data.get('deep_analysis','')}\n\n"
        f"---\n"
        f"*Report generated completely autonomously via the Autonomous Lab 2026 Engine.*"
    )
    try:
        r = requests.post(
            "https://dev.to/api/articles",
            json={"article": {
                "title": f"Autonomous Lab Alert: {data.get('title')}",
                "body_markdown": body,
                "tags": ["crypto", "blockchain", "security", "ai"],
                "published": True
            }},
            headers={"api-key": key},
            timeout=15
        )
        r.raise_for_status()
        print(f"Dev.to article published: {r.json().get('url','')}")
    except Exception as e:
        print(f"Dev.to publishing step encountered an error: {e}")

def write_seo_files():
    date_today = datetime.now().strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.2">
  <url>
    <loc>https://autonomous-portfolio-2026.live/</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    try:
        with open("sitemap.xml", "w") as f:
            f.write(sitemap)
        with open("robots.txt", "w") as f:
            f.write("User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n")
        print("SEO assets successfully exported.")
    except Exception as e:
        print(f"SEO writing error: {e}")

# ─────────────────────────────────────────────
# LAYER 5: Frontend Design Compilation
# ─────────────────────────────────────────────
def build_html(data, final_history, date_str):
    color        = data.get('color', '#8B0000')
    threat       = data.get('threat_level', 'High')
    title        = data.get('title', 'Intelligence Analysis')
    news_bullets = data.get('news_bullets', [])
    threat_txt   = data.get('threat', '')
    opp_txt      = data.get('opportunity', '')
    threat_score = data.get('threat_score', 5)
    opp_score    = data.get('opportunity_score', 5)
    deep         = data.get('deep_analysis', '').replace('\n', '<br><br>')
    tokens       = data.get('tokens_to_watch', [])
    critic       = data.get('critic', '')

    threat_colors = {"Critical":"#ef4444","High":"#f97316","Medium":"#eab308","Low":"#22c55e"}
    threat_color  = threat_colors.get(threat, "#94a3b8")

    bullets_html = "".join([
        f'<div class="flex gap-3 mb-3 items-start">'
        f'<span style="color:{color}" class="mt-0.5 flex-shrink-0">›</span>'
        f'<p class="text-sm text-slate-300 leading-snug">{b}</p>'
        f'</div>'
        for b in news_bullets
    ])
    tokens_html = "".join([
        f'<span class="inline-block px-3 py-1 rounded-full text-[11px] font-black mono mr-2 mb-2" '
        f'style="background:{color}22;color:{color};border:1px solid {color}44">{t}</span>'
        for t in tokens
    ])

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lab 2026 — {title}</title>
    
    <!-- GOOGLE ADSENSE VERIFICATION SCRIPT -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527"
         crossorigin="anonymous"></script>

    <meta name="description" content="Real-time crypto and Web3 intelligence. Threat score, opportunity signals, tokens to watch — updated every 2 hours by AI.">
    <meta name="keywords" content="crypto intelligence, web3 security, DeFi signals, AI research dashboard, blockchain 2026">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{title} — Autonomous Lab 2026">
    <meta property="og:description" content="Threat: {threat_score}/10 | Opportunity: {opp_score}/10">
    <meta property="og:url" content="https://autonomous-portfolio-2026.live">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title} — Autonomous Lab 2026">
    <link rel="canonical" href="https://autonomous-portfolio-2026.live/">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        *{{box-sizing:border-box}}
        body{{background:#06070f;color:#f1f5f9;font-family:'Space Grotesk',sans-serif;margin:0}}
        .mono{{font-family:'JetBrains Mono',monospace}}
        .glass{{background:rgba(15,23,42,0.5);border:1px solid rgba(255,255,255,0.06);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}}
        .score-bar{{height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden}}
        .score-fill{{height:100%;border-radius:99px}}
        #deepdive{{display:none}}
        @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.3}}}}
        .blink{{animation:pulse 2s infinite}}
        @keyframes fadeup{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
        .fadein{{animation:fadeup 0.5s ease forwards}}
    </style>
</head>
<body class="p-4 md:p-8 lg:p-12 min-h-screen">

<header class="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-4 mb-10 pb-6 border-b border-white/5">
    <div>
        <h1 class="text-2xl md:text-3xl font-black tracking-tighter uppercase">
            AUTONOMOUS_<span style="color:{color}">LAB</span><span class="text-slate-600">_2026</span>
        </h1>
        <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mt-1 flex items-center gap-2">
            <span class="blink" style="color:{color}">●</span>
            <span id="terminal-live-status">AI Agent Pipeline Online // Monitoring Nodes...</span>
        </p>
    </div>
    <div class="text-right text-[10px] mono uppercase font-bold">
        <p style="color:{threat_color}" class="mb-1">● {threat} Threat Environment</p>
        <p class="text-slate-500">Last Synced: {date_str}</p>
    </div>
</header>

<main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
    <div class="lg:col-span-8 space-y-6 fadein">

        <section class="glass rounded-2xl p-6 md:p-8 border-l-4" style="border-color:{color}">
            <p class="text-[10px] mono font-black uppercase tracking-[0.4em] mb-3" style="color:{color}">● Today's Intelligence Brief</p>
            <h2 class="text-3xl md:text-5xl font-black tracking-tighter leading-tight text-white mb-6">{title}</h2>
            <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-3">What happened today:</p>
            <div class="space-y-1">{bullets_html}</div>
        </section>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="glass rounded-2xl p-6 border-t-2 border-red-500/60">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-[10px] mono font-black text-red-400 uppercase tracking-widest">⚠️ Threat Signal</p>
                    <p class="text-2xl font-black text-red-400">{threat_score}<span class="text-sm text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4"><div class="score-fill bg-red-500" style="width:{t_bar}%"></div></div>
                <p class="text-sm text-slate-300 leading-relaxed">{threat_txt}</p>
            </div>
            <div class="glass rounded-2xl p-6 border-t-2" style="border-color:{color}88">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-[10px] mono font-black uppercase tracking-widest" style="color:{color}">💡 Opportunity Signal</p>
                    <p class="text-2xl font-black" style="color:{color}">{opp_score}<span class="text-sm text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4"><div class="score-fill" style="width:{o_bar}%;background:{color}"></div></div>
                <p class="text-sm text-slate-300 leading-relaxed">{opp_txt}</p>
            </div>
        </div>

        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest mb-4">🪙 Tokens To Watch</p>
            <div class="mb-2">{tokens_html}</div>
            <p class="text-[9px] text-slate-600 italic mt-2">* Not financial advice. For research only.</p>
        </div>

        <div class="glass rounded-2xl p-6">
            <div class="flex justify-between items-center">
                <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest">📊 Deep Analysis</p>
                <button id="deepbtn"
                    onclick="var d=document.getElementById('deepdive'),b=document.getElementById('deepbtn');if(d.style.display==='none'||!d.style.display){{d.style.display='block';b.innerText='Close ↑'}}else{{d.style.display='none';b.innerText='Read More ↓'}}"
                    class="text-[10px] mono font-black uppercase px-4 py-2 rounded-full border border-white/10 hover:border-white/30 transition">
                    Read More ↓
                </button>
            </div>
            <div id="deepdive" class="mt-6 pt-6 border-t border-white/5 text-sm text-slate-300 leading-relaxed">{deep}</div>
        </div>

        <div class="glass rounded-2xl p-6 border-l-4 border-yellow-500/40">
            <p class="text-[10px] mono font-black text-yellow-500 uppercase tracking-widest mb-3">🤔 Contrarian View</p>
            <p class="text-sm text-slate-400 italic leading-relaxed">"{critic}"</p>
            <p class="text-[9px] mono text-slate-600 mt-3 uppercase">— Powered by Groq / Llama 3.3 70b</p>
        </div>

        <!-- SHARE BUTTON -->
        <div class="glass rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
            <div>
                <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest mb-1">📢 Share This Report</p>
                <p class="text-xs text-slate-500">Found this useful? Share it with your network.</p>
            </div>
            <a href="https://twitter.com/intent/tweet?text={title}%20%E2%80%94%20Threat%3A%20{threat_score}%2F10%20%7C%20Opportunity%3A%20{opp_score}%2F10%0A%0Ahttps%3A%2F%2Fautonomous-portfolio-2026.live%20%23crypto%20%23web3%20%23AI"
               target="_blank"
               class="flex items-center gap-2 px-6 py-3 rounded-full font-black text-[11px] uppercase tracking-widest transition hover:opacity-80"
               style="background:#1d9bf0;color:white">
                𝕏 Share on X
            </a>
        </div>

    </div>

    <aside class="lg:col-span-4 space-y-6">
        <div class="glass rounded-2xl p-6 text-center">
            <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-4">Signal Summary</p>
            <div class="grid grid-cols-2 gap-3">
                <div class="rounded-xl p-4" style="background:{color}11;border:1px solid {color}33">
                    <p class="text-3xl font-black" style="color:{color}">{opp_score}</p>
                    <p class="text-[9px] mono text-slate-500 uppercase mt-1">Opportunity</p>
                </div>
                <div class="rounded-xl p-4 bg-red-500/10 border border-red-500/20">
                    <p class="text-3xl font-black text-red-400">{threat_score}</p>
                    <p class="text-[9px] mono text-slate-500 uppercase mt-1">Threat</p>
                </div>
            </div>
            
            <!-- EXPLANATION SUBTEXT FOR USER STRATEGY -->
            <div class="mt-4 pt-4 border-t border-white/5 text-[10px] text-slate-500 mono text-left space-y-2">
                <p>💡 <strong class="text-slate-400">High Opportunity:</strong> Narrative buy pressure building.</p>
                <p>⚠️ <strong class="text-slate-400">High Threat:</strong> De-risk, secure keys, hold stable assets.</p>
            </div>
            
            <p class="text-[9px] mono text-slate-600 mt-4 uppercase">{date_str}</p>
        </div>

        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-bold text-slate-500 uppercase tracking-widest mb-4 pb-3 border-b border-white/5">📁 Signal Archive</p>
            <div class="max-h-[380px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10"><!-- H_S -->{final_history}<!-- H_E --></div>
        </div>

        <div class="rounded-2xl p-6 bg-white/[0.02] border border-white/5 text-[10px] mono text-slate-600">
            <p class="text-slate-400 font-bold uppercase tracking-widest mb-3">AI Stack:</p>
            <p class="mb-1">» RSS: HackerNews / Krebs / CoinTelegraph</p>
            <p class="mb-1">» Research: Tavily Search API</p>
            <p class="mb-1">» Brain: Gemini 2.5 Flash</p>
            <p class="mb-1">» Critic: Llama 3.3 via Groq</p>
            <p class="mb-1">» Notify: Telegram Bot</p>
            <p class="mb-1">» SEO: Dev.to Auto-Publish</p>
            <p class="mt-4 text-[8px] opacity-30 uppercase tracking-widest">Free AI Pipeline // 2026</p>
        </div>

        <div class="rounded-2xl p-4 bg-yellow-500/5 border border-yellow-500/10">
            <p class="text-[9px] text-yellow-500/50 leading-relaxed">
                ⚠️ AI-generated for research and education only. Not financial advice. Always do your own research.
            </p>
        </div>

        <!-- DONATION -->
        <div class="glass rounded-2xl p-6 border border-yellow-500/20">
            <p class="text-[10px] mono font-black text-yellow-400 uppercase tracking-widest mb-3">💰 Support This Lab</p>
            <p class="text-xs text-slate-400 leading-relaxed mb-4">If this dashboard saved you time or helped you spot an opportunity — support the work.</p>
            <div class="rounded-xl p-3 mb-3" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06)">
                <p class="text-[9px] mono text-slate-500 uppercase mb-1">USDT (BEP20 / BSC Network)</p>
                <p class="text-[10px] mono text-yellow-400 break-all leading-relaxed">0x30ce31b427707335343b43708a35b20955f1763c2</p>
                <button onclick="navigator.clipboard.writeText('0x30ce31b427707335343b43708a35b20955f1763c2');this.innerText='✅ Copied!';setTimeout(()=>this.innerText='Copy Address',2000)"
                    class="mt-2 text-[9px] mono font-black uppercase px-3 py-1 rounded-full border border-white/10 hover:border-yellow-500/50 hover:text-yellow-400 transition text-slate-500">
                    Copy Address
                </button>
            </div>
            <p class="text-[9px] text-slate-600 italic">⚠️ BSC network only. Send USDT BEP20.</p>
        </div>

        <!-- ABOUT -->
        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest mb-4">👤 About</p>
            <p class="text-xs text-slate-400 leading-relaxed mb-3">
                Built by <span class="text-white font-bold">Kchour</span>, a developer from
                <span class="text-white font-bold">Phnom Penh, Cambodia</span> — experimenting
                with autonomous AI systems and real-time intelligence pipelines.
            </p>
            <p class="text-xs text-slate-500 leading-relaxed">
                This lab runs a fully automated multi-agent pipeline that pulls live news,
                researches deeper context, and generates expert analysis — updated every 2 hours,
                entirely free, entirely autonomous.
            </p>
            <a href="https://github.com/kchour96-dev/autonomous-portfolio-2026"
               target="_blank"
               class="inline-block mt-4 text-[10px] mono font-black uppercase tracking-widest px-4 py-2 rounded-full border border-white/10 hover:border-white/30 transition text-slate-400 hover:text-white">
                View on GitHub →
            </a>
            <a href="https://t.me/AII2026futher"
               target="_blank"
               class="inline-block mt-2 text-[10px] mono font-black uppercase tracking-widest px-4 py-2 rounded-full border border-blue-500/30 hover:border-blue-500/60 transition text-blue-400 hover:text-blue-300">
                📢 Join Telegram →
            </a>
        </div>

    </aside>
</main>

<footer class="max-w-7xl mx-auto mt-12 pt-6 border-t border-white/5 flex flex-wrap justify-between gap-2 text-[9px] mono text-slate-700">
    <p>AUTONOMOUS-PORTFOLIO-2026.LIVE // AI AGENT PIPELINE // {date_str}</p>
    <p>NOT FINANCIAL ADVICE // RESEARCH ONLY</p>
</footer>

<script>
    // System Thinking Simulator to make the page look and feel continuously live
    const agentProcesses = [
        "Analyzing security vectors via Gemini Brain...",
        "Evaluating systemic risk thresholds via Llama 3.3...",
        "Parsing active exploits from HackerNews RSS...",
        "Scraping background articles via Tavily API...",
        "Compiling real-time sentiment metrics...",
        "Validating network signature data..."
    ];
    setInterval(() => {{
        const el = document.getElementById('terminal-live-status');
        if(el) el.innerText = agentProcesses[Math.floor(Math.random() * agentProcesses.length)];
    }}, 8000);
</script>
</body>
</html>"""

# ─────────────────────────────────────────────
# MAIN EXECUTOR
# ─────────────────────────────────────────────
def run_production_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    if not g_key:
        print("Fatal Error: GEMINI API secret not mapped in environment variables. Aborting.")
        return

    # Create safety backup in case generation pipeline hits failure loops
    old_content = ""
    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")
        with open("index.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    rss_context = get_rss_context()
    research    = get_research(rss_context, t_key)
    data        = get_gemini_data(research, g_key)

    if not data:
        print("Warning: All pipeline LLM pathways failed. Restoring index backup.")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    # Isolate history records
    history_html = ""
    if "<!-- H_S -->" in old_content and "<!-- H_E -->" in old_content:
        history_html = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]

    date_str  = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_entry = (
        f"<div class='mb-3 pl-3 border-l border-white/10 opacity-50 text-[10px]'>"
        f"<p class='mono text-slate-500'>{date_str}</p>"
        f"<p class='font-bold text-slate-300 uppercase tracking-tight'>{data.get('title','Intelligence Alert')}</p>"
        f"<p class='text-slate-500'>⚠️ {data.get('threat_score','?')}/10 &nbsp;💡 {data.get('opportunity_score','?')}/10</p>"
        f"</div>"
    )
    final_history = (new_entry + history_html)[:4500]  # Limit cache footprint sizes

    html_payload = build_html(data, final_history, date_str)
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_payload)
        print("Dashboard generation complete: index.html written successfully.")
    except Exception as e:
        print(f"Error: index.html block write failed -> {e}")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    if os.path.exists("index.html.bak"):
        os.remove("index.html.bak")

    # Post processing pipeline tasks
    write_seo_files()
    post_to_devto(data)
    send_telegram(
        data.get('title',''),
        data.get('threat',''),
        data.get('opportunity',''),
        data.get('threat_score','?'),
        data.get('opportunity_score','?')
    )
    print("✅ Autonomous execution loop successfully synchronized!")

if __name__ == "__main__":
    run_production_agent()
```
eof

### Summary of what was added:
* **Google AdSense integration:** I placed the asynchronous Google AdSense script code directly inside the `<head>` block of your generated HTML string:
  ```html
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527"
       crossorigin="anonymous"></script>
