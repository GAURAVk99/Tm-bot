import os
import json
import asyncio
from typing import Dict, Any, List

from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Message

# ------------------ CONFIG ------------------
API_ID = 20877162                # <-- change this
API_HASH = "6dfa90f0624d13f591753174e2c56e8a"     # <-- change this
BOT_TOKEN = "8324819345:AAFGhL7h3_dFu9_M_jS-nJ2ZiwGHMKIQZ_c"   # <-- change this

SESSIONS_DIR = "sessions"
RULES_FILE = "rules.json"

os.makedirs(SESSIONS_DIR, exist_ok=True)

# ------------------ STATE ------------------
user_states: Dict[int, str] = {}
pending_clients: Dict[int, Client] = {}
pending_codes: Dict[int, Dict[str, str]] = {}

active_forward_clients: Dict[int, Client] = {}
forward_tasks: Dict[int, asyncio.Task] = {}

# ------------------ RULES ------------------
def load_rules() -> Dict[str, Any]:
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_rules(rules: Dict[str, Any]):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

rules = load_rules()

def session_path_for(uid: int) -> str:
    return os.path.join(SESSIONS_DIR, f"user_{uid}")

def ensure_user_rule(uid: int):
    key = str(uid)
    if key not in rules:
        rules[key] = {
            "sources": [],
            "destinations": [],
            "keywords": [],
            "skip_media": False,
            "prefix": "",
            "suffix": ""
        }
        save_rules(rules)

def parse_id_list(text: str) -> List[int]:
    out = []
    for p in [p.strip() for p in text.split(",") if p.strip()]:
        try:
            out.append(int(p))
        except:
            pass
    return out

def is_user_logged_in(uid: int) -> bool:
    return os.path.exists(session_path_for(uid) + ".session")

# ------------------ BOT ------------------
bot = Client("saas_forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------ COMMAND HANDLERS ------------------
@bot.on_message(filters.command("start"))
async def cmd_start(c: Client, m: Message):
    uid = m.from_user.id
    user_states.pop(uid, None)

    text = (
        "👋 Welcome to Forwarder SaaS Bot!\n\n"
        "🤖 **Available Commands:**\n"
        "/login - Login with your Telegram account\n"
        "/set_sources - Set source chat IDs\n"
        "/set_destinations - Set destination chat IDs\n"
        "/set_options - Configure forwarding options\n"
        "/start_forwarding - Start forwarding messages\n"
        "/stop_forwarding - Stop forwarding\n"
        "/status - Check your current status\n"
        "/logout - Logout and delete session\n"
        "/cancel - Cancel current operation\n\n"
    )
    if is_user_logged_in(uid):
        text += "✅ **Status:** Logged in\n"
    else:
        text += "❌ **Status:** Not logged in\n"
    await m.reply_text(text)

@bot.on_message(filters.command("login"))
async def cmd_login(c: Client, m: Message):
    uid = m.from_user.id
    if is_user_logged_in(uid):
        await m.reply_text("✅ Already logged in.\nUse /logout to switch accounts.")
        return
    user_states[uid] = "awaiting_phone"
    await m.reply_text("📱 Send your phone number in international format (e.g. +919876543210)")

@bot.on_message(filters.command("cancel"))
async def cmd_cancel(c: Client, m: Message):
    uid = m.from_user.id
    temp_client = pending_clients.pop(uid, None)
    if temp_client:
        try:
            await temp_client.disconnect()
        except:
            pass
    pending_codes.pop(uid, None)
    user_states.pop(uid, None)
    await m.reply_text("❌ Operation cancelled.")

@bot.on_message(filters.command("status"))
async def cmd_status(c: Client, m: Message):
    uid = m.from_user.id
    ensure_user_rule(uid)
    r = rules[str(uid)]
    running = uid in forward_tasks and not forward_tasks[uid].done()
    text = (
        f"👤 User ID: {uid}\n"
        f"🔐 Session: {'✅' if is_user_logged_in(uid) else '❌'}\n"
        f"🔄 Forwarding: {'✅ Running' if running else '❌ Stopped'}\n"
        f"📥 Sources: {r['sources'] or 'Not set'}\n"
        f"📤 Destinations: {r['destinations'] or 'Not set'}\n"
        f"🔍 Keywords: {r['keywords'] or 'None'}\n"
        f"📷 Skip Media: {r['skip_media']}\n"
        f"📝 Prefix: {r['prefix']}\n"
        f"📝 Suffix: {r['suffix']}\n"
    )
    await m.reply_text(text)

@bot.on_message(filters.command("logout"))
async def cmd_logout(c: Client, m: Message):
    uid = m.from_user.id
    await stop_forwarding_for(uid)
    for ext in [".session", ".session-journal"]:
        p = session_path_for(uid) + ext
        if os.path.exists(p):
            os.remove(p)
    rules.pop(str(uid), None)
    save_rules(rules)
    await m.reply_text("✅ Logged out and session removed.")

# ------------------ TEXT HANDLER ------------------
@bot.on_message(filters.private & filters.text)
async def handle_text(c: Client, m: Message):
    uid = m.from_user.id
    text = m.text.strip()
    state = user_states.get(uid)

    # login flow
    if state == "awaiting_phone":
        phone = text
        temp_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH)
        await temp_client.connect()
        sent = await temp_client.send_code(phone)
        pending_clients[uid] = temp_client
        pending_codes[uid] = {"phone": phone, "hash": sent.phone_code_hash}
        user_states[uid] = "awaiting_otp"
        await m.reply_text("📩 Code sent. Send the OTP here.")
        return

    if state == "awaiting_otp":
        otp = text
        info = pending_codes.get(uid)
        temp_client = pending_clients.get(uid)
        try:
            await temp_client.sign_in(info["phone"], info["hash"], otp)
        except SessionPasswordNeeded:
            user_states[uid] = "awaiting_2fa"
            await m.reply_text("🔐 2FA enabled. Send your password.")
            return
        await temp_client.disconnect()
        pending_clients.pop(uid, None)
        pending_codes.pop(uid, None)
        user_states.pop(uid, None)
        ensure_user_rule(uid)
        await m.reply_text("✅ Login successful.\nUse /set_sources, /set_destinations then /start_forwarding.")
        return

    if state == "awaiting_2fa":
        pwd = text
        temp_client = pending_clients.get(uid)
        await temp_client.check_password(pwd)
        await temp_client.disconnect()
        pending_clients.pop(uid, None)
        pending_codes.pop(uid, None)
        user_states.pop(uid, None)
        ensure_user_rule(uid)
        await m.reply_text("✅ 2FA login successful.")
        return

    # rules setup
    if state == "awaiting_sources":
        ids = parse_id_list(text)
        rules[str(uid)]["sources"] = ids
        save_rules(rules)
        user_states.pop(uid, None)
        await m.reply_text(f"✅ Sources saved: {ids}")
        return

    if state == "awaiting_destinations":
        ids = parse_id_list(text)
        rules[str(uid)]["destinations"] = ids
        save_rules(rules)
        user_states.pop(uid, None)
        await m.reply_text(f"✅ Destinations saved: {ids}")
        return

    if state == "awaiting_options":
        r = rules[str(uid)]
        for ln in text.splitlines():
            if ln.startswith("keywords:"):
                r["keywords"] = [k.strip() for k in ln.split(":", 1)[1].split("|")]
            if ln.startswith("skip_media:"):
                r["skip_media"] = ln.split(":", 1)[1].strip().lower() in ("1", "true", "yes")
            if ln.startswith("prefix:"):
                r["prefix"] = ln.split(":", 1)[1].strip()
            if ln.startswith("suffix:"):
                r["suffix"] = ln.split(":", 1)[1].strip()
        save_rules(rules)
        user_states.pop(uid, None)
        await m.reply_text("✅ Options saved.")
        return

    # commands as text
    if text.startswith("/set_sources"):
        user_states[uid] = "awaiting_sources"
        await m.reply_text("📥 Send source chat IDs (comma separated).")
        return
    if text.startswith("/set_destinations"):
        user_states[uid] = "awaiting_destinations"
        await m.reply_text("📤 Send destination chat IDs (comma separated).")
        return
    if text.startswith("/set_options"):
        user_states[uid] = "awaiting_options"
        await m.reply_text("⚙️ Send options like:\nkeywords: word1|word2\nskip_media: true\nprefix: [INFO]\nsuffix: ~END")
        return
    if text.startswith("/start_forwarding"):
        await start_forwarding_for(uid, m)
        return
    if text.startswith("/stop_forwarding"):
        await stop_forwarding_for_uid_and_reply(uid, m)
        return

# ------------------ FORWARDING ------------------
def message_matches_rules(m: Message, r: dict) -> bool:
    # Skip media if option enabled
    if r.get("skip_media"):
        if m.photo or m.video or m.audio or m.document or m.voice:
            return False

    # Check keywords
    kws = r.get("keywords", [])
    if kws and len(kws) > 0:
        text = (m.text or "") + " " + (m.caption or "")
        text = text.lower()
        return any(kw.lower() in text for kw in kws)

    # If no keywords set, allow all
    return True

async def run_forward_client(uid: int):
    key = str(uid)
    ensure_user_rule(uid)
    r = rules[key]
    srcs, dests = r["sources"], r["destinations"]
    if not srcs or not dests:
        return

    try:
        client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH, workers=3)

        @client.on_message(filters.chat(srcs) & ~filters.service)
        async def _forward_handler(cli, m: Message):
            try:
                if not message_matches_rules(m, r):
                    return
                prefix, suffix = r.get("prefix", ""), r.get("suffix", "")
                text_content = m.text or m.caption
                for dest in dests:
                    try:
                        if text_content:
                            final_text = f"{prefix}{text_content}{suffix}"
                            if m.media and not r.get("skip_media"):
                                if prefix or suffix:
                                    await m.copy(dest, caption=final_text if m.caption else None)
                                else:
                                    await m.copy(dest)
                                if (prefix or suffix) and not m.caption:
                                    await client.send_message(dest, final_text)
                            else:
                                await client.send_message(dest, final_text)
                        else:
                            if not r.get("skip_media"):
                                await m.copy(dest)
                    except Exception as e:
                        await bot.send_message(uid, f"⚠️ Error forwarding to {dest}: {e}")
            except Exception as e:
                await bot.send_message(uid, f"⚠️ Error in forward handler: {e}")

        await client.start()
        active_forward_clients[uid] = client
        me = await client.get_me()
        await bot.send_message(uid, f"🚀 Forwarding started!\n✅ Connected as: {me.first_name} ({me.id})\n📥 Sources: {srcs}\n📤 Destinations: {dests}")

        # Keep running until stopped
        await asyncio.Event().wait()

    except Exception as e:
        await bot.send_message(uid, f"❌ Forwarding crashed: {e}")
    finally:
        client = active_forward_clients.pop(uid, None)
        if client:
            try:
                await client.stop()
                await bot.send_message(uid, "🛑 Forwarding stopped.")
            except:
                pass

# ------------------ HELPERS ------------------
async def start_forwarding_for(uid: int, reply_target: Message = None):
    key = str(uid)
    if not os.path.exists(session_path_for(uid) + ".session"):
        await reply_target.reply_text("❌ Not logged in.")
        return
    if not rules[key]["sources"] or not rules[key]["destinations"]:
        await reply_target.reply_text("❌ Sources or destinations not set.")
        return
    if uid in forward_tasks and not forward_tasks[uid].done():
        await reply_target.reply_text("⚠️ Forwarding already running.")
        return
    task = asyncio.create_task(run_forward_client(uid))
    forward_tasks[uid] = task
    await asyncio.sleep(2)
    if uid in active_forward_clients:
        await reply_target.reply_text("🚀 Forwarding started.")
    else:
        await reply_target.reply_text("❌ Failed to start.")

async def stop_forwarding_for(uid: int):
    client = active_forward_clients.pop(uid, None)
    if client:
        try:
            await client.stop()
            await bot.send_message(uid, "🛑 Forwarding stopped manually.")
        except:
            pass
    task = forward_tasks.pop(uid, None)
    if task and not task.done():
        task.cancel()

async def stop_forwarding_for_uid_and_reply(uid: int, m: Message):
    await stop_forwarding_for(uid)
    await m.reply_text("🛑 Forwarding stopped.")

# ------------------ START BOT ------------------
if __name__ == "__main__":
    print("🤖 SaaS Forwarder Bot Running...")
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Bot crashed: {e}")