import os
import requests
import json
from datetime import datetime

def run_advanced_agent():
    gemini_key = os.getenv("AI_AGENT_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not gemini_key or not tavily_key:
        print(f"ERROR: Missing Keys! Gemini: {'OK' if gemini_key else 'MISSING'}, Tavily: {'OK' if tavily_key else 'MISSING'}")
        exit(1)

    print("Step 1: Agent 'Researcher' is browsing the web...")
    try:
        search_url = "https://api.tavily.com/search"
        search_data = {
            "api_key": tavily_key,
            "query": "top tech news breakthroughs for 2026",
            "search_depth": "basic",
            "max_results": 3
        }
        search_response = requests.post(search_url, json=search_data)
        search_results = search_response.json().get('results', [])
        
        context = ""
        for res in search_results:
            context += f"Source: {res['title']} - {res['content']}\n"
    except Exception as e:
        print(f"Search failed, using default context. Error: {e}")
        context = "Focus on general AI and robotics advancements for 2026."

    print("Step 2: Agent 'Architect' is synthesizing data...")
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Based on this research: {context}
    Create a 2026 tech forecast. Return ONLY a JSON object with:
    "hot_topic", "analysis", "source_url", "thought_log" (list of 3 strings).
    """
    
    try:
        gemini_response = requests.post(gemini_url, json={"contents": [{"parts": [{"text": prompt}]}]})
        raw_text = gemini_response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Clean the AI response to ensure it is valid JSON
        clean_json = raw_text.strip()
        if clean_json.startswith("```json"): clean_json = clean_json[7:]
        if clean_json.endswith("```"): clean_json = clean_json[:-3]
        
        ai_data = json.loads(clean_json.strip())
    except Exception as e:
        print(f"AI Synthesis failed. Error: {e}. Raw response: {raw_text if 'raw_text' in locals() else 'None'}")
        exit(1)

    # --- GENERATE HTML ---
    date_str = datetime.now().strftime("%B %d, %Y")
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>Autonomous 2026 | {ai_data.get('hot_topic', 'Update')}</title>
</head>
<body class="bg-[#050505] text-gray-100 min-h-screen p-6 flex items-center justify-center">
    <div class="max-w-4xl w-full border border-white/10 bg-white/5 p-8 rounded-3xl backdrop-blur-xl shadow-2xl">
        <div class="flex justify-between items-center mb-10 text-[10px] font-mono text-gray-500 uppercase tracking-widest">
            <span class="text-green-500 animate-pulse">● Multi-Agent Flow Active</span>
            <span>{date_str}</span>
        </div>
        <h1 class="text-5xl md:text-7xl font-black mb-6 tracking-tighter text-white italic underline decoration-green-500">
            {ai_data.get('hot_topic', 'SYSTEM UPDATE').upper()}
        </h1>
        <p class="text-2xl text-gray-400 mb-10 leading-tight">"{ai_data.get('analysis', 'Processing daily trends...')}"</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="p-5 border border-white/5 bg-black/40 rounded-2xl">
                <p class="text-[10px] text-green-500 uppercase mb-4 font-bold tracking-widest">Internal Thought Process</p>
                <ul class="text-xs space-y-2 font-mono text-gray-400">
                    { "".join([f"<li>> {t}</li>" for t in ai_data.get('thought_log', [])]) }
                </ul>
            </div>
            <div class="p-5 border border-white/5 bg-black/40 rounded-2xl">
                <p class="text-[10px] text-blue-500 uppercase mb-4 font-bold tracking-widest">Primary Research Link</p>
                <a href="{ai_data.get('source_url', '#')}" target="_blank" class="text-xs text-blue-400 break-all hover:text-white transition">
                    {ai_data.get('source_url', 'No Source Found')}
                </a>
            </div>
        </div>
        <div class="text-[10px] text-gray-700 text-center uppercase tracking-[0.3em]">Autonomous Portfolio 2026 // Built by AI</div>
    </div>
</body>
</html>
    """
    
    with open("index.html", "w") as f:
        f.write(html_content)
    print("Update successful!")

if __name__ == "__main__":
    run_advanced_agent()
