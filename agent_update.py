import os
import requests
import json
import re
import shutil
from datetime import datetime

# ───────────────────────────────────────────────────────────────────────
# AUTOMATED ADSENSE COMPLIANCE ENGINE (Zero-Token Architecture)
# ───────────────────────────────────────────────────────────────────────

def generate_seo_and_compliance():
    """
    Automatically generates robots.txt, sitemap.xml, and the matching
    Glass-morphic subpages required to clear the Google AdSense review.
    """
    date_now = datetime.now().strftime("%d %b %Y")
    iso_date = datetime.now().strftime("%Y-%m-%d")

    # 1. Generate robots.txt
    robots_content = """User-agent: *
Allow: /
Disallow: /private/

Sitemap: https://autonomous-portfolio-2026.live/sitemap.xml
"""
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots_content)
    print("✓ robots.txt generated.")

    # 2. Generate sitemap.xml
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://autonomous-portfolio-2026.live/</loc>
        <lastmod>{iso_date}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://autonomous-portfolio-2026.live/about.html</loc>
        <lastmod>{iso_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://autonomous-portfolio-2026.live/privacy.html</loc>
        <lastmod>{iso_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    <url>
        <loc>https://autonomous-portfolio-2026.live/terms.html</loc>
        <lastmod>{iso_date}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
</urlset>
"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print("✓ sitemap.xml generated.")

    # Shared UI Header Template matching your Glass Style Layout
    html_head = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { background: #06070f; color: #f1f5f9; font-family: 'Space Grotesk', sans-serif; margin: 0; line-height: 1.7; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.06); backdrop-filter: blur(24px); }
        .bg-grid { background-image: linear-gradient(rgba(255, 255, 255, 0.01) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.01) 1px, transparent 1px); background-size: 60px 60px; }
    </style>
</head>"""

    # 3. Compile privacy.html
    privacy_html = html_head + f"""
<body class="min-h-screen bg-grid p-6 md:p-12 flex items-center justify-center">
    <div class="max-w-3xl w-full glass rounded-3xl p-8 md:p-12 border border-slate-800">
        <a href="/" class="text-xs mono text-red-400 uppercase tracking-widest hover:text-red-300 transition">← Return to Main Terminal</a>
        <h1 class="text-3xl font-bold mt-6 mb-2 text-white tracking-tight">Privacy Policy</h1>
        <p class="text-xs mono text-slate-500 mb-8">System Identity: SECURE-NODE-2026 | Verified: {date_now}</p>
        
        <div class="space-y-6 text-slate-400 text-sm font-light">
            <p>At Autonomous Lab 2026, accessible via <span class="mono text-slate-200">https://autonomous-portfolio-2026.live/</span>, protecting the digital footprint of our global researchers is highly prioritized.</p>
            <h2 class="text-lg font-semibold text-white mt-6">Cookie Infrastructure & Google AdSense</h2>
            <p>Google, as a third-party advertisement deployment entity, serves programmatic contextual marketing fields across this terminal infrastructure. Google uses specialized DART cookies to align advertisements based on historical navigation indicators across external decentralized domains.</p>
            <h2 class="text-lg font-semibold text-white mt-6">Data Architecture & Log Output</h2>
            <p>Our autonomous pipelines store baseline automated server logging datasets. These records include anonymized IP streams, browser identifiers, Internet Service Provider records, and diagnostic timestamp arrays. This information is processed strictly for systemic diagnostic monitoring.</p>
        </div>
    </div>
</body>
</html>"""

    # 4. Compile terms.html
    terms_html = html_head + f"""
<body class="min-h-screen bg-grid p-6 md:p-12 flex items-center justify-center">
    <div class="max-w-3xl w-full glass rounded-3xl p-8 md:p-12 border border-slate-800">
        <a href="/" class="text-xs mono text-red-400 uppercase tracking-widest hover:text-red-300 transition">← Return to Main Terminal</a>
        <h1 class="text-3xl font-bold mt-6 mb-2 text-white tracking-tight">Terms of Service</h1>
        <p class="text-xs mono text-slate-500 mb-8">System Identity: LEGAL-REGULATORY-NODE | Verified: {date_now}</p>
        
        <div class="space-y-6 text-slate-400 text-sm font-light">
            <h2 class="text-lg font-semibold text-white">1. Autonomous Content Limitations</h2>
            <p>All systemic data vectors, risk evaluations, and telemetry scores compiled across this platform are generated via automated algorithmic sequences. This data does not contain human execution models and is made available solely for security parsing and historical analysis.</p>
            <h2 class="text-lg font-semibold text-white mt-6">2. Absolute Non-Advisory Disclaimer</h2>
            <p>The information displayed across this intelligence system does not constitute transactional, trading, legal, or financial advice. Users execute protocol engagements, smart contract updates, or capital allocation models entirely at their own risk.</p>
        </div>
    </div>
</body>
</html>"""

    # 5. Compile about.html (The System Architecture Showpiece)
    about_html = html_head + f"""
<body class="min-h-screen bg-grid p-6 md:p-12 flex items-center justify-center">
    <div class="max-w-3xl w-full glass rounded-3xl p-8 md:p-12 border border-slate-800">
        <a href="/" class="text-xs mono text-red-400 uppercase tracking-widest hover:text-red-300 transition">← Return to Main Terminal</a>
        <h1 class="text-3xl font-bold mt-6 mb-2 text-white tracking-tight">System Architecture</h1>
        <p class="text-xs mono text-slate-500 mb-8">System Identity: AEGIS-NODE-LOGIC | Status: Operational</p>
        
        <div class="space-y-6 text-slate-400 text-sm font-light">
            <p>Autonomous Lab 2026 is an experimental, non-custodial decentralized telemetry cluster tracking threat vectors, zero-day vulnerabilities, and market sentiment models throughout the Web3 ecosystem.</p>
            
            <h2 class="text-lg font-semibold text-white mt-6">Automated Pipeline Telemetry</h2>
            <pre class="bg-slate-950/80 p-5 rounded-2xl font-mono text-xs text-emerald-400 border border-slate-800/80 overflow-x-auto leading-relaxed">
[ RSS STREAM INGESTION ] ──> (Threat Context Extraction)
                                   │
[ COINGECKO API NODE ]   ──> (Quant Asset Valuation)
                                   │
                                   ▼
[ NEURAL ENGINE PROCESSING ] ──> (Llama & Gemini Compilation)
                                   │
                                   ▼
[ GITHUB ACTIONS RUNNER ]   ───> [ AUTONOMOUS PRODUCTION BUILD ]
            </pre>
            <p>This workspace operates as a completely headless deployment asset. It triggers micro-compilation blocks every 120 minutes to maintain analytical integrity over network changes without manual overhead.</p>
        </div>
    </div>
</body>
</html>"""

    # Write compliance documents seamlessly into repository root
    with open("privacy.html", "w", encoding="utf-8") as f: f.write(privacy_html)
    with open("terms.html", "w", encoding="utf-8") as f: f.write(terms_html)
    with open("about.html", "w", encoding="utf-8") as f: f.write(about_html)
    print("✓ AdSense Legal Multi-Pages successfully linked and written.")

# ───────────────────────────────────────────────────────────────────────
# MAIN PIPELINE OVERWRITE ADJUSTMENT
# ───────────────────────────────────────────────────────────────────────

# Ensure this exact execution block is wired into your main loop:
if __name__ == "__main__":
    # ... Your existing logic that fetches data, formats tokens, and generates variables ...
    
    # Build and write dynamic HTML
    html = build_html(data, final_history, date_str, price_context, sentiment_mood, sentiment_score, trending_tokens, btc, eth, sol)

    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html written successfully.")
        
        # TRIGGER THE AUTOMATED SEO & COMPLIANCE STACK HERE
        generate_seo_and_compliance()
        
    except Exception as e:
        print(f"Write failed: {e}")
        if os.path.exists("index.html.bak"):
            shutil.copy("index.html.bak", "index.html")
