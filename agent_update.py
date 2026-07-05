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
    """Fetch news from multiple RSS feeds"""
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
            clean = [t.strip() for t in titles[1:2] if t.strip()]
            items.extend(clean)
        except Exception as e:
            print(f"✗ RSS failed {url}: {e}")
    result = " | ".join(items[:6]) if items else "Crypto and Web3 market developments 2026"
    print(f"✓ RSS context: {result[:80]}...")
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
        print(f"✓ Prices: {context}")
        return context, btc, eth, sol
    except Exception as e:
        print(f"✗ Price fetch failed: {e}")
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
        print(f"✓ Trending: {tokens}")
        return tokens
    except Exception as e:
        print(f"✗ Trending fetch failed: {e}")
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
        
        negative_words = ['tank', 'crash', 'bleed', 'hack', 'breach', 'attack', 'fall', 'drop', 'loss', 'probe', 'ban', 'leave', 'slow']
        positive_words = ['surge', 'rally', 'rise', 'higher', 'buy', 'boom', 'growth', 'lead', 'win', 'boost', 'top']
        
        neg = sum(1 for t in titles for w in negative_words if w in t.lower())
        pos = sum(1 for t in titles for w in positive_words if w in t.lower())
        total = len(titles) if titles else 1
        
        if neg > pos:
            mood = "BEARISH"
            mood_score = min(int((neg / total) * 10), 10)
        else:
            mood = "BULLISH"
            mood_score = min(int((pos / total) * 10), 10)
        
        headlines = " | ".join(titles[:5])
        print(f"✓ CoinDesk sentiment: {mood} ({neg} neg / {pos} pos)")
        return headlines, mood, mood_score
    except Exception as e:
        print(f"✗ CoinDesk sentiment failed: {e}")
        return "", "NEUTRAL", 5

# ─────────────────────────────────────────────
# LAYER 1B: POSITIVE NEWS DISCOVERY
# ─────────────────────────────────────────────
def get_positive_crypto_news():
    """Auto-discover positive news from free APIs - NO AUTH NEEDED"""
    positive_sources = []
    
    # 1️⃣ CRYPTOCOMPARE (Free, no key)
    try:
        r = requests.get(
            "https://min-api.cryptocompare.com/data/v1/news/?lang=EN",
            timeout=8
        )
        articles = r.json().get('Data', [])[:10]
        for article in articles:
            title = article.get('title', '')
            if any(word in title.lower() for word in 
                   ['rally', 'surge', 'adoption', 'partner', 'launch', 'upgrade', 'approval', 'growth']):
                positive_sources.append({
                    'source': 'CryptoCompare',
                    'title': title,
                    'sentiment': 'positive'
                })
        print(f"✓ CryptoCompare: {len([x for x in positive_sources if x['source']=='CryptoCompare'])} positive news")
    except Exception as e:
        print(f"✗ CryptoCompare failed: {e}")
    
    # 2️⃣ HACKER NEWS CRYPTO (Free)
    try:
        r = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=8
        )
        top_ids = r.json()[:15]
        for id in top_ids:
            try:
                sr = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json", timeout=5)
                item = sr.json()
                if item.get('title') and any(word in item.get('title','').lower() for word in 
                    ['crypto', 'bitcoin', 'ethereum', 'blockchain', 'web3', 'defi', 'adoption']):
                    positive_sources.append({
                        'source': 'HackerNews',
                        'title': item['title'],
                        'sentiment': 'neutral'
                    })
            except:
                pass
        print(f"✓ HackerNews: Found {len([x for x in positive_sources if x['source']=='HackerNews'])} relevant articles")
    except Exception as e:
        print(f"✗ HackerNews failed: {e}")
    
    # 3️⃣ GITHUB TRENDING (Free, no auth)
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": "crypto web3 defi stars:>100",
                "sort": "stars",
                "order": "desc",
                "per_page": 5
            },
            timeout=8
        )
        repos = r.json().get('items', [])
        for repo in repos:
            positive_sources.append({
                'source': 'GitHub',
                'title': f"{repo['name']}: New crypto project gaining stars",
                'sentiment': 'positive',
                'url': repo['html_url']
            })
        print(f"✓ GitHub Trending: {len([x for x in positive_sources if x['source']=='GitHub'])} trending repos")
    except Exception as e:
        print(f"✗ GitHub trending failed: {e}")
    
    # 4️⃣ COINGECKO MARKET CAP GAINERS (Free)
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_change_24h_desc",
                "per_page": 5,
                "sparkline": False
            },
            timeout=8
        )
        gainers = r.json()
        for coin in gainers[:3]:
            if coin.get('market_cap_change_percentage_24h', 0) > 5:
                positive_sources.append({
                    'source': 'CoinGecko',
                    'title': f"{coin.get('name')} up {coin.get('market_cap_change_percentage_24h', 0):.1f}% (Market strength)",
                    'sentiment': 'positive'
                })
        print(f"✓ CoinGecko Gainers: {len([x for x in positive_sources if x['source']=='CoinGecko'])} found")
    except Exception as e:
        print(f"✗ CoinGecko gainers failed: {e}")
    
    return positive_sources

def extract_good_news_for_gemini(positive_news):
    """Format positive news into readable text for Gemini"""
    if not positive_news:
        return "No major positive developments detected today."
    
    good_news_text = "✅ POSITIVE DEVELOPMENTS TODAY:\n"
    for i, news in enumerate(positive_news[:6], 1):
        source = news.get('source', 'Unknown')
        title = news.get('title', 'Update')
        good_news_text += f"{i}. [{source}] {title}\n"
    
    return good_news_text

# ─────────────────────────────────────────────
# LAYER 2: Tavily — Deep research
# ─────────────────────────────────────────────
def get_research(rss_context, t_key):
    """Tavily search for deep research (optional)"""
    if not t_key:
        print("ℹ No TAVILY key, using RSS context only.")
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
            print(f"✓ Tavily loaded: {len(combined)} chars")
            return combined
    except Exception as e:
        print(f"✗ Tavily failed: {e}")
    return rss_context

# ─────────────────────────────────────────────
# LAYER 3: Gemini — with model fallback chain
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    """Call Gemini API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_groq(prompt, key, model="llama-3.3-70b-versatile"):
    """Groq fallback — 14,400 free requests/day"""
    if not key:
        raise ValueError("No GROQ key")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a JSON API. Output ONLY valid JSON. No markdown, no backticks, no explanation. Just the raw JSON object."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        json=payload, headers=headers, timeout=30
    )
    resp.raise_for_status()
    raw = resp.json()['choices'][0]['message']['content']
    raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
    raw = raw.replace('```json','').replace('```','').strip()
    return raw

def get_gemini_data_balanced(research_context, g_key, price_context="", sentiment_mood="NEUTRAL", 
                             sentiment_score=5, trending_tokens=None, positive_news=""):
    """ENHANCED: Include BOTH negative research AND positive news for balanced perspective"""
    trending_str = ", ".join(trending_tokens) if trending_tokens else "BTC, ETH, SOL"
    
    prompt = f"""You are a balanced crypto and Web3 analyst. Generate BOTH threats AND opportunities.

REAL MARKET DATA:
- Prices: {price_context}
- Market Sentiment: {sentiment_mood} ({sentiment_score}/10)
- Trending tokens: {trending_str}

⚠️ THREATS & RESEARCH:
{research_context[:2000]}

✅ POSITIVE DEVELOPMENTS:
{positive_news}

YOUR TASK:
Create a BALANCED intelligence report. Consider both risks AND opportunities.
If good news exists (partnerships, upgrades, adoption), highlight it EQUALLY to threats.
Be data-driven and realistic.

Return ONLY this JSON (no markdown, no backticks):
{{
  "title": "Balanced headline covering both risks and opportunities",
  "news_bullets": [
    "First news point with data",
    "Positive development or opportunity",
    "Risk or challenge to watch"
  ],
  "threat": "Main systemic risk (specific, data-driven)",
  "opportunity": "Main opportunity (specific, data-driven)",
  "threat_score": 5,
  "opportunity_score": 6,
  "threat_level": "Medium",
  "deep_analysis": "Paragraph 1: Root cause\\nParagraph 2: Market impact\\nParagraph 3: 48-hour outlook",
  "analyst_note": "Executive summary from senior analyst perspective",
  "tokens_to_watch": ["TOKEN1", "TOKEN2", "TOKEN3"],
  "critic": "Contrarian view why opportunity might be wrong",
  "color": "#hexcolor"
}}"""

    groq_key = os.getenv("GROQ")

    # 7-model fallback chain
    attempts = [
        ("gemini-2.5-flash",      "gemini", g_key,    None),
        ("gemini-2.0-flash",      "gemini", g_key,    None),
        ("groq-llama-3.3-70b",    "groq",   groq_key, "llama-3.3-70b-versatile"),
        ("groq-llama-3.1-8b",     "groq",   groq_key, "llama-3.1-8b-instant"),
        ("gemini-2.0-flash-lite", "gemini", g_key,    None),
        ("groq-gemma2-9b",        "groq",   groq_key, "gemma2-9b-it"),
        ("gemini-1.5-flash-8b",   "gemini", g_key,    None),
    ]

    for model_name, provider, key, groq_model in attempts:
        try:
            print(f"→ Trying: {model_name}")
            if provider == "groq":
                raw = call_groq(prompt, key, groq_model)
            else:
                raw = call_gemini(prompt, key, model_name)
            
            print(f"  Response: {len(raw)} chars")
            raw_clean = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
            raw_clean = raw_clean.replace('```json','').replace('```','').strip()
            match = re.search(r'\{.*\}', raw_clean, re.DOTALL)
            
            if not match:
                raise ValueError("No JSON found")
            
            data = json.loads(match.group(0))
            
            if not data.get('title') or not data.get('news_bullets'):
                raise ValueError("Missing required fields")
            
            print(f"✓ SUCCESS with {model_name}: {data.get('title','')[:50]}")
            return data
        except Exception as e:
            print(f"✗ {model_name} failed: {str(e)[:80]}")
            continue

    print("✗ ALL MODELS FAILED. Using fallback data.")
    return None

# ─────────────────────────────────────────────
# EXTRACT: Preserve static sections from old HTML
# ─────────────────────────────────────────────
def extract_preserved_sections(old_html):
    """Extract and preserve static sections from old HTML"""
    preserved = {
        'google_ads': '',
        'privacy_links': '',
        'donation_links': '',
        'about_section': '',
        'head_custom': ''
    }
    
    try:
        # Extract Google Analytics/Ads
        ads_match = re.search(r'<script async src="https://pagead2\.googlesyndication\.com[^>]*>.*?</script>', old_html, re.DOTALL)
        if ads_match:
            preserved['google_ads'] = ads_match.group(0)
            print("✓ Preserved: Google Ads script")
    except:
        pass
    
    try:
        # Extract privacy/about links (look for comment markers or footer links)
        privacy_match = re.search(r'<!-- PRIVACY -->.*?<!-- /PRIVACY -->', old_html, re.DOTALL)
        if privacy_match:
            preserved['privacy_links'] = privacy_match.group(0)
            print("✓ Preserved: Privacy section")
    except:
        pass
    
    try:
        # Extract donation/BNB invite links
        donation_match = re.search(r'<!-- DONATE -->.*?<!-- /DONATE -->', old_html, re.DOTALL)
        if donation_match:
            preserved['donation_links'] = donation_match.group(0)
            print("✓ Preserved: Donation section")
    except:
        pass
    
    try:
        # Extract any custom head content (between <!-- CUSTOM_HEAD --> markers)
        head_match = re.search(r'<!-- CUSTOM_HEAD -->.*?<!-- /CUSTOM_HEAD -->', old_html, re.DOTALL)
        if head_match:
            preserved['head_custom'] = head_match.group(0)
            print("✓ Preserved: Custom head section")
    except:
        pass
    
    return preserved

# ─────────────────────────────────────────────
# UPDATE HTML: Smart patching instead of rebuild
# ─────────────────────────────────────────────
def update_html_content(old_html, data, final_history, date_str, price_context="", 
                       sentiment_mood="NEUTRAL", sentiment_score=5, trending_tokens=None, 
                       btc=None, eth=None, sol=None, preserved=None):
    """Update ONLY dynamic content in existing HTML template"""
    if btc is None: btc = {}
    if eth is None: eth = {}
    if sol is None: sol = {}
    if preserved is None: preserved = {}

    html = old_html
    
    # Update metadata
    title = data.get('title', 'Intelligence Report')
    threat_score = int(str(data.get('threat_score', 5))) if str(data.get('threat_score', 5)).isdigit() else 5
    opp_score = int(str(data.get('opportunity_score', 5))) if str(data.get('opportunity_score', 5)).isdigit() else 5
    
    html = re.sub(r'<title>.*?</title>', f'<title>Autonomous Lab 2026 — {title}</title>', html)
    html = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="Real-time crypto intelligence: Threat {threat_score}/10 | Opportunity {opp_score}/10">', html)
    html = re.sub(r'(<meta property="og:title"[^>]*content=")[^"]*', f'\\1{title} — Autonomous Lab', html)
    html = re.sub(r'(<meta property="og:description"[^>]*content=")[^"]*', f'\\1Threat: {threat_score}/10 | Opportunity: {opp_score}/10', html)
    
    # Restore Google Ads if lost
    if preserved.get('google_ads') and '<script async src="https://pagead2.googlesyndication.com' not in html:
        html = html.replace('</head>', f"{preserved['google_ads']}\n</head>")
        print("✓ Restored: Google Ads script")
    
    # Update main hero title
    html = re.sub(
        r'<h2 class="text-4xl font-bold mb-6 text-white">.*?</h2>',
        f'<h2 class="text-4xl font-bold mb-6 text-white">{title}</h2>',
        html, count=1
    )
    
    # Update threat score
    html = re.sub(
        r'(<p class="text-xs uppercase text-red-400 mb-2">Threat</p>.*?<p class="text-4xl font-bold text-red-400 count-number">)\d+',
        f'\\1{threat_score}',
        html, flags=re.DOTALL, count=1
    )
    
    # Update opportunity score
    html = re.sub(
        r'(<p class="text-xs uppercase mb-2" style="color:[^"]*">Opportunity</p>.*?<p class="text-4xl font-bold count-number"[^>]*>)\d+',
        f'\\1{opp_score}',
        html, flags=re.DOTALL, count=1
    )
    
    # Update threat text
    threat_txt = data.get('threat', '')
    html = re.sub(
        r'(<p class="text-xs uppercase text-red-400 mb-2">Threat</p>.*?<p class="text-sm text-slate-400 mt-3">).*?(?=</p>)',
        f'\\1{threat_txt}',
        html, flags=re.DOTALL, count=1
    )
    
    # Update opportunity text
    opp_txt = data.get('opportunity', '')
    html = re.sub(
        r'(<p class="text-xs uppercase mb-2" style="color:[^"]*">Opportunity</p>.*?<p class="text-4xl font-bold count-number"[^>]*>\d+.*?<p class="text-sm text-slate-400 mt-3">).*?(?=</p>)',
        f'\\1{opp_txt}',
        html, flags=re.DOTALL, count=1
    )
    
    # Update prices
    if btc.get('usd'):
        btc_color = "#22c55e" if btc.get('usd_24h_change', 0) >= 0 else "#ef4444"
        btc_change = btc.get('usd_24h_change', 0) or 0
        html = re.sub(
            r'(<span>BTC</span><span style="color:[^"]*">)\$[^<]+</span>',
            f'<span style="color:{btc_color}">${btc.get("usd",0):,.0f} {btc_change:+.1f}%</span>',
            html, count=1
        )
    
    if eth.get('usd'):
        eth_color = "#22c55e" if eth.get('usd_24h_change', 0) >= 0 else "#ef4444"
        eth_change = eth.get('usd_24h_change', 0) or 0
        html = re.sub(
            r'(<span>ETH</span><span style="color:[^"]*">)\$[^<]+</span>',
            f'<span style="color:{eth_color}">${eth.get("usd",0):,.0f} {eth_change:+.1f}%</span>',
            html, count=1
        )
    
    if sol.get('usd'):
        sol_color = "#22c55e" if sol.get('usd_24h_change', 0) >= 0 else "#ef4444"
        sol_change = sol.get('usd_24h_change', 0) or 0
        html = re.sub(
            r'(<span>SOL</span><span style="color:[^"]*">)\$[^<]+</span>',
            f'<span style="color:{sol_color}">${sol.get("usd",0):,.2f} {sol_change:+.1f}%</span>',
            html, count=1
        )
    
    # Update sentiment
    sent_color = "#22c55e" if sentiment_mood == "BULLISH" else "#ef4444"
    sent_width = min(sentiment_score * 10, 100)
    html = re.sub(
        r'(<p class="text-2xl font-bold mb-3" style="color:[^"]*">)BULLISH|BEARISH|NEUTRAL',
        f'\\1{sentiment_mood}',
        html, count=1
    )
    html = re.sub(
        r'(style="background: linear-gradient\(to right[^"]*\) 0%, )#[a-f0-9]{6}',
        f'\\1{sent_color}',
        html, count=1
    )
    
    # Update archive history with markers
    if '<!-- H_S -->' in html and '<!-- H_E -->' in html:
        html = re.sub(
            r'(<!-- H_S -->).*?(<!-- H_E -->)',
            f'\\1{final_history}\\2',
            html, flags=re.DOTALL
        )
    
    # Update footer date
    html = re.sub(
        r'• \d{1,2} \w+ \d{4} \| \d{2}:\d{2} UTC •',
        f'• {date_str} •',
        html
    )
    
    return html

# ─────────────────────────────────────────────
# NOTIFY: Telegram
# ─────────────────────────────────────────────
def send_telegram(title, threat, opportunity, threat_score, opp_score):
    """Send update to Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        print("ℹ Telegram not configured")
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
        print("✓ Telegram sent")
    except Exception as e:
        print(f"✗ Telegram failed: {e}")

# ─────────────────────────────────────────────
# PUBLISH: Dev.to
# ─────────────────────────────────────────────
def post_to_devto(data):
    """Publish article to Dev.to"""
    key = os.getenv("DEV")
    if not key:
        print("ℹ Dev.to key not set")
        return
    
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])])
    tokens = ", ".join(data.get('tokens_to_watch', []))
    body = (
        f"> 🔗 Live Dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n"
        f"> 📢 Telegram: [t.me/AII2026futher](https://t.me/AII2026futher)\n\n"
        f"## Today's Headlines\n\n{bullets}\n\n"
        f"## ⚠️ Threat [{data.get('threat_score','?')}/10]\n\n{data.get('threat','')}\n\n"
        f"## 💡 Opportunity [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity','')}\n\n"
        f"## 🪙 Tokens To Watch\n\n{tokens}\n\n"
        f"## 📊 Analysis\n\n{data.get('deep_analysis','')}\n\n"
        f"---\n*AI-powered • Gemini + Groq + Free APIs. Updated every 2 hours.*"
    )
    try:
        r = requests.post(
            "https://dev.to/api/articles",
            json={"article": {
                "title": data.get('title', 'Crypto Intelligence Update'),
                "body_markdown": body,
                "tags": ["crypto", "web3", "defi", "ai"],
                "published": True
            }},
            headers={"api-key": key},
            timeout=15
        )
        r.raise_for_status()
        print(f"✓ Dev.to published")
    except Exception as e:
        print(f"✗ Dev.to failed: {e}")

# ─────────────────────────────────────────────
# SEO files
# ─────────────────────────────────────────────
def write_seo_files():
    """Generate sitemap and robots.txt"""
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
    <loc>https://autonomous-portfolio-2026.live/about.html</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)
    with open("robots.txt", "w") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n")
    print("✓ SEO files updated")

# ─────────────────────────────────────────────
# BUILD HTML (template only, for first run)
# ─────────────────────────────────────────────
def build_html(data, final_history, date_str, price_context="", sentiment_mood="NEUTRAL", 
               sentiment_score=5, trending_tokens=None, btc=None, eth=None, sol=None):
    """Build complete HTML page (used only for initial creation)"""
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
    threat_label  = {"Critical":"● CRITICAL","High":"● HIGH","Medium":"● MEDIUM","Low":"● LOW"}.get(threat, "● UNKNOWN")

    try: ts = int(str(threat_score))
    except: ts = 5
    try: os_ = int(str(opp_score))
    except: os_ = 5

    if ts >= 7:
        bias_label = "📉 BEARISH BIAS"; bias_desc = "High threat — short-term selling pressure"; bias_color = "#ef4444"
    elif os_ >= 7:
        bias_label = "📈 BULLISH BIAS"; bias_desc = "Strong opportunity — mid-term buying"; bias_color = "#22c55e"
    else:
        bias_label = "⚖️ MIXED SIGNALS"; bias_desc = "Wait for clarity"; bias_color = "#eab308"

    bullets_html = ""
    for i, b in enumerate(news_bullets, 1):
        bullets_html += f'<div class="flex gap-5 items-start group/item p-4 rounded-2xl hover:bg-white/[0.02]"><span class="mt-1 flex-shrink-0 w-8 h-8 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center text-sm font-bold">{i}</span><p class="text-slate-300">{b}</p></div>'

    tokens_html = ""
    for i, t in enumerate(tokens):
        if t.strip():
            delay = i * 0.1
            tokens_html += f'<span class="tag bg-red-500/5 text-red-400 border border-red-500/20 hover:bg-red-500/10"><span class="w-2 h-2 rounded-full bg-red-400 blink" style="animation-delay:{delay}s"></span>{t}</span>'

    analyst_note = data.get('analyst_note', f'Monitoring {", ".join(tokens[:2]) if tokens else "market"}.')
    deep_paras = [p.strip() for p in deep_raw.split('\n') if p.strip()]
    para_titles = ["Root Cause Analysis", "Market Impact", "48-Hour Outlook"]
    deep_html = ""
    for i, para in enumerate(deep_paras[:3]):
        ptitle = para_titles[i] if i < len(para_titles) else f"Analysis {i+1}"
        deep_html += f'<div class="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.04]"><h4 class="text-lg font-bold text-white mb-3">{ptitle}</h4><p class="text-slate-400">{para}</p></div>'

    trending_html = ""
    if trending_tokens:
        for t in trending_tokens[:5]:
            trending_html += f'<span class="text-[11px] mono px-3 py-1 rounded-full bg-white/5 text-slate-400 border border-white/10">{t}</span>\n'

    btc_change = btc.get('usd_24h_change', 0) or 0
    eth_change = eth.get('usd_24h_change', 0) or 0
    sol_change = sol.get('usd_24h_change', 0) or 0
    btc_color = "#22c55e" if btc_change >= 0 else "#ef4444"
    eth_color = "#22c55e" if eth_change >= 0 else "#ef4444"
    sol_color = "#22c55e" if sol_change >= 0 else "#ef4444"
    btc_price = f"${btc.get('usd',0):,.0f}" if btc.get('usd') else "—"
    eth_price = f"${eth.get('usd',0):,.0f}" if eth.get('usd') else "—"
    sol_price = f"${sol.get('usd',0):,.2f}" if sol.get('usd') else "—"
    sent_color = "#22c55e" if sentiment_mood == "BULLISH" else "#ef4444"
    sent_width = min(sentiment_score * 10, 100)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lab 2026 — {title}</title>
    <meta name="description" content="Real-time crypto intelligence: Threat {threat_score}/10 | Opportunity {opp_score}/10">
    <meta name="keywords" content="crypto, web3, defi, security, ai, blockchain">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{title} — Autonomous Lab">
    <meta property="og:description" content="Threat: {threat_score}/10 | Opportunity: {opp_score}/10">
    <meta property="og:url" content="https://autonomous-portfolio-2026.live">
    <link rel="canonical" href="https://autonomous-portfolio-2026.live/">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3639279484055527" crossorigin="anonymous"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ background: #06070f; color: #f1f5f9; font-family: 'Space Grotesk', sans-serif; margin: 0; }}
        .glass {{ background: rgba(15,23,42,0.4); border: 1px solid rgba(255,255,255,0.06); backdrop-filter: blur(24px); border-radius: 24px; }}
        .blink {{ animation: pulse 2.5s ease-in-out infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
        .tag {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 99px; font-size: 0.875rem; border: 1px solid; }}
        .count-number {{ animation: fadeIn 0.8s ease forwards; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    </style>
</head>
<body class="min-h-screen">

<div class="w-full border-b border-white/10 bg-[#06070f]/90 sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
            <span class="w-2.5 h-2.5 rounded-full bg-red-500 blink"></span>
            <span class="text-xs font-bold text-slate-400 uppercase">AI Pipeline Online</span>
        </div>
        <span class="text-xs font-bold" style="color:{threat_color}">{threat_label}</span>
    </div>
</div>

<div class="max-w-6xl mx-auto px-4 py-12">
    <h1 class="text-5xl font-bold mb-8">AUTONOMOUS LAB <span style="color:#ef4444">.2026</span></h1>
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 space-y-8">
            <!-- HERO -->
            <div class="glass p-8">
                <h2 class="text-4xl font-bold mb-6 text-white">{title}</h2>
                <div class="space-y-2">{bullets_html}</div>
            </div>

            <!-- SIGNALS -->
            <div class="grid grid-cols-2 gap-6">
                <div class="glass p-6">
                    <p class="text-xs uppercase text-red-400 mb-2">Threat</p>
                    <p class="text-4xl font-bold text-red-400 count-number">{ts}</p>
                    <p class="text-slate-400">/10</p>
                    <p class="text-sm text-slate-400 mt-3">{threat_txt}</p>
                </div>
                <div class="glass p-6" style="border-color:{color}33">
                    <p class="text-xs uppercase mb-2" style="color:{color}">Opportunity</p>
                    <p class="text-4xl font-bold count-number" style="color:{color}">{os_}</p>
                    <p class="text-slate-400">/10</p>
                    <p class="text-sm text-slate-400 mt-3">{opp_txt}</p>
                </div>
            </div>

            <!-- TOKENS -->
            <div class="glass p-8">
                <p class="text-xs uppercase mb-4 font-bold">🪙 Tokens to Watch</p>
                <div class="flex flex-wrap gap-3">{tokens_html}</div>
            </div>

            <!-- ANALYSIS -->
            <div class="glass p-8">
                <p class="text-xs uppercase mb-4 font-bold">📊 Deep Analysis</p>
                <div class="space-y-4">{deep_html}</div>
            </div>

            <!-- ANALYST NOTE -->
            <div class="glass p-8 border-l-4" style="border-color:{color}">
                <p class="text-lg font-bold mb-2 text-white">✍️ Analyst's Note</p>
                <p class="text-slate-300">{analyst_note}</p>
            </div>

            <!-- CONTRARIAN -->
            <div class="glass p-8">
                <p class="text-xs uppercase mb-3 text-yellow-400 font-bold">🤔 Contrarian View</p>
                <p class="text-lg italic text-slate-200">"{critic}"</p>
            </div>
        </div>

        <!-- SIDEBAR -->
        <aside class="space-y-8">
            <!-- PRICES -->
            <div class="glass p-6">
                <p class="text-xs uppercase font-bold mb-4">Live Prices</p>
                <div class="space-y-3 text-sm">
                    <div class="flex justify-between"><span>BTC</span><span style="color:{btc_color}">{btc_price} {btc_change:+.1f}%</span></div>
                    <div class="flex justify-between"><span>ETH</span><span style="color:{eth_color}">{eth_price} {eth_change:+.1f}%</span></div>
                    <div class="flex justify-between"><span>SOL</span><span style="color:{sol_color}">{sol_price} {sol_change:+.1f}%</span></div>
                </div>
            </div>

            <!-- SENTIMENT -->
            <div class="glass p-6">
                <p class="text-xs uppercase font-bold mb-2">Market Sentiment</p>
                <p class="text-2xl font-bold mb-3" style="color:{sent_color}">{sentiment_mood}</p>
                <div class="w-full h-2 bg-slate-700 rounded" style="background: linear-gradient(to right, rgba(0,0,0,0.3) 0%, {sent_color} {sent_width}%, rgba(0,0,0,0.1) 100%)"></div>
            </div>

            <!-- MARKET BIAS -->
            <div class="glass p-6" style="border-color:{bias_color}20">
                <p class="text-xs uppercase font-bold mb-3" style="color:{bias_color}">Combined Signal</p>
                <p class="text-2xl font-bold" style="color:{bias_color}">{bias_label}</p>
                <p class="text-sm text-slate-400 mt-2">{bias_desc}</p>
            </div>

            <!-- TRENDING -->
            <div class="glass p-6">
                <p class="text-xs uppercase font-bold mb-3">🔥 Trending</p>
                <div class="flex flex-wrap gap-2">{trending_html if trending_html else '<span class="text-xs text-slate-600">Loading...</span>'}</div>
            </div>

            <!-- ARCHIVE -->
            <div class="glass p-6">
                <p class="text-xs uppercase font-bold mb-3">📁 Archive</p>
                <div class="max-h-80 overflow-y-auto text-xs space-y-2 text-slate-400">
                    <!-- H_S -->{final_history}<!-- H_E -->
                </div>
            </div>

            <!-- DISCLAIMER -->
            <div class="glass p-4 border-yellow-500/20">
                <p class="text-xs text-yellow-600">⚠️ AI-generated research. Not financial advice.</p>
            </div>
        </aside>
    </div>
</div>

<footer class="mt-16 pt-8 border-t border-white/10 text-center text-xs text-slate-600">
    <p>© 2026 Autonomous Lab • {date_str} • <a href="https://github.com/kchour96-dev" class="hover:text-white">GitHub</a></p>
</footer>

</body>
</html>"""

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run_production_agent():
    """Main orchestration function"""
    print("\n" + "="*60)
    print("🤖 AUTONOMOUS LAB AGENT STARTING")
    print("="*60 + "\n")
    
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    if not g_key:
        print("❌ FATAL: GEMINI key not set. Aborting.")
        return

    # BACKUP & EXTRACT
    old_content = ""
    preserved = {}
    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")
        with open("index.html", "r", encoding="utf-8") as f:
            old_content = f.read()
        print("✓ Backup created")
        
        # Extract preserved sections
        preserved = extract_preserved_sections(old_content)
        print("✓ Preserved sections extracted")

    # LAYER 1: Fetch all data sources
    print("\n[LAYER 1] Gathering intelligence...\n")
    rss_context = get_rss_context()
    price_context, btc, eth, sol = get_price_context()
    trending_tokens = get_trending_tokens()
    coindesk_headlines, sentiment_mood, sentiment_score = get_coindesk_sentiment()
    positive_news = get_positive_crypto_news()
    positive_news_text = extract_good_news_for_gemini(positive_news)
    
    # LAYER 2: Deep research (optional)
    print("\n[LAYER 2] Deep research...\n")
    research = get_research(rss_context + " " + coindesk_headlines, t_key)

    # Check for duplicate stories
    print("\n[LAYER 3] Analyzing for duplicates...\n")
    last_title = ""
    if "<!-- H_S -->" in old_content:
        try:
            hist = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]
            match = re.search(r"'font-bold text-slate-200'>([^<]+)", hist)
            if match:
                last_title = match.group(1)
                print(f"ℹ Last story: {last_title[:50]}")
        except:
            pass

    full_context = research
    if last_title:
        full_context += f"\n\nIMPORTANT: Last report was '{last_title[:50]}...'. Pick DIFFERENT angle."

    # LAYER 4: Gemini analysis (BALANCED)
    print("\n[LAYER 4] Gemini analysis (balanced)...\n")
    data = get_gemini_data_balanced(full_context, g_key, price_context, sentiment_mood, 
                                   sentiment_score, trending_tokens, positive_news_text)

    if not data:
        print("\n❌ All models failed. Keeping old site.\n")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    # Build archive
    print("\n[LAYER 5] Building archive...\n")
    history_html = ""
    if "<!-- H_S -->" in old_content and "<!-- H_E -->" in old_content:
        raw_history = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]
        clean_entries = re.findall(
            r"<div class='archive-item[^>]*>.*?</div>",
            raw_history, re.DOTALL
        )
        valid_entries = []
        for entry in clean_entries[:20]:
            if any(bad in entry for bad in ['setTimeout', 'innerHTML', 'onclick']):
                continue
            if re.search(r'\d{2} \w+ \d{4}', entry):
                valid_entries.append(entry)
        history_html = "".join(valid_entries[:15])

    date_str = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    ts = int(str(data.get('threat_score', 5))) if str(data.get('threat_score', 5)).isdigit() else 5
    os_ = int(str(data.get('opportunity_score', 5))) if str(data.get('opportunity_score', 5)).isdigit() else 5
    
    new_entry = (
        f"<div class='archive-item'>"
        f"<p class='text-xs text-slate-500'>{date_str}</p>"
        f"<p class='font-bold text-slate-200'>{data.get('title','Update')[:40]}</p>"
        f"<p class='text-xs'>⚠️ {ts}/10 | 💡 {os_}/10</p>"
        f"</div>"
    )
    final_history = (new_entry + history_html)[:8000]

    # UPDATE or BUILD HTML
    print("\n[LAYER 6] Updating/Building HTML...\n")
    if old_content:
        # Use smart patching for existing HTML
        html = update_html_content(old_content, data, final_history, date_str, price_context, 
                                  sentiment_mood, sentiment_score, trending_tokens, btc, eth, sol, preserved)
        print("✓ HTML patched (content updated, UI preserved)")
    else:
        # Build from scratch for first run
        html = build_html(data, final_history, date_str, price_context, sentiment_mood, 
                         sentiment_score, trending_tokens, btc, eth, sol)
        print("✓ HTML built from template")

    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✓ index.html updated successfully")
    except Exception as e:
        print(f"❌ Write failed: {e}")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    if os.path.exists("index.html.bak"):
        os.remove("index.html.bak")

    # POST-BUILD
    print("\n[LAYER 7] Post-build tasks...\n")
    write_seo_files()
    post_to_devto(data)
    send_telegram(
        data.get('title',''),
        data.get('threat',''),
        data.get('opportunity',''),
        data.get('threat_score','?'),
        data.get('opportunity_score','?')
    )

    print("\n" + "="*60)
    print("✅ PRODUCTION SYNC COMPLETE!")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_production_agent()
