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
REAL market data right now:
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
