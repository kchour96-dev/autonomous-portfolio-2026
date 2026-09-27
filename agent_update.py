import os
import requests
import json
import re
import shutil
from datetime import datetime

def call_gemini(prompt, g_key, model="gemini-2.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text']

def call_groq(prompt, key, model="llama-3.3-70b-versatile"):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a JSON API for advanced AI Prompt Engineering. Return ONLY raw, valid JSON with properly escaped newlines (\\n). No markdown wrappers."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2500,
        "temperature": 0.8
    }
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    raw = resp.json()['choices'][0]['message']['content']
    return re.sub(r'[\x00-\x1f\x7f]', ' ', raw).replace('```json', '').replace('```', '').strip()

def generate_prompts(g_key, groq_key):
    prompt = """Generate 3 masterclass AI prompts across these categories:
1. VISUAL: A cinematic Midjourney v6.1 prompt for gaming/fantasy/sci-fi art (include 4 layers: subject, environment, lens specs, color grade, and --ar 16:9).
2. STORY: A Deep-Thinking narrative prompt for ChatGPT/Claude with a [THINKING_BLOCK] analyzing core dilemma, sensory map, and plot twist.
3. MUSIC: A bilingual English/Japanese song lyric pack formatted for Suno v3.5 with [Verse], [Chorus], and musical tags.

IMPORTANT: Ensure all newline characters within strings are strictly escaped as \\n.

Return ONLY this JSON schema:
{
  "visual": {
    "title": "Short Title (max 6 words)",
    "description": "1 clear sentence explaining the composition setup",
    "prompt": "Full Midjourney prompt here...",
    "pro_tip": "One clear swap or ratio tip"
  },
  "story": {
    "title": "Story Architecture Title",
    "description": "1 sentence on why this framework triggers narrative depth",
    "prompt": "Full prompt with THINKING_BLOCK instructions..."
  },
  "music": {
    "title": "Song Concept Title",
    "description": "Genre & vocal styling breakdown",
    "prompt": "Full lyrics and musical tags..."
  },
  "creator_note": "A sharp 1-sentence analytical insight on prompting"
}"""

    attempts = [
        ("gemini-2.5-flash", "gemini", g_key, None),
        ("groq-llama-3.3-70b", "groq", groq_key, "llama-3.3-70b-versatile"),
        ("gemini-2.0-flash", "gemini", g_key, None),
    ]

    for model_name, provider, key, groq_model in attempts:
        if not key:
            continue
        try:
            print(f"→ Generating new prompts with {model_name}...")
            if provider == "groq":
                raw = call_groq(prompt, key, groq_model)
            else:
                raw = call_gemini(prompt, key, model_name)
            
            clean = re.search(r'\{.*\}', raw, re.DOTALL)
            if clean:
                data = json.loads(clean.group(0), strict=False)
                if "visual" in data and "story" in data and "music" in data:
                    print(f"✓ Prompt generation successful: {data['visual']['title']}")
                    return data
        except Exception as e:
            print(f"✗ {model_name} failed: {e}")
            continue
    return None

def update_index_html(data):
    if not os.path.exists("index.html"):
        print("❌ index.html not found.")
        return

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update Visual Section
    html = re.sub(
        r'(<h2[^>]*id="title-visual"[^>]*>).*?(</h2>)',
        f'\\1{data["visual"]["title"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<p[^>]*id="desc-visual"[^>]*>).*?(</p>)',
        f'\\1{data["visual"]["description"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<pre[^>]*id="prompt-visual"[^>]*>).*?(</pre>)',
        f'\\1{data["visual"]["prompt"]}\\2', html, flags=re.DOTALL
    )
    if "pro_tip" in data["visual"]:
        html = re.sub(
            r'(<span[^>]*id="tip-visual"[^>]*>).*?(</span>)',
            f'\\1{data["visual"]["pro_tip"]}\\2', html, flags=re.DOTALL
        )

    # 2. Update Story Section
    html = re.sub(
        r'(<h3[^>]*id="title-story"[^>]*>).*?(</h3>)',
        f'\\1{data["story"]["title"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<p[^>]*id="desc-story"[^>]*>).*?(</p>)',
        f'\\1{data["story"]["description"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<pre[^>]*id="prompt-story"[^>]*>).*?(</pre>)',
        f'\\1{data["story"]["prompt"]}\\2', html, flags=re.DOTALL
    )

    # 3. Update Music Section
    html = re.sub(
        r'(<h3[^>]*id="title-music"[^>]*>).*?(</h3>)',
        f'\\1{data["music"]["title"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<p[^>]*id="desc-music"[^>]*>).*?(</p>)',
        f'\\1{data["music"]["description"]}\\2', html, flags=re.DOTALL
    )
    html = re.sub(
        r'(<pre[^>]*id="prompt-music"[^>]*>).*?(</pre>)',
        f'\\1{data["music"]["prompt"]}\\2', html, flags=re.DOTALL
    )

    # 4. Update Creator Note
    if "creator_note" in data:
        html = re.sub(
            r'(<p[^>]*id="creator-note"[^>]*>).*?(</p>)',
            f'\\1"{data["creator_note"]}"\\2', html, flags=re.DOTALL
        )

    # 5. Update Archive (Bounded to top 15 entries)
    date_str = datetime.now().strftime("%d %b %Y")
    new_archive_item = (
        f"                    <div class='archive-item p-2 rounded-lg hover:bg-white/5'>\n"
        f"                        <p class='text-xs text-slate-500'>{date_str}</p>\n"
        f"                        <p class='font-bold text-slate-200'>{data['visual']['title'][:35]}</p>\n"
        f"                        <p class='text-xs text-emerald-400'>Visual · Midjourney</p>\n"
        f"                    </div>"
    )

    if "<!-- H_S -->" in html and "<!-- H_E -->" in html:
        archive_block = html.split("<!-- H_S -->")[1].split("<!-- H_E -->")[0]
        existing_items = re.findall(r"<div class='archive-item[^>]*>.*?</div>", archive_block, re.DOTALL)
        combined_items = [new_archive_item] + existing_items[:14]
        new_archive_html = "\n" + "\n".join(combined_items) + "\n                    "
        html = re.sub(
            r'(<!-- H_S -->).*?(<!-- H_E -->)',
            f'\\1{new_archive_html}\\2',
            html, flags=re.DOTALL
        )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html updated with fully synchronized titles, descriptions, and prompts.")

def write_seo_files():
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
    with open("sitemap.xml", "w") as f:
        f.write(sitemap)
    with open("robots.txt", "w") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: https://autonomous-portfolio-2026.live/sitemap.xml\n")
    print("✓ Sitemap & robots.txt written")

def run():
    g_key = os.getenv("GEMINI")
    groq_key = os.getenv("GROQ")
    if not g_key and not groq_key:
        print("❌ No API keys found (GEMINI or GROQ).")
        return

    data = generate_prompts(g_key, groq_key)
    if data:
        update_index_html(data)
        write_seo_files()

if __name__ == "__main__":
    run()
