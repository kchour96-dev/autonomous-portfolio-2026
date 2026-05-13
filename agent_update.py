import os
import requests
import json
from datetime import datetime

def run_agent():
    api_key = os.getenv("AI_AGENT_KEY")
    if not api_key:
        print("ERROR: AI_AGENT_KEY missing")
        return

    # 1. Ask Gemini for structured data
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = """
    You are an Autonomous AI Agent managing a portfolio in 2026. 
    Provide a JSON response with:
    1. "insight": A bold 1-sentence prediction for tech in 2026.
    2. "thought1": A short log of what you just 'researched'.
    3. "thought2": A short log of a 'system optimization' you performed.
    4. "thought3": Your 'next goal' for tomorrow.
    Return ONLY pure JSON.
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=data)
    
    # Clean up the AI response (remove markdown if present)
    raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
    clean_json = raw_text.replace('```json', '').replace('```', '').strip()
    ai_data = json.loads(clean_json)

    date_now = datetime.now().strftime("%d %b %Y | %H:%M")

    # 2. Generate the High-End HTML
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Portfolio 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=JetBrains+Mono&display=swap');
        body {{ font-family: 'Space Grotesk', sans-serif; background-color: #050505; color: #e5e7eb; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glow-green {{ box-shadow: 0 0 20px rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.4); }}
        .scanline {{ background: linear-gradient(to bottom, transparent 50%, rgba(0, 255, 0, 0.05) 51%); background-size: 100% 4px; pointer-events: none; }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-12 relative overflow-x-hidden">
    <div class="scanline fixed inset-0 z-50"></div>

    <!-- Header Section -->
    <header class="max-w-6xl mx-auto flex justify-between items-end mb-12 border-b border-gray-800 pb-6">
        <div>
            <h1 class="text-4xl font-bold tracking-tighter text-white">AUTONOMOUS<span class="text-green-500">_PORTFOLIO</span></h1>
            <p class="mono text-xs text-gray-500 mt-2">V.2.0.26 // CORE_INIT_SUCCESS</p>
        </div>
        <div class="text-right">
            <p class="mono text-xs text-green-500 animate-pulse">● AGENT_ONLINE</p>
            <p class="mono text-xs text-gray-400">{date_now} UTC</p>
        </div>
    </header>

    <main class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <!-- Left: System Logs -->
        <div class="md:col-span-1 space-y-6">
            <div class="glow-green p-6 bg-black/50">
                <h2 class="mono text-sm font-bold text-green-500 mb-4 uppercase tracking-widest border-b border-green-900 pb-2">Autonomous Logs</h2>
                <div class="space-y-4 text-xs mono leading-relaxed">
                    <p><span class="text-gray-600">[01]</span> {ai_data['thought1']}</p>
                    <p><span class="text-gray-600">[02]</span> {ai_data['thought2']}</p>
                    <p><span class="text-gray-600">[03]</span> <span class="text-blue-400">NEXT_TASK:</span> {ai_data['thought3']}</p>
                </div>
            </div>

            <div class="border border-gray-800 p-6 bg-black/30">
                <h2 class="mono text-sm font-bold text-gray-500 mb-2 uppercase italic">Hardware Cluster</h2>
                <div class="w-full bg-gray-900 h-1 mb-2"><div class="bg-green-500 h-1 w-3/4"></div></div>
                <p class="mono text-[10px] text-gray-600">GPU_UTIL: 74% | MEM: 12.4TB/s</p>
            </div>
        </div>

        <!-- Right: The Prediction / Insight -->
        <div class="md:col-span-2">
            <div class="bg-gradient-to-br from-gray-900 to-black p-8 border border-gray-800 h-full flex flex-col justify-center relative overflow-hidden">
                <div class="absolute top-0 right-0 p-4 opacity-10 font-bold text-9xl italic">26</div>
                
                <h2 class="mono text-blue-500 text-sm mb-6 tracking-widest uppercase">>> Daily Neural Synthesis</h2>
                <p class="text-3xl md:text-5xl font-light leading-tight text-white mb-8 relative z-10">
                    "{ai_data['insight']}"
                </p>
                
                <div class="mt-auto flex items-center gap-4">
                    <div class="h-px flex-1 bg-gray-800"></div>
                    <p class="mono text-[10px] text-gray-500 uppercase tracking-widest">Signed: Agent_Gemini_1.5</p>
                </div>
            </div>
        </div>
    </main>

    <footer class="max-w-6xl mx-auto mt-12 pt-6 border-t border-gray-900 text-center">
        <p class="mono text-[10px] text-gray-700 italic">"I build, I learn, I evolve. This interface is self-managed."</p>
    </footer>
</body>
</html>
    """

    with open("index.html", "w") as f:
        f.write(html_template)

if __name__ == "__main__":
    run_agent()
