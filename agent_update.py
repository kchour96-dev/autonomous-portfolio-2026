import os
import requests
import json
import re
import html
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# ─────────────────────────────────────────────
# 1. LIVE STEAM RELEASES & 100% OFF FREE GAMES
# ─────────────────────────────────────────────
def get_free_and_new_games():
    """
    Fetches 100% free games, Steam deals, and new game releases.
    Uses free public endpoints with reliable fallbacks.
    """
    games = []
    
    # 1. Fetch 100% Free / Free-to-Claim Games (GamerPower Freebie API)
    try:
        r = requests.get("https://www.gamerpower.com/api/giveaways?platform=pc", headers=HEADERS, timeout=7)
        if r.status_code == 200:
            giveaways = r.json()
            for item in giveaways[:3]:
                title = item.get("title", "Free Game Claim")
                link = item.get("open_giveaway_url") or item.get("gamerpower_url")
                worth = item.get("worth", "N/A")
                games.append({
                    "title": title,
                    "link": link,
                    "tag": "100% FREE",
                    "price": f"Free (Was {worth})",
                    "source": "Steam / PC Freebie",
                    "badge_color": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                })
    except Exception as e:
        print(f"Notice: Free games giveaway feed skipped ({e})")

    # 2. Fetch Steam Featured New Releases & Specials
    try:
        r = requests.get("https://store.steampowered.com/api/featuredcategories/?l=english", headers=HEADERS, timeout=7)
        if r.status_code == 200:
            data = r.json()
            # New releases / Top sellers
            specials = data.get("specials", {}).get("items", []) + data.get("new_releases", {}).get("items", [])
            for item in specials[:4]:
                name = item.get("name")
                app_id = item.get("id")
                final_price = item.get("final_price", 0)
                discount = item.get("discount_percent", 0)
                
                if discount > 0:
                    price_str = f"-{discount}% (${final_price/100:.2f})"
                    tag = "ON SALE"
                    color = "bg-amber-500/20 text-amber-400 border-amber-500/30"
                elif final_price == 0:
                    price_str = "Free to Play"
                    tag = "FREE"
                    color = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                else:
                    price_str = f"${final_price/100:.2f}"
                    tag = "NEW RELEASE"
                    color = "bg-sky-500/20 text-sky-400 border-sky-500/30"

                link = f"https://store.steampowered.com/app/{app_id}"
                
                # Prevent duplicates
                if not any(g["title"] == name for g in games):
                    games.append({
                        "title": name,
                        "link": link,
                        "tag": tag,
                        "price": price_str,
                        "source": "Steam Store",
                        "badge_color": color
                    })
    except Exception as e:
        print(f"Notice: Steam featured store feed skipped ({e})")

    # Generate Cards
    if games:
        html_cards = []
        for g in games[:5]:
            clean_title = html.escape(g["title"])
            card = (
                f"                    <div class='p-3.5 rounded-xl bg-white/5 hover:bg-white/10 transition border border-white/5 flex flex-col justify-between'>\n"
                f"                        <div>\n"
                f"                            <div class='flex items-center justify-between mb-1.5'>\n"
                f"                                <span class='text-[10px] font-bold px-2 py-0.5 rounded border {g['badge_color']}'>{g['tag']}</span>\n"
                f"                                <span class='text-xs font-mono text-emerald-400 font-bold'>{g['price']}</span>\n"
                f"                            </div>\n"
                f"                            <a href='{g['link']}' target='_blank' rel='noopener noreferrer' class='font-bold text-white hover:text-amber-400 transition text-xs block leading-snug'>\n"
                f"                                {clean_title}\n"
                f"                            </a>\n"
                f"                        </div>\n"
                f"                        <div class='mt-2 text-[10px] text-slate-400 flex items-center justify-between border-t border-white/5 pt-1.5'>\n"
                f"                            <span>● {g['source']}</span>\n"
                f"                            <span class='text-amber-400 hover:underline'>Get Game ↗</span>\n"
                f"                        </div>\n"
                f"                    </div>"
            )
            html_cards.append(card)
        return "\n".join(html_cards)

    # Static fallback
    return (
        "                    <div class='p-3 rounded-xl bg-white/5 text-slate-300'>\n"
        "                        <p class='font-bold text-white text-xs'>Check Steam Store for Free Releases</p>\n"
        "                        <p class='text-slate-400 text-[11px] mt-0.5'>Daily updates refresh at 10:00 AM PST.</p>\n"
        "                    </div>"
    )

# ─────────────────────────────────────────────
# 2. LIVE GAME ECONOMY (WOW TOKEN)
# ─────────────────────────────────────────────
def get_wow_token():
    urls = [
        "https://wowtokenprice.com/api/v1/tokens/prices",
        "https://data.wowtoken.app/snapshot/us.json"
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                data = r.json()
                price = data.get("price")
                if not price and ("us" in data or "US" in data):
                    sub = data.get("us") or data.get("US")
                    price = sub.get("price") if isinstance(sub, dict) else sub
                if price:
                    clean = int(float(str(price).replace(",", "")))
                    formatted = f"{clean:,} Gold"
                    return formatted
        except Exception:
            continue
    return "314,500 Gold"

# ─────────────────────────────────────────────
# 3. DAILY GENERAL GAMING NEWS
# ─────────────────────────────────────────────
def get_live_game_news():
    feeds = [
        ("PC Gamer", "https://www.pcgamer.com/rss/"),
        ("Wowhead", "https://www.wowhead.com/news/rss/all")
    ]
    news_items = []
    
    for source_name, feed_url in feeds:
        try:
            r = requests.get(feed_url, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', r.text)
                links = re.findall(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', r.text)
                
                for t, l in zip(titles[1:4], links[1:4]):
                    clean_title = re.sub(r'<[^>]+>', '', t).strip()
                    clean_link = l.strip()
                    if clean_title and clean_link.startswith("http"):
                        news_items.append({
                            "title": clean_title,
                            "link": clean_link,
                            "source": source_name
                        })
                    if len(news_items) >= 4:
                        break
        except Exception:
            continue
        if len(news_items) >= 4:
            break

    if news_items:
        cards = []
        for item in news_items[:4]:
            cards.append(
                f"                    <div class='p-3 rounded-xl bg-white/5 hover:bg-white/10 transition border border-white/5'>\n"
                f"                        <a href='{item['link']}' target='_blank' rel='noopener noreferrer' class='font-bold text-white hover:text-amber-400 transition text-xs block leading-snug'>\n"
                f"                            {item['title'][:70]}...\n"
                f"                        </a>\n"
                f"                        <div class='flex items-center justify-between mt-1.5 text-[10px] text-slate-400'>\n"
                f"                            <span class='text-amber-400/90 font-bold'>● {item['source']}</span>\n"
                f"                            <span>Daily Release</span>\n"
                f"                        </div>\n"
                f"                    </div>"
            )
        return "\n".join(cards)
    return ""

# ─────────────────────────────────────────────
# 4. SITE BUILDER
# ─────────────────────────────────────────────
def update_site():
    if not os.path.exists("index.html"):
        print("❌ Error: index.html not found.")
        return

    today_str = datetime.utcnow().strftime('%B %d, %Y')
    print(f"\n[OmniGaming Daily Agent] Running for {today_str}...")

    token_price = get_wow_token()
    game_deals_html = get_free_and_new_games()
    news_html = get_live_game_news()

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Token Price
    content = re.sub(r'(<span id="token-price"[^>]*>).*?(</span>)', f'\\g<1>{token_price}\\2', content)
    content = re.sub(r'(<span[^>]*id="side-token"[^>]*>).*?(</span>)', f'\\g<1>{token_price}\\2', content)

    # 2. Update Daily Date Banner
    content = re.sub(r'(<span id="last-updated"[^>]*>).*?(</span>)', f'\\g<1>Updated: {today_str}\\2', content)

    # 3. Replace Game Releases & Free Games Container
    content = re.sub(
        r'(<!-- DAILY_GAMES_START -->).*?(<!-- DAILY_GAMES_END -->)',
        f'\\1\n{game_deals_html}\n\\2',
        content,
        flags=re.DOTALL
    )

    # 4. Replace General News Container
    content = re.sub(
        r'(<!-- DAILY_NEWS_START -->).*?(<!-- DAILY_NEWS_END -->)',
        f'\\1\n{news_html}\n\\2',
        content,
        flags=re.DOTALL
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ index.html updated successfully with daily free/buy game releases!")

if __name__ == "__main__":
    update_site()
