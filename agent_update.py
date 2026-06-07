import os
import requests
import json
import re
import shutil
from datetime import datetime
import google.generativeai as genai

# ───────────────────────────────────────────────────────────────────────
# LAYER 1: DATA INGESTION
# ───────────────────────────────────────────────────────────────────────

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
            titles = re.findall(r'<title>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?</title>', r.text, re.DOTALL)
            clean = [t.strip() for t in titles[1:2] if t.strip()]
            items.extend(clean)
        except: continue
    return " | ".join(items[:6])[:1500]

def get_price_context():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true", timeout=8)
        return r.json()
    except: return {}

# ───────────────────────────────────────────────────────────────────────
# LAYER 2: AI ANALYSIS
# ───────────────────────────────────────────────────────────────────────

def analyze_with_ai(rss, price):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Analyze: {rss} | Prices: {price}. Return JSON: title, threat_score, opportunity_score, root_cause, market_impact, outlook, contrarian."
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except: return None

# ───────────────────────────────────────────────────────────────────────
# LAYER 3: COMPLIANCE (SITEMAP/PAGES)
# ───────────────────────────────────────────────────────────────────────

def generate_compliance():
    # Generate Sitemaps & Legal pages
    with open("sitemap.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://autonomous-portfolio-2026.live/</loc></url></urlset>')
    
    # Create static files if they don't exist
    for page in ["privacy.html", "terms.html", "about.html"]:
        if not os.path.exists(page):
            with open(page, "w") as f:
                f.write(f"<html><body><h1>{page.replace('.html','').capitalize()}</h1><a href='/'>Back</a></body></html>")

# ───────────────────────────────────────────────────────────────────────
# LAYER 4: PIPELINE EXECUTION
# ───────────────────────────────────────────────────────────────────────

def main():
    data = analyze_with_ai(get_rss_context(), get_price_context())
    if not data: return
    
    # Load index.html
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Regex only targets the markers; your donation links remain untouched
    html = re.sub(r".*?", f"{data.get('title')}", html, flags=re.DOTALL)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    generate_compliance()
    print("✓ Pipeline successfully completed.")

if __name__ == "__main__":
    main()
