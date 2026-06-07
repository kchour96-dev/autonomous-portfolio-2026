import os
import requests
import json
import re
import shutil
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
# LAYER 2: AI PROCESSING (GEMINI)
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
    except: return {"title": "Update", "threat_score": 5, "opportunity_score": 5}

# ───────────────────────────────────────────────────────────────────────
# LAYER 3: ADSENSE COMPLIANCE
# ───────────────────────────────────────────────────────────────────────

def generate_adsense_compliance():
    """Generates mandatory compliance pages and sitemap for AdSense."""
    d = datetime.utcnow().strftime("%d %b %Y")
    base = "<style>body{background:#06070f;color:#f1f5f9;font-family:sans-serif;padding:50px;} .box{background:#111;padding:30px;border-radius:15px;}</style>"
    
    pages = {
        "privacy.html": f"<h1>Privacy Policy</h1><div class='box'><p>Last Updated: {d}. We use Google AdSense to serve ads. This site is an AI experiment.</p></div>",
        "terms.html": f"<h1>Terms of Service</h1><div class='box'><p>This site is for educational purposes only. Not financial advice.</p></div>",
        "about.html": f"<h1>System Architecture</h1><div class='box'><p>Autonomous Lab 2026 runs on a headless AI pipeline updating security intelligence every 2 hours.</p></div>"
    }
    
    for filename, content in pages.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<html><head>{base}</head><body>{content}<br><a href='/'>Back to Dashboard</a></body></html>")

    with open("sitemap.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://autonomous-portfolio-2026.live/</loc></url></urlset>')

# ───────────────────────────────────────────────────────────────────────
# LAYER 4: MAIN PIPELINE
# ───────────────────────────────────────────────────────────────────────

def main():
    date_str = datetime.utcnow().strftime("%d %b %Y | %H:%M UTC")
    data = analyze_with_ai(get_rss_context(), get_price_context())
    
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
    else: return

    # Inject data into markers (H_S/H_E are your archive markers in index.html)
    ts = data.get('threat_score', 5)
    os_ = data.get('opportunity_score', 5)
    
    # Save files
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html) # Ensure 'html' variable is updated with your regex logic
        generate_adsense_compliance()
        print("✓ Pipeline Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
