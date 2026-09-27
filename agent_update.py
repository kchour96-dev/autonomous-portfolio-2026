import os
import requests
import json
import re
from datetime import datetime

# ─────────────────────────────────────────────
# 1. FREE PUBLIC WOW DATA (NO AUTH REQUIRED)
# ─────────────────────────────────────────────
def get_free_wow_token_price():
    """Fetch live US WoW Token gold price from public community tracker (Zero Auth)"""
    urls = [
        "https://wowtokenprice.com/api/v1/tokens/prices",
        "https://data.wowtoken.app/snapshot/us.json"
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    # Check common schema variations
                    price = data.get("price") or data.get("formatted_buy")
                    if not price and ("us" in data or "US" in data):
                        sub = data.get("us") or data.get("US")
                        price = sub.get("price") if isinstance(sub, dict) else sub
                    if price:
                        clean_num = int(float(str(price).replace(",", "")))
                        formatted = f"{clean_num:,} Gold"
                        print(f"✓ Public WoW Token Price: {formatted}")
                        return formatted
        except Exception as e:
            continue

    print("ℹ Using cached fallback for WoW Token Price.")
    return "312,450 Gold"


def get_free_weekly_affixes():
    """Fetch live Mythic+ dungeon affixes from Raider.IO's open public API (Zero Auth)"""
    url = "https://raider.io/api/v1/mythic-plus/affixes?region=us&locale=en"
    try:
        resp = requests.get(url, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            details = data.get("affix_details", [])
            names = [a.get("name") for a in details if a.get("name")]
            if len(names) >= 2:
                print(f"✓ Raider.IO Live Affixes: {names[0]} & {names[1]}")
                return names[0], names[1]
    except Exception as e:
        print(f"ℹ Affix fetch notice ({e}). Using standard rotation.")
    return "Fortified", "Bursting"

# ─────────────────────────────────────────────
# 2. AI THEORYCRAFTING GENERATOR (GEMINI & GROQ)
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model="gemini-2.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_groq(prompt, key, model="llama-3.3-70b-versatile"):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a JSON API. Return ONLY valid JSON. Escape all newlines properly."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.7
    }
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    raw = resp.json()['choices'][0]['message']['content']
    return re.sub(r'[\x00-\x1f\x7f]', ' ', raw).replace('```json', '').replace('
