import os
import requests
import json
from datetime import datetime

def send_telegram(topic, insight):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        print("Telegram secrets missing. Skipping social post.")
        return
    
    msg = f"🚀 *2026 AUTONOMOUS UPDATE*\n\n*Topic:* {topic}\n*Insight:* {insight}\n\n🔗 https://autonomous-portfolio-2026.live"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram status: {r.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")

def run_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    # 1. Research
    context = "latest 2026 tech trends"
    if t_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={"api_key": t_key, "query": "tech 2026 news", "max_results": 1})
            context = r.json()['results'][0]['content']
        except: print("Search failed, using brain only.")

    # 2. Brain
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"Research: {context}. Return ONLY JSON: {{\"topic\": \"Short Name\", \"insight\": \"2 sentences\"}}"
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        txt = resp.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(txt.replace('```json', '').replace('```', '').strip())
    except:
        data = {"topic": "Core Update", "insight": "System is evolving autonomously."}

    # 3. Web Design
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f"""<!DOCTYPE html><html lang="en"><head><script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-black text-white p-10 font-mono flex items-center justify-center min-h-screen">
        <div class="border-2 border-green-500 p-8 rounded-3xl max-w-xl shadow-[0_0_30px_rgba(34,197,94,0.3)]">
            <div class="text-[10px] text-green-500 mb-6 uppercase tracking-widest">● Agent Online // {date_str}</div>
            <h1 class="text-5xl font-black mb-4 uppercase italic">{data['topic']}</h1>
            <p class="text-xl text-gray-400 italic mb-8 leading-tight">"{data['insight']}"</p>
            <div class="text-[9px] text-gray-700 tracking-[0.4em]">autonomous-portfolio-2026.live</div>
        </div>
    </body></html>"""
    
    with open("index.html", "w") as f:
        f.write(html)
    
    # 4. Social Post
    send_telegram(data['topic'], data['insight'])

if __name__ == "__main__":
    run_agent()
