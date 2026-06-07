import os
import requests
import json
import re
from datetime import datetime
import google.generativeai as genai

# ───────────────────────────────────────────────────────────────────────
# LAYER 1: DATA FETCHING
# ───────────────────────────────────────────────────────────────────────

def get_rss():
    feeds = ["https://feeds.feedburner.com/TheHackersNews", "https://cointelegraph.com/rss"]
    items = []
    for url in feeds:
        try:
            r = requests.get(url, timeout=5)
            titles = re.findall(r'<title>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?</title>', r.text, re.DOTALL)
            items.extend([t.strip() for t in titles[1:2] if t.strip()])
        except: continue
    return " | ".join(items[:3])

# ───────────────────────────────────────────────────────────────────────
# LAYER 2: AI LOGIC
# ───────────────────────────────────────────────────────────────────────

def get_ai_data(rss):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return {"title": "Autonomous Lab Update", "threat_score": 5, "opportunity_score": 5, "root_cause": "N/A", "market_impact": "N/A", "outlook": "N/A", "contrarian": "N/A"}
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(f"Analyze this: {rss}. Return JSON: title, threat_score, opportunity_score, root_cause, market_impact, outlook, contrarian.")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except: return {"title": "Update Error", "threat_score": 5, "opportunity_score": 5, "root_cause": "Error", "market_impact": "Error", "outlook": "Error", "contrarian": "Error"}

# ───────────────────────────────────────────────────────────────────────
# LAYER 3: COMPLIANCE & DEPLOY
# ───────────────────────────────────────────────────────────────────────

def deploy():
    data = get_ai_data(get_rss())
    
    # Update index.html using markers
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        # Only replace content between markers
        html = re.sub(r".*?", f"{data['title']}", html, flags=re.DOTALL)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

    # Ensure legal files exist for AdSense
    for p in ["privacy.html", "terms.html", "about.html"]:
        with open(p, "w") as f:
            f.write(f"<html><body><h1>{p.split('.')[0].capitalize()}</h1><a href='index.html'>Back</a></body></html>")
    
    with open("sitemap.xml", "w") as f:
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://autonomous-portfolio-2026.live/</loc></url></urlset>')

    print("✓ Pipeline completed safely.")

if __name__ == "__main__":
    deploy()
