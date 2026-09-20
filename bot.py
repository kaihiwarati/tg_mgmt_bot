"""
Telegram Management Bot — Aesthetic UI Edition
Telethon + SQLite + nekos.best

Made For My Love
"""

import asyncio
import os
import random
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import aiohttp
from telethon import TelegramClient, events, Button
from telethon.tl.types import Channel, Chat, ChatBannedRights, ChatAdminRights
from telethon.tl.functions.channels import EditBannedRequest, EditAdminRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_NAME = os.getenv("BOT_NAME", "Guardian")
SUPERADMINS = {int(x) for x in os.getenv("SUPERADMINS", "").split(",") if x.strip().isdigit()}
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "").strip()
LOG_CHANNEL_ID = int(LOG_CHANNEL) if LOG_CHANNEL.lstrip("-").isdigit() else None
STARTUP_NOTIFY = os.getenv("STARTUP_NOTIFY", "").strip()
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes", "on")

DATA_DIR = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "bot.db"

SESSION = "bot_session" if BOT_TOKEN else "session"
client = TelegramClient(SESSION, API_ID, API_HASH)

START_TIME = time.time()
PERMISSION_TIMEOUT = 60

# Consent actions — ask target first
CONSENT_ACTIONS = {"hug", "kiss", "sex","dance","cuddle"}

# Custom assets-only categories (no nekos)
CUSTOM_ONLY = {"hug", "kiss", "sex", "dance", "bite", "lick", "cuddle","kill","punch","spank","shy"}


def log(*args):
    if DEBUG:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}]", *args)


# ═══════════════════════════════════════════════════════════
# AESTHETIC UI SYSTEM
# ═══════════════════════════════════════════════════════════

BULLET = "▸"
DOT = "·"


def mention(user_id: int, name: str) -> str:
    if not user_id:
        return name
    return f"[{name}](tg://user?id={user_id})"


def success(heading: str, fields: list[tuple[str, str]] | None = None, flavor: str = "") -> str:
    icon = random.choice(["✅", "🌟", "✨", "💫"])
    out = f"{icon} **{heading}**"
    if fields:
        out += "\n\n" + "\n".join(f"  {BULLET} {k}: {v}" for k, v in fields)
    if flavor:
        out += f"\n\n*{flavor}*"
    return out


def error(heading: str, msg: str = "") -> str:
    out = f"❌ **{heading}**"
    if msg:
        out += f"\n\n  {BULLET} {msg}"
    return out


def info(heading: str, fields: list[tuple[str, str]] | None = None) -> str:
    out = f"ℹ️ **{heading}**"
    if fields:
        out += "\n\n" + "\n".join(f"  {BULLET} {k}: {v}" for k, v in fields)
    return out


def action_line(icon: str, actor: str, verb: str, target: str = "") -> str:
    if target:
        return f"{icon} **{actor}** {verb} **{target}**"
    return f"{icon} **{actor}** {verb}"


def stats_panel(icon: str, heading: str, fields: list[tuple[str, str]]) -> str:
    out = f"{icon} **{heading}**\n"
    out += "\n" + "\n".join(f"  {BULLET} {k}: {v}" for k, v in fields)
    return out


def list_panel(icon: str, heading: str, items: list[str], count: int = None, max_show: int = 30) -> str:
    total = count if count is not None else len(items)
    out = f"{icon} **{heading}** ({total})\n"
    shown = items[:max_show]
    out += "\n" + "\n".join(f"  {BULLET} {it}" for it in shown)
    if total > max_show:
        out += f"\n  {BULLET} ... and {total - max_show} more"
    return out


def greet_for_hour() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "Good morning ☀️"
    if 12 <= h < 17:
        return "Good afternoon 🌤"
    if 17 <= h < 22:
        return "Good evening 🌆"
    return "Still awake? 🌙"


def humanize_uptime(sec: float) -> str:
    sec = int(sec)
    d, sec = divmod(sec, 86400)
    h, sec = divmod(sec, 3600)
    m, sec = divmod(sec, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{sec}s")
    return " ".join(parts)


def humanize_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h}h {m}m"
    d, h = divmod(h, 24)
    return f"{d}d {h}h"


async def typing(event, seconds: float = 0.4):
    try:
        async with client.action(event.chat_id, "typing"):
            await asyncio.sleep(seconds)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# FLAVOR
# ═══════════════════════════════════════════════════════════

FLAVOR = {
    "ban": ["obliterated. RIP.", "voted off the island.", "→ /dev/null",
            "gone. Poof.", "got the hammer.", "left the multiverse."],
    "kick": ["took a one-way flight.", "yeeted into the void.",
             "launched into orbit.", "took the express exit.",
             "escorted out.", "vanished from the room."],
    "fuck": ["got the big F.", "F. Gone.", "→ 🚫", "FF. Press F.",
             "received the F.", "was F'd. Into the abyss."],
    "mute": ["silenced.", "🔇 shhh.", "can't talk now.",
             "chat privileges revoked.", "went quiet. Forcefully."],
    "warn": ["eyes on you.", "watch it.", "noted.", "strike recorded.",
             "careful now.", "one more and things get serious."],
    "unwarn": ["clean slate. Almost.", "a little leniency goes a long way.",
               "forgiven. This time.", "one warning lifted."],
    "promote": ["crown delivered.", "rose through the ranks.",
                "new power unlocked.", "welcome to the council.",
                "one of us now.", "the throne awaits."],
    "demote": ["back to civilian life.", "the crown returns.",
               "power revoked.", "down the ladder.", "stripped of rank."],
    "lock": ["sealed. 🔒", "no more of that.", "doors closed.",
             "shut. Barred. Locked.", "off the menu."],
    "unlock": ["freed. 🔓", "open for business.", "doors opened.",
               "back online.", "let it flow."],
    "filter": ["filter armed.", "watching for that word.",
               "auto-response loaded.", "trigger set.", "locked and loaded."],
    "purge": ["messages swept away.", "gone. All of it.",
              "the void called.", "cleaned. Spotless.", "history erased."],
    "afk": ["away. Don't burn the place down.", "gone but not forgotten.",
            "AFK mode engaged.", "brb. Maybe. Or later."],
}


def flavor(key: str) -> str:
    pool = FLAVOR.get(key)
    return random.choice(pool) if pool else ""


# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


def init_db():
    # Drop old media table (feature removed)
    cur.execute("DROP TABLE IF EXISTS media")
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        chat_id INTEGER, key TEXT, value TEXT,
        PRIMARY KEY (chat_id, key)
    );
    CREATE TABLE IF NOT EXISTS filters (
        chat_id INTEGER, keyword TEXT,
        text TEXT, media_type TEXT, file_id TEXT,
        PRIMARY KEY (chat_id, keyword)
    );
    CREATE TABLE IF NOT EXISTS warnings (
        chat_id INTEGER, user_id INTEGER, count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS afk (
        user_id INTEGER PRIMARY KEY,
        reason TEXT, since REAL
    );
    CREATE TABLE IF NOT EXISTS locks (
        chat_id INTEGER, lock_type TEXT,
        PRIMARY KEY (chat_id, lock_type)
    );
    CREATE TABLE IF NOT EXISTS wyr_votes (
        msg_id INTEGER,
        chat_id INTEGER,
        user_id INTEGER,
        choice TEXT,
        PRIMARY KEY (msg_id, user_id)
    );
    """)
    conn.commit()


init_db()


def get_setting(chat_id: int, key: str, default=None):
    cur.execute("SELECT value FROM settings WHERE chat_id=? AND key=?", (chat_id, key))
    row = cur.fetchone()
    return row["value"] if row else default


def set_setting(chat_id: int, key: str, value):
    cur.execute(
        "INSERT INTO settings(chat_id,key,value) VALUES(?,?,?) "
        "ON CONFLICT(chat_id,key) DO UPDATE SET value=excluded.value",
        (chat_id, key, str(value)),
    )
    conn.commit()


def del_setting(chat_id: int, key: str):
    cur.execute("DELETE FROM settings WHERE chat_id=? AND key=?", (chat_id, key))
    conn.commit()


# ═══════════════════════════════════════════════════════════
# PERMISSIONS
# ═══════════════════════════════════════════════════════════

async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in SUPERADMINS:
        return True
    try:
        p = await client.get_permissions(chat_id, user_id)
        return bool(p.is_admin or p.is_creator)
    except Exception:
        return False


async def require_admin(event) -> bool:
    if not await is_admin(event.chat_id, event.sender_id):
        await event.reply(error("Permission denied", "Only group admins can use this."))
        return False
    return True


# ═══════════════════════════════════════════════════════════
# TARGET RESOLUTION
# ═══════════════════════════════════════════════════════════

async def resolve_target(event):
    if event.is_reply:
        msg = await event.get_reply_message()
        if msg and msg.sender_id:
            try:
                u = await client.get_entity(msg.sender_id)
                return msg.sender_id, getattr(u, "first_name", str(msg.sender_id))
            except Exception:
                return msg.sender_id, str(msg.sender_id)

    if event.message.entities:
        for ent in event.message.entities:
            if hasattr(ent, "user_id"):
                try:
                    u = await client.get_entity(ent.user_id)
                    return ent.user_id, getattr(u, "first_name", str(ent.user_id))
                except Exception:
                    return ent.user_id, str(ent.user_id)

    text = event.message.message or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    arg = parts[1].split()[0]

    if arg.startswith("@"):
        uname = arg[1:].lower()
        try:
            async for u in client.iter_participants(event.chat_id, search=uname):
                if getattr(u, "username", "") and u.username.lower() == uname:
                    return u.id, getattr(u, "first_name", uname)
        except Exception:
            pass
        try:
            u = await client.get_entity(arg)
            return u.id, getattr(u, "first_name", uname)
        except Exception:
            return None, None

    if arg.lstrip("-").isdigit():
        uid = int(arg)
        try:
            u = await client.get_entity(uid)
            return uid, getattr(u, "first_name", str(uid))
        except Exception:
            return uid, str(uid)

    return None, None


# ═══════════════════════════════════════════════════════════
# MEDIA — assets/ for custom, nekos for the rest
# ═══════════════════════════════════════════════════════════

NEKOS_BASE = "https://nekos.best/api/v2"

NEKOS_MAP = {
    "angry": "baka",
    "sad": "cry",
    "pat": "pat", "slap": "slap", "bonk": "bonk", "tickle": "tickle",
    "cry": "cry", "highfive": "highfive", "murder": "punch",
    "smug": "smug", "blush": "blush", "smile": "smile",
    "wave": "wave", "wink": "wink", "pout": "pout",
    "happy": "happy", "laugh": "laugh", "facepalm": "facepalm",
    "afk": "sleep", "brb": "wave", "wish": "dance",
    "couple": "cuddle", "waifu": "waifu",
    "welcome": "wave", "goodbye": "wave", "start": "wave",
}

_session: aiohttp.ClientSession | None = None


async def http() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def nekos_fetch(endpoint: str) -> str | None:
    try:
        s = await http()
        async with s.get(f"{NEKOS_BASE}/{endpoint}",
                         timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                return None
            data = await r.json()
            results = data.get("results") or []
            if not results:
                return None
            return results[0].get("url")
    except Exception:
        return None


async def pick_media(category: str) -> str | None:
    # 1. Local assets for custom-only categories
    if category in CUSTOM_ONLY:
        folder = ASSETS_DIR / category
        if folder.is_dir():
            files = [p for p in folder.iterdir()
                     if p.suffix.lower() in {".gif", ".png", ".jpg", ".jpeg", ".mp4", ".webm"}]
            if files:
                return str(random.choice(files))
        return None  # No nekos fallback for these

    # 2. Nekos for everything else
    endpoint = NEKOS_MAP.get(category)
    if endpoint:
        return await nekos_fetch(endpoint)
    return None


async def send_media_reply(event, category: str, caption: str = "") -> bool:
    media = await pick_media(category)
    if media:
        try:
            await event.reply(caption or None, file=media)
            return True
        except Exception as e:
            log(f"[media send failed] {category}: {e}")

    if category in CUSTOM_ONLY:
        try:
            await event.reply(f"🖼 No media in `assets/{category}/`")
        except Exception:
            pass
        return True

    return False


# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

async def log_action(action: str, actor, target_name: str = "",
                     chat_title: str = "", extra: str = ""):
    if not LOG_CHANNEL_ID:
        return
    try:
        actor_name = getattr(actor, "first_name", str(actor)) if actor else "system"
        actor_id = getattr(actor, "id", 0) if actor else 0
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            f"⭐ **{action.upper()} EVENT**\n\n"
            f"  {BULLET} User: {target_name}\n"
            f"  {BULLET} By: {actor_name} (`{actor_id}`)\n"
            f"  {BULLET} Chat: {chat_title}\n"
        )
        if extra:
            text += f"  {BULLET} Note: {extra}\n"
        text += f"  {BULLET} Time: {ts}"
        await client.send_message(LOG_CHANNEL_ID, text)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# BAN / MUTE CORE
# ═══════════════════════════════════════════════════════════

async def apply_ban(chat_id: int, user_id: int, until=None):
    rights = ChatBannedRights(
        until_date=until or 0, view_messages=True, send_messages=True,
        send_media=True, send_stickers=True, send_gifs=True,
        send_games=True, send_inline=True, embed_links=True,
    )
    await client(EditBannedRequest(chat_id, user_id, rights))


async def apply_mute(chat_id: int, user_id: int, until=None):
    rights = ChatBannedRights(until_date=until or 0, send_messages=True)
    await client(EditBannedRequest(chat_id, user_id, rights))


async def apply_unmute(chat_id: int, user_id: int):
    rights = ChatBannedRights(until_date=0)
    await client(EditBannedRequest(chat_id, user_id, rights))


TIME_RE = re.compile(r"^(\d+)([smhd])$", re.I)
UNIT = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_time(s: str):
    m = TIME_RE.match(s.strip())
    return int(m.group(1)) * UNIT[m.group(2).lower()] if m else None


# ═══════════════════════════════════════════════════════════
# START / HELP / ID / UPTIME
# ═══════════════════════════════════════════════════════════

HELP_PAGES = {
    1: ("🟢 Basic", [
        "/start — Greet",
        "/help — This menu",
        "/id — Show IDs",
        "/uptime — Bot uptime",
    ]),
    2: ("🟠 Admin", [
        "/promote — Promote user",
        "/demote — Demote user",
        "/adminlist — List admins",
    ]),
    3: ("🔴 Anti-Spam", [
        "/antiflood [on/off] [n]",
        "/antiraid [on/off]",
    ]),
    4: ("🔨 Bans", [
        "/ban — Ban user",
        "/kick — Kick user",
        "/fuck — Ban (fun)",
        "/mute — Mute user",
        "/tmute <time> — Temp mute",
        "/unban — Unban user",
    ]),
    5: ("🔎 Filters", [
        "/filters — List filters",
        "/filter <kw> [resp] — Add filter",
        "/stop <kw> — Remove filter",
    ]),
    6: ("📌 Pins & Locks", [
        "/pin — Pin reply",
        "/unpin — Unpin",
        "/lock <type> — Lock type",
        "/lockall — Lock all",
        "/unlockall — Unlock all",
        "/lock_media — Lock media only",
        "/unlock_media — Unlock media",
        "/locks — List locks",
    ]),
    7: ("⚠️ Warn & Tag", [
        "/warn — Warn user",
        "/unwarn — Remove warn",
        "/setwarns <n> — Set limit",
        "/tagall <text> — Tag all",
        "/cancel — Stop tagall",
    ]),
    8: ("🧹 Purge & Greet", [
        "/purge — Delete messages",
        "/setwelcome [text] — Set welcome",
        "/setgoodbye [text] — Set goodbye",
        "/off — Disable greetings",
    ]),
    9: ("🎲 Fun", [
        "Consent: /hug /kiss /sex",
        "         /dance /cuddle",
        "Direct: /bite /lick /kill",
        "        /punch /spank ",
        "Nekos: /sad /angry /pat",
        "       /slap /bonk /tickle",
        "       /cry /smug /blush",
        "       /smile /wave /wink",
        "       /pout /happy /laugh",
        "       /facepalm /highfive",
        "       /murder",
    ]),
    10: ("💑 Social & AFK", [
        "/couple — Random pair",
        "/waifu — Today's waifu",
        "/love — Love bond %",
        "/crush — Crush level %",
        "/iq — Random IQ",
        "/wish <text> — Make a wish",
        "/afk [reason] — Set AFK",
        "/brb [note] — Be right back",
    ]),
    11: ("🎮 Games", [
        "/truth — Random truth question",
        "/dare — Random dare challenge",
        "/wyr — Would You Rather",
    ]),
}
TOTAL_HELP_PAGES = len(HELP_PAGES)


def help_page_text(page: int) -> str:
    heading, lines = HELP_PAGES[page]
    body = "\n".join(f"  {BULLET} {ln}" for ln in lines)
    return f"📖 **Help** {DOT} {page}/{TOTAL_HELP_PAGES}\n\n{heading}\n\n{body}"


def help_page_buttons(page: int):
    return [
        [Button.inline("◀ Back", b"start_back")],
        [
            Button.inline("◀", f"help:{page-1}".encode()),
            Button.inline(f"{page}/{TOTAL_HELP_PAGES}", b"noop"),
            Button.inline("▶", f"help:{page+1}".encode()),
        ],
    ]


def start_hero(name: str) -> str:
    return (
        f"👋 Hey **{name}**\n\n"
        f"I keep your group clean, safe, and a bit fun.\n\n"
        f"  {BULLET} Uptime: {humanize_uptime(time.time() - START_TIME)}\n"
        f"  {BULLET} Commands: 70+\n\n"
        f"📖 /help for all commands"
    )


def start_buttons():
    return [
        [Button.inline("📖 Help", b"help:1"), Button.inline("🆔 My ID", b"myid")],
        [Button.inline("🎲 Fun", b"fun"), Button.inline("👑 Admin", b"admin")],
    ]


@client.on(events.NewMessage(pattern=r"^/start(?:@\w+)?$"))
async def cmd_start(event):
    sender = await event.get_sender()
    name = getattr(sender, "first_name", "friend")
    await typing(event, 0.4)

    hero = start_hero(name)
    media = await pick_media("start")
    if media:
        try:
            await event.reply(hero, file=media, buttons=start_buttons())
            return
        except Exception:
            pass
    await event.reply(hero, buttons=start_buttons())


@client.on(events.NewMessage(pattern=r"^/help(?:@\w+)?$"))
async def cmd_help(event):
    await event.reply(help_page_text(1), buttons=help_page_buttons(1))


@client.on(events.CallbackQuery(data=re.compile(rb"^help:(\d+)$")))
async def cb_help(event):
    page = int(event.pattern_match.group(1))
    if page < 1:
        page = TOTAL_HELP_PAGES
    if page > TOTAL_HELP_PAGES:
        page = 1
    try:
        await event.edit(help_page_text(page), buttons=help_page_buttons(page))
    except Exception:
        pass
    await event.answer()


@client.on(events.CallbackQuery(data=b"start_back"))
async def cb_start_back(event):
    sender = await event.get_sender()
    name = getattr(sender, "first_name", "friend")
    try:
        await event.edit(start_hero(name), buttons=start_buttons())
    except Exception:
        pass
    await event.answer()


@client.on(events.CallbackQuery(data=b"noop"))
async def cb_noop(event):
    await event.answer()


@client.on(events.CallbackQuery(data=b"myid"))
async def cb_myid(event):
    await event.answer(f"Your ID: {event.sender_id}", alert=True)


@client.on(events.CallbackQuery(data=b"fun"))
async def cb_fun(event):
    await event.answer("Try /hug /kiss /sex /dance!", alert=True)


@client.on(events.CallbackQuery(data=b"admin"))
async def cb_admin(event):
    if await is_admin(event.chat_id, event.sender_id):
        await event.answer("You're an admin 👑", alert=True)
    else:
        await event.answer("You're not an admin here.", alert=True)


@client.on(events.NewMessage(pattern=r"^/id(?:@\w+)?$"))
async def cmd_id(event):
    chat = await event.get_chat()
    fields = [
        ("Chat", f"`{event.chat_id}`"),
        ("You", f"`{event.sender_id}`"),
        ("Type", type(chat).__name__),
    ]
    if event.is_reply:
        msg = await event.get_reply_message()
        if msg and msg.sender_id:
            fields.append(("Replied", f"`{msg.sender_id}`"))
    await event.reply(info("Identity", fields))


@client.on(events.NewMessage(pattern=r"^/uptime(?:@\w+)?$"))
async def cmd_uptime(event):
    await event.reply(info("Uptime", [
        ("Duration", humanize_uptime(time.time() - START_TIME)),
        ("Started", datetime.fromtimestamp(START_TIME).strftime("%Y-%m-%d %H:%M")),
    ]))


# ═══════════════════════════════════════════════════════════
# ADMIN — /promote and /demote
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/promote(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_promote(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/promote @username` or reply to a message"))
    try:
        rights = ChatAdminRights(
            change_info=True, delete_messages=True, ban_users=True,
            invite_users=True, pin_messages=True, add_admins=False,
            manage_call=True, other=True,
        )
        await client(EditAdminRequest(chat_id, uid, rights, "Admin"))
        await log_action("Promote", await event.get_sender(), name)
        sender = await event.get_sender()
        await event.reply(action_line("👑", sender.first_name, "promoted", name)
                          + f"\n\n*{flavor('promote')}*")
    except Exception as e:
        await event.reply(error("Failed", f"`{e}`"))


@client.on(events.NewMessage(pattern=r"^/demote(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_demote(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/demote @username` or reply to a message"))
    try:
        empty = ChatAdminRights(
            change_info=False, delete_messages=False, ban_users=False,
            invite_users=False, pin_messages=False, add_admins=False,
            manage_call=False, other=False,
        )
        await client(EditAdminRequest(chat_id, uid, empty, ""))
        await log_action("Demote", await event.get_sender(), name)
        sender = await event.get_sender()
        await event.reply(action_line("⬇️", sender.first_name, "demoted", name))
    except Exception as e:
        await event.reply(error("Failed", f"`{e}`"))


@client.on(events.NewMessage(pattern=r"^/adminlist(?:@\w+)?$"))
async def cmd_adminlist(event):
    chat_id = event.chat_id
    try:
        admins = []
        async for u in client.iter_participants(chat_id):
            try:
                p = await client.get_permissions(chat_id, u.id)
                if p.is_admin or p.is_creator:
                    rank = "Creator" if p.is_creator else "Admin"
                    admins.append(f"{mention(u.id, u.first_name or str(u.id))} — {rank}")
            except Exception:
                continue
        if not admins:
            return await event.reply(error("No admins found"))
        await event.reply(list_panel("👑", "Admins", admins))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


# ═══════════════════════════════════════════════════════════
# ANTI-SPAM
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/antiflood(?:@\w+)?(?:\s+(\w+))?(?:\s+(\d+))?$"))
async def cmd_antiflood(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    mode = (event.pattern_match.group(1) or "").lower()
    n = event.pattern_match.group(2)
    if mode == "on":
        limit = int(n) if n else 5
        set_setting(chat_id, "antiflood", limit)
        return await event.reply(success("Anti-flood ON", [("Limit", f"{limit} msgs / 10s")]))
    if mode == "off":
        del_setting(chat_id, "antiflood")
        return await event.reply(success("Anti-flood OFF"))
    cur_l = get_setting(chat_id, "antiflood")
    state = f"ON ({cur_l}/10s)" if cur_l else "OFF"
    await event.reply(info("Anti-flood", [("Status", state), ("Usage", "`/antiflood on 5`")]))


@client.on(events.NewMessage(pattern=r"^/antiraid(?:@\w+)?(?:\s+(\w+))?$"))
async def cmd_antiraid(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    mode = (event.pattern_match.group(1) or "").lower()
    if mode == "on":
        set_setting(chat_id, "antiraid", 1)
        return await event.reply(success("Anti-raid ON", [("Policy", "auto-ban <60s")]))
    if mode == "off":
        del_setting(chat_id, "antiraid")
        return await event.reply(success("Anti-raid OFF"))
    state = "ON" if get_setting(chat_id, "antiraid") else "OFF"
    await event.reply(info("Anti-raid", [("Status", state)]))


_flood_tracker: dict[tuple, list] = {}


@client.on(events.NewMessage)
async def antiflood_watch(event):
    if not event.is_group:
        return
    limit = get_setting(event.chat_id, "antiflood")
    if not limit:
        return
    if await is_admin(event.chat_id, event.sender_id):
        return
    key = (event.chat_id, event.sender_id)
    now = time.time()
    arr = _flood_tracker.setdefault(key, [])
    arr.append(now)
    arr[:] = [t for t in arr if now - t < 10]
    if len(arr) >= int(limit):
        try:
            until = int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
            await apply_mute(event.chat_id, event.sender_id, until=until)
            await event.reply(success("Muted", [("Reason", "Flood"), ("Duration", "10m")]))
        except Exception:
            pass
        _flood_tracker[key] = []


# ═══════════════════════════════════════════════════════════
# BAN / KICK / FUCK / MUTE / UNBAN
# ═══════════════════════════════════════════════════════════

async def _send(event, text: str, buttons=None):
    try:
        await client.send_message(event.chat_id, text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)


async def _ban_like(event, flavor_key: str, label: str, icon: str):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", f"`/{flavor_key} @username` or reply"))
    try:
        await apply_ban(chat_id, uid)
        await log_action(label, await event.get_sender(), name)
        sender = await event.get_sender()
        buttons = [[Button.inline("🌙 Unban", f"unban:{uid}".encode())]]
        await _send(event,
                    action_line(icon, sender.first_name, f"{label.lower()}ed", name)
                    + f"\n\n*{flavor(flavor_key)}*",
                    buttons=buttons)
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/ban(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_ban(event):
    await _ban_like(event, "ban", "Ban", "🔨")


@client.on(events.NewMessage(pattern=r"^/fuck(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_fuck(event):
    await _ban_like(event, "fuck", "Fuck", "💀")


@client.on(events.NewMessage(pattern=r"^/kick(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_kick(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/kick @username` or reply"))
    try:
        await client.kick_participant(chat_id, uid)
        await log_action("Kick", await event.get_sender(), name)
        sender = await event.get_sender()
        await _send(event,
                    action_line("👢", sender.first_name, "kicked", name)
                    + f"\n\n*{flavor('kick')}*")
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/mute(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_mute(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/mute @username` or reply"))
    try:
        await apply_mute(chat_id, uid)
        await log_action("Mute", await event.get_sender(), name)
        sender = await event.get_sender()
        await _send(event,
                    action_line("🔇", sender.first_name, "muted", name)
                    + f"\n\n*{flavor('mute')}*")
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/tmute(?:@\w+)?(?:\s+(\d+[smhd]))?(?:\s+(.+))?$"))
async def cmd_tmute(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    tstr = event.pattern_match.group(1)
    if not tstr:
        return await event.reply(error("Usage", "`/tmute 10m @user` or reply"))
    secs = parse_time(tstr)
    if not secs:
        return await event.reply(error("Bad duration", "Use 10s / 5m / 2h / 1d"))
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/tmute 10m @username` or reply"))
    until = int((datetime.utcnow() + timedelta(seconds=secs)).timestamp())
    try:
        await apply_mute(chat_id, uid, until=until)
        await log_action("TMute", await event.get_sender(), name, extra=f"for {tstr}")
        sender = await event.get_sender()
        await _send(event, action_line("🔇", sender.first_name, f"muted {name} for {tstr}"))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/unban(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_unban(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/unban @username` or reply"))
    try:
        await apply_unmute(chat_id, uid)
        await log_action("Unban", await event.get_sender(), name)
        sender = await event.get_sender()
        await _send(event, action_line("🌙", sender.first_name, "unbanned", name))
    except Exception as e:
        await event.reply(error("Failed", str(e)))

@client.on(events.NewMessage(pattern=r"^/unmute(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_unmute(event):
    """Remove mute (send_messages restriction), but keep ban restrictions intact."""
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/unmute @username` or reply"))

    try:
        # Get current banned rights and only lift send_messages
        from telethon.tl.functions.channels import GetParticipantRequest
        try:
            participant = await client(GetParticipantRequest(chat_id, uid))
            current = participant.participant
        except Exception:
            current = None

        # Simpler approach: just reset send_messages to False, keep others as-is
        # Fetch current state via get_permissions
        perms = await client.get_permissions(chat_id, uid)

        # Build new rights — remove mute only
        # Keep view_messages restriction if banned (view_messages=True means banned)
        view_banned = not perms.is_admin and not getattr(perms, "view_messages", True)

        rights = ChatBannedRights(
            until_date=0,
            view_messages=view_banned,  # keep ban if user was banned
            send_messages=False,         # unmute
            send_media=False,
            send_stickers=False,
            send_gifs=False,
            send_games=False,
            send_inline=False,
            embed_links=False,
        )
        await client(EditBannedRequest(chat_id, uid, rights))
        await log_action("Unmute", await event.get_sender(), name)
        sender = await event.get_sender()
        await event.reply(action_line("🔊", sender.first_name, "unmuted", name))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.CallbackQuery(data=re.compile(rb"^unban:(\d+)$")))
async def cb_unban(event):
    uid = int(event.pattern_match.group(1))
    try:
        await apply_unmute(event.chat_id, uid)
        await event.answer("Unbanned ✅")
        try:
            await event.edit(f"🌙 User `{uid}` unbanned")
        except Exception:
            pass
    except Exception as e:
        await event.answer(f"Failed: {e}", alert=True)


# ═══════════════════════════════════════════════════════════
# FILTERS
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/filters(?:@\w+)?$"))
async def cmd_filters(event):
    chat_id = event.chat_id
    cur.execute("SELECT keyword, media_type FROM filters WHERE chat_id=?", (chat_id,))
    rows = cur.fetchall()
    if not rows:
        return await event.reply(error("No filters set"))
    items = [f"`{r['keyword']}`" for r in rows]
    await event.reply(list_panel("🔎", "Filters", items))


@client.on(events.NewMessage(pattern=r"^/filter(?:@\w+)?\s+(\S+)(?:\s+(.+))?$"))
async def cmd_filter(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    kw = event.pattern_match.group(1).lower()
    inline_resp = event.pattern_match.group(2)
    text = inline_resp
    media_type = None
    file_ref = None

    if event.is_reply:
        msg = await event.get_reply_message()
        if msg:
            if not text and msg.message:
                text = msg.message
            if msg.media:
                media_type = type(msg.media).__name__
                file_ref = f"msg:{chat_id}:{msg.id}"

    if not text and not file_ref:
        return await event.reply(error("Usage", "`/filter kw response` or reply to a message"))

    cur.execute(
        "INSERT OR REPLACE INTO filters(chat_id,keyword,text,media_type,file_id) VALUES(?,?,?,?,?)",
        (chat_id, kw, text, media_type, file_ref),
    )
    conn.commit()
    fields = [("Keyword", f"`{kw}`")]
    if media_type:
        fields.append(("Media", media_type))
    await event.reply(success("Filter saved", fields))


@client.on(events.NewMessage(pattern=r"^/stop(?:@\w+)?\s+(.+)$"))
async def cmd_stop_filter(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    kw = event.pattern_match.group(1).lower()
    cur.execute("DELETE FROM filters WHERE chat_id=? AND keyword=?", (chat_id, kw))
    conn.commit()
    if cur.rowcount:
        await event.reply(success(f"Filter removed: {kw}"))
    else:
        await event.reply(error(f"No filter `{kw}`"))


# ═══════════════════════════════════════════════════════════
# PINS
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/pin(?:@\w+)?$"))
async def cmd_pin(event):
    if not await require_admin(event):
        return
    if not event.is_reply:
        return await event.reply(error("Reply to a message to pin it"))
    msg = await event.get_reply_message()
    try:
        await client.pin_message(event.chat_id, msg.id, notify=False)
        await event.reply(success("Pinned"))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/unpin(?:@\w+)?$"))
async def cmd_unpin(event):
    if not await require_admin(event):
        return
    try:
        await client.unpin_message(event.chat_id)
        await event.reply(success("Unpinned"))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


# ═══════════════════════════════════════════════════════════
# LOCKS
# ═══════════════════════════════════════════════════════════

LOCK_TYPES = {
    "links": dict(embed_links=True),
    "media": dict(send_media=True),
    "stickers": dict(send_stickers=True),
    "gifs": dict(send_gifs=True),
    "games": dict(send_games=True),
    "inline": dict(send_inline=True),
    "polls": dict(send_polls=True),
}


async def _apply_locks(chat_id: int):
    cur.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,))
    types = [r["lock_type"] for r in cur.fetchall()]
    kwargs = {}
    for t in types:
        kwargs.update(LOCK_TYPES.get(t, {}))
    rights = ChatBannedRights(until_date=0, **kwargs)
    await client(EditChatDefaultBannedRightsRequest(chat_id, rights))


@client.on(events.NewMessage(pattern=r"^/lock(?:@\w+)?\s+(\w+)$"))
async def cmd_lock(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    t = event.pattern_match.group(1).lower()
    if t not in LOCK_TYPES:
        return await event.reply(error(f"Unknown lock", f"Try: {', '.join(LOCK_TYPES)}"))
    cur.execute("INSERT OR IGNORE INTO locks VALUES(?,?)", (chat_id, t))
    conn.commit()
    await _apply_locks(chat_id)
    await event.reply(success(f"Locked: {t}"))


@client.on(events.NewMessage(pattern=r"^/lockall(?:@\w+)?$"))
async def cmd_lockall(event):
    """Lock the entire chat — only admins can send messages."""
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    try:
        rights = ChatBannedRights(
            until_date=0,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True,
            send_polls=True,
        )
        await client(EditChatDefaultBannedRightsRequest(chat_id, rights))
        await event.reply(success("Chat locked", [("Note", "Only admins can send messages")]))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/unlockall(?:@\w+)?$"))
async def cmd_unlockall(event):
    """Fully unlock the chat — everyone can send anything."""
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    try:
        # Clear any stored lock flags in DB
        cur.execute("DELETE FROM locks WHERE chat_id=?", (chat_id,))
        conn.commit()
        # Reset all restrictions
        await client(EditChatDefaultBannedRightsRequest(chat_id, ChatBannedRights(until_date=0)))
        await event.reply(success("Chat unlocked"))
    except Exception as e:
        await event.reply(error("Failed", str(e)))

@client.on(events.NewMessage(pattern=r"^/lock_media(?:@\w+)?$"))
async def cmd_lock_media(event):
    """Lock only media — text still allowed."""
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    try:
        # Preserve current lock state — only add media restriction
        cur.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,))
        existing = {r["lock_type"] for r in cur.fetchall()}
        existing.add("media")

        kwargs = {}
        for t in existing:
            kwargs.update(LOCK_TYPES.get(t, {}))
        # Ensure only media-related restrictions, keep other stored types
        kwargs["send_media"] = True
        kwargs["send_stickers"] = True
        kwargs["send_gifs"] = True

        rights = ChatBannedRights(until_date=0, **kwargs)
        await client(EditChatDefaultBannedRightsRequest(chat_id, rights))

        cur.execute("INSERT OR IGNORE INTO locks VALUES(?,?)", (chat_id, "media"))
        conn.commit()
        await event.reply(success("Media locked", [("Note", "Text still allowed")]))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/unlock_media(?:@\w+)?$"))
async def cmd_unlock_media(event):
    """Unlock media only."""
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    try:
        cur.execute("DELETE FROM locks WHERE chat_id=? AND lock_type IN ('media','stickers','gifs')",
                    (chat_id,))
        conn.commit()

        cur.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,))
        remaining = {r["lock_type"] for r in cur.fetchall()}
        kwargs = {}
        for t in remaining:
            kwargs.update(LOCK_TYPES.get(t, {}))

        rights = ChatBannedRights(until_date=0, **kwargs)
        await client(EditChatDefaultBannedRightsRequest(chat_id, rights))
        await event.reply(success("Media unlocked"))
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/locks(?:@\w+)?$"))
async def cmd_locks(event):
    chat_id = event.chat_id
    cur.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,))
    rows = cur.fetchall()
    if not rows:
        return await event.reply(error("No locks active"))
    await event.reply(list_panel("🔒", "Active locks", [r["lock_type"] for r in rows]))


# ═══════════════════════════════════════════════════════════
# TAG ALL
# ═══════════════════════════════════════════════════════════

_tag_cancel: set[int] = set()


@client.on(events.NewMessage(pattern=r"^/tagall(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_tagall(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    text = event.pattern_match.group(1) or "📣 Attention everyone!"
    _tag_cancel.discard(chat_id)

    async def run():
        try:
            batch = []
            async for u in client.iter_participants(chat_id):
                if u.bot or u.deleted:
                    continue
                batch.append(mention(u.id, u.first_name or "user"))
                if len(batch) >= 5:
                    if chat_id in _tag_cancel:
                        return
                    await client.send_message(chat_id, f"{text}\n" + " ".join(batch))
                    batch = []
                    await asyncio.sleep(1.5)
            if batch:
                await client.send_message(chat_id, f"{text}\n" + " ".join(batch))
        except Exception as e:
            await client.send_message(chat_id, error("Tag failed", str(e)))

    asyncio.create_task(run())
    await event.reply(success("Tagging started", [("Note", "use /cancel to stop")]))


@client.on(events.NewMessage(pattern=r"^/cancel(?:@\w+)?$"))
async def cmd_cancel(event):
    _tag_cancel.add(event.chat_id)
    await event.reply(success("Tagging cancelled"))


# ═══════════════════════════════════════════════════════════
# WARNINGS
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/setwarns(?:@\w+)?\s+(\d+)$"))
async def cmd_setwarns(event):
    if not await require_admin(event):
        return
    n = int(event.pattern_match.group(1))
    if n < 1 or n > 20:
        return await event.reply(error("Invalid", "Choose 1–20"))
    set_setting(event.chat_id, "warn_limit", n)
    await event.reply(success(f"Warn limit set to {n}"))


def warn_limit(chat_id: int) -> int:
    return int(get_setting(chat_id, "warn_limit", 3))


@client.on(events.NewMessage(pattern=r"^/warn(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_warn(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/warn @username` or reply"))
    cur.execute("INSERT OR IGNORE INTO warnings VALUES(?,?,0)", (chat_id, uid))
    cur.execute("UPDATE warnings SET count=count+1 WHERE chat_id=? AND user_id=?", (chat_id, uid))
    conn.commit()
    cur.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, uid))
    count = cur.fetchone()["count"]
    limit = warn_limit(chat_id)
    bar = "▰" * count + "▱" * max(0, limit - count)

    if count >= limit:
        try:
            await apply_mute(chat_id, uid)
            cur.execute("UPDATE warnings SET count=0 WHERE chat_id=? AND user_id=?", (chat_id, uid))
            conn.commit()
            await log_action("Warn-limit mute", await event.get_sender(), name)
            return await _send(event,
                f"⚠️ **{name}** muted — warn limit\n\n  {BULLET} {bar} {limit}/{limit}")
        except Exception as e:
            return await event.reply(error("Failed", str(e)))

    await event.reply(
        f"⚠️ **{name}** warned — {count}/{limit}\n\n  {BULLET} {bar}"
    )


@client.on(events.NewMessage(pattern=r"^/unwarn(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_unwarn(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    uid, name = await resolve_target(event)
    if not uid:
        return await event.reply(error("Usage", "`/unwarn @username` or reply"))
    cur.execute("UPDATE warnings SET count=MAX(count-1,0) WHERE chat_id=? AND user_id=?",
                (chat_id, uid))
    conn.commit()
    cur.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, uid))
    row = cur.fetchone()
    count = row["count"] if row else 0
    limit = warn_limit(chat_id)
    bar = "▰" * count + "▱" * max(0, limit - count)
    await event.reply(f"✅ **{name}** unwarned — {count}/{limit}\n\n  {BULLET} {bar}")


# ═══════════════════════════════════════════════════════════
# PURGE
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/purge(?:@\w+)?(?:\s+(\d+))?$"))
async def cmd_purge(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    n_arg = event.pattern_match.group(1)
    ids: list[int] = []

    if event.is_reply:
        # Reply-based purge — use message IDs directly (no history fetch)
        reply = await event.get_reply_message()

        # Deleted from reply to command message
        start = reply.id
        end = event.message.id

        if end <= start:
            return await event.reply(error("Can't purge — reply is newer than command"))

        # Build ID range (supergroup IDs are sequential)
        ids = list(range(start, end + 1))

    elif n_arg:
        # /purge 50 — delete last N by counting backwards from command
        n = min(int(n_arg), 100)
        end = event.message.id
        start = max(1, end - n)
        ids = list(range(start, end + 1))

    else:
        return await event.reply(error("Usage", "Reply to a message or use `/purge 50`"))

    if not ids:
        return await event.reply(error("Nothing to purge"))

    # Delete in chunks of 100
    deleted = 0
    failed = 0
    for i in range(0, len(ids), 100):
        chunk = ids[i:i+100]
        try:
            await client.delete_messages(chat_id, chunk)
            deleted += len(chunk)
        except Exception:
            for mid in chunk:
                try:
                    await client.delete_messages(chat_id, mid)
                    deleted += 1
                except Exception:
                    failed += 1

    notice = await event.reply(
        success(f"Purged {deleted} messages")
        + (f"\n\n  {BULLET} Failed: {failed} (older than 48h or not deletable)" if failed else "")
    )
    await asyncio.sleep(3)
    try:
        await notice.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# GREETINGS — welcome + goodbye with photo/GIF/video
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/setwelcome(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_setwelcome(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    text = event.pattern_match.group(1)
    media_ref = None
    media_kind = None

    if event.is_reply:
        msg = await event.get_reply_message()
        if msg:
            if not text and msg.message:
                text = msg.message
            if msg.photo:
                media_kind = "photo"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.video:
                media_kind = "video"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.gif:
                media_kind = "gif"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.document:
                media_kind = "document"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.sticker:
                media_kind = "sticker"
                media_ref = f"msg:{chat_id}:{msg.id}"

    if not text and not media_ref:
        return await event.reply(error("Usage",
            "`/setwelcome text` or reply to a photo/GIF/video"))

    fields = []
    if text:
        set_setting(chat_id, "welcome_text", text)
        fields.append(("Text", "set"))
    if media_ref:
        set_setting(chat_id, "welcome_media", media_ref)
        fields.append(("Media", media_kind))
    set_setting(chat_id, "greetings", "on")
    await event.reply(success("Welcome saved", fields))


@client.on(events.NewMessage(pattern=r"^/setgoodbye(?:@\w+)?(?:\s+(.+))?$"))
async def cmd_setgoodbye(event):
    if not await require_admin(event):
        return
    chat_id = event.chat_id
    text = event.pattern_match.group(1)
    media_ref = None
    media_kind = None

    if event.is_reply:
        msg = await event.get_reply_message()
        if msg:
            if not text and msg.message:
                text = msg.message
            if msg.photo:
                media_kind = "photo"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.video:
                media_kind = "video"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.gif:
                media_kind = "gif"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.document:
                media_kind = "document"
                media_ref = f"msg:{chat_id}:{msg.id}"
            elif msg.sticker:
                media_kind = "sticker"
                media_ref = f"msg:{chat_id}:{msg.id}"

    if not text and not media_ref:
        return await event.reply(error("Usage",
            "`/setgoodbye text` or reply to a photo/GIF/video"))

    fields = []
    if text:
        set_setting(chat_id, "goodbye_text", text)
        fields.append(("Text", "set"))
    if media_ref:
        set_setting(chat_id, "goodbye_media", media_ref)
        fields.append(("Media", media_kind))
    set_setting(chat_id, "greetings", "on")
    await event.reply(success("Goodbye saved", fields))


@client.on(events.NewMessage(pattern=r"^/off(?:@\w+)?$"))
async def cmd_off(event):
    if not await require_admin(event):
        return
    set_setting(event.chat_id, "greetings", "off")
    await event.reply(success("Greetings disabled"))


def _fmt_greeting(template: str, user, chat) -> str:
    return (
        template
        .replace("{mention}", mention(user.id, user.first_name or "user"))
        .replace("{name}", user.first_name or "user")
        .replace("{id}", str(user.id))
        .replace("{chat}", getattr(chat, "title", "the group"))
    )


_join_seen: dict[tuple, float] = {}


async def _send_stored_media(chat_id: int, ref: str, caption: str) -> bool:
    """Re-send a stored msg:<chat>:<id> reference."""
    try:
        _, src_chat, src_id = ref.split(":")
        src_msg = await client.get_messages(int(src_chat), ids=int(src_id))
        if src_msg and src_msg.media:
            await client.send_file(chat_id, src_msg.media, caption=caption or None)
            return True
    except Exception as e:
        log(f"[stored media failed] {ref}: {e}")
    return False


@client.on(events.ChatAction)
async def on_chat_action(event):
    if not event.is_group:
        return
    chat_id = event.chat_id
    if get_setting(chat_id, "greetings", "on") != "on":
        return

    if event.user_joined:
        try:
            user = await event.get_user()
        except Exception:
            return
        if not user:
            return

        key = (chat_id, user.id)
        now = time.time()
        if now - _join_seen.get(key, 0) < 5:
            return
        _join_seen[key] = now

        template = get_setting(chat_id, "welcome_text")
        media = get_setting(chat_id, "welcome_media")
        chat = await event.get_chat()

        caption = _fmt_greeting(template, user, chat) if template else \
            f"👋 Welcome, {mention(user.id, user.first_name)}!"

        if media:
            if await _send_stored_media(chat_id, media, caption):
                return
        # Fallback to nekos or text
        if not template:
            if not await send_media_reply(event, "welcome", caption):
                await event.reply(caption)
        else:
            await event.reply(caption)

    elif event.user_left or event.user_kicked:
        try:
            user = await event.get_user()
        except Exception:
            return
        if not user:
            return

        key = (chat_id, user.id, "leave")
        now = time.time()
        if now - _join_seen.get(key, 0) < 5:
            return
        _join_seen[key] = now

        template = get_setting(chat_id, "goodbye_text")
        media = get_setting(chat_id, "goodbye_media")
        chat = await event.get_chat()

        caption = _fmt_greeting(template, user, chat) if template else \
            f"👋 Goodbye, {mention(user.id, user.first_name)}!"

        if media:
            if await _send_stored_media(chat_id, media, caption):
                return
        if not template:
            if not await send_media_reply(event, "goodbye", caption):
                await event.reply(caption)
        else:
            await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# AFK / BRB
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/?afk(?:@\w+)?(?:\s+(.+))?$", func=lambda e: e.is_group))
async def cmd_afk(event):
    # Slash-less trigger safety: only fire if the message starts with "afk"
    msg = event.message.message or ""
    if not msg.lower().startswith("afk"):
        return
    reason = (event.pattern_match.group(1) or "AFK").strip()
    cur.execute("INSERT OR REPLACE INTO afk VALUES(?,?,?)",
                (event.sender_id, reason, time.time()))
    conn.commit()
    sender = await event.get_sender()
    caption = (
        f"💤 **{sender.first_name}** is now away\n\n"
        f"  {BULLET} Reason: {reason}"
    )
    if not await send_media_reply(event, "afk", caption):
        await event.reply(caption)


@client.on(events.NewMessage(pattern=r"^/?brb(?:@\w+)?(?:\s+(.+))?$", func=lambda e: e.is_group))
async def cmd_brb(event):
    msg = event.message.message or ""
    if not msg.lower().startswith("brb"):
        return
    reason = (event.pattern_match.group(1) or "BRB").strip()
    cur.execute("INSERT OR REPLACE INTO afk VALUES(?,?,?)",
                (event.sender_id, reason, time.time()))
    conn.commit()
    sender = await event.get_sender()
    caption = (
        f"🔙 **{sender.first_name}** will be back\n\n"
        f"  {BULLET} Note: {reason}"
    )
    if not await send_media_reply(event, "brb", caption):
        await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# CONSENT SYSTEM — hug / kiss / sex
# ═══════════════════════════════════════════════════════════

pending_perms: dict[int, dict] = {}


async def request_consent(event, action: str):
    sender = await event.get_sender()
    uid, name = await resolve_target(event)

    if not uid:
        return await event.reply(error("Usage",
            f"Reply to someone or use `/{action} @username`"))

    if uid == sender.id:
        return await event.reply(error("Hmm", "You can't do that to yourself"))

    sender_m = mention(sender.id, sender.first_name)
    target_m = mention(uid, name)

    prompt = (
        f"💌 **Permission request**\n\n"
        f"  {BULLET} From: {sender_m}\n"
        f"  {BULLET} To: {target_m}\n"
        f"  {BULLET} Action: {action}\n\n"
        f"{target_m}, do you accept?"
    )

    sent = await event.reply(prompt, buttons=[
        [Button.inline("✅ Accept", f"perm:yes:{sender.id}:{uid}:{action}".encode()),
         Button.inline("❌ Decline", f"perm:no:{sender.id}:{uid}:{action}".encode())],
    ])

    pending_perms[sent.id] = {
        "requester_id": sender.id,
        "requester_name": sender.first_name,
        "target_id": uid,
        "target_name": name,
        "action": action,
        "chat_id": event.chat_id,
    }

    asyncio.create_task(_expire_permission(sent.id, event.chat_id))


async def _expire_permission(msg_id: int, chat_id: int):
    await asyncio.sleep(PERMISSION_TIMEOUT)
    if msg_id in pending_perms:
        info_ = pending_perms.pop(msg_id)
        try:
            await client.edit_message(
                chat_id, msg_id,
                f"⏱ **Request expired**\n\n  {BULLET} {info_['target_name']} didn't respond"
            )
        except Exception:
            pass


@client.on(events.CallbackQuery(data=re.compile(rb"^perm:(yes|no):(\d+):(\d+):(\w+)$")))
async def cb_permission(event):
    choice = event.pattern_match.group(1).decode()
    requester_id = int(event.pattern_match.group(2))
    target_id = int(event.pattern_match.group(3))
    action = event.pattern_match.group(4).decode()

    if event.sender_id != target_id:
        await event.answer("This request isn't for you", alert=True)
        return

    info_ = pending_perms.pop(event.message_id, None)
    if not info_:
        await event.answer("This request has expired", alert=True)
        return

    target_user = await client.get_entity(target_id)
    target_name = getattr(target_user, "first_name", "user")

    if choice == "no":
        await event.edit(f"💔 **{target_name}** declined the {action}")
        await event.answer("Declined")
        return

    requester_user = await client.get_entity(requester_id)
    requester_name = getattr(requester_user, "first_name", "user")

    emoji_pool = ["💖", "💕", "💗", "💞", "💓", "🌸"]
    e = random.choice(emoji_pool)
    caption = f"{e} {mention(requester_id, requester_name)} had done **{action}** with {mention(target_id, target_name)} {e}"

    try:
        await event.delete()
    except Exception:
        pass

    media = await pick_media(action)
    if media:
        try:
            await client.send_file(event.chat_id, media, caption=caption)
            await event.answer("Accepted 💖")
            return
        except Exception as e2:
            log(f"[consent media failed] {e2}")

    # No media — send hint + caption
    if action in CUSTOM_ONLY:
        await client.send_message(event.chat_id,
            f"🖼 No media in `assets/{action}/`\n\n{caption}")
    else:
        await client.send_message(event.chat_id, caption)
    await event.answer("Accepted 💖")


# ═══════════════════════════════════════════════════════════
# CONSENT COMMANDS — hug / kiss / sex
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=rf"^/({'|'.join(CONSENT_ACTIONS)})(?:@\w+)?(?:\s+.*)?$"))
async def cmd_consent(event):
    action = event.pattern_match.group(1).lower()
    await request_consent(event, action)


# ═══════════════════════════════════════════════════════════
# DIRECT CUSTOM — dance / bite / lick / cuddle / kill (no consent)
# ═══════════════════════════════════════════════════════════

DIRECT_CUSTOM_VERBS = {
    "bite": ("bites", "bites"),
    "lick": ("licks", "licks"),
    "kill": ("kills", "kills"),
    "punch": ("punches", "punches"),
    "spank": ("spanks","spanks")
}


@client.on(events.NewMessage(pattern=rf"^/({'|'.join(DIRECT_CUSTOM_VERBS)})(?:@\w+)?(?:\s+.*)?$"))
async def cmd_direct_custom(event):
    action = event.pattern_match.group(1).lower()
    with_target_verb, no_target_verb = DIRECT_CUSTOM_VERBS[action]
    sender = await event.get_sender()

    target = ""
    target_id = 0
    if event.is_reply:
        msg = await event.get_reply_message()
        try:
            u = await client.get_entity(msg.sender_id)
            target = u.first_name
            target_id = u.id
        except Exception:
            pass
    else:
        # Try parsing @username / user id from command args
        text = event.message.message or ""
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            arg = parts[1].split()[0]
            if arg.startswith("@"):
                try:
                    u = await client.get_entity(arg)
                    target = u.first_name
                    target_id = u.id
                except Exception:
                    pass
            elif arg.lstrip("-").isdigit():
                try:
                    u = await client.get_entity(int(arg))
                    target = u.first_name
                    target_id = u.id
                except Exception:
                    pass

    icon = {
        "kill": "⚔️",
        "spank": "😏",
        "bite": "✨",
        "lick": "✨",
        "punch": "✨",
    }
    icon = icon.get(action, "✨" )

    if target:
        caption = f"{icon} **{sender.first_name}** {with_target_verb} **{target}** {icon}"
    else:
        caption = f"{icon} **{sender.first_name}** {no_target_verb} {icon}"

    if not await send_media_reply(event, action, caption):
        await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# SELF-ONLY FUN — shy (custom assets)
# ═══════════════════════════════════════════════════════════

SELF_ACTIONS = {
    "shy": "is shy",
}


@client.on(events.NewMessage(pattern=rf"^/({'|'.join(SELF_ACTIONS)})(?:@\w+)?$"))
async def cmd_self_fun(event):
    action = event.pattern_match.group(1).lower()
    verb = SELF_ACTIONS.get(action, action)
    sender = await event.get_sender()

    target = ""
    target_id = 0
    if event.is_reply:
        msg = await event.get_reply_message()
        try:
            u = await client.get_entity(msg.sender_id)
            target = u.first_name
            target_id = u.id
        except Exception:
            pass

    if target:
        caption = f"✨ {mention(sender.id, sender.first_name)} {verb} around {mention(target_id, target)} ✨"
    else:
        caption = f"✨ {mention(sender.id, sender.first_name)} {verb} ✨"

    if not await send_media_reply(event, action, caption):
        await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# NEKOS FUN — pat / slap / bonk / tickle / cry / smug / etc.
# ═══════════════════════════════════════════════════════════

NEKOS_FUN = {
    "angry": "is angry at",
    "pat": "pats",
    "slap": "slaps",
    "bonk": "bonks",
    "tickle": "tickles",
    "cry": "cries",
    "smug": "smugs",
    "blush": "blushes",
    "smile": "smiles",
    "wave": "waves",
    "wink": "winks",
    "pout": "pouts",
    "sad": "is sad",
    "happy": "is happy",
    "laugh": "laughs",
    "facepalm": "facepalms",
    "highfive": "high-fives",
    "murder": "murders",
}


@client.on(events.NewMessage(pattern=rf"^/({'|'.join(NEKOS_FUN)})(?:@\w+)?(?:\s+.*)?$"))
async def cmd_nekos_fun(event):
    action = event.pattern_match.group(1).lower()
    verb = NEKOS_FUN[action]
    sender = await event.get_sender()

    target = ""
    target_id = 0
    if event.is_reply:
        msg = await event.get_reply_message()
        try:
            u = await client.get_entity(msg.sender_id)
            target = u.first_name
            target_id = u.id
        except Exception:
            pass
    else:
        text = event.message.message or ""
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            arg = parts[1].split()[0]
            if arg.startswith("@"):
                try:
                    u = await client.get_entity(arg)
                    target = u.first_name
                    target_id = u.id
                except Exception:
                    pass
            elif arg.lstrip("-").isdigit():
                try:
                    u = await client.get_entity(int(arg))
                    target = u.first_name
                    target_id = u.id
                except Exception:
                    pass

    if target:
        caption = f"✨ **{sender.first_name}** {verb} **{target}** ✨"
    else:
        caption = f"✨ **{sender.first_name}** {verb} ✨"

    if not await send_media_reply(event, action, caption):
        await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# SOCIAL — couple / waifu / wish
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage(pattern=r"^/couple(?:@\w+)?$"))
async def cmd_couple(event):
    chat_id = event.chat_id
    try:
        users = []
        async for u in client.iter_participants(chat_id):
            if not u.bot and not u.deleted:
                users.append(u)
        if len(users) < 2:
            return await event.reply(error("Need at least 2 members"))
        a, b = random.sample(users, 2)
        pct = random.randint(50, 100)
        caption = (
            f"🎀 **Couple Of The Day** 🎀\n\n"
            f"  {BULLET} {mention(a.id, a.first_name)} + {mention(b.id, b.first_name)}\n"
            f"  {BULLET} Compatibility: {pct}%"
        )
        if not await send_media_reply(event, "couple", caption):
            await event.reply(caption)
    except Exception as e:
        await event.reply(error("Failed", str(e)))

async def _pick_target_or_random(event):
    """Return (user_id, name). Uses target if given, else random member."""
    uid, name = await resolve_target(event)
    if uid:
        return uid, name
    # Pick random member
    try:
        users = []
        async for u in client.iter_participants(event.chat_id):
            if not u.bot and not u.deleted and u.id != event.sender_id:
                users.append(u)
        if users:
            u = random.choice(users)
            return u.id, getattr(u, "first_name", str(u.id))
    except Exception:
        pass
    return None, None


@client.on(events.NewMessage(pattern=r"^/love(?:@\w+)?(?:\s+.*)?$"))
async def cmd_love(event):
    sender = await event.get_sender()
    uid, name = await _pick_target_or_random(event)
    if not uid:
        return await event.reply(error("No target found"))
    pct = random.randint(1, 100)

    # Heart progression
    if pct >= 80:
        bar = "❤️❤️❤️❤️❤️"
    elif pct >= 60:
        bar = "❤️❤️❤️❤️"
    elif pct >= 40:
        bar = "❤️❤️❤️"
    elif pct >= 20:
        bar = "❤️❤️"
    else:
        bar = "❤️"

    caption = (
        f"💕 **Love**\n\n"
        f"  {BULLET} {mention(sender.id, sender.first_name)} → {mention(uid, name)}\n"
        f"  {BULLET} Bond: {pct}%\n"
        f"  {BULLET} {bar}"
    )
    if not await send_media_reply(event, "love", caption):
        await event.reply(caption)


@client.on(events.NewMessage(pattern=r"^/crush(?:@\w+)?(?:\s+.*)?$"))
async def cmd_crush(event):
    sender = await event.get_sender()
    uid, name = await _pick_target_or_random(event)
    if not uid:
        return await event.reply(error("No target found"))
    pct = random.randint(1, 100)

    if pct >= 80:
        bar = "💘💘💘💘💘"
    elif pct >= 60:
        bar = "💘💘💘💘"
    elif pct >= 40:
        bar = "💘💘💘"
    elif pct >= 20:
        bar = "💘💘"
    else:
        bar = "💘"

    caption = (
        f"💘 **{sender.first_name}'s secret crush is {name}**\n\n"
        f"  {BULLET} Bond: {pct}%\n"
        f"  {BULLET} {bar}"
    )
    if not await send_media_reply(event, "crush", caption):
        await event.reply(caption)


@client.on(events.NewMessage(pattern=r"^/iq(?:@\w+)?(?:\s+.*)?$"))
async def cmd_iq(event):
    uid, name = await _pick_target_or_random(event)
    if not uid:
        return await event.reply(error("No target found"))

    iq = random.randint(60, 180)

    if iq >= 150:
        verdict = "Genius level"
    elif iq >= 130:
        verdict = "Very smart"
    elif iq >= 110:
        verdict = "Above average"
    elif iq >= 90:
        verdict = "Average"
    elif iq >= 75:
        verdict = "Below average"
    else:
        verdict = "Room temperature"

    await event.reply(
        f"🧠 **IQ Test**\n\n"
        f"  {BULLET} User: {mention(uid, name)}\n"
        f"  {BULLET} IQ: **{iq}**\n"
        f"  {BULLET} Verdict: {verdict}"
    )


@client.on(events.NewMessage(pattern=r"^/waifu(?:@\w+)?$"))
async def cmd_waifu(event):
    chat_id = event.chat_id
    sender = await event.get_sender()
    try:
        users = []
        async for u in client.iter_participants(chat_id):
            if not u.bot and not u.deleted:
                users.append(u)
        if not users:
            return await event.reply(error("No members found"))
        w = random.choice(users)
        pct = random.randint(50, 100)
        caption = (
            f"✨ **{sender.first_name}'s Today's Waifu** ✨\n\n"
            f"  {BULLET} {mention(w.id, w.first_name)}\n"
            f"  {BULLET} Bond: {pct}%"
        )
        if not await send_media_reply(event, "waifu", caption):
            await event.reply(caption)
    except Exception as e:
        await event.reply(error("Failed", str(e)))


@client.on(events.NewMessage(pattern=r"^/wish(?:@\w+)?\s+(.+)$"))
async def cmd_wish(event):
    text = event.pattern_match.group(1)
    pct = random.randint(1, 100)
    caption = (
        f"🌠 **Wish**\n\n"
        f"  {BULLET} \"{text}\"\n"
        f"  {BULLET} Chance: {pct}%"
    )
    if not await send_media_reply(event, "wish", caption):
        await event.reply(caption)


# ═══════════════════════════════════════════════════════════
# GAMES — truth / dare / wyr
# ═══════════════════════════════════════════════════════════

TRUTH_POOL = [
    "What's your most embarrassing childhood memory?",
    "Who in this group would you trade lives with?",
    "What's the last lie you told?",
    "What's a secret you've never told anyone here?",
    "Who was your first crush?",
    "What's the most awkward thing you've done on a date?",
    "Have you ever ghosted someone? Why?",
    "What's the biggest mistake you've made this year?",
    "Who in this group would you swap phones with?",
    "What's the weirdest dream you remember?",
    "Have you ever cried during a movie? Which one?",
    "What's the most childish thing you still do?",
    "Who do you text the most?",
    "What's the worst gift you've ever received?",
    "What's the last thing you searched on your phone?",
    "Who in this group would you trust with a secret?",
    "What's a habit you wish you could quit?",
    "What's your biggest fear?",
    "Have you ever pretended to like someone?",
    "What's the most embarrassing thing in your camera roll?",
    "What's the biggest lie you've told a parent?",
    "Who in this group is most likely to become famous?",
    "What's a song you're embarrassed to admit you like?",
    "Have you ever stalked an ex online?",
    "What's the longest you've gone without showering?",
    "What's the most illegal thing you've ever done?",
    "What's the last time you cried and why?",
    "Who in this group would you want on your team in a zombie apocalypse?",
    "What's the worst haircut you've ever had?",
    "What's something you've never told your best friend?",
    "What's the biggest thing you've broken?",
    "Have you ever faked being sick to avoid something?",
    "What's the most embarrassing thing your parents caught you doing?",
    "What's your most irrational fear?",
    "What's the worst advice you've ever given?",
    "Who in this group would you swap places with for a day?",
    "What's a compliment you've never received but want?",
    "What's the strangest thing you've ever eaten?",
    "What's the most money you've ever spent on one thing?",
    "What's the last thing that made you cry laughing?",
]

DARE_POOL = [
    "Send your most recent photo to the group.",
    "Send the last emoji you used as your only message for the next hour.",
    "Change your profile pic to something embarrassing for 24 hours.",
    "Send a voice note singing your favourite song.",
    "Text your crush 'hey' and screenshot the reply.",
    "Send a screenshot of your last 5 searches.",
    "Send your most unflattering selfie.",
    "Say 'I love everyone here' three times in the chat.",
    "Send a voice note saying a tongue twister five times fast.",
    "Reveal your most recent phone notification.",
    "Show your screen time for the last week.",
    "Type a full paragraph using only your non-dominant hand.",
    "Send a message to the group in all caps for the next 10 minutes.",
    "Send the 10th photo in your gallery.",
    "Voice note a dramatic reading of the last message in this chat.",
    "Compliment the last person who messaged here.",
    "Share your most embarrassing playlist name.",
    "Send a selfie with the goofiest face you can make.",
    "Voice note your best impression of someone in this group.",
    "Send a screenshot of your most recent chat with anyone.",
    "Post a status saying 'I love being roasted' for 1 hour.",
    "Say something nice about everyone in the last 5 messages.",
    "Voice note singing the alphabet but every letter is a different accent.",
    "Reveal what you're wearing right now.",
    "Send your most used emoji 20 times.",
    "Describe everyone in this chat in one word.",
    "Confess your guiltiest pleasure.",
    "Send a photo of the messiest part of your room.",
    "Text someone random 'thank you' and share their response.",
    "Give a 30-second speech in the voice notes about why you love this group.",
    "Send a selfie with a hat made out of whatever is nearest you.",
    "Type the next 5 messages with your eyes closed.",
    "Send your most recently taken screenshot.",
    "Do 10 push-ups and send proof.",
    "Voice note yourself saying a sentence that makes no sense.",
    "Tell everyone your worst habit.",
    "Share a photo from your childhood.",
    "Reveal the last thing you saved on Instagram/TikTok.",
    "Send a text to someone with 'I knew it' and screenshot their reply.",
    "Describe your day in exactly 3 emojis, no text.",
]

WYR_POOL = [
    ("Never sleep again", "Never eat again"),
    ("Always be 10 minutes late", "Always be 20 minutes early"),
    ("Have unlimited money", "Have unlimited time"),
    ("Be able to fly", "Be able to read minds"),
    ("Never use social media again", "Never watch any movie again"),
    ("Always speak in rhymes", "Always speak in third person"),
    ("Live in a mansion alone", "Live in a small apartment with 10 friends"),
    ("Only eat sweet food", "Only eat savoury food"),
    ("Never feel pain", "Never feel joy"),
    ("Be famous for something embarrassing", "Be forgotten for something great"),
    ("Have a rewind button for life", "Have a pause button for life"),
    ("Always know when someone's lying", "Always get away with lying"),
    ("Live without music", "Live without internet"),
    ("Only text in emojis", "Only text in voice notes"),
    ("Have a pet dragon", "Have a pet dinosaur"),
    ("Be able to time travel but only backwards", "Be able to time travel but only forwards"),
    ("Have unlimited free food", "Have unlimited free travel"),
    ("Be the funniest person in the room", "Be the smartest person in the room"),
    ("Never age", "Never get sick"),
    ("Always have to tell the truth", "Always have to lie"),
    ("Be able to teleport anywhere", "Be able to freeze time"),
    ("Have a photographic memory", "Be able to forget anything on command"),
    ("Have free Wi-Fi everywhere", "Have free food everywhere"),
    ("Only communicate through gifs", "Only communicate through memes"),
    ("Live 100 years in the past", "Live 100 years in the future"),
    ("Be able to talk to animals", "Be able to talk to plants"),
    ("Have a personal chef", "Have a personal trainer"),
    ("Own a private island", "Own a private jet"),
    ("Never have to work again", "Never have to sleep again"),
    ("Be a famous singer", "Be a famous actor"),
]


def _reply_target(event):
    """Return (id, name) of the target from reply or @username arg. Or (None, None)."""
    # handled inline in commands
    return None, None


@client.on(events.NewMessage(pattern=r"^/truth(?:@\w+)?(?:\s+.*)?$"))
async def cmd_truth(event):
    await _send_game(event, "🤔", "Truth", TRUTH_POOL)


@client.on(events.NewMessage(pattern=r"^/dare(?:@\w+)?(?:\s+.*)?$"))
async def cmd_dare(event):
    await _send_game(event, "😈", "Dare", DARE_POOL)


async def _send_game(event, icon: str, label: str, pool: list):
    target = ""
    if event.is_reply:
        msg = await event.get_reply_message()
        try:
            u = await client.get_entity(msg.sender_id)
            target = u.first_name
        except Exception:
            pass
    else:
        text = event.message.message or ""
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            arg = parts[1].split()[0]
            if arg.startswith("@"):
                try:
                    u = await client.get_entity(arg)
                    target = u.first_name
                except Exception:
                    pass
            elif arg.lstrip("-").isdigit():
                try:
                    u = await client.get_entity(int(arg))
                    target = u.first_name
                except Exception:
                    pass

    question = random.choice(pool)

    if target:
        out = f"{icon} **{label} for {target}**\n\n  {BULLET} {question}"
    else:
        out = f"{icon} **{label}**\n\n  {BULLET} {question}"

    await event.reply(out)


@client.on(events.NewMessage(pattern=r"^/wyr(?:@\w+)?$"))
async def cmd_wyr(event):
    a, b = random.choice(WYR_POOL)
    text = (
        f"🤷 **Would You Rather**\n\n"
        f"  {BULLET} A: {a}\n"
        f"  {BULLET} B: {b}\n\n"
        f"Vote now!"
    )
    sent = await event.reply(text, buttons=[
        [Button.inline("🅰️ A", b"wyr:A"), Button.inline("🅱️ B", b"wyr:B")]
    ])
    cur.execute(
        "INSERT OR REPLACE INTO settings(chat_id,key,value) VALUES(?,?,?)",
        (event.chat_id, f"wyr_opts_{sent.id}", f"{a}|{b}")
    )
    conn.commit()


@client.on(events.CallbackQuery(data=re.compile(rb"^wyr:([AB])$")))
async def cb_wyr(event):
    choice = event.pattern_match.group(1).decode()

    # Save vote
    cur.execute(
        "INSERT OR REPLACE INTO wyr_votes(msg_id, chat_id, user_id, choice) VALUES(?,?,?,?)",
        (event.message_id, event.chat_id, event.sender_id, choice)
    )
    conn.commit()

    # Load options
    cur.execute(
        "SELECT value FROM settings WHERE chat_id=? AND key=?",
        (event.chat_id, f"wyr_opts_{event.message_id}")
    )
    row = cur.fetchone()
    if not row:
        await event.answer("This poll has expired")
        return

    a_text, b_text = row["value"].split("|", 1)

    # Count votes
    cur.execute("SELECT choice, COUNT(*) c FROM wyr_votes WHERE msg_id=? GROUP BY choice",
                (event.message_id,))
    counts = {"A": 0, "B": 0}
    for r in cur.fetchall():
        counts[r["choice"]] = r["c"]

    total = counts["A"] + counts["B"]

    text = (
        f"🤷 **Would You Rather**\n\n"
        f"  {BULLET} A: {a_text} — {counts['A']} votes\n"
        f"  {BULLET} B: {b_text} — {counts['B']} votes\n\n"
        f"Voted: {total}"
    )

    try:
        await event.edit(text, buttons=[
            [Button.inline("🅰️ A", b"wyr:A"), Button.inline("🅱️ B", b"wyr:B")]
        ])
    except Exception:
        pass
    await event.answer(f"You voted {choice}")


# ═══════════════════════════════════════════════════════════
# MESSAGE HANDLER — filters + AFK clear + AFK mention
# ═══════════════════════════════════════════════════════════

@client.on(events.NewMessage)
async def message_handler(event):
    if not event.is_group:
        return
    msg = event.message.message or ""
    if not msg or msg.startswith("/"):
        return

        # ── 1. Filters ──
    try:
        text_lower = msg.lower()
        cur.execute(
            "SELECT keyword, text, file_id FROM filters WHERE chat_id=?",
            (event.chat_id,),
        )
        rows = cur.fetchall()
        for row in rows:
            kw = row["keyword"]

            # Smart matching
            if re.search(r"[^\w\s]", kw):
                # Contains symbols (@, #, ., etc.) → substring match
                matched = kw in text_lower
            else:
                # Pure word → word-boundary match
                matched = bool(re.search(rf"\b{re.escape(kw)}\b", text_lower))

            if matched:
                caption = row["text"] or ""
                fid = row["file_id"]

                if fid and fid.startswith("msg:"):
                    try:
                        _, src_chat, src_id = fid.split(":")
                        src_msg = await client.get_messages(int(src_chat), ids=int(src_id))
                        if src_msg and src_msg.media:
                            await client.send_file(event.chat_id, src_msg.media,
                                                   caption=caption or None)
                            return
                        elif src_msg and src_msg.message:
                            await event.reply(caption or src_msg.message)
                            return
                    except Exception as e:
                        log(f"[filter media failed] {e}")

                if caption:
                    await event.reply(caption)
                return
    except Exception as e:
        log(f"[filter error] {e}")

    # ── 2. AFK clear ──
    try:
        cur.execute("SELECT reason, since FROM afk WHERE user_id=?", (event.sender_id,))
        row = cur.fetchone()
        if row:
            gone_for = humanize_duration(time.time() - row["since"])
            cur.execute("DELETE FROM afk WHERE user_id=?", (event.sender_id,))
            conn.commit()
            sender = await event.get_sender()
            await event.reply(
                f"👋 **Welcome back, {sender.first_name}**\n\n"
                f"  {BULLET} Away for: {gone_for}\n"
                f"  {BULLET} Reason was: {row['reason']}"
            )
            return
    except Exception as e:
        log(f"[afk clear error] {e}")

    # ── 3. AFK mention ──
    try:
        for m in re.finditer(r"@(\w+)", msg):
            try:
                u = await client.get_entity(m.group(1))
            except Exception:
                continue
            cur.execute("SELECT reason, since FROM afk WHERE user_id=?", (u.id,))
            row = cur.fetchone()
            if row:
                gone_for = humanize_duration(time.time() - row["since"])
                await event.reply(
                    f"💤 **{u.first_name}** is AFK\n\n"
                    f"  {BULLET} Reason: {row['reason']}\n"
                    f"  {BULLET} Gone for: {gone_for}"
                )
                break
    except Exception as e:
        log(f"[afk mention error] {e}")


# ═══════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════

async def send_startup_message():
    if not STARTUP_NOTIFY:
        return
    me = await client.get_me()
    dest = STARTUP_NOTIFY
    if dest.lower() == "me":
        if me.bot:
            if not SUPERADMINS:
                print("⚠️ STARTUP_NOTIFY=me needs a user ID in bot mode. Skipping.")
                return
            dest = next(iter(SUPERADMINS))
        else:
            dest = "me"
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = (
            f"🚀 **Bot Online**\n\n"
            f"  {BULLET} Name: {BOT_NAME}\n"
            f"  {BULLET} User: @{me.username or me.id}\n"
            f"  {BULLET} Mode: {'Bot' if me.bot else 'User'}\n"
            f"  {BULLET} Started: {now}"
        )
        await client.send_message(dest, text)
        print(f"📨 Startup message sent to {dest}")
    except Exception as e:
        print(f"⚠️ Could not send startup message: {e}")


# ═══════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════

async def main():
    # Clean up broken media references from before the msg: refactor
    try:
        cur.execute("DELETE FROM filters WHERE file_id IS NOT NULL AND file_id NOT LIKE 'msg:%'")
        cleaned = cur.rowcount
        conn.commit()
        if cleaned:
            print(f"🧹 Cleaned {cleaned} broken media filters")
    except Exception:
        pass

    if BOT_TOKEN:
        await client.start(bot_token=BOT_TOKEN)
    else:
        await client.start()

    me = await client.get_me()
    print("=" * 50)
    print(f"✅ Logged in as {me.username or me.id} (bot={me.bot})")
    print(f"✨ {BOT_NAME} bot is running.")
    print(f"   Started at {datetime.now().isoformat(timespec='seconds')}")
    print(f"   DEBUG mode: {DEBUG}")
    print("=" * 50)

    await send_startup_message()
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down cleanly…")
    finally:
        try:
            client.loop.run_until_complete(client.disconnect())
        except Exception:
            pass
