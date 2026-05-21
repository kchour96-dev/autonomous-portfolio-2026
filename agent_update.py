import os
import time
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
                            if count >= 2:
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
# LAYER 3: LLM Engines with retry logic
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}},
        headers={"Content-Type": "application/json"},
        timeout=45
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
        "messages": [
            {"role": "system", "content": "You are a JSON API. Output only a valid JSON object. Start with { and end with }. No markdown, no backticks, no explanation."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=45
    )
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']

def parse_json_safe(raw):
    """Robustly extract JSON from any LLM response."""
    cleaned = raw.strip()
    # Remove markdown code fences
    backticks = chr(96) * 3
    cleaned = re.sub(rf'{backticks}(?:json)?\s*', '', cleaned).strip()
    # Try direct parse first
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Try extracting first JSON object
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # Try fixing common issues: trailing commas
    try:
        fixed = re.sub(r',\s*([}\]])', r'\1', cleaned)
        match2 = re.search(r'\{.*\}', fixed, re.DOTALL)
        if match2:
            return json.loads(match2.group(0))
    except Exception:
        pass
    raise ValueError("Could not extract valid JSON from response")

def get_ai_data(research_context, g_key):
    prompt = f"""You are an elite autonomous AI cybersecurity researcher and Web3 risk analyst.
Evaluate this intelligence data: {research_context}

Respond with ONLY a raw JSON object. No markdown, no backticks, no explanation before or after.

{{
  "title": "A punchy 4-6 word alert header summarizing today's key event",
  "news_bullets": [
    "First crucial summary sentence with specific players, targets, or protocols",
    "Second sentence with technical exploit details or root cause",
    "Third sentence detailing immediate ecosystem-wide impact"
  ],
  "threat": "One dense sentence analyzing the precise systemic risk",
  "opportunity": "One forward-looking sentence about protocols or positions that benefit",
  "threat_score": 8,
  "opportunity_score": 6,
  "threat_level": "High",
  "deep_analysis": "Three expert paragraphs on root causes, supply-chain impacts, and mid-term predictions. Separate with newline.",
  "tokens_to_watch": ["SYM1", "SYM2", "SYM3"],
  "critic": "One contrarian statement challenging why the opportunity might be premature or risky.",
  "color": "#8B0000"
}}

RULES:
- tokens_to_watch: No BTC or ETH. Use targeted protocol tokens only.
- threat_level: Only use Critical, High, Medium, or Low.
- Return ONLY the JSON object, nothing else."""

    # Updated fallback order: verified working model names May 2026
    attempts = [
        ("gemini-2.5-flash",        "gemini", g_key),
        ("gemini-2.0-flash-lite",   "gemini", g_key),
        ("groq-llama-3.3-70b",      "groq",   os.getenv("GROQ")),
        ("gemini-1.5-flash-8b",     "gemini", g_key),
        ("gemini-1.5-flash",        "gemini", g_key),
    ]

    for model_name, provider, key in attempts:
        for attempt_num in range(2):  # retry once per engine
            try:
                print(f"Triggering pipeline via: {model_name} (attempt {attempt_num + 1})...")
                if provider == "groq" and not key:
                    print("Skipping Groq: No GROQ key in environment.")
                    break

                if provider == "groq":
                    raw = call_groq(prompt, key)
                else:
                    raw = call_gemini(prompt, key, model_name)

                parsed_data = parse_json_safe(raw)
                print(f"✅ Pipeline SUCCESS via {model_name}!")
                return parsed_data

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else "?"
                print(f"Engine failure [{model_name}]: HTTP {status} -> {e}")
                if status in (503, 429):
                    wait = 10 * (attempt_num + 1)
                    print(f"Rate limit / overload. Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    break  # 404, 400 etc — no point retrying same model
            except Exception as e:
                print(f"Engine failure [{model_name}]: {e}")
                if attempt_num == 0:
                    time.sleep(5)
                else:
                    break

    print("❌ All AI engines failed.")
    return None

# ─────────────────────────────────────────────
# LAYER 4: Notification & Automation
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
        print("Dev.to credentials absent. Skipping.")
        return
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])])
    body = (
        f"> 🔗 Live Dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n"
        f"> 📢 Telegram: [t.me/AII2026futher](https://t.me/AII2026futher)\n\n"
        f"## Live Headlines\n\n{bullets}\n\n"
        f"## ⚠️ Threat [{data.get('threat_score','?')}/10]\n\n{data.get('threat','')}\n\n"
        f"## 💡 Opportunity [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity','')}\n\n"
        f"## 🪙 Tokens To Watch\n\n{', '.join(data.get('tokens_to_watch', []))}\n\n"
        f"## 📊 Deep Analysis\n\n{data.get('deep_analysis','')}\n\n"
        f"---\n*Generated autonomously by Autonomous Lab 2026.*"
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
        print(f"Dev.to published: {r.json().get('url','')}")
    except Exception as e:
        print(f"Dev.to error: {e}")

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
        print("SEO files written.")
    except Exception as e:
        print(f"SEO write error: {e}")

# ─────────────────────────────────────────────
# LAYER 5: HTML Builder (with Market Bias Panel + bigger fonts)
# ─────────────────────────────────────────────
def build_market_bias_panel(threat_score, opp_score, color):
    ts = int(str(threat_score)) if str(threat_score).isdigit() else 5
    os_ = int(str(opp_score)) if str(opp_score).isdigit() else 5

    if ts >= 8 and os_ >= 7:
        combined_label = "⚠️ MIXED / UNCERTAIN"
        combined_sub   = "Both signals high — avoid leveraged &amp; futures positions"
        combined_style = "background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2)"
        combined_color = "text-yellow-300"
    elif ts >= 8:
        combined_label = "📉 BEARISH BIAS"
        combined_sub   = "High threat — short-term selling pressure likely"
        combined_style = "background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2)"
        combined_color = "text-red-400"
    elif os_ >= 7:
        combined_label = "📈 BULLISH BIAS"
        combined_sub   = "Opportunity high — some tokens may see buying interest"
        combined_style = "background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2)"
        combined_color = "text-green-400"
    else:
        combined_label = "😐 NEUTRAL"
        combined_sub   = "Low signals — no strong directional bias"
        combined_style = "background:rgba(148,163,184,0.08);border:1px solid rgba(148,163,184,0.2)"
        combined_color = "text-slate-400"

    threat_arrow  = "↓" if ts >= 8 else ("↑?" if ts <= 4 else "→")
    opp_arrow     = "↑?" if os_ >= 7 else "→"

    return f"""
        <!-- MARKET BIAS PANEL -->
        <div class="glass rounded-2xl p-6" style="border:1px solid rgba(249,115,22,0.2)">
            <p class="text-xs mono font-black uppercase tracking-widest mb-4" style="color:#f97316">📊 Market Bias This Cycle</p>

            <div class="rounded-xl p-4 mb-4 text-center" style="{combined_style}">
                <p class="text-[10px] mono text-slate-400 uppercase tracking-widest mb-1">Combined Reading</p>
                <p class="text-xl font-black {combined_color}">{combined_label}</p>
                <p class="text-sm text-slate-400 mt-1">{combined_sub}</p>
            </div>

            <div class="space-y-3 mb-4">
                <div class="flex items-center justify-between rounded-xl px-4 py-3" style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.15)">
                    <div>
                        <p class="text-xs mono text-red-400 uppercase tracking-widest font-bold">🔴 Threat {ts}/10</p>
                        <p class="text-sm text-slate-300 mt-1">Possible <span class="font-bold text-red-400">selling pressure</span></p>
                    </div>
                    <p class="text-3xl font-black text-red-400">{threat_arrow}</p>
                </div>
                <div class="flex items-center justify-between rounded-xl px-4 py-3" style="background:rgba(139,0,0,0.08);border:1px solid rgba(139,0,0,0.2)">
                    <div>
                        <p class="text-xs mono uppercase tracking-widest font-bold" style="color:#e57373">💡 Opportunity {os_}/10</p>
                        <p class="text-sm text-slate-300 mt-1">Some tokens may see <span class="font-bold" style="color:#e57373">buying interest</span></p>
                    </div>
                    <p class="text-3xl font-black" style="color:#e57373">{opp_arrow}</p>
                </div>
            </div>

            <div class="rounded-xl p-4 mb-3" style="background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.05)">
                <p class="text-xs mono text-slate-300 uppercase tracking-widest mb-3 font-black">📖 How To Read This:</p>
                <div class="space-y-2">
                    <div class="flex items-start gap-2">
                        <span class="text-sm">🔴</span>
                        <p class="text-sm text-slate-300">Threat <span class="text-white font-bold">8–10</span> = Market may go <span class="text-red-400 font-bold">DOWN</span> short-term. Be careful.</p>
                    </div>
                    <div class="flex items-start gap-2">
                        <span class="text-sm">💡</span>
                        <p class="text-sm text-slate-300">Opportunity <span class="text-white font-bold">7–10</span> = Some tokens may go <span class="text-green-400 font-bold">UP</span> mid-term.</p>
                    </div>
                    <div class="flex items-start gap-2">
                        <span class="text-sm">⚖️</span>
                        <p class="text-sm text-slate-300">Both high = <span class="text-yellow-400 font-bold">MIXED</span>. Wait for clarity. Do NOT use futures.</p>
                    </div>
                </div>
            </div>

            <div class="rounded-lg px-3 py-2" style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.1)">
                <p class="text-xs text-red-400/80 leading-relaxed">
                    ⚠️ <strong>News sentiment only.</strong> Price can move opposite to the news. <strong>Never trade futures based on this alone.</strong>
                </p>
            </div>
        </div>
        <!-- END MARKET BIAS PANEL -->"""

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
        f'<p class="text-base text-slate-300 leading-relaxed">{b}</p>'
        f'</div>'
        for b in news_bullets
    ])
    tokens_html = "".join([
        f'<span class="inline-block px-4 py-1.5 rounded-full text-sm font-black mono mr-2 mb-2" '
        f'style="background:{color}22;color:{color};border:1px solid {color}44">{t}</span>'
        for t in tokens
    ])

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10

    market_bias_html = build_market_bias_panel(threat_score, opp_score, color)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lab 2026 — {title}</title>
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
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527" crossorigin="anonymous"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        *{{box-sizing:border-box}}
        body{{background:#06070f;color:#f1f5f9;font-family:'Space Grotesk',sans-serif;margin:0;font-size:16px}}
        .mono{{font-family:'JetBrains Mono',monospace}}
        .glass{{background:rgba(15,23,42,0.5);border:1px solid rgba(255,255,255,0.06);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}}
        .score-bar{{height:6px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden}}
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
        <h1 class="text-3xl md:text-4xl font-black tracking-tighter uppercase">
            AUTONOMOUS_<span style="color:{color}">LAB</span><span class="text-slate-600">_2026</span>
        </h1>
        <p class="text-xs mono text-slate-500 uppercase tracking-widest mt-1 flex items-center gap-2">
            <span class="blink" style="color:{color}">●</span>
            <span id="terminal-live-status">AI Agent Pipeline Online // Monitoring Nodes...</span>
        </p>
    </div>
    <div class="text-right text-xs mono uppercase font-bold">
        <p style="color:{threat_color}" class="mb-1">● {threat} Threat Environment</p>
        <p class="text-slate-500">Last Synced: {date_str}</p>
    </div>
</header>

<main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
    <div class="lg:col-span-8 space-y-6 fadein">

        <section class="glass rounded-2xl p-6 md:p-8 border-l-4" style="border-color:{color}">
            <p class="text-xs mono font-black uppercase tracking-[0.4em] mb-3" style="color:{color}">● Today's Intelligence Brief</p>
            <h2 class="text-3xl md:text-5xl font-black tracking-tighter leading-tight text-white mb-6">{title}</h2>
            <p class="text-xs mono text-slate-500 uppercase tracking-widest mb-3">What happened today:</p>
            <div class="space-y-1">{bullets_html}</div>
        </section>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="glass rounded-2xl p-6 border-t-2 border-red-500/60">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-xs mono font-black text-red-400 uppercase tracking-widest">⚠️ Threat Signal</p>
                    <p class="text-3xl font-black text-red-400">{threat_score}<span class="text-base text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4"><div class="score-fill bg-red-500" style="width:{t_bar}%"></div></div>
                <p class="text-base text-slate-300 leading-relaxed">{threat_txt}</p>
            </div>
            <div class="glass rounded-2xl p-6 border-t-2" style="border-color:{color}88">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-xs mono font-black uppercase tracking-widest" style="color:{color}">💡 Opportunity Signal</p>
                    <p class="text-3xl font-black" style="color:{color}">{opp_score}<span class="text-base text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4"><div class="score-fill" style="width:{o_bar}%;background:{color}"></div></div>
                <p class="text-base text-slate-300 leading-relaxed">{opp_txt}</p>
            </div>
        </div>

        <div class="glass rounded-2xl p-6">
            <p class="text-xs mono font-black text-slate-500 uppercase tracking-widest mb-4">🪙 Tokens To Watch</p>
            <div class="mb-2">{tokens_html}</div>
            <p class="text-xs text-slate-600 italic mt-2">* Not financial advice. For research only.</p>
        </div>

        <div class="glass rounded-2xl p-6">
            <div class="flex justify-between items-center">
                <p class="text-xs mono font-black text-slate-500 uppercase tracking-widest">📊 Deep Analysis</p>
                <button id="deepbtn"
                    onclick="var d=document.getElementById('deepdive'),b=document.getElementById('deepbtn');if(d.style.display==='none'||!d.style.display){{d.style.display='block';b.innerText='Close ↑'}}else{{d.style.display='none';b.innerText='Read More ↓'}}"
                    class="text-xs mono font-black uppercase px-4 py-2 rounded-full border border-white/10 hover:border-white/30 transition">
                    Read More ↓
                </button>
            </div>
            <div id="deepdive" class="mt-6 pt-6 border-t border-white/5 text-base text-slate-300 leading-relaxed">{deep}</div>
        </div>

        <div class="glass rounded-2xl p-6 border-l-4 border-yellow-500/40">
            <p class="text-xs mono font-black text-yellow-500 uppercase tracking-widest mb-3">🤔 Contrarian View</p>
            <p class="text-base text-slate-400 italic leading-relaxed">"{critic}"</p>
            <p class="text-xs mono text-slate-600 mt-3 uppercase">— Powered by Groq / Llama 3.3 70b</p>
        </div>

        <div class="glass rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
            <div>
                <p class="text-xs mono font-black text-slate-500 uppercase tracking-widest mb-1">📢 Share This Report</p>
                <p class="text-sm text-slate-500">Found this useful? Share it with your network.</p>
            </div>
            <a href="https://twitter.com/intent/tweet?text={title}%20%E2%80%94%20Threat%3A%20{threat_score}%2F10%20%7C%20Opportunity%3A%20{opp_score}%2F10%0A%0Ahttps%3A%2F%2Fautonomous-portfolio-2026.live%20%23crypto%20%23web3%20%23AI"
               target="_blank"
               class="flex items-center gap-2 px-6 py-3 rounded-full font-black text-xs uppercase tracking-widest transition hover:opacity-80"
               style="background:#1d9bf0;color:white">
                𝕏 Share on X
            </a>
        </div>

    </div>

    <aside class="lg:col-span-4 space-y-6">

        <div class="glass rounded-2xl p-6 text-center">
            <p class="text-xs mono text-slate-500 uppercase tracking-widest mb-4">Signal Summary</p>
            <div class="grid grid-cols-2 gap-3">
                <div class="rounded-xl p-4" style="background:{color}11;border:1px solid {color}33">
                    <p class="text-4xl font-black" style="color:{color}">{opp_score}</p>
                    <p class="text-xs mono text-slate-500 uppercase mt-1">Opportunity</p>
                </div>
                <div class="rounded-xl p-4 bg-red-500/10 border border-red-500/20">
                    <p class="text-4xl font-black text-red-400">{threat_score}</p>
                    <p class="text-xs mono text-slate-500 uppercase mt-1">Threat</p>
                </div>
            </div>
            <p class="text-xs mono text-slate-600 mt-4 uppercase">{date_str}</p>
        </div>

        {market_bias_html}

        <div class="glass rounded-2xl p-6">
            <p class="text-xs mono font-bold text-slate-500 uppercase tracking-widest mb-4 pb-3 border-b border-white/5">📁 Signal Archive</p>
            <div class="max-h-[420px] overflow-y-auto pr-2"><!-- H_S -->{final_history}<!-- H_E --></div>
        </div>

        <div class="rounded-2xl p-6 bg-white/[0.02] border border-white/5 text-xs mono text-slate-600">
            <p class="text-slate-400 font-bold uppercase tracking-widest mb-3">AI Stack:</p>
            <p class="mb-1">» RSS: HackerNews / Krebs / CoinTelegraph</p>
            <p class="mb-1">» Research: Tavily Search API</p>
            <p class="mb-1">» Brain: Gemini 2.5 Flash</p>
            <p class="mb-1">» Critic: Llama 3.3 via Groq</p>
            <p class="mb-1">» Notify: Telegram Bot</p>
            <p class="mb-1">» SEO: Dev.to Auto-Publish</p>
            <p class="mt-4 text-[9px] opacity-30 uppercase tracking-widest">Free AI Pipeline // 2026</p>
        </div>

        <div class="rounded-2xl p-4 bg-yellow-500/5 border border-yellow-500/10">
            <p class="text-xs text-yellow-500/60 leading-relaxed">
                ⚠️ AI-generated for research and education only. Not financial advice. Always do your own research.
            </p>
        </div>

        <div class="glass rounded-2xl p-6 border border-yellow-500/20">
            <p class="text-xs mono font-black text-yellow-400 uppercase tracking-widest mb-3">💰 Support This Lab</p>
            <p class="text-sm text-slate-400 leading-relaxed mb-4">If this dashboard saved you time or helped you spot an opportunity — support the work.</p>
            <div class="rounded-xl p-3 mb-3" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06)">
                <p class="text-xs mono text-slate-500 uppercase mb-1">USDT (BEP20 / BSC Network)</p>
                <p class="text-xs mono text-yellow-400 break-all leading-relaxed">0x30ce31b427707335343b43708a35b20955f1763c2</p>
                <button onclick="navigator.clipboard.writeText('0x30ce31b427707335343b43708a35b20955f1763c2');this.innerText='✅ Copied!';setTimeout(()=>this.innerText='Copy Address',2000)"
                    class="mt-2 text-xs mono font-black uppercase px-3 py-1 rounded-full border border-white/10 hover:border-yellow-500/50 hover:text-yellow-400 transition text-slate-500">
                    Copy Address
                </button>
            </div>
            <p class="text-xs text-slate-600 italic">⚠️ BSC network only. Send USDT BEP20.</p>
        </div>

        <div class="glass rounded-2xl p-6">
            <p class="text-xs mono font-black text-slate-500 uppercase tracking-widest mb-4">👤 About</p>
            <p class="text-sm text-slate-400 leading-relaxed mb-3">
                Built by <span class="text-white font-bold">Kchour</span>, a developer from
                <span class="text-white font-bold">Phnom Penh, Cambodia</span> — experimenting
                with autonomous AI systems and real-time intelligence pipelines.
            </p>
            <p class="text-sm text-slate-500 leading-relaxed">
                This lab runs a fully automated multi-agent pipeline that pulls live news,
                researches deeper context, and generates expert analysis — updated every 2 hours,
                entirely free, entirely autonomous.
            </p>
            <a href="https://github.com/kchour96-dev/autonomous-portfolio-2026"
               target="_blank"
               class="inline-block mt-4 text-xs mono font-black uppercase tracking-widest px-4 py-2 rounded-full border border-white/10 hover:border-white/30 transition text-slate-400 hover:text-white">
                View on GitHub →
            </a>
            <a href="https://t.me/AII2026futher"
               target="_blank"
               class="inline-block mt-2 text-xs mono font-black uppercase tracking-widest px-4 py-2 rounded-full border border-blue-500/30 hover:border-blue-500/60 transition text-blue-400 hover:text-blue-300">
                📢 Join Telegram →
            </a>
        </div>

    </aside>
</main>

<footer class="max-w-7xl mx-auto mt-12 pt-6 border-t border-white/5 flex flex-wrap justify-between gap-2 text-xs mono text-slate-700">
    <p>AUTONOMOUS-PORTFOLIO-2026.LIVE // AI AGENT PIPELINE // {date_str}</p>
    <p>NOT FINANCIAL ADVICE // RESEARCH ONLY</p>
</footer>

<script>
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
        print("Fatal Error: GEMINI API key not set in environment. Aborting.")
        return

    old_content = ""
    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")
        with open("index.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    rss_context = get_rss_context()
    research    = get_research(rss_context, t_key)
    data        = get_ai_data(research, g_key)

    if not data:
        print("Warning: All AI engines failed. Keeping existing index.html.")
        if os.path.exists("index.html.bak"):
            os.remove("index.html.bak")
        return

    history_html = ""
    if "<!-- H_S -->" in old_content and "<!-- H_E -->" in old_content:
        history_html = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]

    date_str  = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_entry = (
        f"<div class='mb-4 pl-3 border-l border-white/10 opacity-60'>"
        f"<p class='text-xs mono text-slate-500'>{date_str}</p>"
        f"<p class='text-sm font-bold text-slate-300 uppercase tracking-tight mt-0.5'>{data.get('title','Intelligence Alert')}</p>"
        f"<p class='text-xs text-slate-500 mt-0.5'>⚠️ {data.get('threat_score','?')}/10 &nbsp;💡 {data.get('opportunity_score','?')}/10</p>"
        f"</div>"
    )
    final_history = (new_entry + history_html)[:5000]

    html_payload = build_html(data, final_history, date_str)
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_payload)
        print("✅ index.html written successfully.")
    except Exception as e:
        print(f"Error writing index.html: {e}")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    if os.path.exists("index.html.bak"):
        os.remove("index.html.bak")

    write_seo_files()
    post_to_devto(data)
    send_telegram(
        data.get('title',''),
        data.get('threat',''),
        data.get('opportunity',''),
        data.get('threat_score','?'),
        data.get('opportunity_score','?')
    )
    print("✅ Autonomous execution loop complete!")

if __name__ == "__main__":
    print(f"🚀 Agent starting: {datetime.now().strftime('%d %b %Y %H:%M UTC')}")
    run_production_agent()
