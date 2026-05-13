import os
import requests
import json
from datetime import datetime

def send_telegram_message(topic, insight):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        print("Telegram secrets missing. Skipping...")
        return

    message = f"🤖 *AUTONOMOUS UPDATE: 2026*\n\n" \
              f"🚀 *Topic:* {topic}\n" \
              f"💡 *Insight:* {insight}\n\n" \
              f"🔗 [View Live Portfolio](https://autonomous-portfolio-2026.live)"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
    print("Telegram notification sent!")

def run_agent():
    gemini_key = os.getenv("GEMINI")
    tavily_key = os.getenv("TAVILY")

    # --- STEP 1: RESEARCH (TAVILY) ---
    context = "Latest AI trends for 2026"
    if tavily_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": tavily_key,
                "query": "hottest tech breakthroughs 2026",
                "max_results": 2
            })
            context = "\n".join([f"{res['title']}: {res['content']}" for res in r.json().get('results', [])])
        except: pass

    # --- STEP 2: BRAIN (GEMINI) ---
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    prompt = f"Research: {context}. You are a 2026 AI. Return ONLY JSON: {{\"topic\": \"Name\", \"insight\": \"2 sentences\", \"thoughts\": [\"log1\", \"log2\"]}}"
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        data = json.loads(resp.json()['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip())
    except:
        data = {"topic": "System Update", "insight": "The 2026 grid is evolving.", "thoughts": ["Analyzing", "Live"]}

    # --- STEP 3: DESIGN (HTML) ---
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black text-white p-10 font-mono">
        <div class="max-w-2xl mx-auto border border-green-500 p-8 rounded-lg">
            <h1 class="text-4xl font-bold text-green-500 mb-4">{data['topic']}</h1>
            <p class="text-xl text-gray-400 mb-6 italic">"{data['insight']}"</p>
            <div class="text-[10px] text-gray-600">Updated: {date_str}</div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html)

    # --- STEP 4: TELEGRAM NOTIFICATION ---
    send_telegram_message(data['topic'], data['insight'])
    print("SUCCESS!")

if __name__ == "__main__":
    run_agent()
