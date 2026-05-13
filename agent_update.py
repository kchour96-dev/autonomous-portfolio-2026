import os
import openai
from datetime import datetime

# 1. Setup the AI (Using OpenAI)
client = openai.OpenAI(api_key=os.getenv("AI_AGENT_KEY"))

def run_agent():
    print("Agent waking up...")
    
    # 2. The AI researches and writes a "2026 Trend Report"
    prompt = "You are an autonomous AI from the year 2026. Write a short, 2-sentence prediction about AI agents for today. Be futuristic and professional."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    prediction = response.choices[0].message.content
    date_str = datetime.now().strftime("%B %d, %Y")

    # 3. The AI creates the new HTML for your website
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Portfolio 2026</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-black text-white font-sans p-10">
    <div class="max-w-3xl mx-auto border border-green-500 p-8 shadow-2xl shadow-green-500/20">
        <h1 class="text-3xl font-bold text-green-400 mb-4 tracking-tighter">SYSTEM: AUTONOMOUS PORTFOLIO 2026</h1>
        <p class="text-sm text-gray-500 mb-8 font-mono">Last Autonomous Update: {date_str}</p>
        
        <div class="mb-10">
            <h2 class="text-xl text-blue-400 font-mono mb-2">>> TODAY'S AI AGENT INSIGHT:</h2>
            <p class="text-2xl leading-relaxed italic text-gray-200">"{prediction}"</p>
        </div>

        <div class="grid grid-cols-2 gap-4 text-xs font-mono text-green-800">
            <div class="border border-green-900 p-2">AGENT_STATUS: ACTIVE</div>
            <div class="border border-green-900 p-2">CONNECTION: ENCRYPTED</div>
            <div class="border border-green-900 p-2">CREATIVITY_LOG: OPTIMIZED</div>
            <div class="border border-green-900 p-2">MODE: SELF_EVOLVING</div>
        </div>
    </div>
</body>
</html>
"""
    
    # 4. Save the file
    with open("index.html", "w") as f:
        f.write(html_content)
    print("Agent successfully updated index.html")

if __name__ == "__main__":
    run_agent()