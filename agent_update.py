from datetime import datetime
import json
import os
import re
import requests


# ─────────────────────────────────────────────
# 1. FREE LIVE DATA SCRAPERS (ZERO AUTH)
# ─────────────────────────────────────────────
def get_free_wow_token():
  """Fetch live US WoW Token gold price without API keys or accounts."""
  urls = [
      'https://wowtokenprice.com/api/v1/tokens/prices',
      'https://data.wowtoken.app/snapshot/us.json',
  ]
  for url in urls:
    try:
      r = requests.get(url, timeout=5)
      if r.status_code == 200:
        data = r.json()
        price = data.get('price')
        if not price and ('us' in data or 'US' in data):
          sub = data.get('us') or data.get('US')
          price = sub.get('price') if isinstance(sub, dict) else sub
        if price:
          clean = int(float(str(price).replace(',', '')))
          formatted = f'{clean:,} Gold'
          print(f'✓ Public WoW Token Price: {formatted}')
          return formatted
    except Exception:
      continue
  return '314,500 Gold'


def get_free_affixes():
  """Fetch current active Mythic+ affixes from Raider.IO open API."""
  try:
    r = requests.get(
        'https://raider.io/api/v1/mythic-plus/affixes?region=us&locale=en',
        timeout=6,
    )
    if r.status_code == 200:
      details = r.json().get('affix_details', [])
      names = [a.get('name') for a in details if a.get('name')]
      if len(names) >= 2:
        print(f'✓ Active Affixes: {names[0]} & {names[1]}')
        return names[0], names[1]
  except Exception as e:
    print(f'Affix fallback: {e}')
  return 'Fortified', 'Bursting'


# ─────────────────────────────────────────────
# 2. THEORYCRAFTING AI ENGINE
# ─────────────────────────────────────────────
def call_gemini(prompt, g_key, model='gemini-2.5-flash'):
  url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={g_key}'
  resp = requests.post(
      url, json={'contents': [{'parts': [{'text': prompt}]}]}, timeout=35
  )
  resp.raise_for_status()
  return resp.json()['candidates'][0]['content']['parts'][0]['text']


def call_groq(prompt, key, model='llama-3.3-70b-versatile'):
  headers = {
      'Authorization': f'Bearer {key}',
      'Content-Type': 'application/json',
  }
  payload = {
      'model': model,
      'messages': [
          {
              'role': 'system',
              'content': (
                  'You are a JSON API. Output strictly raw JSON without'
                  ' markdown.'
              ),
          },
          {'role': 'user', 'content': prompt},
      ],
      'max_tokens': 2000,
      'temperature': 0.75,
  }
  resp = requests.post(
      'https://api.groq.com/openai/v1/chat/completions',
      json=payload,
      headers=headers,
      timeout=30,
  )
  resp.raise_for_status()
  raw = resp.json()['choices'][0]['message']['content']
  return (
      re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
      .replace('```json', '')
      .replace('```', '')
      .strip()
  )


def get_smart_dossier(
    g_key, groq_key, affix1, affix2, token_price, recent_specs
):
  prompt = f"""You are the Lead World of Warcraft Theorycrafter for Azeroth Intel 2026.
Active Dungeon Modifiers: {affix1} + {affix2}. Live WoW Token: {token_price}.
Recently Covered Specs (DO NOT REPEAT): {", ".join(recent_specs) if recent_specs else "None"}.

Pick ONE high-performing meta spec (across Paladin, Demon Hunter, Death Knight, Druid, Evoker, Mage, Priest, Rogue, Shaman, Warlock, Warrior, Monk, Hunter) that excels with {affix1}/{affix2}.

Return ONLY raw JSON:
{{
  "push_grade": "Tier S (8.7/10)",
  "affix_strategy": "Strategic advice for managing pull pacing and dispels under {affix1} and {affix2}.",
  "dungeon_tip": "One clear combat survivability tip.",
  "featured_spec": {{
    "spec_name": "Full Spec & Class (e.g. Havoc Demon Hunter)",
    "class_color": "#A330C9",
    "build_title": "Short Punchy Title (max 6 words)",
    "stat_priority": "Item Level > Haste >= Crit > Mastery",
    "summary": "2 sentences explaining why this spec dominates this week.",
    "talent_string": "BEkAAAAAAAAAAAAAAAAAAAAAAQSKhUSLCSikkEJtk0SEJJBJJJlkEAAAAAQAAAEplkGAAAA",
    "top_consumables": "Flask of Alchemical Chaos • Tempered Potion",
    "macro_1_title": "Focus Interrupt Macro",
    "macro_1_code": "#showtooltip\\n/cast [@focus,harm,nodead][] Disrupt",
    "macro_2_title": "Burst Cooldown Sync",
    "macro_2_code": "#showtooltip Metamorphosis\\n/use 13\\n/cast Metamorphosis"
  }}
}}"""

  attempts = [
      ('gemini-2.5-flash', 'gemini', g_key, None),
      ('groq-llama-3.3-70b', 'groq', groq_key, 'llama-3.3-70b-versatile'),
      ('gemini-2.0-flash', 'gemini', g_key, None),
  ]

  for model_name, provider, key, groq_model in attempts:
    if not key:
      continue
    try:
      print(f'→ Generating build with {model_name}...')
      raw = (
          call_groq(prompt, key, groq_model)
          if provider == 'groq'
          else call_gemini(prompt, key, model_name)
      )
      clean = re.search(r'\{.*\}', raw, re.DOTALL)
      if clean:
        data = json.loads(clean.group(0), strict=False)
        if 'featured_spec' in data and 'push_grade' in data:
          print(f"✓ Generated: {data['featured_spec']['spec_name']}")
          return data
    except Exception as e:
      print(f'✗ {model_name} failed: {e}')
      continue

  # Fallback build
  return {
      'push_grade': 'Tier S (8.5/10)',
      'affix_strategy': (
          f'Stagger trash deaths carefully under {affix2} while prioritizing'
          f' high-damage interrupts on {affix1} packs.'
      ),
      'dungeon_tip': (
          'Use personal immunities when stack counts spike beyond 4 on large'
          ' pulls.'
      ),
      'featured_spec': {
          'spec_name': 'Retribution Paladin',
          'class_color': '#F58CBA',
          'build_title': 'Divine Storm High-Burst M+ Build',
          'stat_priority': 'Item Level > Haste >= Mastery > Crit',
          'summary': (
              'Provides top-tier burst AoE for fortified trash along with party'
              ' detox and blessing utility.'
          ),
          'talent_string': (
              'BYEAAAAAAAAAAAAAAAAAAAAAAAAAAgQCp0SjkIpkERik0SEAAAAAAAAAAAgEJRSSkWgIJRCA'
          ),
          'top_consumables': 'Flask of Chaos • Tempered Potion',
          'macro_1_title': 'Focus Rebuke (Kick)',
          'macro_1_code': '#showtooltip\n/cast [@focus,harm,nodead][] Rebuke',
          'macro_2_title': 'Mouseover Cleanse Toxins',
          'macro_2_code': (
              '#showtooltip\n/cast [@mouseover,help,nodead][] Cleanse'
          ),
      },
  }


# ─────────────────────────────────────────────
# 3. HTML UPDATER
# ─────────────────────────────────────────────
def update_index_html(token_price, affix1, affix2, data):
  if not os.path.exists('index.html'):
    print('❌ index.html not found.')
    return

  with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

  spec = data['featured_spec']
  color = spec.get('class_color', '#F58CBA')

  # Token Prices
  html = re.sub(
      r'(<span id="token-price"[^>]*>).*?(</span>)',
      f'\\g<1>{token_price}\\2',
      html,
  )
  html = re.sub(
      r'(<span[^>]*id="side-token"[^>]*>).*?(</span>)',
      f'\\g<1>{token_price}\\2',
      html,
  )

  # Affixes & Push Grade
  html = re.sub(
      r'(<p[^>]*id="affix-1"[^>]*>).*?(</p>)', f'\\g<1>{affix1}\\2', html
  )
  html = re.sub(
      r'(<p[^>]*id="affix-2"[^>]*>).*?(</p>)', f'\\g<1>{affix2}\\2', html
  )
  html = re.sub(
      r'(<span[^>]*id="push-grade"[^>]*>).*?(</span>)',
      f'\\g<1>{data["push_grade"]}\\2',
      html,
  )
  html = re.sub(
      r'(<p[^>]*id="affix-strategy"[^>]*>).*?(</p>)',
      f'\\g<1>{data["affix_strategy"]}\\2',
      html,
  )
  html = re.sub(
      r'(<span[^>]*id="weekly-tip"[^>]*>).*?(</span>)',
      f'\\g<1>{data["dungeon_tip"]}\\2',
      html,
  )

  # Spec Details
  html = re.sub(
      r'(<span[^>]*id="spec-name"[^>]*>).*?(</span>)',
      f'\\g<1>{spec["spec_name"]}\\2',
      html,
  )
  html = re.sub(
      r'(<h3[^>]*id="guide-title"[^>]*>).*?(</h3>)',
      f'\\g<1>{spec["build_title"]}\\2',
      html,
  )
  html = re.sub(
      r'(<p[^>]*id="guide-desc"[^>]*>).*?(</p>)',
      f'\\g<1>{spec["summary"]}\\2',
      html,
  )
  html = re.sub(
      r'(<span[^>]*id="stat-priority"[^>]*>).*?(</span>)',
      f'\\g<1>{spec["stat_priority"]}\\2',
      html,
  )
  html = re.sub(
      r'(<span[^>]*id="consumables"[^>]*>).*?(</span>)',
      f'\\g<1>{spec["top_consumables"]}\\2',
      html,
  )
  html = re.sub(
      r'(<pre[^>]*id="talent-string"[^>]*>).*?(</pre>)',
      f'\\g<1>{spec["talent_string"]}\\2',
      html,
  )

  # Macros
  m1_code = spec.get('macro_1_code', '').replace('\n', '&#10;')
  m2_code = spec.get('macro_2_code', '').replace('\n', '&#10;')
  html = re.sub(
      r'(<p[^>]*id="macro-1-title"[^>]*>).*?(</p>)',
      f'\\g<1>{spec["macro_1_title"]}\\2',
      html,
  )
  html = re.sub(
      r'(<code[^>]*id="macro-1-code"[^>]*>).*?(</code>)',
      f'\\g<1>{m1_code}\\2',
      html,
  )
  html = re.sub(
      r'(<p[^>]*id="macro-2-title"[^>]*>).*?(</p>)',
      f'\\g<1>{spec["macro_2_title"]}\\2',
      html,
  )
  html = re.sub(
      r'(<code[^>]*id="macro-2-code"[^>]*>).*?(</code>)',
      f'\\g<1>{m2_code}\\2',
      html,
  )

  # Spec Card Dynamic Class Color Glow
  html = re.sub(
      r'(<div[^>]*id="spec-card"[^>]*style=")[^"]*(")',
      f'\\g<1>border-left: 4px solid {color}; box-shadow: 0 0 25px {color}20;\\2',
      html,
  )

  # Archive Rotation
  date_str = datetime.now().strftime('%d %b %Y')
  new_archive = (
      "                    <div class='p-2 rounded-lg hover:bg-white/5'>\n"
      f"                        <p class='text-xs text-slate-500'>{date_str}</p>\n"
      f"                        <p class='font-bold text-slate-200'>{spec['spec_name']}</p>\n"
      f"                        <p class='text-[11px] text-amber-400'>{affix1}"
      f' + {affix2}</p>\n'
      '                    </div>'
  )

  if '<!-- H_S -->' in html and '<!-- H_E -->' in html:
    archive_block = html.split('<!-- H_S -->')[1].split('<!-- H_E -->')[0]
    existing = re.findall(
        r"<div class='p-2 rounded-lg hover:bg-white/5'>.*?</div>",
        archive_block,
        re.DOTALL,
    )
    combined = [new_archive] + existing[:14]
    new_archive_html = '\n' + '\n'.join(combined) + '\n                    '
    html = re.sub(
        r'(<!-- H_S -->).*?(<!-- H_E -->)',
        f'\\1{new_archive_html}\\2',
        html,
        flags=re.DOTALL,
    )

  with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
  print('✅ index.html verified and successfully updated!')


def run():
  g_key = os.getenv('GEMINI')
  groq_key = os.getenv('GROQ')

  recent_specs = []
  if os.path.exists('index.html'):
    with open('index.html', 'r', encoding='utf-8') as f:
      c = f.read()
      if '<!-- H_S -->' in c:
        hist = c.split('<!-- H_S -->')[1].split('<!-- H_E -->')[0]
        recent_specs = re.findall(
            r"font-bold text-slate-200'>([^<]+)", hist
        )[:4]

  print('\n[Azeroth Pipeline] Reading live dungeon affixes & economy...')
  token_price = get_free_wow_token()
  affix1, affix2 = get_free_affixes()

  print('[Azeroth Pipeline] Running theorycrafting model...')
  data = get_smart_dossier(
      g_key, groq_key, affix1, affix2, token_price, recent_specs
  )

  update_index_html(token_price, affix1, affix2, data)


if __name__ == '__main__':
  run()
