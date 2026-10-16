import os
import requests
import json
import re
import html
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# Affiliate Links & Telegram Settings
G2G_REFLINK = "https://www.g2g.com/mjq"
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHAT_ID", "@AII2026futher")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ─────────────────────────────────────────────
# 1. LIVE STEAM RELEASES, FREE GAMES & G2G DEALS
# ─────────────────────────────────────────────
def get_free_and_new_games():
    """
    Fetches 100% free PC games, Steam specials, and includes
    the verified G2G partner marketplace deal.
    Returns: (html_cards_str, list_of_game_objects_for_telegram)
    """
    games = []
    
    # 1. ALWAYS RECOMMENDED: Featured G2G Marketplace Card
    g2g_card = {
        "title": "G2G Gamer Market — Discounted Game Keys, Top-Ups & In-Game Gold",
        "link": G2G_REFLINK,
        "tag": "FEATURED PARTNER",
        "price": "Best Market Rate",
        "source": "G2G Verified Marketplace",
        "badge_color": "bg-purple-500/20 text-purple-300 border-purple-500/40",
        "is_partner": True
    }
    games.append(g2g_card)

    # 2. Fetch 100% Free / Free-to-Claim Games (GamerPower Freebie API)
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
                    "badge_color": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                    "is_partner": False
                })
    except Exception as e:
        print(f"Notice: Free games giveaway feed skipped ({e})")

    # 3. Fetch Steam Featured New Releases & Specials
    try:
        r = requests.get("https://store.steampowered.com/api/featuredcategories/?l=english", headers=HEADERS, timeout=7)
        if r.status_code == 200:
            data = r.json()
            specials = data.get("specials", {}).get("items", []) + data.get("new_releases", {}).get("items", [])
            for item in specials[:3]:
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
                
                if not any(g["title"] == name for g in games):
                    games.append({
                        "title": name,
                        "link": link,
                        "tag": tag,
                        "price": price_str,
                        "source": "Steam Store",
                        "badge_color": color,
                        "is_partner": False
                    })
    except Exception as e:
        print(f"Notice: Steam featured store feed skipped ({e})")

    # Generate HTML Cards
    html_cards = []
    for g in games[:6]:
        clean_title = html.escape(g["title"])
        action_text = "Claim Deal ↗" if g["is_partner"] else "Get Game ↗"
        card = (
            f"                    <div class='glass-card p-4 rounded-2xl border border-slate-800 flex flex-col justify-between hover:border-cyan-500/30 transition group'>\n"
            f"                        <div>\n"
            f"                            <div class='flex items-center justify-between mb-2'>\n"
            f"                                <span class='text-[10px] font-bold px-2.5 py-0.5 rounded-full border {g['badge_color']} font-mono'>{g['tag']}</span>\n"
            f"                                <span class='text-xs font-mono text-emerald-400 font-bold'>{g['price']}</span>\n"
            f"                            </div>\n"
            f"                            <a href='{g['link']}' target='_blank' rel='noopener noreferrer' class='font-bold text-white group-hover:text-cyan-400 transition text-xs block leading-snug'>\n"
            f"                                {clean_title}\n"
            f"                            </a>\n"
            f"                        </div>\n"
            f"                        <div class='mt-3 text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-2 font-mono'>\n"
            f"                            <span>● {g['source']}</span>\n"
            f"                            <a href='{g['link']}' target='_blank' rel='noopener noreferrer' class='text-cyan-400 hover:underline font-semibold'>{action_text}</a>\n"
            f"                        </div>\n"
            f"                    </div>"
        )
        html_cards.append(card)

    return "\n".join(html_cards), games

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
                    return f"{clean:,} Gold"
        except Exception:
            continue
    return "314,500 Gold"

# ─────────────────────────────────────────────
# 3. DAILY GAMING NEWS
# ─────────────────────────────────────────────
def get_live_game_news():
    feeds = [
        ("PC Gamer", "https://www.pcgamer.com/rss/"),
        ("Steam News", "https://store.steampowered.com/news/rss")
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
                f"                    <div class='p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 transition'>\n"
                f"                        <a href='{item['link']}' target='_blank' rel='noopener noreferrer' class='font-bold text-white hover:text-cyan-400 transition text-xs block leading-snug'>\n"
                f"                            {item['title'][:70]}...\n"
                f"                        </a>\n"
                f"                        <div class='flex items-center justify-between mt-2 text-[10px] text-slate-400 font-mono'>\n"
                f"                            <span class='text-cyan-400 font-semibold'>● {item['source']}</span>\n"
                f"                            <span>Daily Feed</span>\n"
                f"                        </div>\n"
                f"                    </div>"
            )
        return "\n".join(cards), news_items
    return "", []

# ─────────────────────────────────────────────
# 4. TELEGRAM AUTO-BROADCASTER
# ─────────────────────────────────────────────
def send_telegram_update(date_str, token_price, games_list):
    """
    Broadcasts the daily gaming update to the specified Telegram channel.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("ℹ️ Telegram: TELEGRAM_BOT_TOKEN not set. Skipping channel broadcast.")
        return

    # Build the Telegram message (HTML formatted)
    msg_lines = [
        f"🎮 <b>OMNIGAMING INTEL DAILY RADAR</b>",
        f"📅 <i>{date_str}</i>",
        f"🪙 <b>WoW Token:</b> <code>{token_price}</code>",
        "",
        "🎁 <b>TODAY'S FREE GAMES & DROPS:</b>"
    ]

    for g in games_list[:4]:
        tag_icon = "💎" if g.get("is_partner") else ("🔥" if "FREE" in g.get("tag", "") else "🎯")
        msg_lines.append(f"{tag_icon} <b>[{g.get('tag')}]</b> <a href='{g.get('link')}'>{html.escape(g.get('title'))}</a>")
        msg_lines.append(f"   └ <i>{g.get('price')} • {g.get('source')}</i>")

    msg_lines.extend([
        "",
        f"🛒 <b>G2G Market Partner:</b> <a href='{G2G_REFLINK}'>Shop Cheap Keys, Gold & Giftcards (20% Off Rate)</a>",
        "",
        "🌐 <b>Live Web Dashboard:</b> https://autonomous-portfolio-2026.live/"
    ])

    full_message = "\n".join(msg_lines)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ Telegram: Successfully broadcasted update to {TELEGRAM_CHANNEL}!")
        else:
            print(f"⚠️ Telegram broadcast response ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ Telegram broadcast error: {e}")

# ─────────────────────────────────────────────
# 5. SITE BUILDER & EXECUTION
# ─────────────────────────────────────────────
def update_site():
    if not os.path.exists("index.html"):
        print("❌ Error: index.html not found.")
        return

    today_str = datetime.utcnow().strftime('%B %d, %Y')
    print(f"\n[OmniGaming Daily Agent] Running for {today_str}...")

    token_price = get_wow_token()
    game_deals_html, raw_games = get_free_and_new_games()
    news_html, raw_news = get_live_game_news()

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update Token Price
    content = re.sub(r'(<span id="token-price"[^>]*>).*?(</span>)', f'\\g<1>{token_price}\\2', content)
    content = re.sub(r'(<span[^>]*id="side-token"[^>]*>).*?(</span>)', f'\\g<1>{token_price}\\2', content)

    # 2. Update Date Banner
    content = re.sub(r'(<span id="last-updated"[^>]*>).*?(</span>)', f'\\g<1>Updated: {today_str}\\2', content)

    # 3. Replace Games Section
    content = re.sub(
        r'(<!-- DAILY_GAMES_START -->).*?(<!-- DAILY_GAMES_END -->)',
        f'\\1\n{game_deals_html}\n\\2',
        content,
        flags=re.DOTALL
    )

    # 4. Replace News Section
    content = re.sub(
        r'(<!-- DAILY_NEWS_START -->).*?(<!-- DAILY_NEWS_END -->)',
        f'\\1\n{news_html}\n\\2',
        content,
        flags=re.DOTALL
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ index.html updated successfully!")

    # 5. Broadcast to Telegram Channel
    send_telegram_update(today_str, token_price, raw_games)

if __name__ == "__main__":
    update_site()
