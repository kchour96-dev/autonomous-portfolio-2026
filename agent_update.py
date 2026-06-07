import os
import requests
import json
import re
import shutil
from datetime import datetime
import google.generativeai as genai

# ───────────────────────────────────────────────────────────────────────
# LAYER 1: DATA INGESTION NODES (Free APIs)
# ───────────────────────────────────────────────────────────────────────

def get_rss_context():
    """Fetches high-variety security and market headlines from top feeds"""
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
            titles = re.findall(r'<title>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?</title>', r.text, re.DOTALL)
            clean = [t.strip() for t in titles[1:2] if t.strip()]
            items.extend(clean)
        except Exception as e:
            print(f"RSS failed {url}: {e}")
            
    result = " | ".join(items[:6]) if items else "Crypto and Web3 market developments 2026"
    return result[:1500] 

def get_price_context():
    """Fetches live market data from free CoinGecko endpoints"""
    try:
        res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",
            timeout=8
        )
        data = res.json()
        btc = data.get('bitcoin', {})
        eth = data.get('ethereum', {})
        sol = data.get('solana', {})
        
        context = (
            f"BTC: ${btc.get('usd', 0):,} ({btc.get('usd_24h_change', 0):+.1f}%) | "
            f"ETH: ${eth.get('usd', 0):,} ({eth.get('usd_24h_change', 0):+.1f}%) | "
            f"SOL: ${sol.get('usd', 0):,} ({sol.get('usd_24h_change', 0):+.1f}%)"
        )
        return context, btc, eth, sol
    except Exception as e:
        print(f"CoinGecko API fallback triggered: {e}")
        return "Market data stream currently re-routing.", {}, {}, {}

# ───────────────────────────────────────────────────────────────────────
# LAYER 2: AI PROCESSING (GEMINI)
# ───────────────────────────────────────────────────────────────────────

def analyze_with_ai(rss_data, price_str):
    """Sends the data to Gemini to generate real analysis"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in environment variables. Using fallback data.")
        return fallback_payload()

    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash for speed and low cost
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an autonomous Web3 cybersecurity AI. Analyze the following recent news and market data:
    News: {rss_data}
    Market: {price_str}
    
    Respond ONLY with a valid JSON object matching this exact structure, no markdown formatting or backticks:
    {{
        "title": "A short, punchy 5-word headline summarizing the main threat",
        "threat_score": "Number between 1 and 10",
        "opportunity_score": "Number between 1 and 10",
        "color": "#ef4444",
        "root_cause": "1 sentence explaining the primary security issue.",
        "market_impact": "1 sentence explaining how this affects crypto prices.",
        "outlook": "1 sentence predicting the next 30 days.",
        "contrarian": "1 sentence offering a contrarian perspective on this news."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up in case Gemini adds markdown formatting
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return fallback_payload()

def fallback_payload():
    return {
        "title": "System Diagnostic Mode Active",
        "threat_score": "5",
        "opportunity_score": "5",
        "color": "#3b82f6",
        "root_cause": "Awaiting new data stream from network nodes.",
        "market_impact": "Market parsing currently running in background tasks.",
        "outlook": "System will resume standard predictive modeling shortly.",
        "contrarian": "Interruption in data flow prevents accurate contrarian modeling."
    }

# ───────────────────────────────────────────────────────────────────────
# LAYER 3: AUTOMATED COMPLIANCE GENERATOR
# ───────────────────────────────────────────────────────────────────────

def generate_compliance_and_seo():
    """Generates sitemap, robots.txt, and matching legal layouts for AdSense"""
    date_str = datetime.utcnow().strftime("%d %b %Y")
    iso_date = datetime.utcnow().strftime("%Y-%m-%d")

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: [https://autonomous-portfolio-2026.live/sitemap.xml](https://autonomous-portfolio-2026.live/sitemap.xml)\n")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="[http://www.sitemaps.org/schemas/sitemap/0.9](http://www.sitemaps.org/schemas/sitemap/0.9)">
    <url><loc>[https://autonomous-portfolio-2026.live/](https://autonomous-portfolio-2026.live/)</loc><lastmod>{iso_date}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>
    <url><loc>[https://autonomous-portfolio-2026.live/about.html](https://autonomous-portfolio-2026.live/about.html)</loc><lastmod>{iso_date}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
    <url><loc>[https://autonomous-portfolio-2026.live/privacy.html](https://autonomous-portfolio-2026.live/privacy.html)</loc><lastmod>{iso_date}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>
    <url><loc>[https://autonomous-portfolio-2026.live/terms.html](https://autonomous-portfolio-2026.live/terms.html)</loc><lastmod>{iso_date}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>
</urlset>"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

    page_head = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script><style>body { background:#06070f; color:#f1f5f9; font-family:sans-serif; } .glass { background:rgba(15,23,42,0.45); border:1px solid rgba(255,255,255,0.06); padding:40px; border-radius:20px; max-width:800px; margin:50px auto; }</style></head><body><div class="glass"><a href="/" style="color:#ef4444; font-size:12px; font-weight:bold; text-transform:uppercase; text-decoration:none;">← System Dashboard</a>"""

    privacy = page_head + f"<h1 class='text-3xl font-bold text-white mt-4 mb-2'>Privacy Policy</h1><p class='text-sm text-slate-400 mb-4'>Last Synced: {date_str}</p><p>We prioritize security transparency. Google AdSense uses diagnostic cookies to optimize ad serving modules based on anonymous click streams across decentralized ecosystems.</p></div></body></html>"
    terms = page_head + f"<h1 class='text-3xl font-bold text-white mt-4 mb-2'>Terms of Service</h1><p class='text-sm text-slate-400 mb-4'>Active Node Validation: 2026</p><p>All vulnerability mappings and threat matrices are processed programmatically by headless node architecture. No data constitutes financial advisory patterns.</p></div></body></html>"
    about = page_head + f"<h1 class='text-3xl font-bold text-white mt-4 mb-2'>System Architecture</h1><p class='text-sm text-slate-400 mb-4'>Node Status: Operational</p><p>Autonomous Lab 2026 is an experimental multi-chain telemetry center gathering and indexing critical cyber vulnerabilities across modern Web3 deployments.</p></div></body></html>"

    with open("privacy.html", "w", encoding="utf-8") as f: f.write(privacy)
    with open("terms.html", "w", encoding="utf-8") as f: f.write(terms)
    with open("about.html", "w", encoding="utf-8") as f: f.write(about)
    print("✓ All AdSense validation documents successfully written.")

# ───────────────────────────────────────────────────────────────────────
# LAYER 4: DYNAMIC RUNTIME MATRIX & ENGINE ASSEMBLY
# ───────────────────────────────────────────────────────────────────────

def build_html(data, date_str):
    """Compiles variables cleanly directly into your pre-designed production dashboard template"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            template = f.read()
    except Exception:
        print("Template missing.")
        return ""

    # Replace variables safely in memory for the Live UI
    template = re.sub(r"Last AI Sync:.*?(?=\|)", f"Last AI Sync: {date_str} ", template)
    
    # Optional: If you have specific ID tags in your HTML like <span id="threat-score">, 
    # you can use re.sub to inject data.get("threat_score") here as well.
    
    return template

def main():
    print("Initializing Autonomous Deployment Pipeline...")
    date_str = datetime.utcnow().strftime("%d %b %Y | %H:%M UTC")
    
    # 1. Harvest Contexts
    rss_data = get_rss_context()
    price_str, btc, eth, sol = get_price_context()
    
    # 2. Extract History State
    history_html = ""
    if os.path.exists("index.html"):
        try:
            with open("index.html", "r", encoding="utf-8") as f:
                content = f.read()
                archive_match = re.search(r'<div id="archive-list"[^>]*>(.*?)</div>', content, re.DOTALL)
                if archive_match:
                    history_html = archive_match.group(1).strip()
        except Exception as e:
            print(f"History reading bypassed: {e}")

    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")

    # 3. REAL AI REQUEST (No more mock payload)
    print("Sending data to AI Engine...")
    ai_payload = analyze_with_ai(rss_data, price_str)
    print(f"AI Response Received: {ai_payload.get('title')}")

    # Generate historic archive entry node snippet
    ts = ai_payload.get('threat_score', '5')
    os_ = ai_payload.get('opportunity_score', '5')
    new_entry = (
        f"<div class='archive-item rounded-xl p-4 cursor-pointer hover:bg-white/5 transition'>"
        f"<p class='text-xs mono text-slate-500 mb-1'>{date_str}</p>"
        f"<p class='text-sm font-bold text-slate-200 uppercase'>{ai_payload.get('title')}</p>"
        f"<div class='flex gap-3 mt-2 text-xs mono'>"
        f"<span class='text-red-400'>⚠️ {ts}/10</span>"
        f"<span class='text-blue-400'>💡 {os_}/10</span>"
        f"</div></div>"
    )
    final_history = (new_entry + history_html)[:8000]

    # Assemble HTML
    html = build_html(ai_payload, date_str)

    # Note: Because your previous HTML logic had a lot of strict replacements, 
    # ensure your index.html has a way to receive this data, or the template update 
    # logic above needs to exactly match your `index.html` structure.

    try:
        # Save HTML
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✓ index.html updated and written.")
        
        # Deploy AdSense Files
        generate_compliance_and_seo()
        
    except Exception as e:
        print(f"Critical execution error during write operation: {e}")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")

if __name__ == "__main__":
    main()
