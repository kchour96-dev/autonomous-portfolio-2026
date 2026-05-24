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

Use the REAL data above to calibrate your scores accurately.
If sentiment is BEARISH, threat score should be higher. If prices are down 3%+, adjust accordingly.
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
def build_html(data, final_history, date_str, price_context="", sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None, btc=None, eth=None, sol=None):
    if btc is None: btc = {}
    if eth is None: eth = {}
    if sol is None: sol = {}
    color        = data.get('color', '#dc2626')
    threat       = data.get('threat_level', 'Unknown')
    title        = data.get('title', 'Intelligence Report')
    news_bullets = data.get('news_bullets', [])
    threat_txt   = data.get('threat', '')
    opp_txt      = data.get('opportunity', '')
    threat_score = data.get('threat_score', 5)
    opp_score    = data.get('opportunity_score', 5)
    deep_raw     = data.get('deep_analysis', '')
    tokens       = data.get('tokens_to_watch', [])
    critic       = data.get('critic', '')

    threat_colors = {"Critical":"#dc2626","High":"#f97316","Medium":"#eab308","Low":"#22c55e"}
    threat_color  = threat_colors.get(threat, "#94a3b8")
    threat_label  = {"Critical":"● CRITICAL THREAT","High":"● HIGH THREAT","Medium":"● MEDIUM THREAT","Low":"● LOW THREAT"}.get(threat, "● UNKNOWN")

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10

    if int(str(threat_score)) if str(threat_score).isdigit() else 5 >= 7:
        bias_label = "📉 BEARISH BIAS"
        bias_desc  = "High threat — short-term selling pressure likely"
        bias_color = "#ef4444"
    elif int(str(opp_score)) if str(opp_score).isdigit() else 5 >= 7:
        bias_label = "📈 BULLISH BIAS"
        bias_desc  = "Strong opportunity — mid-term buying interest"
        bias_color = "#22c55e"
    else:
        bias_label = "⚖️ MIXED SIGNALS"
        bias_desc  = "Wait for clarity before acting"
        bias_color = "#eab308"

    bullets_html = ""
    for i, b in enumerate(news_bullets, 1):
        bullets_html += f"""
            <div class="flex gap-5 items-start group/item p-4 rounded-2xl hover:bg-white/[0.02] transition duration-300">
                <span class="mt-1 flex-shrink-0 w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 text-sm font-bold">{i}</span>
                <p class="text-lg text-slate-300 leading-relaxed group-hover/item:text-slate-200 transition">{b}</p>
            </div>"""

    tokens_html = ""
    for i, t in enumerate(tokens):
        if t.strip():
            delay = i * 0.3
            tokens_html += f'<span class="tag bg-red-500/5 text-red-400 border border-red-500/20 hover:bg-red-500/10 hover:border-red-500/40 text-base"><span class="w-2 h-2 rounded-full bg-red-400 blink" style="animation-delay:{delay}s"></span>{t.strip()}</span>\n'

    deep_paras = [p.strip() for p in deep_raw.split('\n') if p.strip()]
    deep_html = ""
    para_titles = ["Root Cause Analysis", "Supply Chain Impact", "Mid-Term Outlook"]
    for i, para in enumerate(deep_paras[:3]):
        ptitle = para_titles[i] if i < len(para_titles) else f"Analysis {i+1}"
        deep_html += f"""
            <div class="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
                <h4 class="text-lg font-bold text-white mb-3 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-red-500"></span>{ptitle}
                </h4>
                <p>{para}</p>
            </div>"""

    trending_html = ""
    if trending_tokens:
        for t in trending_tokens[:5]:
            trending_html += f'<span class="text-[11px] mono px-3 py-1 rounded-full bg-white/5 text-slate-400 border border-white/10">{t}</span>\n'

    # Sentiment bar
    sent_color = "#22c55e" if sentiment_mood == "BULLISH" else "#ef4444"
    sent_width = sentiment_score * 10

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
    <meta property="og:description" content="Threat: {threat_score}/10 | Opportunity: {opp_score}/10 — Live crypto intelligence">
    <meta property="og:url" content="https://autonomous-portfolio-2026.live">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title} — Autonomous Lab 2026">
    <meta name="twitter:description" content="Threat {threat_score}/10 | Opp {opp_score}/10 — {threat_txt[:80]}">
    <link rel="canonical" href="https://autonomous-portfolio-2026.live/">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527" crossorigin="anonymous"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *{{box-sizing:border-box}}
        body{{background:#06070f;color:#f1f5f9;font-family:'Space Grotesk',sans-serif;margin:0;font-size:18px;line-height:1.7;-webkit-font-smoothing:antialiased}}
        .mono{{font-family:'JetBrains Mono',monospace}}
        .glass{{background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.06);backdrop-filter:blur(24px) saturate(1.2);-webkit-backdrop-filter:blur(24px) saturate(1.2);box-shadow:0 4px 24px rgba(0,0,0,0.2),inset 0 1px 0 rgba(255,255,255,0.04)}}
        .glass-hover:hover{{background:rgba(15,23,42,0.5);border-color:rgba(255,255,255,0.1);transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,0.3)}}
        .score-bar{{height:6px;background:rgba(255,255,255,0.04);border-radius:99px;overflow:hidden}}
        .score-fill{{height:100%;border-radius:99px;transition:width 1.5s cubic-bezier(0.4,0,0.2,1)}}
        .score-fill::after{{content:'';position:absolute;top:0;right:0;bottom:0;width:30px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.4));border-radius:0 99px 99px 0}}
        @keyframes pulse{{0%,100%{{opacity:1;box-shadow:0 0 12px currentColor}}50%{{opacity:0.4;box-shadow:0 0 4px currentColor}}}}
        .blink{{animation:pulse 2.5s ease-in-out infinite}}
        @keyframes fadeUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}
        .fadein{{animation:fadeUp 0.7s cubic-bezier(0.16,1,0.3,1) forwards}}
        .fadein-delay-1{{animation-delay:0.15s;opacity:0}}
        .fadein-delay-2{{animation-delay:0.3s;opacity:0}}
        .fadein-delay-3{{animation-delay:0.45s;opacity:0}}
        .fadein-delay-4{{animation-delay:0.6s;opacity:0}}
        @keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
        .shimmer{{background:linear-gradient(90deg,transparent,rgba(255,255,255,0.03),transparent);background-size:200% 100%;animation:shimmer 8s infinite}}
        @keyframes countUp{{from{{opacity:0;transform:translateY(20px) scale(0.8)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
        .count-number{{animation:countUp 0.8s cubic-bezier(0.34,1.56,0.64,1) forwards}}
        ::-webkit-scrollbar{{width:6px}}
        ::-webkit-scrollbar-track{{background:transparent}}
        ::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.1);border-radius:99px}}
        .tag{{display:inline-flex;align-items:center;gap:8px;padding:8px 20px;border-radius:99px;font-size:0.875rem;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:0.05em;transition:all 0.3s ease;cursor:default}}
        .tag:hover{{transform:scale(1.05)}}
        .btn-primary{{position:relative;overflow:hidden;transition:all 0.3s ease}}
        .btn-primary::before{{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent);transition:left 0.5s ease}}
        .btn-primary:hover::before{{left:100%}}
        #deepdive{{max-height:0;overflow:hidden;opacity:0;transition:max-height 0.6s cubic-bezier(0.4,0,0.2,1),opacity 0.5s ease,padding 0.5s ease}}
        #deepdive.active{{max-height:1200px;opacity:1}}
        .bg-grid{{background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:80px 80px}}
        .status-dot{{width:10px;height:10px;border-radius:50%;display:inline-block}}
        .archive-item{{transition:all 0.3s ease;border-left:3px solid transparent}}
        .archive-item:hover{{background:rgba(255,255,255,0.02);border-left-color:rgba(220,38,38,0.6);padding-left:20px}}
        .gradient-text{{background:linear-gradient(135deg,#fff 0%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
        .big-number{{font-size:clamp(3rem,8vw,5rem);font-weight:800;line-height:1;letter-spacing:-0.04em}}
        .section-label{{font-size:0.75rem;font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#94a3b8}}
        .card-header{{display:flex;align-items:center;gap:12px;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.04)}}
        .highlight-box{{background:rgba(220,38,38,0.04);border:1px solid rgba(220,38,38,0.12);border-radius:16px;padding:24px}}
    </style>
</head>
<body class="min-h-screen bg-grid">

<div class="w-full border-b border-white/[0.04] bg-[#06070f]/90 backdrop-blur-xl sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 md:px-8 py-4 flex justify-between items-center">
        <div class="flex items-center gap-4">
            <span class="status-dot blink bg-red-500"></span>
            <span class="text-xs mono font-semibold text-slate-400 uppercase tracking-widest" id="terminal-live-status">AI Agent Pipeline Online // Monitoring Nodes...</span>
        </div>
        <div class="flex items-center gap-6 text-xs mono text-slate-500">
            <span class="hidden sm:inline">Last Synced: {date_str}</span>
            <span class="px-3 py-1.5 rounded-lg font-bold tracking-wider" style="background:{threat_color}18;color:{threat_color};border:1px solid {threat_color}33">{threat_label}</span>
        </div>
    </div>
</div>

<div class="p-4 md:p-8 lg:p-12">

<header class="max-w-7xl mx-auto mb-16 fadein">
    <div class="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-8 pb-10 border-b border-white/[0.06]">
        <div class="space-y-4">
            <div class="flex items-center gap-4 mb-3">
                <div class="h-px w-16 bg-gradient-to-r from-red-500 to-transparent"></div>
                <span class="text-xs mono font-bold text-red-400 uppercase tracking-[0.3em]">Intelligence Dashboard</span>
            </div>
            <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[0.9]">
                <span class="gradient-text">AUTONOMOUS</span><br>
                <span class="text-red-600">LAB<span class="text-slate-600 font-light">.2026</span></span>
            </h1>
            <p class="text-base text-slate-500 max-w-xl leading-relaxed mt-4">Real-time autonomous intelligence pipeline monitoring crypto security threats, Web3 vulnerabilities, and market signals.</p>
        </div>
        <div class="flex items-center gap-4 bg-white/[0.02] border border-white/[0.06] rounded-2xl px-6 py-4">
            <span class="w-3 h-3 rounded-full bg-emerald-500 blink" style="animation-duration:3s"></span>
            <div>
                <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-1">System Status</p>
                <p class="text-sm font-bold text-emerald-400 uppercase tracking-wide">Operational</p>
            </div>
        </div>
    </div>
</header>

<main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">

    <div class="lg:col-span-8 space-y-8">

        <section class="glass rounded-3xl p-8 md:p-12 relative overflow-hidden fadein fadein-delay-1 group">
            <div class="absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 transition duration-700" style="background:{color}0d"></div>
            <div class="relative z-10">
                <div class="flex items-center gap-4 mb-8">
                    <span class="px-4 py-2 rounded-xl text-xs mono font-bold uppercase tracking-widest" style="background:{threat_color}18;border:1px solid {threat_color}33;color:{threat_color}">● {threat} Alert</span>
                    <span class="text-xs mono text-slate-500 uppercase tracking-widest">Today's Intelligence Brief</span>
                </div>
                <h2 class="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white mb-8 leading-[1.05]">{title}</h2>
                <div class="space-y-2">{bullets_html}</div>
            </div>
        </section>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 fadein fadein-delay-2">
            <div class="glass rounded-3xl p-8 relative overflow-hidden group glass-hover transition-all duration-300">
                <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-red-700 via-red-500 to-red-400"></div>
                <div class="card-header" style="border-color:rgba(239,68,68,0.1)">
                    <div>
                        <p class="section-label text-red-400 mb-1">Threat Signal</p>
                        <p class="text-sm text-slate-500">Systemic Risk Assessment</p>
                    </div>
                </div>
                <div class="flex items-baseline gap-2 mb-2">
                    <span class="big-number text-red-400 count-number" data-target="{threat_score}">0</span>
                    <span class="text-2xl text-slate-600 font-light">/10</span>
                </div>
                <div class="score-bar mb-6 relative"><div class="score-fill bg-gradient-to-r from-red-700 via-red-500 to-red-400" style="width:0%" data-width="{t_bar}%"></div></div>
                <p class="text-base text-slate-400 leading-relaxed">{threat_txt}</p>
            </div>
            <div class="glass rounded-3xl p-8 relative overflow-hidden group glass-hover transition-all duration-300">
                <div class="absolute top-0 left-0 w-full h-1.5" style="background:linear-gradient(to right,{color}99,{color})"></div>
                <div class="card-header" style="border-color:{color}1a">
                    <div>
                        <p class="section-label mb-1" style="color:{color}">Opportunity Signal</p>
                        <p class="text-sm text-slate-500">Market Positioning</p>
                    </div>
                </div>
                <div class="flex items-baseline gap-2 mb-2">
                    <span class="big-number count-number" style="color:{color}" data-target="{opp_score}">0</span>
                    <span class="text-2xl text-slate-600 font-light">/10</span>
                </div>
                <div class="score-bar mb-6 relative"><div class="score-fill" style="width:0%;background:linear-gradient(to right,{color}99,{color})" data-width="{o_bar}%"></div></div>
                <p class="text-base text-slate-400 leading-relaxed">{opp_txt}</p>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 fadein fadein-delay-3">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">🪙 Tokens To Watch</p>
                    <p class="text-sm text-slate-500">AI-identified positioning opportunities</p>
                </div>
                <span class="text-xs mono text-slate-600 uppercase tracking-widest px-3 py-1 rounded-lg bg-white/[0.02] border border-white/[0.04]">Research Only</span>
            </div>
            <div class="flex flex-wrap gap-4 mb-6">{tokens_html}</div>
            <div class="highlight-box">
                <p class="text-sm text-slate-500 leading-relaxed"><span class="text-red-400 font-bold">Note:</span> AI pattern recognition based on current threat landscape. Not financial advice.</p>
            </div>
        </div>

        <div class="glass rounded-3xl overflow-hidden fadein fadein-delay-3">
            <div class="p-8 md:p-10">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="section-label mb-1">📊 Deep Analysis</p>
                        <p class="text-sm text-slate-500">Expanded technical breakdown</p>
                    </div>
                    <button id="deepbtn" onclick="toggleDeepDive()" class="btn-primary text-sm mono font-bold uppercase tracking-widest px-6 py-3 rounded-2xl border border-white/10 hover:border-white/30 transition bg-white/[0.02] hover:bg-white/[0.05] text-slate-300 flex items-center gap-2">
                        <span>Read Analysis</span>
                        <svg class="w-4 h-4 transition-transform" id="deep-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                    </button>
                </div>
            </div>
            <div id="deepdive" class="px-8 md:px-10 pb-10 text-base text-slate-400 leading-relaxed border-t border-white/[0.04]">
                <div class="pt-8 space-y-5">{deep_html}</div>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 border-l-4 border-yellow-500/30 relative overflow-hidden fadein fadein-delay-3">
            <div class="absolute -right-8 -top-8 w-40 h-40 bg-yellow-500/5 rounded-full blur-3xl"></div>
            <div class="relative z-10">
                <div class="flex items-center gap-3 mb-6">
                    <span class="text-2xl">🤔</span>
                    <p class="section-label text-yellow-500">Contrarian View</p>
                </div>
                <blockquote class="text-2xl md:text-3xl text-slate-200 font-light italic leading-relaxed border-l-4 border-yellow-500/20 pl-6">"{critic}"</blockquote>
                <div class="mt-6 flex items-center gap-3 pt-6 border-t border-white/[0.04]">
                    <div class="w-10 h-10 rounded-full bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center"><span class="text-yellow-500 text-lg">🧠</span></div>
                    <div>
                        <p class="text-sm font-bold text-slate-300">AI Critic Model</p>
                        <p class="text-xs mono text-slate-500 uppercase tracking-widest">Groq / Llama 3.3 70b</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 flex flex-wrap items-center justify-between gap-6 fadein fadein-delay-4">
            <div>
                <p class="section-label mb-1">📢 Share This Report</p>
                <p class="text-base text-slate-500">Found this useful? Share it with your network.</p>
            </div>
            <a href="https://twitter.com/intent/tweet?text={title}%20%E2%80%94%20Threat%3A%20{threat_score}%2F10%20%7C%20Opportunity%3A%20{opp_score}%2F10%0A%0Ahttps%3A%2F%2Fautonomous-portfolio-2026.live%20%23crypto%20%23web3%20%23AI" target="_blank" class="btn-primary flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-sm uppercase tracking-widest transition text-white shadow-xl" style="background:#1d9bf0;box-shadow:0 8px 24px rgba(29,155,240,0.2)">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                <span>Share on X</span>
            </a>
        </div>

    </div>

    <aside class="lg:col-span-4 space-y-8">

        <div class="glass rounded-3xl p-6 relative overflow-hidden fadein fadein-delay-1">
            <div class="card-header border-b border-white/[0.04] pb-4 mb-4">
                <div>
                    <p class="section-label mb-1">📈 Live Market</p>
                    <p class="text-[10px] mono text-slate-500 uppercase tracking-widest" id="market-status">Syncing Feed...</p>
                </div>
                <span class="w-2 h-2 rounded-full bg-emerald-500 blink" id="ticker-pulse"></span>
            </div>
            
            <div class="space-y-4">
                <div class="flex justify-between items-center p-3 rounded-xl bg-white/[0.01] border border-white/[0.02]">
                    <span class="font-bold tracking-wide text-slate-200">BTC</span>
                    <div class="text-right mono">
                        <p id="live-btc-price" class="font-bold text-white text-base">Fetching...</p>
                        <p id="live-btc-change" class="text-xs">--</p>
                    </div>
                </div>
                <div class="flex justify-between items-center p-3 rounded-xl bg-white/[0.01] border border-white/[0.02]">
                    <span class="font-bold tracking-wide text-slate-200">ETH</span>
                    <div class="text-right mono">
                        <p id="live-eth-price" class="font-bold text-white text-base">Fetching...</p>
                        <p id="live-eth-change" class="text-xs">--</p>
                    </div>
                </div>
                <div class="flex justify-between items-center p-3 rounded-xl bg-white/[0.01] border border-white/[0.02]">
                    <span class="font-bold tracking-wide text-slate-200">SOL</span>
                    <div class="text-right mono">
                        <p id="live-sol-price" class="font-bold text-white text-base">Fetching...</p>
                        <p id="live-sol-change" class="text-xs">--</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass rounded-3xl p-6 fadein fadein-delay-2">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">📊 Media Bias</p>
                    <p class="text-sm text-slate-500">CoinDesk NLP Scrape</p>
                </div>
            </div>
            <div class="mb-4">
                <div class="flex justify-between text-sm mb-1">
                    <span class="font-bold" style="color:{sent_color}">{sentiment_mood}</span>
                    <span class="mono text-slate-400">{sentiment_score}/10</span>
                </div>
                <div class="score-bar relative"><div class="score-fill" style="width:{sent_width}%;background:{sent_color}"></div></div>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">Calculated by scanning the top breaking media anchors for high-density panic or expansion keywords.</p>
        </div>

        <div class="glass rounded-3xl p-6 border-t-4 fadein fadein-delay-3" style="border-color:{bias_color}">
            <p class="section-label mb-2">🤖 Engine Bias</p>
            <h3 class="text-xl font-bold text-white mb-1">{bias_label}</h3>
            <p class="text-sm text-slate-400 mb-4">{bias_desc}</p>
            <div class="text-[11px] mono text-slate-500 border-t border-white/[0.04] pt-3">
                <p>Pipeline: FALCON_MODEL_2026</p>
                <p>Status: ACTIVE_INFERENCE</p>
            </div>
        </div>

        <div class="glass rounded-3xl p-6 fadein fadein-delay-3">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">🔥 Trending Searches</p>
                    <p class="text-sm text-slate-500">Global macro search density</p>
                </div>
            </div>
            <div class="flex flex-wrap gap-2">{trending_html}</div>
        </div>

        <div class="glass rounded-3xl p-6 fadein fadein-delay-4 relative overflow-hidden">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">⏳ Node Timeline</p>
                    <p class="text-sm text-slate-500">Recent analysis snapshots</p>
                </div>
            </div>
            <div class="space-y-4 max-h-[380px] overflow-y-auto pr-2" style="scrollbar-width:thin;">
                {final_history}</div>
        </div>

    </aside>

</main>

<footer class="max-w-7xl mx-auto mt-24 pt-8 border-t border-white/[0.04] flex flex-col sm:flex-row justify-between items-center gap-4 text-xs mono text-slate-600 mb-12">
    <p>© 2026 AUTONOMOUS PORTFOLIO LAB. ALL RIGHTS RESERVED.</p>
    <div class="flex gap-6">
        <a href="privacy.html" class="hover:text-slate-400 transition">PRIVACY POLICY</a>
        <a href="https://t.me/AII2026futher" target="_blank" class="hover:text-slate-400 transition flex items-center gap-1">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-1-.65-.35-1 .22-1.62.15-.15 2.7-2.48 2.75-2.7.01-.03.01-.14-.07-.2-.08-.07-.19-.05-.27-.03-.12.02-1.96 1.24-5.54 3.65-.52.36-1 .53-1.42.52-.47-.01-1.37-.26-2.03-.48-.82-.27-1.47-.42-1.42-.88.03-.24.35-.49.97-.74 3.79-1.65 6.32-2.74 7.57-3.27 3.6-1.5 4.35-1.76 4.84-1.77.11 0 .35.03.51.16.13.11.17.26.19.37z"/></svg>TELEGRAM
        </a>
    </div>
</footer>

</div>

<script>
    function toggleDeepDive() {
        const d = document.getElementById('deepdive');
        const b = document.getElementById('deepbtn');
        const icon = document.getElementById('deep-icon');
        d.classList.toggle('active');
        if (d.classList.contains('active')) {
            b.querySelector('span').innerText = "Collapse View";
            icon.style.transform = "rotate(180deg)";
        } else {
            b.querySelector('span').innerText = "Read Analysis";
            icon.style.transform = "rotate(0deg)";
        }
    }

    // REAL-TIME AUTO-MONITORING PRICE REFRESHER
    async function fetchRealTimeMarket() {
        const pulse = document.getElementById('ticker-pulse');
        const status = document.getElementById('market-status');
        try {
            if (pulse) pulse.classList.add('scale-150');
            const res = await fetch("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true");
            if (!res.ok) throw new Error();
            const data = await res.json();
            
            const fmt = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 });
            const pct = new Intl.NumberFormat('en-US', { signDisplay: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 });

            if (data.bitcoin) {
                document.getElementById('live-btc-price').innerText = fmt.format(data.bitcoin.usd);
                const chg = data.bitcoin.usd_24h_change || 0;
                const el = document.getElementById('live-btc-change');
                el.innerText = pct.format(chg) + '%';
                el.className = `text-xs font-bold ${chg >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
            }
            if (data.ethereum) {
                document.getElementById('live-eth-price').innerText = fmt.format(data.ethereum.usd);
                const chg = data.ethereum.usd_24h_change || 0;
                const el = document.getElementById('live-eth-change');
                el.innerText = pct.format(chg) + '%';
                el.className = `text-xs font-bold ${chg >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
            }
            if (data.solana) {
                document.getElementById('live-sol-price').innerText = fmt.format(data.solana.usd);
                const chg = data.solana.usd_24h_change || 0;
                const el = document.getElementById('live-sol-change');
                el.innerText = pct.format(chg) + '%';
                el.className = `text-xs font-bold ${chg >= 0 ? 'text-emerald-400' : 'text-red-400'}`;
            }
            if (status) status.innerText = `Live // ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}`;
        } catch(e) {
            if (status) status.innerText = "Reconnecting feed...";
        } finally {
            setTimeout(() => { if (pulse) pulse.classList.remove('scale-150'); }, 400);
        }
    }

    // Initial triggers on execution
    fetchRealTimeMarket();
    setInterval(fetchRealTimeMarket, 30000);

    // Progressive counter animator
    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll('.count-number').forEach(el => {
            const tgt = parseInt(el.getAttribute('data-target')) || 0;
            let cur = 0;
            const steps = 20;
            const stepTime = 30;
            const increment = tgt / steps;
            const timer = setInterval(() => {
                cur += increment;
                if (cur >= tgt) {
                    el.innerText = tgt;
                    clearInterval(timer);
                } else {
                    el.innerText = Math.floor(cur);
                }
            }, stepTime);
        });
        setTimeout(() => {
            document.querySelectorAll('.score-fill').forEach(f => {
                f.style.width = f.getAttribute('data-width');
            });
        }, 100);
    });
</script>
</body>
</html>"""

# ─────────────────────────────────────────────
# MAIN EXECUTION INTERFACE
# ─────────────────────────────────────────────
def main():
    print("--- START SYSTEM CORE RE-RUN ---")
    t_key = os.getenv("TAVILY")
    g_key = os.getenv("GEMINI")
    if not g_key:
        print("Missing critical GEMINI environment variable.")
        return

    rss = get_rss_context()
    price_context, btc, eth, sol = get_price_context()
    trending_tokens = get_trending_tokens()
    sentiment_headlines, sentiment_mood, sentiment_score = get_coindesk_sentiment()

    research_context = get_research(rss, t_key)
    data = get_gemini_data(research_context, g_key, price_context, sentiment_mood, sentiment_score, trending_tokens)
    if not data:
        return

    # Dynamic History Tracking Layer
    history_html = ""
    if os.path.exists("index.html"):
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                old = f.read()
            if "" in old and "" in old:
                history_html = old.split("")[1].split("")[0]
        except Exception:
            pass

    date_str  = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_entry = (
        f"<div class='mb-3 pl-3 border-l border-white/10 opacity-50 text-[10px]'>\n"
        f"<p class='mono text-slate-500'>{date_str}</p>\n"
        f"<p class='font-bold text-slate-300 uppercase tracking-tight'>{data.get('title','Update')}</p>\n"
        f"<p class='text-slate-500'>⚠️ {data.get('threat_score','?')}/10 &nbsp;💡 {data.get('opportunity_score','?')}/10</p>\n"
        f"</div>\n"
    )
    final_history = (new_entry + history_html)[:4000]

    html = build_html(data, final_history, date_str, price_context, sentiment_mood, sentiment_score, trending_tokens, btc, eth, sol)
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html written successfully.")
    except Exception as e:
        print(f"Write failed: {e}")
        return

    post_to_devto(data)
    send_telegram(data.get('title'), data.get('threat'), data.get('opportunity'), data.get('threat_score'), data.get('opportunity_score'))
    write_seo_files()
    print("--- SYSTEM CYCLED CLEANLY ---")

if __name__ == "__main__":
    main()
