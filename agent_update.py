import os
import requests
import json
import re
from datetime import datetime
import google.generativeai as genai

# ───────────────────────────────────────────────────────────────────────
# LAYER 1: DATA INGESTION NODES
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
        data = r.json()
        return data, data.get('bitcoin', {}), data.get('ethereum', {}), data.get('solana', {})
    except: return {}, {}, {}, {}

# ───────────────────────────────────────────────────────────────────────
# LAYER 2: AI PROCESSING
# ───────────────────────────────────────────────────────────────────────

def analyze_with_ai(rss, price):
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Analyze: {rss} | Prices: {price}. Return JSON: title, threat_score, opportunity_score, root_cause, market_impact, outlook, contrarian."
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except: return {"title": "Update", "threat_score": 5, "opportunity_score": 5, "root_cause": "Analyzing...", "market_impact": "...", "outlook": "...", "contrarian": "..."}

# ───────────────────────────────────────────────────────────────────────
# LAYER 3: COMPLIANCE GENERATOR
# ───────────────────────────────────────────────────────────────────────

def generate_compliance():
    d = datetime.utcnow().strftime("%d %b %Y")
    base = "<style>body{background:#06070f;color:#f1f5f9;font-family:sans-serif;padding:50px;line-height:1.6;} .box{background:#111;padding:30px;border-radius:15px;}</style>"
    
    pages = {
        "privacy.html": f"<h1>Privacy Policy</h1><div class='box'><p>Last Updated: {d}. This site uses Google AdSense to serve ads. Automated AI research lab.</p></div>",
        "terms.html": f"<h1>Terms of Service</h1><div class='box'><p>Educational purposes only. Not financial advice.</p></div>",
        "about.html": f"<h1>System Architecture</h1><div class='box'><p>Autonomous Lab 2026 uses a headless AI pipeline to track security intelligence.</p></div>"
    }
    
    for fn, content in pages.items():
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"<html><head>{base}</head><body>{content}<br><a href='/'>Back to Dashboard</a></body></html>")

    with open("sitemap.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://autonomous-portfolio-2026.live/</loc></url></urlset>')

# ───────────────────────────────────────────────────────────────────────
# LAYER 4: MAIN PIPELINE
# ───────────────────────────────────────────────────────────────────────

def main():
    data = analyze_with_ai(get_rss_context(), get_price_context())
    
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Fixed regex patterns to match the markers I gave you previously
    html = re.sub(r".*?", f"{data.get('title')}", html, flags=re.DOTALL)
    html = re.sub(r".*?", f"{data.get('root_cause')}", html, flags=re.DOTALL)
    html = re.sub(r".*?", f"{data.get('market_impact')}", html, flags=re.DOTALL)
    html = re.sub(r".*?", f"{data.get('outlook')}", html, flags=re.DOTALL)
    html = re.sub(r".*?", f"{data.get('contrarian')}", html, flags=re.DOTALL)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    generate_compliance()
    print("✓ Deployment complete.")

if __name__ == "__main__":
    main()
