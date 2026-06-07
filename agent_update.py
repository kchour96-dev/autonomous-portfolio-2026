import os
import requests
import json
import re
import shutil
from datetime import datetime
import google.generativeai as genai

# [KEEP YOUR get_rss_context and get_price_context functions exactly as they are]

def main():
    # 1. Fetch AI Data
    date_str = datetime.utcnow().strftime("%d %b %Y | %H:%M UTC")
    data = analyze_with_ai(get_rss_context(), get_price_context())
    
    # 2. Read template
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 3. USE PROTECTED REPLACEMENTS 
    # This only touches the specific ID/Marker tags
    # It will NOT delete your donation links or footer
    html = re.sub(r'.*?', f'{data.get("title")}', html, flags=re.DOTALL)
    
    # Update Archive (Protecting the rest of the file)
    new_archive = f"<div class='archive-item'>...{data.get('title')}...</div>"
    html = re.sub(r'.*?', f'{new_archive}', html, flags=re.DOTALL)

    # 4. Save
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    generate_adsense_compliance()
    print("✓ Pipeline Success")
