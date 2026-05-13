import os
import requests
import json
from datetime import datetime

def run_agent():
    # Get Keys
    gemini_key = os.getenv("AI_AGENT_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    print("Checking keys...")
    if not gemini_key:
        print("ERROR: AI_AGENT_KEY is missing!")
        return

    # --- STEP 1: RESEARCH (TAVILY) ---
    context = "General tech trends for 2026"
    if tavily_key:
        print("Searching the web with Tavily...")
        try:
            r = requests.post("https://api.tavily.com/search", json={
                "api_key": tavily_key,
                "query": "hottest tech trends 2026 robotics ai space",
                "max_results": 2
            }, timeout=10)
            if r.status_code == 200:
                results = r.json().get('results', [])
                context = "\n".join([f"{res['title']}: {res['content']}" for res in results])
                print("Search successful.")
            else:
                print(f"Search API returned error {r.status_code}. Using backup context.")
        except Exception as e:
            print(f"Search failed: {e}. Using backup context.")
    else:
        print("TAVILY_API_KEY missing. Skipping search step.")

    # --- STEP 2: BRAIN (GEMINI) ---
    print("Talking to Gemini...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    prompt = f"""
    Based on this research: {context}
    You are a 2026 AI Agent. Create a website update.
    Return ONLY a JSON object: 
    {{"topic": "Name", "insight": "2 sentences", "thoughts": ["step 1", "step 2", "step 3"]}}
    """
    
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        # Clean JSON
        clean_text = raw_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
    except Exception as e:
        print(f"Gemini failed: {e}. Using default data.")
        data = {
            "topic": "Autonomous Systems",
            "insight": "AI agents are now managing 90% of digital infrastructure.",
            "thoughts": ["Analyzing nodes", "Optimizing latency", "Deploying update"]
        }

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
        <div class="max-w-2xl mx-auto border border-green-900 p-8 rounded-lg bg-gray-900/50">
            <div class="flex justify-between text-[10px] text-green-500 mb-10">
                <span>STATUS: ONLINE</span>
                <span>{date_str}</span>
            </div>
            <h1 class="text-4xl font-bold mb-4 text-white uppercase tracking-tighter italic underline decoration-green-500">
                {data['topic']}
            </h1>
            <p class="text-xl text-gray-400 mb-8 italic">"{data['insight']}"</p>
            <div class="bg-black/50 p-4 border border-white/5 rounded text-xs text-gray-500">
                <p class="mb-2 text-blue-500 uppercase font-bold">Agent Logs:</p>
                {"".join([f"<p>> {t}</p>" for t in data['thoughts']])}
            </div>
            <div class="mt-10 text-center text-[10px] text-gray-700 uppercase tracking-widest">
                autonomous-portfolio-2026.live // v1.2
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w") as f:
        f.write(html)
    print("DONE! Website updated.")

if __name__ == "__main__":
    run_agent()
