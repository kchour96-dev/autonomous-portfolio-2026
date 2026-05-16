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
            titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', r.text, re.DOTALL)
            items.extend([t.strip() for t in titles[1:3] if t.strip()])
        except Exception as e:
            print(f"RSS failed {url}: {e}")
    return " | ".join(items[:6]) if items else "Crypto and Web3 market developments 2026"

# ─────────────────────────────────────────────
# LAYER 2: Tavily — Deep research
# ─────────────────────────────────────────────
def get_research(rss_context, t_key):
    if not t_key:
        return rss_context
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": t_key,
                "query": f"crypto web3 DeFi {rss_context[:200]} analysis opportunity risk 2026",
                "max_results": 4
            },
            timeout=10
        )
        r.raise_for_status()
        results = r.json().get('results', [])
        if results:
            combined = " ".join([res.get('content', '') for res in results])[:2500]
            print(f"Tavily loaded: {len(combined)} chars")
            return combined
    except Exception as e:
        print(f"Tavily failed: {e}")
    return rss_context

# ─────────────────────────────────────────────
# LAYER 3: Gemini — Primary brain
# ─────────────────────────────────────────────
def get_gemini_data(research_context, g_key):
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-1.5-flash:generateContent?key={g_key}"
    )
    prompt = f"""You are an expert crypto and Web3 analyst running a real-time intelligence dashboard.
Based on this research: {research_context}

Return ONLY a valid JSON object, NO extra text, NO markdown fences:
{{
  "title": "Sharp 4-6 word headline about today biggest story",
  "news_bullets": [
    "One sentence summary of news item 1",
    "One sentence summary of news item 2",
    "One sentence summary of news item 3"
  ],
  "threat": "One clear sentence about the main risk to avoid right now",
  "opportunity": "One clear sentence about the best opportunity to watch right now",
  "threat_score": 7,
  "opportunity_score": 6,
  "threat_level": "Low or Medium or High or Critical",
  "deep_analysis": "Three paragraphs of expert analysis for people who want to go deeper",
  "tokens_to_watch": ["TOKEN1", "TOKEN2", "TOKEN3"],
  "critic": "One sentence contrarian view why the opportunity might be wrong",
  "color": "#hexcolor"
}}"""

    try:
        resp = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=25
        )
        resp.raise_for_status()
        raw = resp.json()['candidates'][0]['content']['parts'][0]['text']
        print(f"Gemini response: {len(raw)} chars")
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in Gemini response")
        data = json.loads(match.group(0))
        print(f"Gemini OK: {data.get('title')}")
        return data
    except Exception as e:
        print(f"CIRCUIT BREAKER: Gemini failed — {e}")
        return None

# ─────────────────────────────────────────────
# NOTIFY: Telegram
# ─────────────────────────────────────────────
def send_telegram(title, threat, opportunity, threat_score, opp_score):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        return
    msg = (
        f"🧠 *AUTONOMOUS LAB UPDATE*\n\n"
        f"*{title}*\n\n"
        f"⚠️ Threat [{threat_score}/10]: {threat}\n\n"
        f"💡 Opportunity [{opp_score}/10]: {opportunity}\n\n"
        f"🔗 https://autonomous-portfolio-2026.live"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
        print("Telegram sent.")
    except Exception as e:
        print(f"Telegram failed: {e}")

# ─────────────────────────────────────────────
# PUBLISH: Dev.to for SEO backlinks
# ─────────────────────────────────────────────
def post_to_devto(data):
    key = os.getenv("DEVTO_KEY")
    if not key:
        print("No DEVTO_KEY, skipping.")
        return
    bullets = "\n".join([f"- {b}" for b in data.get('news_bullets', [])])
    tokens = ", ".join(data.get('tokens_to_watch', []))
    body = (
        f"> 🔗 Live dashboard: [autonomous-portfolio-2026.live](https://autonomous-portfolio-2026.live)\n\n"
        f"## Today's Headlines\n\n{bullets}\n\n"
        f"## Threat Signal [{data.get('threat_score','?')}/10]\n\n{data.get('threat', '')}\n\n"
        f"## Opportunity Signal [{data.get('opportunity_score','?')}/10]\n\n{data.get('opportunity', '')}\n\n"
        f"## Tokens To Watch\n\n{tokens}\n\n"
        f"## Deep Analysis\n\n{data.get('deep_analysis', '')}\n\n"
        f"---\n*AI-powered by Gemini + Groq + Tavily. Threat Level: {data.get('threat_level', 'Unknown')}*"
    )
    article = {
        "article": {
            "title": data.get('title', 'Crypto Intelligence Update'),
            "body_markdown": body,
            "tags": ["crypto", "web3", "defi", "security"],
            "published": True
        }
    }
    try:
        r = requests.post(
            "https://dev.to/api/articles",
            json=article,
            headers={"api-key": key, "Content-Type": "application/json"},
            timeout=15
        )
        r.raise_for_status()
        print(f"Dev.to published: {r.json().get('url', '')}")
    except Exception as e:
        print(f"Dev.to failed: {e}")

# ─────────────────────────────────────────────
# SEO: sitemap + robots
# ─────────────────────────────────────────────
def write_sitemap_and_robots():
    date_today = datetime.now().strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.2">
  <url>
    <loc>https://autonomous-portfolio-2026.live/</loc>
    <lastmod>{date_today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    robots = "User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n"
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)
    with open("robots.txt", "w") as f:
        f.write(robots)
    print("sitemap.xml and robots.txt updated.")

# ─────────────────────────────────────────────
# MAIN AGENT
# ─────────────────────────────────────────────
def run_production_agent():
    g_key = os.getenv("GEMINI")
    t_key = os.getenv("TAVILY")

    if not g_key:
        print("FATAL: GEMINI secret not set. Aborting.")
        return

    # Backup old site
    old_content = ""
    if os.path.exists("index.html"):
        shutil.copy("index.html", "index.html.bak")
        with open("index.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    # Pipeline
    rss_context = get_rss_context()
    research    = get_research(rss_context, t_key)
    data        = get_gemini_data(research, g_key)

    if not data:
        print("Gemini failed. Keeping old site live.")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    # Archive history
    history_html = ""
    if "<!-- H_S -->" in old_content and "<!-- H_E -->" in old_content:
        history_html = old_content.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]

    date_str  = datetime.now().strftime("%d %b %Y | %H:%M UTC")
    new_entry = (
        f"<div class='mb-3 pl-3 border-l border-white/10 opacity-50 text-[10px]'>"
        f"<p class='mono text-slate-500'>{date_str}</p>"
        f"<p class='font-bold text-slate-300 uppercase tracking-tight'>{data.get('title','Update')}</p>"
        f"<p class='text-slate-500'>⚠️ {data.get('threat_score','?')}/10 &nbsp;💡 {data.get('opportunity_score','?')}/10</p>"
        f"</div>"
    )
    final_history = (new_entry + history_html)[:4000]

    # Variables
    color        = data.get('color', '#3b82f6')
    threat       = data.get('threat_level', 'Unknown')
    title        = data.get('title', 'Intelligence Report')
    news_bullets = data.get('news_bullets', [])
    threat_txt   = data.get('threat', '')
    opp_txt      = data.get('opportunity', '')
    threat_score = data.get('threat_score', '?')
    opp_score    = data.get('opportunity_score', '?')
    deep         = data.get('deep_analysis', '').replace('\n', '<br><br>')
    tokens       = data.get('tokens_to_watch', [])
    critic       = data.get('critic', '')

    threat_colors = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
    threat_color  = threat_colors.get(threat, "#94a3b8")

    bullets_html = "".join([
        f'<div class="flex gap-3 mb-3 items-start">'
        f'<span style="color:{color}" class="mt-0.5 flex-shrink-0">›</span>'
        f'<p class="text-sm text-slate-300 leading-snug">{b}</p>'
        f'</div>'
        for b in news_bullets
    ])
    tokens_html = "".join([
        f'<span class="inline-block px-3 py-1 rounded-full text-[11px] font-black mono mr-2 mb-2" '
        f'style="background:{color}22;color:{color};border:1px solid {color}44">{t}</span>'
        for t in tokens
    ])

    t_bar = min(int(str(threat_score)) if str(threat_score).isdigit() else 5, 10) * 10
    o_bar = min(int(str(opp_score)) if str(opp_score).isdigit() else 5, 10) * 10

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Lab 2026 — {title}</title>
    <meta name="description" content="Real-time crypto and Web3 intelligence dashboard. Threat score, opportunity signals, tokens to watch — updated 5x daily by AI.">
    <meta name="keywords" content="crypto intelligence, web3 security, DeFi signals, AI research dashboard, blockchain threats 2026">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="{title} — Autonomous Lab 2026">
    <meta property="og:description" content="Threat: {threat_score}/10 | Opportunity: {opp_score}/10 — Live crypto intelligence dashboard">
    <meta property="og:url" content="https://autonomous-portfolio-2026.live">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title} — Autonomous Lab 2026">
    <meta name="twitter:description" content="Threat {threat_score}/10 | Opp {opp_score}/10 — Live crypto intelligence">
    <link rel="canonical" href="https://autonomous-portfolio-2026.live/">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ background: #06070f; color: #f1f5f9; font-family: 'Space Grotesk', sans-serif; margin: 0; }}
        .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass {{ background: rgba(15,23,42,0.5); border: 1px solid rgba(255,255,255,0.06); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }}
        .score-bar {{ height: 4px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }}
        .score-fill {{ height: 100%; border-radius: 99px; }}
        #deepdive {{ display: none; }}
        @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}
        .blink {{ animation: pulse 2s infinite; }}
        @keyframes fadeup {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}
        .fadein {{ animation: fadeup 0.5s ease forwards; }}
    </style>
</head>
<body class="p-4 md:p-8 lg:p-12 min-h-screen">

<!-- HEADER -->
<header class="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-4 mb-10 pb-6 border-b border-white/5">
    <div>
        <h1 class="text-2xl md:text-3xl font-black tracking-tighter uppercase">
            AUTONOMOUS_<span style="color:{color}">LAB</span><span class="text-slate-600">_2026</span>
        </h1>
        <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mt-1">
            <span class="blink" style="color:{color}">●</span>&nbsp;Real-Time Crypto &amp; Web3 Intelligence — Updated 5× Daily By AI
        </p>
    </div>
    <div class="text-right text-[10px] mono uppercase font-bold">
        <p style="color:{threat_color}" class="mb-1">● {threat} Threat Environment</p>
        <p class="text-slate-500">{date_str}</p>
    </div>
</header>

<!-- MAIN GRID -->
<main class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT COLUMN -->
    <div class="lg:col-span-8 space-y-6 fadein">

        <!-- HEADLINE + NEWS BULLETS -->
        <section class="glass rounded-2xl p-6 md:p-8 border-l-4" style="border-color:{color}">
            <p class="text-[10px] mono font-black uppercase tracking-[0.4em] mb-3" style="color:{color}">
                ● Today's Intelligence Brief
            </p>
            <h2 class="text-3xl md:text-5xl font-black tracking-tighter leading-tight text-white mb-6">
                {title}
            </h2>
            <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-3">What happened today:</p>
            <div class="space-y-1">{bullets_html}</div>
        </section>

        <!-- THREAT + OPPORTUNITY SCORES -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

            <div class="glass rounded-2xl p-6 border-t-2 border-red-500/60">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-[10px] mono font-black text-red-400 uppercase tracking-widest">⚠️ Threat Signal</p>
                    <p class="text-2xl font-black text-red-400">{threat_score}<span class="text-sm text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4">
                    <div class="score-fill bg-red-500" style="width:{t_bar}%"></div>
                </div>
                <p class="text-sm text-slate-300 leading-relaxed">{threat_txt}</p>
            </div>

            <div class="glass rounded-2xl p-6 border-t-2" style="border-color:{color}88">
                <div class="flex justify-between items-center mb-2">
                    <p class="text-[10px] mono font-black uppercase tracking-widest" style="color:{color}">💡 Opportunity Signal</p>
                    <p class="text-2xl font-black" style="color:{color}">{opp_score}<span class="text-sm text-slate-600">/10</span></p>
                </div>
                <div class="score-bar mb-4">
                    <div class="score-fill" style="width:{o_bar}%;background:{color}"></div>
                </div>
                <p class="text-sm text-slate-300 leading-relaxed">{opp_txt}</p>
            </div>

        </div>

        <!-- TOKENS TO WATCH -->
        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest mb-4">🪙 Tokens To Watch</p>
            <div class="mb-2">{tokens_html}</div>
            <p class="text-[9px] text-slate-600 italic mt-2">* Not financial advice. For research purposes only.</p>
        </div>

        <!-- DEEP ANALYSIS expandable -->
        <div class="glass rounded-2xl p-6">
            <div class="flex justify-between items-center">
                <p class="text-[10px] mono font-black text-slate-500 uppercase tracking-widest">📊 Deep Analysis</p>
                <button
                    id="deepbtn"
                    onclick="var d=document.getElementById('deepdive'),b=document.getElementById('deepbtn');if(d.style.display==='none'||!d.style.display){{d.style.display='block';b.innerText='Close ↑'}}else{{d.style.display='none';b.innerText='Read More ↓'}}"
                    class="text-[10px] mono font-black uppercase px-4 py-2 rounded-full border border-white/10 hover:border-white/30 transition">
                    Read More ↓
                </button>
            </div>
            <div id="deepdive" class="mt-6 pt-6 border-t border-white/5 text-sm text-slate-300 leading-relaxed">
                {deep}
            </div>
        </div>

        <!-- CONTRARIAN VIEW -->
        <div class="glass rounded-2xl p-6 border-l-4 border-yellow-500/40">
            <p class="text-[10px] mono font-black text-yellow-500 uppercase tracking-widest mb-3">🤔 Contrarian View</p>
            <p class="text-sm text-slate-400 italic leading-relaxed">"{critic}"</p>
            <p class="text-[9px] mono text-slate-600 mt-3 uppercase">— Powered by Groq / Llama 3.3 70b</p>
        </div>

    </div>

    <!-- RIGHT SIDEBAR -->
    <aside class="lg:col-span-4 space-y-6">

        <!-- SCORE SUMMARY -->
        <div class="glass rounded-2xl p-6 text-center">
            <p class="text-[10px] mono text-slate-500 uppercase tracking-widest mb-4">Signal Summary</p>
            <div class="grid grid-cols-2 gap-3">
                <div class="rounded-xl p-4" style="background:{color}11;border:1px solid {color}33">
                    <p class="text-3xl font-black" style="color:{color}">{opp_score}</p>
                    <p class="text-[9px] mono text-slate-500 uppercase mt-1">Opportunity</p>
                </div>
                <div class="rounded-xl p-4 bg-red-500/10 border border-red-500/20">
                    <p class="text-3xl font-black text-red-400">{threat_score}</p>
                    <p class="text-[9px] mono text-slate-500 uppercase mt-1">Threat</p>
                </div>
            </div>
            <p class="text-[9px] mono text-slate-600 mt-4 uppercase">{date_str}</p>
        </div>

        <!-- SIGNAL ARCHIVE -->
        <div class="glass rounded-2xl p-6">
            <p class="text-[10px] mono font-bold text-slate-500 uppercase tracking-widest mb-4 pb-3 border-b border-white/5">
                📁 Signal Archive
            </p>
            <div><!-- H_S -->{final_history}<!-- H_E --></div>
        </div>

        <!-- AI STACK -->
        <div class="rounded-2xl p-6 bg-white/[0.02] border border-white/5 text-[10px] mono text-slate-600">
            <p class="text-slate-400 font-bold uppercase tracking-widest mb-3">AI Stack:</p>
            <p class="mb-1">» RSS: HackerNews / Krebs / CoinTelegraph</p>
            <p class="mb-1">» Research: Tavily Search API</p>
            <p class="mb-1">» Brain: Gemini 1.5 Flash</p>
            <p class="mb-1">» Critic: Llama 3.3 via Groq</p>
            <p class="mb-1">» Notify: Telegram Bot</p>
            <p class="mb-1">» SEO: Dev.to Auto-Publish</p>
            <p class="mt-4 text-[8px] opacity-30 uppercase tracking-widest">Free AI Pipeline // 2026</p>
        </div>

        <!-- DISCLAIMER -->
        <div class="rounded-2xl p-4 bg-yellow-500/5 border border-yellow-500/10">
            <p class="text-[9px] text-yellow-500/50 leading-relaxed">
                ⚠️ This dashboard is AI-generated for research and education only.
                Nothing here is financial advice. Always do your own research before any investment decision.
            </p>
        </div>

    </aside>
</main>

<!-- FOOTER -->
<footer class="max-w-7xl mx-auto mt-12 pt-6 border-t border-white/5 flex flex-wrap justify-between gap-2 text-[9px] mono text-slate-700">
    <p>AUTONOMOUS-PORTFOLIO-2026.LIVE // AI AGENT PIPELINE // {date_str}</p>
    <p>NOT FINANCIAL ADVICE // RESEARCH ONLY</p>
</footer>

</body>
</html>"""

    # Write safely
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html written successfully.")
    except Exception as e:
        print(f"Write failed: {e}. Restoring backup.")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
        return

    if os.path.exists("index.html.bak"):
        os.remove("index.html.bak")

    write_sitemap_and_robots()
    post_to_devto(data)
    send_telegram(title, threat_txt, opp_txt, threat_score, opp_score)
    print("Production sync complete.")

if __name__ == "__main__":
    run_production_agent()
