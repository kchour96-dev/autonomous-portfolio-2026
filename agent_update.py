import os
import requests
import json
from datetime import datetime

def run_agent():
    # Get Keys using your specific names from the screenshot
    gemini_key = os.getenv("GEMINI")
    tavily_key = os.getenv("TAVILY")

    if not gemini_key:
        print("ERROR: Secret named 'GEMINI' not found!")
        return

    # --- STEP 1: RESEARCH (TAVILY) ---
    context = "Latest AI and Robotics trends for 2026"
    if tavily_key:
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": tavily_key,
                "query": "hottest tech breakthroughs 2026",
                "max_results": 2
            }, timeout=10)
            if r.status_code == 200:
                results = r.json().get('results', [])
                context = "\n".join([f"{res['title']}: {res['content']}" for res in results])
        except Exception as e:
            print(f"Search failed: {e}")

    # --- STEP 2: BRAIN (GEMINI) ---
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    prompt = f"Based on research: {context}. You are a 2026 AI Agent. Create a website update. Return ONLY JSON: {{\"topic\": \"Name\", \"insight\": \"2 sentences\", \"thoughts\": [\"log1\", \"log2\", \"log3\"]}}"
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
    except:
        data = {"topic": "Auto-System", "insight": "System is evolving.", "thoughts": ["Analyzing", "Optimizing", "Live"]}

    # --- STEP 3: DESIGN (HTML) ---
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <title>Autonomous 2026</title>
    </head>
    <body class="bg-black text-white p-10 font-mono">
        <div class="max-w-2xl mx-auto border border-green-900 p-8 rounded-lg bg-gray-900/50 shadow-[0_0_50px_rgba(34,197,94,0.1)]">
            <div class="flex justify-between text-[10px] text-green-500 mb-10">
                <span class="animate-pulse">● SYSTEM_ACTIVE</span>
                <span>{date_str}</span>
            </div>
            <h1 class="text-5xl font-black mb-4 text-white uppercase tracking-tighter italic underline decoration-green-500">
                {data['topic']}
            </h1>
            <p class="text-xl text-gray-400 mb-8 leading-tight italic">"{data['insight']}"</p>
            <div class="bg-black/80 p-4 border border-white/5 rounded text-[10px] text-gray-500">
                <p class="mb-2 text-green-500 font-bold tracking-widest">AGENT_LOGS:</p>
                {"".join([f"<p class='mb-1'>> {t}</p>" for t in data['thoughts']])}
            </div>
            <div class="mt-10 text-center text-[9px] text-gray-700 uppercase tracking-[0.5em]">
                autonomous-portfolio-2026.live
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html)
    print("SUCCESS!")

if __name__ == "__main__":
    run_agent()
