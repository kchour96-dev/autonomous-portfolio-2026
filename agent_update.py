import os
import requests
import json
import re
import shutil
from datetime import datetime

# ─────────────────────────────────────────────
# LAYER 1: RSS — Real world news
# ─────────────────────────────────────────────
def get_rss_context():
    feeds = [
        "https://feeds.feedburner.com/TheHackersNews",
        "https://krebsonsecurity.com/feed/",
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
    ]
    items = []
    for url in feeds:
        try:
            r = requests.get(url, timeout=8)
            titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', r.text, re.DOTALL)
            # Take only 1 headline per feed to get variety
            clean = [t.strip() for t in titles[1:2] if t.strip()]
            items.extend(clean)
        except Exception as e:
            print(f"RSS failed {url}: {e}")
    result = " | ".join(items[:6]) if items else "Crypto and Web3 market developments 2026"
    print(f"RSS context: {result[:100]}...")
    return result

def get_price_context():
    """Free CoinGecko API — no API key needed"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana,binancecoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            },
            timeout=8
        )
        r.raise_for_status()
        d = r.json()
        btc = d.get('bitcoin', {})
        eth = d.get('ethereum', {})
        sol = d.get('solana', {})
        context = (
            f"BTC ${btc.get('usd',0):,} ({btc.get('usd_24h_change',0):+.1f}% 24h) | "
            f"ETH ${eth.get('usd',0):,} ({eth.get('usd_24h_change',0):+.1f}% 24h) | "
            f"SOL ${sol.get('usd',0):,} ({sol.get('usd_24h_change',0):+.1f}% 24h)"
        )
        print(f"Prices: {context}")
        return context, btc, eth, sol
    except Exception as e:
        print(f"Price fetch failed: {e}")
        return "", {}, {}, {}

def get_trending_tokens():
    """CoinGecko trending — no API key needed"""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=8
        )
        r.raise_for_status()
        coins = r.json().get('coins', [])
        tokens = [c['item']['symbol'].upper() for c in coins[:5]]
        print(f"Trending: {tokens}")
        return tokens
    except Exception as e:
        print(f"Trending fetch failed: {e}")
        return []

def get_coindesk_sentiment():
    """Pull CoinDesk RSS and extract sentiment labels"""
    try:
        r = requests.get(
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            timeout=8
        )
        text = r.text
        titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', text, re.DOTALL)
        titles = [t.strip() for t in titles[1:8] if t.strip()]
        # Count sentiment keywords
        negative_words = ['tank', 'crash', 'bleed', 'hack', 'breach', 'attack', 'fall', 'drop', 'loss', 'probe', 'ban', 'leave', 'slow']
        positive_words = ['surge', 'rally', 'rise', 'higher', 'buy', 'boom', 'growth', 'lead', 'win', 'boost', 'top']
        neg = sum(1 for t in titles for w in negative_words if w in t.lower())
        pos = sum(1 for t in titles for w in positive_words if w in t.lower())
        total = len(titles)
        if neg > pos:
            mood = "BEARISH"
            mood_score = min(int((neg / total) * 10), 10)
        else:
            mood = "BULLISH"
            mood_score = min(int((pos / total) * 10), 10)
        headlines = " | ".join(titles[:5])
        print(f"CoinDesk sentiment: {mood} ({neg} neg / {pos} pos) — {headlines[:80]}")
        return headlines, mood, mood_score
    except Exception as e:
        print(f"CoinDesk sentiment failed: {e}")
        return "", "NEUTRAL", 5

# ─────────────────────────────────────────────
# LAYER 2: Tavily — Deep research
# ─────────────────────────────────────────────
def get_research(rss_context, t_key):
    if not t_key:
        print("No TAVILY key, using RSS context only.")
        return rss_context
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": t_key,
                "query": f"crypto web3 DeFi {rss_context[:150]} risk opportunity 2026",
                "max_results": 3
            },
            timeout=10
        )
        r.raise_for_status()
        results = r.json().get('results', [])
        if results:
            combined = " ".join([res.get('content', '') for res in results])[:2000]
            print(f"Tavily loaded: {len(combined)} chars")
            return combined
    except Exception as e:
        print(f"Tavily failed: {e}")
    return rss_context

# ─────────────────────────────────────────────
# LAYER 3: Gemini — with model fallback chain
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_groq(prompt, key):
    """Groq fallback — 14,400 free requests/day"""
    if not key:
        raise ValueError("No GROQ key")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload, headers=headers, timeout=30
    )
    resp.raise_for_status()
    raw = resp.json()['choices'][0]['message']['content']
    # Remove control characters that break JSON parsing
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    return raw

def get_gemini_data(research_context, g_key, price_context="", sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None):
    trending_str = ", ".join(trending_tokens) if trending_tokens else "BTC, ETH, SOL"
    prompt = f"""You are an expert crypto and Web3 analyst running a real-time intelligence dashboard.

REAL MARKET DATA RIGHT NOW:
- Prices: {price_context}
- Market Sentiment from CoinDesk headlines: {sentiment_mood} (score: {sentiment_score}/10)
- Trending tokens people are searching right now: {trending_str}

NEWS RESEARCH:
{research_context}

Use the REAL data above to calibrate your scores accurately. If sentiment is BEARISH, threat score should be higher. If prices are down 3%+, adjust accordingly.

Return ONLY a valid JSON object. No markdown fences. No extra text:
{{
  "title": "Sharp 4-6 word headline about today biggest story",
  "news_bullets": [
    "One sentence summary of news item 1",
    "One sentence summary of news item 2",
    "One sentence summary of news item 3"
  ],
  "threat": "One clear sentence about the main risk based on real data",
  "opportunity": "One clear sentence about the best opportunity based on real data",
  "threat_score": 7,
  "opportunity_score": 6,
  "threat_level": "Medium",
  "deep_analysis": "Three paragraphs of expert analysis separated by newlines",
  "tokens_to_watch": ["USE_TRENDING_TOKENS_FROM_ABOVE", "SECOND_TRENDING_TOKEN", "THIRD_TRENDING_TOKEN"],
  "critic": "One sentence contrarian view why the opportunity might be wrong",
  "color": "#hexcolor matching the mood"
}}

IMPORTANT: For tokens_to_watch use the TRENDING tokens provided above — those are what people are actually searching right now."""

    # Updated fallback chain with working models only
    attempts = [
        ("gemini-2.5-flash",        "gemini", g_key),
        ("gemini-2.0-flash",        "gemini", g_key),
        ("groq-llama-3.3-70b",      "groq",   os.getenv("GROQ")),
        ("gemini-2.0-flash-lite",   "gemini", g_key),
    ]

    for model_name, provider, key in attempts:
        try:
            print(f"Trying: {model_name}")
            if provider == "groq":
                raw = call_groq(prompt, key)
            else:
                raw = call_gemini(prompt, key, model_name)
            print(f"Response: {len(raw)} chars")
            # Clean control characters before parsing
            raw_clean = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
            match = re.search(r'\{.*\}', raw_clean, re.DOTALL)
            if not match:
                raise ValueError("No JSON found")
            data = json.loads(match.group(0))
            print(f"SUCCESS with {model_name}: {data.get('title','no title')}")
            return data
        except Exception as e:
            print(f"{model_name} failed: {e}")
            continue

    print("ALL MODELS FAILED. Circuit breaker triggered.")
    return None

# ─────────────────────────────────────────────
# NOTIFY: Telegram
# ─────────────────────────────────────────────
def send_telegram(title, threat, opportunity, threat_score, opp_score):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        return
    msg = (
        f"🧠 *AUTONOMOUS LAB UPDATE*\n\n"
        f"*{title}*\n\n"
        f"⚠️ Threat [{threat_score}/10]: {threat}\n\n"
        f"💡 Opportunity [{opp_score}/10]: {opportunity}\n\n"
        f"🔗 https://autonomous-portfolio-2026.live"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        print("Telegram sent.")
    except Exception as e:
        print(f"Telegram failed: {e}")

# ─────────────────────────────────────────────
# PUBLISH: Dev.to
# ─────────────────────────────────────────────
def post_to_devto(data):
    key = os.getenv("DEV")
    if not key:
        print("No DEV key, skipping.")
        return
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])])
    tokens = ", ".join(data.get('tokens_to_watch', []))
    body = (
        f"> 🔗 Live Dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n"
        f"> 📢 Telegram Channel: [t.me/AII2026futher](https://t.me/AII2026futher)\n\n"
        f"## Today's Headlines\n\n{bullets}\n\n"
        f"## ⚠️ Threat Signal [{data.get('threat_score','?')}/10]\n\n{data.get('threat','')}\n\n"
        f"## 💡 Opportunity Signal [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity','')}\n\n"
        f"## 🪙 Tokens To Watch\n\n{tokens}\n\n"
        f"## 📊 Deep Analysis\n\n{data.get('deep_analysis','')}\n\n"
        f"---\n"
        f"*AI-powered dashboard — Gemini + Groq + Tavily. Updated every 2 hours automatically.*\n\n"
        f"📢 Follow our Telegram for real-time alerts: https://t.me/AII2026futher"
    )
    try:
        r = requests.post(
            "https://dev.to/api/articles",
            json={"article": {
                "title": data.get('title', 'Crypto Intelligence Update'),
                "body_markdown": body,
                "tags": ["crypto", "web3", "defi", "security"],
                "published": True
            }},
            headers={"api-key": key},
            timeout=15
        )
        r.raise_for_status()
        print(f"Dev.to published: {r.json().get('url','')}")
    except Exception as e:
        print(f"Dev.to failed: {e}")

# ─────────────────────────────────────────────
# SEO files
# ─────────────────────────────────────────────
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
  <url>
    <loc>https://autonomous-portfolio-2026.live/privacy.html</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>"""
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)
    with open("robots.txt", "w") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n")
    print("SEO files updated.")

# ─────────────────────────────────────────────
# BUILD HTML
# ─────────────────────────────────────────────
def build_html(data, final_history, date_str, price_context="", sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None, btc={}, eth={}, sol={}):
    color        = data.get('color', '#3b82f6')
    threat       = data.get('threat_level', 'Unknown')
    title        = data.get('title', 'Intelligence Report')
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
    tokens_html = " ".join([
        f'<span class="inline-block px-3 py-1 rounded-full text-[11px] font-black mono mr-1 mb-2" '
        f'style="background:{color}22;color:{color};border:1px solid {color}44">{t.strip()}</span>'
        for t in tokens if t.strip()
    ])

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10

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
        <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mt-1">
            <span class="blink" style="color:{color}">●</span>&nbsp;Real-Time Crypto &amp; Web3 Intelligence — Updated Every 2 Hours By AI
        </p>
    </div>
    <div class="text-right text-[10px] mono uppercase font-bold">
        <p style="color:{threat_color}" class="mb-1">● {threat} Threat Environment</p>
        <p class="text-slate-500">{date_str}</p>
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
            <p class="text-[9px] mono text-slate-600 mt-4 uppercase">{date_str}</p>
        </div>

        <!-- LIVE MARKET DATA -->
        <div class="glass rounded-2xl p-5 space-y-4">
            <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest">📈 Live Market</p>

            <!-- Prices -->
            <div class="space-y-2">
                <div class="flex justify-between items-center">
                    <span class="text-[10px] mono text-slate-500">BTC</span>
                    <span class="text-[11px] mono font-black {'text-green-400' if btc.get('usd_24h_change',0) >= 0 else 'text-red-400'}">${btc.get('usd',0):,} <span class="text-[9px]">({btc.get('usd_24h_change',0):+.1f}%)</span></span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-[10px] mono text-slate-500">ETH</span>
                    <span class="text-[11px] mono font-black {'text-green-400' if eth.get('usd_24h_change',0) >= 0 else 'text-red-400'}">${eth.get('usd',0):,} <span class="text-[9px]">({eth.get('usd_24h_change',0):+.1f}%)</span></span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-[10px] mono text-slate-500">SOL</span>
                    <span class="text-[11px] mono font-black {'text-green-400' if sol.get('usd_24h_change',0) >= 0 else 'text-red-400'}">${sol.get('usd',0):,} <span class="text-[9px]">({sol.get('usd_24h_change',0):+.1f}%)</span></span>
                </div>
            </div>

            <!-- Sentiment -->
            <div class="pt-3 border-t border-white/5">
                <div class="flex justify-between items-center mb-1">
                    <span class="text-[9px] mono text-slate-500 uppercase">News Sentiment</span>
                    <span class="text-[10px] mono font-black {'text-green-400' if sentiment_mood == 'BULLISH' else 'text-red-400'}">{sentiment_mood}</span>
                </div>
                <div class="score-bar">
                    <div class="score-fill {'bg-green-500' if sentiment_mood == 'BULLISH' else 'bg-red-500'}" style="width:{sentiment_score * 10}%"></div>
                </div>
            </div>

            <!-- Trending -->
            <div class="pt-3 border-t border-white/5">
                <p class="text-[9px] mono text-slate-500 uppercase mb-2">🔥 Trending Now</p>
                <div class="flex flex-wrap gap-1">
                    {''.join([f'<span class="text-[9px] mono px-2 py-0.5 rounded-full bg-white/5 text-slate-400 border border-white/10">{t}</span>' for t in (trending_tokens or [])])}
                </div>
            </div>

            <p class="text-[8px] mono text-slate-700">via CoinGecko • not financial advice</p>
        </div>

        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-bold text-slate-500 uppercase tracking-widest mb-4 pb-3 border-b border-white/5">📁 Signal Archive</p>
            <div><!-- H_S -->{final_history}<!-- H_E --></div>
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
</body>
</html>"""

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run_production_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    if not g_key:
        print("FATAL: GEMINI secret not set. Aborting.")
        return

    # Backup
    old_content = ""
    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")
        with open("index.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    # Run pipeline — all data sources
    rss_context                              = get_rss_context()
    price_context, btc, eth, sol             = get_price_context()
    trending_tokens                          = get_trending_tokens()
    coindesk_headlines, sentiment_mood, sentiment_score = get_coindesk_sentiment()
    research = get_research(rss_context + " " + coindesk_headlines, t_key)

    # Avoid duplicate stories
    last_title = ""
    if "<!-- H_S -->" in old_content:
        try:
            hist  = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]
            match = re.search(r"tracking-tight'>(.*?)</p>", hist)
            if match:
                last_title = match.group(1)
                print(f"Last story: {last_title}")
        except: pass

    full_context = research
    if last_title:
        full_context += f"\n\nIMPORTANT: Last report was about '{last_title}'. Pick a DIFFERENT story today."

    data = get_gemini_data(full_context, g_key, price_context, sentiment_mood, sentiment_score, trending_tokens)

    if not data:
        print("All models failed. Keeping old site.")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    # Build archive
    history_html = ""
    if "<!-- H_S -->" in old_content and "<!-- H_E -->" in old_content:
        history_html = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]

    date_str  = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_entry = (
        f"<div class='mb-3 pl-3 border-l border-white/10 opacity-50 text-[10px]'>"
        f"<p class='mono text-slate-500'>{date_str}</p>"
        f"<p class='font-bold text-slate-300 uppercase tracking-tight'>{data.get('title','Update')}</p>"
        f"<p class='text-slate-500'>⚠️ {data.get('threat_score','?')}/10 &nbsp;💡 {data.get('opportunity_score','?')}/10</p>"
        f"</div>"
    )
    final_history = (new_entry + history_html)[:4000]

    # Write HTML
    html = build_html(data, final_history, date_str, price_context, sentiment_mood, sentiment_score, trending_tokens, btc, eth, sol)
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html written successfully.")
    except Exception as e:
        print(f"Write failed: {e}")
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
    print("✅ Production sync complete!")

if __name__ == "__main__":
    run_production_agent()
