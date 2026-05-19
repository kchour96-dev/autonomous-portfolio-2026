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
        "https://decrypt.co/feed"
    ]
    items = []
    for url in feeds:
        try:
            r = requests.get(url, timeout=8)
            # Improved regex to handle various RSS title formats
            titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', r.text, re.DOTALL)
            # items[0] is usually the site title, so we take 1 and 2
            for t in titles[1:3]:
                clean_t = t.strip()
                if clean_t and len(clean_t) > 10:
                    items.append(clean_t)
        except Exception as e:
            print(f"RSS failed {url}: {e}")
    
    result = " | ".join(items[:8]) if items else "Crypto and Web3 market developments 2026"
    print(f"RSS context loaded: {len(items)} items found.")
    return result

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
                "query": f"latest crypto web3 DeFi news {rss_context[:100]} analysis 2026",
                "search_depth": "advanced",
                "max_results": 3
            },
            timeout=15
        )
        r.raise_for_status()
        results = r.json().get('results', [])
        if results:
            combined = " ".join([f"Title: {res.get('title')}\nContent: {res.get('content')}" for res in results])
            print(f"Tavily research successfully compiled: {len(combined)} chars")
            return combined[:3000]
    except Exception as e:
        print(f"Tavily research node failed: {e}")
    return rss_context

# ─────────────────────────────────────────────
# LAYER 3: Gemini — Fixed Model Fallback
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model):
    # Using
