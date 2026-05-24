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
            r = requests.get(url, timeout=8) [cite: 1]
            titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', r.text, re.DOTALL) [cite: 1]
            # Take only 1 headline per feed to get variety
            clean = [t.strip() for t in titles[1:2] if t.strip()] [cite: 1]
            items.extend(clean) [cite: 1]
        except Exception as e:
            print(f"RSS failed {url}: {e}") [cite: 1]
    result = " | ".join(items[:6]) if items else "Crypto and Web3 market developments 2026" [cite: 1]
    print(f"RSS context: {result[:100]}...") [cite: 1]
    return result [cite: 2]

def get_price_context():
    """Free CoinGecko API — no API key needed""" [cite: 2]
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana,binancecoin", [cite: 2]
                "vs_currencies": "usd", [cite: 2]
                "include_24hr_change": "true" [cite: 2]
            },
            timeout=8 [cite: 2]
        )
        r.raise_for_status() [cite: 2]
        d = r.json() [cite: 2]
        btc = d.get('bitcoin', {}) [cite: 2]
        eth = d.get('ethereum', {}) [cite: 2]
        sol = d.get('solana', {}) [cite: 2]
        context = (
            f"BTC ${btc.get('usd',0):,} ({btc.get('usd_24h_change',0):+.1f}% 24h) | " [cite: 2]
            f"ETH ${eth.get('usd',0):,} ({eth.get('usd_24h_change',0):+.1f}% 24h) | " [cite: 3]
            f"SOL ${sol.get('usd',0):,} ({sol.get('usd_24h_change',0):+.1f}% 24h)" [cite: 3]
        )
        print(f"Prices: {context}") [cite: 3]
        return context, btc, eth, sol [cite: 3]
    except Exception as e:
        print(f"Price fetch failed: {e}") [cite: 3]
        return "", {}, {}, {} [cite: 3]

def get_trending_tokens():
    """CoinGecko trending — no API key needed""" [cite: 3]
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=8 [cite: 3]
        )
        r.raise_for_status() [cite: 3]
        coins = r.json().get('coins', []) [cite: 3]
        tokens = [c['item']['symbol'].upper() for c in coins[:5]] [cite: 3]
        print(f"Trending: {tokens}") [cite: 3]
        return tokens [cite: 3]
    except Exception as e:
        print(f"Trending fetch failed: {e}") [cite: 3]
        return [] [cite: 3]

def get_coindesk_sentiment():
    """Pull CoinDesk RSS and extract sentiment labels""" [cite: 3]
    try:
        r = requests.get(
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            timeout=8 [cite: 3]
        )
        text = r.text [cite: 3]
        titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', text, re.DOTALL) [cite: 3]
        titles = [t.strip() for t in titles[1:8] if t.strip()] [cite: 3, 4]
        # Count sentiment keywords
        negative_words = ['tank', 'crash', 'bleed', 'hack', 'breach', 'attack', 'fall', 'drop', 'loss', 'probe', 'ban', 'leave', 'slow'] [cite: 4]
        positive_words = ['surge', 'rally', 'rise', 'higher', 'buy', 'boom', 'growth', 'lead', 'win', 'boost', 'top'] [cite: 4]
        neg = sum(1 for t in titles for w in negative_words if w in t.lower()) [cite: 4]
        pos = sum(1 for t in titles for w in positive_words if w in t.lower()) [cite: 4]
        total = len(titles) [cite: 4]
        if neg > pos: [cite: 4]
            mood = "BEARISH" [cite: 4]
            mood_score = min(int((neg / total) * 10), 10) [cite: 4]
        else:
            mood = "BULLISH" [cite: 4]
            mood_score = min(int((pos / total) * 10), 10) [cite: 4]
        headlines = " | ".join(titles[:5]) [cite: 4, 5]
        print(f"CoinDesk sentiment: {mood} ({neg} neg / {pos} pos) — {headlines[:80]}") [cite: 5]
        return headlines, mood, mood_score [cite: 5]
    except Exception as e:
        print(f"CoinDesk sentiment failed: {e}") [cite: 5]
        return "", "NEUTRAL", 5 [cite: 5]

# ─────────────────────────────────────────────
# LAYER 2: Tavily — Deep research
# ─────────────────────────────────────────────
def get_research(rss_context, t_key):
    if not t_key: [cite: 5]
        print("No TAVILY key, using RSS context only.") [cite: 5]
        return rss_context [cite: 5]
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": t_key,
                "query": f"crypto web3 DeFi {rss_context[:150]} risk opportunity 2026", [cite: 5]
                "max_results": 3 [cite: 5]
            },
            timeout=10 [cite: 5]
        )
        r.raise_for_status() [cite: 5]
        results = r.json().get('results', []) [cite: 5]
        if results: [cite: 5]
            combined = " ".join([res.get('content', '') for res in results])[:2000] [cite: 5]
            print(f"Tavily loaded: {len(combined)} chars") [cite: 5]
            return combined [cite: 5]
    except Exception as e: [cite: 5, 6]
        print(f"Tavily failed: {e}") [cite: 6]
    return rss_context [cite: 6]

# ─────────────────────────────────────────────
# LAYER 3: Gemini — with model fallback chain
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}" [cite: 6]
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]}, [cite: 6]
        timeout=30 [cite: 6]
    )
    resp.raise_for_status() [cite: 6]
    return resp.json()['candidates'][0]['content']['parts'][0]['text'] [cite: 6]

def call_groq(prompt, key):
    """Groq fallback — 14,400 free requests/day""" [cite: 6]
    if not key: [cite: 6]
        raise ValueError("No GROQ key") [cite: 6]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"} [cite: 6]
    payload = {
        "model": "llama-3.3-70b-versatile", [cite: 6]
        "messages": [{"role": "user", "content": prompt}], [cite: 6]
        "max_tokens": 2000, [cite: 6]
        "temperature": 0.7 [cite: 6]
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload, headers=headers, timeout=30 [cite: 6]
    )
    resp.raise_for_status() [cite: 6]
    raw = resp.json()['choices'][0]['message']['content'] [cite: 6]
    # Remove control characters that break JSON parsing
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw) [cite: 6, 7]
    return raw [cite: 7]

def get_gemini_data(research_context, g_key, price_context="", sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None):
    trending_str = ", ".join(trending_tokens) if trending_tokens else "BTC, ETH, SOL" [cite: 7]
    prompt = f"""You are an expert crypto and Web3 analyst running a real-time intelligence dashboard. [cite: 7]
REAL MARKET DATA RIGHT NOW: [cite: 8]
- Prices: {price_context} [cite: 8]
- Market Sentiment from CoinDesk headlines: {sentiment_mood} (score: {sentiment_score}/10) [cite: 8]
- Trending tokens people are searching right now: {trending_str} [cite: 8]

NEWS RESEARCH:
{research_context} [cite: 8]

Use the REAL data above to calibrate your scores accurately. [cite: 8]
If sentiment is BEARISH, threat score should be higher. If prices are down 3%+, adjust accordingly. [cite: 9]
Return ONLY a valid JSON object. No markdown fences. No extra text: [cite: 10]
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
  "critic": "One sentence contrarian view why the opportunity might be wrong", [cite: 10]
  "color": "#hexcolor matching the mood" [cite: 11]
}}

IMPORTANT: For tokens_to_watch use the TRENDING tokens provided above — those are what people are actually searching right now.""" [cite: 11]

    # Updated fallback chain with working models only
    attempts = [
        ("gemini-2.5-flash", "gemini", g_key), [cite: 11]
        ("gemini-2.0-flash", "gemini", g_key), [cite: 11]
        ("groq-llama-3.3-70b", "groq", os.getenv("GROQ")), [cite: 11]
        ("gemini-2.0-flash-lite", "gemini", g_key), [cite: 11]
    ]

    for model_name, provider, key in attempts:
        try:
            print(f"Trying: {model_name}") [cite: 11]
            if provider == "groq": [cite: 11]
                raw = call_groq(prompt, key) [cite: 11]
            else:
                raw = call_gemini(prompt, key, model_name) [cite: 11]
            print(f"Response: {len(raw)} chars") [cite: 11]
            # Clean control characters before parsing
            raw_clean = re.sub(r'[\x00-\x1f\x7f]', ' ', raw) [cite: 11]
            match = re.search(r'\{.*\}', raw_clean, re.DOTALL) [cite: 11]
            if not match: [cite: 11, 12]
                raise ValueError("No JSON found") [cite: 12]
            data = json.loads(match.group(0)) [cite: 12]
            print(f"SUCCESS with {model_name}: {data.get('title','no title')}") [cite: 12]
            return data [cite: 12]
        except Exception as e: [cite: 12]
            print(f"{model_name} failed: {e}") [cite: 12]
            continue [cite: 12]

    print("ALL MODELS FAILED. Circuit breaker triggered.") [cite: 12, 13]
    return None [cite: 13]

# ─────────────────────────────────────────────
# NOTIFY: Telegram
# ─────────────────────────────────────────────
def send_telegram(title, threat, opportunity, threat_score, opp_score):
    token = os.getenv("TELEGRAM_BOT_TOKEN") [cite: 13]
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID") [cite: 13]
    if not token or not chat_id: [cite: 13]
        return [cite: 13]
    msg = (
        f"🧠 *AUTONOMOUS LAB UPDATE*\n\n" [cite: 13]
        f"*{title}*\n\n" [cite: 13]
        f"⚠️ Threat [{threat_score}/10]: {threat}\n\n" [cite: 13]
        f"💡 Opportunity [{opp_score}/10]: {opportunity}\n\n" [cite: 13]
        f"🔗 https://autonomous-portfolio-2026.live" [cite: 13]
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage", [cite: 13]
            data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, [cite: 13]
            timeout=10 [cite: 13]
        )
        print("Telegram sent.") [cite: 13]
    except Exception as e: [cite: 13]
        print(f"Telegram failed: {e}") [cite: 13]

# ─────────────────────────────────────────────
# PUBLISH: Dev.to
# ─────────────────────────────────────────────
def post_to_devto(data):
    key = os.getenv("DEV") [cite: 13]
    if not key: [cite: 13]
        print("No DEV key, skipping.") [cite: 13]
        return [cite: 13]
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])]) [cite: 13]
    tokens = ", ".join(data.get('tokens_to_watch', [])) [cite: 13, 14]
    body = (
        f"> 🔗 Live Dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n" [cite: 14]
        f"> 📢 Telegram Channel: [t.me/AII2026futher](https://t.me/AII2026futher)\n\n" [cite: 14]
        f"## Today's Headlines\n\n{bullets}\n\n" [cite: 14]
        f"## ⚠️ Threat Signal [{data.get('threat_score','?')}/10]\n\n{data.get('threat','')}\n\n" [cite: 14]
        f"## 💡 Opportunity Signal [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity','')}\n\n" [cite: 14]
        f"## 🪙 Tokens To Watch\n\n{tokens}\n\n" [cite: 14]
        f"## 📊 Deep Analysis\n\n{data.get('deep_analysis','')}\n\n" [cite: 14]
        f"---\n" [cite: 14]
        f"*AI-powered dashboard — Gemini + Groq + Tavily. Updated every 2 hours automatically.*\n\n" [cite: 14, 15]
        f"📢 Follow our Telegram for real-time alerts: https://t.me/AII2026futher" [cite: 15]
    )
    try:
        r = requests.post(
            "https://dev.to/api/articles", [cite: 15]
            json={"article": {
                "title": data.get('title', 'Crypto Intelligence Update'), [cite: 15]
                "body_markdown": body, [cite: 15]
                "tags": ["crypto", "web3", "defi", "security"], [cite: 15]
                "published": True [cite: 15]
            }},
            headers={"api-key": key}, [cite: 15]
            timeout=15 [cite: 15]
        )
        r.raise_for_status() [cite: 15]
        print(f"Dev.to published: {r.json().get('url','')}") [cite: 15]
    except Exception as e: [cite: 15]
        print(f"Dev.to failed: {e}") [cite: 15]

# ─────────────────────────────────────────────
# SEO files
# ─────────────────────────────────────────────
def write_seo_files():
    date_today = datetime.now().strftime("%Y-%m-%d") [cite: 15]
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
</urlset>""" [cite: 15]
    with open("sitemap.xml", "w") as f: [cite: 15]
        f.write(sitemap) [cite: 15]
    with open("robots.txt", "w") as f: [cite: 15]
        f.write("User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n") [cite: 15]
    print("SEO files updated.") [cite: 15, 16]

# ─────────────────────────────────────────────
# BUILD HTML
# ─────────────────────────────────────────────
def build_html(data, final_history, date_str, price_context="", sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None, btc=None, eth=None, sol=None):
    if btc is None: btc = {} [cite: 16]
    if eth is None: eth = {} [cite: 16]
    if sol is None: sol = {} [cite: 16]
    color        = data.get('color', '#dc2626') [cite: 16]
    threat       = data.get('threat_level', 'Unknown') [cite: 16]
    title        = data.get('title', 'Intelligence Report') [cite: 16]
    news_bullets = data.get('news_bullets', []) [cite: 16]
    threat_txt   = data.get('threat', '') [cite: 16]
    opp_txt      = data.get('opportunity', '') [cite: 16]
    threat_score = data.get('threat_score', 5) [cite: 16]
    opp_score    = data.get('opportunity_score', 5) [cite: 16]
    deep_raw     = data.get('deep_analysis', '') [cite: 16]
    tokens       = data.get('tokens_to_watch', []) [cite: 16]
    critic       = data.get('critic', '') [cite: 16]

    threat_colors = {"Critical":"#dc2626","High":"#f97316","Medium":"#eab308","Low":"#22c55e"} [cite: 16]
    threat_color  = threat_colors.get(threat, "#94a3b8") [cite: 16]
    threat_label  = {"Critical":"● CRITICAL THREAT","High":"● HIGH THREAT","Medium":"● MEDIUM THREAT","Low":"● LOW THREAT"}.get(threat, "● UNKNOWN") [cite: 16, 17]

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10 [cite: 17]
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10 [cite: 17]

    # Market bias logic
    if (int(str(threat_score)) if str(threat_score).isdigit() else 5) >= 7: [cite: 17]
        bias_label = "📉 BEARISH BIAS" [cite: 17]
        bias_desc  = "High threat — short-term selling pressure likely" [cite: 17]
        bias_color = "#ef4444" [cite: 17]
    elif (int(str(opp_score)) if str(opp_score).isdigit() else 5) >= 7: [cite: 17]
        bias_label = "📈 BULLISH BIAS" [cite: 17]
        bias_desc  = "Strong opportunity — mid-term buying interest" [cite: 17]
        bias_color = "#22c55e" [cite: 17]
    else:
        bias_label = "⚖️ MIXED SIGNALS" [cite: 17]
        bias_desc  = "Wait for clarity before acting" [cite: 17]
        bias_color = "#eab308" [cite: 17]

    # Build bullets HTML
    bullets_html = "" [cite: 17, 18]
    for i, b in enumerate(news_bullets, 1): [cite: 18]
        bullets_html += f"""
            <div class="flex gap-5 items-start group/item p-4 rounded-2xl hover:bg-white/[0.02] transition duration-300">
                <span class="mt-1 flex-shrink-0 w-8 h-8 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 text-sm font-bold">{i}</span>
                <p class="text-lg text-slate-300 leading-relaxed group-hover/item:text-slate-200 transition">{b}</p>
            </div>""" [cite: 18]

    # Tokens HTML
    tokens_html = "" [cite: 18]
    for i, t in enumerate(tokens): [cite: 18]
        if t.strip(): [cite: 18]
            delay = i * 0.3 [cite: 18]
            tokens_html += f'<span class="tag bg-red-500/5 text-red-400 border border-red-500/20 hover:bg-red-500/10 hover:border-red-500/40 text-base"><span class="w-2 h-2 rounded-full bg-red-400 blink" style="animation-delay:{delay}s"></span>{t.strip()}</span>\n' [cite: 18]

    # Deep analysis paragraphs
    deep_paras = [p.strip() for p in deep_raw.split('\n') if p.strip()] [cite: 18]
    deep_html = "" [cite: 18]
    para_titles = ["Root Cause Analysis", "Supply Chain Impact", "Mid-Term Outlook"] [cite: 18, 19]
    for i, para in enumerate(deep_paras[:3]): [cite: 19]
        ptitle = para_titles[i] if i < len(para_titles) else f"Analysis {i+1}" [cite: 19]
        deep_html += f"""
            <div class="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
                <h4 class="text-lg font-bold text-white mb-3 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-red-500"></span>{ptitle}
                </h4>
                <p>{para}</p>
            </div>""" [cite: 19]

    # Trending tokens sidebar
    trending_html = "" [cite: 19]
    if trending_tokens: [cite: 19]
        for t in trending_tokens[:5]: [cite: 19]
            trending_html += f'<span class="text-[11px] mono px-3 py-1 rounded-full bg-white/5 text-slate-400 border border-white/10">{t}</span>\n' [cite: 19]

    # Price rows
    btc_change = btc.get('usd_24h_change', 0) or 0 [cite: 19]
    eth_change = eth.get('usd_24h_change', 0) or 0 [cite: 19]
    sol_change = sol.get('usd_24h_change', 0) or 0 [cite: 19]
    btc_color = "#22c55e" if btc_change >= 0 else "#ef4444" [cite: 19]
    eth_color = "#22c55e" if eth_change >= 0 else "#ef4444" [cite: 19, 20]
    sol_color = "#22c55e" if sol_change >= 0 else "#ef4444" [cite: 20]
    btc_price = f"${btc.get('usd',0):,}" if btc.get('usd') else "—" [cite: 20]
    eth_price = f"${eth.get('usd',0):,}" if eth.get('usd') else "—" [cite: 20]
    sol_price = f"${sol.get('usd',0):,}" if sol.get('usd') else "—" [cite: 20]

    # Sentiment bar
    sent_color = "#22c55e" if sentiment_mood == "BULLISH" else "#ef4444" [cite: 20]
    sent_width = sentiment_score * 10 [cite: 20]

    # STRUCTURAL STYLE AND JS BLOCK BRACES ARE DOUBLED BELOW TO ESCAPE PYTHON F-STRING EVALUATION
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lab 2026 — {title}</title>
    <meta name="description" content="Real-time crypto and Web3 intelligence. Threat score, opportunity signals, tokens to watch — updated every 2 hours by AI."> [cite: 20, 21]
    <meta name="keywords" content="crypto intelligence, web3 security, DeFi signals, AI research dashboard, blockchain 2026"> [cite: 21]
    <meta name="robots" content="index, follow"> [cite: 21]
    <meta property="og:title" content="{title} — Autonomous Lab 2026"> [cite: 21]
    <meta property="og:description" content="Threat: {threat_score}/10 | Opportunity: {opp_score}/10 — Live crypto intelligence"> [cite: 21, 22]
    <meta property="og:url" content="https://autonomous-portfolio-2026.live"> [cite: 22]
    <meta property="og:type" content="website"> [cite: 22]
    <meta name="twitter:card" content="summary"> [cite: 22]
    <meta name="twitter:title" content="{title} — Autonomous Lab 2026"> [cite: 22]
    <meta name="twitter:description" content="Threat {threat_score}/10 | Opp {opp_score}/10 — {threat_txt[:80]}"> [cite: 22, 23]
    <link rel="canonical" href="https://autonomous-portfolio-2026.live/"> [cite: 23]
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527" crossorigin="anonymous"></script> [cite: 23]
    <script src="https://cdn.tailwindcss.com"></script> [cite: 23]
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet"> [cite: 23]
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
        .fadein-delay-4{{animation-delay:0.6s;opacity:0}} [cite: 23]
        @keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}} [cite: 23]
        .shimmer{{background:linear-gradient(90deg,transparent,rgba(255,255,255,0.03),transparent);background-size:200% 100%;animation:shimmer 8s infinite}} [cite: 23]
        @keyframes countUp{{from{{opacity:0;transform:translateY(20px) scale(0.8)}}to{{opacity:1;transform:translateY(0) scale(1)}}}} [cite: 23]
        .count-number{{animation:countUp 0.8s cubic-bezier(0.34,1.56,0.64,1) forwards}} [cite: 23]
        ::-webkit-scrollbar{{width:6px}} [cite: 23]
        ::-webkit-scrollbar-track{{background:transparent}} [cite: 23]
        ::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.1);border-radius:99px}} [cite: 23]
        .tag{{display:inline-flex;align-items:center;gap:8px;padding:8px 20px;border-radius:99px;font-size:0.875rem;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:0.05em;transition:all 0.3s ease;cursor:default}} [cite: 23]
        .tag:hover{{transform:scale(1.05)}} [cite: 23]
        .btn-primary{{position:relative;overflow:hidden;transition:all 0.3s ease}} [cite: 23]
        .btn-primary::before{{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent);transition:left 0.5s ease}} [cite: 23]
        .btn-primary:hover::before{{left:100%}} [cite: 23]
        #deepdive{{max-height:0;overflow:hidden;opacity:0;transition:max-height 0.6s cubic-bezier(0.4,0,0.2,1),opacity 0.5s ease,padding 0.5s ease}} [cite: 24]
        #deepdive.active{{max-height:1200px;opacity:1}} [cite: 24]
        .bg-grid{{background-image:linear-gradient(rgba(255,255,255,0.015) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.015) 1px,transparent 1px);background-size:80px 80px}} [cite: 24]
        .status-dot{{width:10px;height:10px;border-radius:50%;display:inline-block}} [cite: 24]
        .archive-item{{transition:all 0.3s ease;border-left:3px solid transparent}} [cite: 24]
        .archive-item:hover{{background:rgba(255,255,255,0.02);border-left-color:rgba(220,38,38,0.6);padding-left:20px}} [cite: 24]
        .gradient-text{{background:linear-gradient(135deg,#fff 0%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}} [cite: 24]
        .big-number{{font-size:clamp(3rem,8vw,5rem);font-weight:800;line-height:1;letter-spacing:-0.04em}} [cite: 24]
        .section-label{{font-size:0.75rem;font-family:'JetBrains Mono',monospace;font-weight:700;text-transform:uppercase;letter-spacing:0.15em;color:#94a3b8}} [cite: 24]
        .card-header{{display:flex;align-items:center;gap:12px;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.04)}} [cite: 24]
        .highlight-box{{background:rgba(220,38,38,0.04);border:1px solid rgba(220,38,38,0.12);border-radius:16px;padding:24px}} [cite: 24]
    </style>
    <script>
        function toggleDeepDive() {{
            const box = document.getElementById('deepdive');
            const icon = document.getElementById('deep-icon');
            box.classList.toggle('active');
            if(box.classList.contains('active')) {{
                icon.style.transform = 'rotate(180deg)';
            }} else {{
                icon.style.transform = 'rotate(0deg)';
            }}
        }}
        
        document.addEventListener("DOMContentLoaded", () => {{
            setTimeout(() => {{
                document.querySelectorAll('.score-fill').forEach(el => {{
                    el.style.width = el.getAttribute('data-width');
                }});
                document.querySelectorAll('.count-number').forEach(el => {{
                    const target = parseInt(el.getAttribute('data-target')) || 0;
                    let current = 0;
                    const duration = 1000;
                    const stepTime = Math.max(Math.floor(duration / (target || 1)), 20);
                    const timer = setInterval(() => {{
                        current += 1;
                        if(current >= target) {{
                            el.innerText = target;
                            clearInterval(timer);
                        }} else {{
                            el.innerText = current;
                        }}
                    }}, stepTime);
                }});
            }}, 300);
        }});
    </script>
</head>
<body class="min-h-screen bg-grid">

<div class="w-full border-b border-white/[0.04] bg-[#06070f]/90 backdrop-blur-xl sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 md:px-8 py-4 flex justify-between items-center">
        <div class="flex items-center gap-4">
            <span class="status-dot blink bg-red-500"></span>
            <span class="text-xs mono font-semibold text-slate-400 uppercase tracking-widest" id="terminal-live-status">AI Agent Pipeline Online // Monitoring Nodes...</span> [cite: 24, 25]
        </div>
        <div class="flex items-center gap-6 text-xs mono text-slate-500">
            <span class="hidden sm:inline">Last Synced: {date_str}</span> [cite: 25]
            <span class="px-3 py-1.5 rounded-lg font-bold tracking-wider" style="background:{threat_color}18;color:{threat_color};border:1px solid {threat_color}33">{threat_label}</span> [cite: 25]
        </div>
    </div>
</div>

<div class="p-4 md:p-8 lg:p-12">

<header class="max-w-7xl mx-auto mb-16 fadein">
    <div class="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-8 pb-10 border-b border-white/[0.06]"> [cite: 25]
        <div class="space-y-4">
            <div class="flex items-center gap-4 mb-3">
                <div class="h-px w-16 bg-gradient-to-r from-red-500 to-transparent"></div>
                <span class="text-xs mono font-bold text-red-400 uppercase tracking-[0.3em]">Intelligence Dashboard</span> [cite: 25]
            </div>
            <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[0.9]"> [cite: 25]
                <span class="gradient-text">AUTONOMOUS</span><br> [cite: 25]
                <span class="text-red-600">LAB<span class="text-slate-600 font-light">.2026</span></span> [cite: 25]
            </h1>
            <p class="text-base text-slate-500 max-w-xl leading-relaxed mt-4">Real-time autonomous intelligence pipeline monitoring crypto security threats, Web3 vulnerabilities, and market signals.</p> [cite: 25]
        </div>
        <div class="flex items-center gap-4 bg-white/[0.02] border border-white/[0.06] rounded-2xl px-6 py-4"> [cite: 25]
            <span class="w-3 h-3 rounded-full bg-emerald-500 blink" style="animation-duration:3s"></span> [cite: 25, 26]
            <div>
                <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-1">System Status</p> [cite: 26]
                <p class="text-sm font-bold text-emerald-400 uppercase tracking-wide">Operational</p> [cite: 26]
            </div>
        </div>
    </div>
</header>

<main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8"> [cite: 26]

    <div class="lg:col-span-8 space-y-8"> [cite: 26]

        <section class="glass rounded-3xl p-8 md:p-12 relative overflow-hidden fadein fadein-delay-1 group"> [cite: 26]
            <div class="absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 transition duration-700" style="background:{color}0d"></div> [cite: 26]
            <div class="relative z-10">
                <div class="flex items-center gap-4 mb-8"> [cite: 26]
                    <span class="px-4 py-2 rounded-xl text-xs mono font-bold uppercase tracking-widest" style="background:{threat_color}18;border:1px solid {threat_color}33;color:{threat_color}">● {threat} Alert</span> [cite: 26]
                    <span class="text-xs mono text-slate-500 uppercase tracking-widest">Today's Intelligence Brief</span> [cite: 26]
                </div>
                <h2 class="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white mb-8 leading-[1.05]">{title}</h2> [cite: 26, 27]
                <div class="space-y-2">{bullets_html}</div> [cite: 27]
            </div>
        </section>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 fadein fadein-delay-2"> [cite: 27]
            <div class="glass rounded-3xl p-8 relative overflow-hidden group glass-hover transition-all duration-300"> [cite: 27]
                <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-red-700 via-red-500 to-red-400"></div> [cite: 27]
                <div class="card-header" style="border-color:rgba(239,68,68,0.1)"> [cite: 27]
                    <div>
                        <p class="section-label text-red-400 mb-1">Threat Signal</p> [cite: 27]
                        <p class="text-sm text-slate-500">Systemic Risk Assessment</p> [cite: 27]
                    </div>
                </div>
                <div class="flex items-baseline gap-2 mb-2"> [cite: 27]
                    <span class="big-number text-red-400 count-number" data-target="{threat_score}">0</span> [cite: 27]
                    <span class="text-2xl text-slate-600 font-light">/10</span> [cite: 27]
                </div>
                <div class="score-bar mb-6 relative"><div class="score-fill bg-gradient-to-r from-red-700 via-red-500 to-red-400" style="width:0%" data-width="{t_bar}%"></div></div> [cite: 27]
                <p class="text-base text-slate-400 leading-relaxed">{threat_txt}</p> [cite: 27]
            </div>

            <div class="glass rounded-3xl p-8 relative overflow-hidden group glass-hover transition-all duration-300"> [cite: 27]
                <div class="absolute top-0 left-0 w-full h-1.5" style="background:linear-gradient(to right,{color}99,{color})"></div> [cite: 27, 28]
                <div class="card-header" style="border-color:{color}1a"> [cite: 28]
                    <div>
                        <p class="section-label mb-1" style="color:{color}">Opportunity Signal</p> [cite: 28]
                        <p class="text-sm text-slate-500">Market Positioning</p> [cite: 28]
                    </div>
                </div>
                <div class="flex items-baseline gap-2 mb-2"> [cite: 28]
                    <span class="big-number count-number" style="color:{color}" data-target="{opp_score}">0</span> [cite: 28]
                    <span class="text-2xl text-slate-600 font-light">/10</span> [cite: 28]
                </div>
                <div class="score-bar mb-6 relative"><div class="score-fill" style="width:0%;background:linear-gradient(to right,{color}99,{color})" data-width="{o_bar}%"></div></div> [cite: 28]
                <p class="text-base text-slate-400 leading-relaxed">{opp_txt}</p> [cite: 28]
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 fadein fadein-delay-3"> [cite: 28]
            <div class="card-header"> [cite: 28]
                <div>
                    <p class="section-label mb-1">🪙 Tokens To Watch</p> [cite: 28]
                    <p class="text-sm text-slate-500">AI-identified positioning opportunities</p> [cite: 28]
                </div>
                <span class="text-xs mono text-slate-600 uppercase tracking-widest px-3 py-1 rounded-lg bg-white/[0.02] border border-white/[0.04]">Research Only</span> [cite: 28]
            </div>
            <div class="flex flex-wrap gap-4 mb-6">{tokens_html}</div> [cite: 28]
            <div class="highlight-box"> [cite: 28]
                <p class="text-sm text-slate-500 leading-relaxed"><span class="text-red-400 font-bold">Note:</span> AI pattern recognition based on current threat landscape. Not financial advice.</p> [cite: 28, 29]
            </div>
        </div>

        <div class="glass rounded-3xl overflow-hidden fadein fadein-delay-3"> [cite: 29]
            <div class="p-8 md:p-10"> [cite: 29]
                <div class="flex justify-between items-center"> [cite: 29]
                    <div>
                        <p class="section-label mb-1">📊 Deep Analysis</p> [cite: 29]
                        <p class="text-sm text-slate-500">Expanded technical breakdown</p> [cite: 29]
                    </div>
                    <button id="deepbtn" onclick="toggleDeepDive()" class="btn-primary text-sm mono font-bold uppercase tracking-widest px-6 py-3 rounded-2xl border border-white/10 hover:border-white/30 transition bg-white/[0.02] hover:bg-white/[0.05] text-slate-300 flex items-center gap-2"> [cite: 29]
                        <span>Read Analysis</span> [cite: 29]
                        <svg class="w-4 h-4 transition-transform" id="deep-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg> [cite: 29]
                    </button>
                </div>
            </div>
            <div id="deepdive" class="px-8 md:px-10 pb-10 text-base text-slate-400 leading-relaxed border-t border-white/[0.04]"> [cite: 29]
                <div class="pt-8 space-y-5">{deep_html}</div> [cite: 29]
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 border-l-4 border-yellow-500/30 relative overflow-hidden fadein fadein-delay-3"> [cite: 30]
            <div class="absolute -right-8 -top-8 w-40 h-40 bg-yellow-500/5 rounded-full blur-3xl"></div> [cite: 30]
            <div class="relative z-10"> [cite: 30]
                <div class="flex items-center gap-3 mb-6"> [cite: 30]
                    <span class="text-2xl">🤔</span> [cite: 30]
                    <p class="section-label text-yellow-500">Contrarian View</p> [cite: 30]
                </div>
                <blockquote class="text-2xl md:text-3xl text-slate-200 font-light italic leading-relaxed border-l-4 border-yellow-500/20 pl-6">"{critic}"</blockquote> [cite: 30]
                <div class="mt-6 flex items-center gap-3 pt-6 border-t border-white/[0.04]"> [cite: 30]
                    <div class="w-10 h-10 rounded-full bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center"><span class="text-yellow-500 text-lg">🧠</span></div> [cite: 30]
                    <div>
                        <p class="text-sm font-bold text-slate-300">AI Critic Model</p> [cite: 30]
                        <p class="text-xs mono text-slate-500 uppercase tracking-widest">Groq / Llama 3.3 70b</p> [cite: 30]
                    </div>
                </div>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 md:p-10 flex flex-wrap items-center justify-between gap-6 fadein fadein-delay-4"> [cite: 30, 31]
            <div>
                <p class="section-label mb-1">📢 Share This Report</p> [cite: 31]
                <p class="text-base text-slate-500">Found this useful? Share it with your network.</p> [cite: 31, 32]
            </div>
            <a href="https://twitter.com/intent/tweet?text={title}%20%E2%80%94%20Threat%3A%20{threat_score}%2F10%20%7C%20Opportunity%3A%20{opp_score}%2F10%0A%0Ahttps%3A%2F%2Fautonomous-portfolio-2026.live%20%23crypto%20%23web3%20%23AI" target="_blank" class="btn-primary flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-sm uppercase tracking-widest transition text-white shadow-xl" style="background:#1d9bf0;box-shadow:0 8px 24px rgba(29,155,240,0.2)"> [cite: 32]
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 7.485 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.035L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                <span>Share on X</span>
            </a>
        </div>
    </div>

    <div class="lg:col-span-4 space-y-8">
        <div class="glass rounded-3xl p-8 fadein fadein-delay-2 border-t-4" style="border-top-color:{bias_color}">
            <p class="section-label mb-2">💡 Market Bias Matrix</p>
            <h3 class="text-2xl font-bold tracking-tight mb-1" style="color:{bias_color}">{bias_label}</h3>
            <p class="text-sm text-slate-400 mb-6 leading-relaxed">{bias_desc}</p>
            <div class="space-y-4 pt-4 border-t border-white/[0.04]">
                <div>
                    <div class="flex justify-between text-xs mono mb-1">
                        <span class="text-slate-500">Threat Indicator</span>
                        <span class="text-red-400">{threat_score}/10</span>
                    </div>
                    <div class="score-bar"><div class="score-fill bg-red-500" style="width:0%" data-width="{threat_score * 10}%"></div></div>
                </div>
                <div>
                    <div class="flex justify-between text-xs mono mb-1">
                        <span class="text-slate-500">Opportunity Indicator</span>
                        <span class="text-emerald-400">{opp_score}/10</span>
                    </div>
                    <div class="score-bar"><div class="score-fill bg-emerald-500" style="width:0%" data-width="{opp_score * 10}%"></div></div>
                </div>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 fadein fadein-delay-2">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">📈 Live Feeds</p>
                    <p class="text-sm text-slate-500">CoinGecko Indexation</p>
                </div>
                <span class="w-2 h-2 rounded-full bg-emerald-400 blink"></span>
            </div>
            <div class="space-y-4">
                <div class="flex items-center justify-between p-3 rounded-2xl bg-white/[0.01] border border-white/[0.02]">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-xl bg-[#f7931a]/10 border border-[#f7931a]/20 flex items-center justify-center font-bold text-xs text-[#f7931a]">₿</div>
                        <div>
                            <p class="text-sm font-bold text-white">BTC</p>
                            <p class="text-[10px] mono text-slate-500">Bitcoin</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold text-white mono">{btc_price}</p>
                        <p class="text-xs mono" style="color:{btc_color}">{btc_change:+.2f}%</p>
                    </div>
                </div>
                <div class="flex items-center justify-between p-3 rounded-2xl bg-white/[0.01] border border-white/[0.02]">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-xl bg-[#627eea]/10 border border-[#627eea]/20 flex items-center justify-center font-bold text-xs text-[#627eea]">Ξ</div>
                        <div>
                            <p class="text-sm font-bold text-white">ETH</p>
                            <p class="text-[10px] mono text-slate-500">Ethereum</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold text-white mono">{eth_price}</p>
                        <p class="text-xs mono" style="color:{eth_color}">{eth_change:+.2f}%</p>
                    </div>
                </div>
                <div class="flex items-center justify-between p-3 rounded-2xl bg-white/[0.01] border border-white/[0.02]">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-xl bg-[#14f195]/10 border border-[#14f195]/20 flex items-center justify-center font-bold text-xs text-[#14f195]">◎</div>
                        <div>
                            <p class="text-sm font-bold text-white">SOL</p>
                            <p class="text-[10px] mono text-slate-500">Solana</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-bold text-white mono">{sol_price}</p>
                        <p class="text-xs mono" style="color:{sol_color}">{sol_change:+.2f}%</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass rounded-3xl p-8 fadein fadein-delay-3">
            <p class="section-label mb-2">🎭 Mood Engine</p>
            <h3 class="text-xl font-bold text-white mb-4">CoinDesk Analytics</h3>
            <div class="p-4 rounded-2xl bg-white/[0.01] border border-white/[0.02] mb-4">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-xs mono text-slate-400">Calculated Mood</span>
                    <span class="text-sm font-bold px-2 py-0.5 rounded text-xs mono" style="background:{sent_color}15;color:{sent_color}">{sentiment_mood}</span>
                </div>
                <div class="score-bar"><div class="score-fill" style="width:0%;background:{sent_color}" data-width="{sent_width}%"></div></div>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">Aggregated threat keyword indexing from active real-time updates.</p>
        </div>

        <div class="glass rounded-3xl p-8 fadein fadein-delay-3">
            <p class="section-label mb-4">🔥 Global Trending Search</p>
            <div class="flex flex-wrap gap-2">{trending_html}</div>
        </div>

        <div class="glass rounded-3xl p-8 fadein fadein-delay-4 max-h-[400px] flex flex-col">
            <div class="card-header">
                <div>
                    <p class="section-label mb-1">🕒 Terminal History</p>
                    <p class="text-sm text-slate-500">Pipeline execution state</p>
                </div>
            </div>
            <div class="space-y-3 overflow-y-auto pr-2 flex-1 text-slate-400">
                {final_history}</div>
        </div>
    </div>
</main>

<footer class="max-w-7xl mx-auto mt-24 pt-8 border-t border-white/[0.04] flex flex-col md:flex-row justify-between items-center gap-4 text-xs mono text-slate-500 pb-12">
    <p>© 2026 Autonomous Intelligence Lab. All pipeline tasks running independently.</p>
    <div class="flex gap-6">
        <a href="privacy.html" class="hover:text-slate-300 transition">Privacy Policy</a>
        <a href="https://t.me/AII2026futher" target="_blank" class="text-red-400 font-bold hover:underline">📢 Telegram alerts</a>
    </div>
</footer>

</div>
</body>
</html>"""
