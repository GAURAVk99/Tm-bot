import os
import json
import asyncio
import sqlite3
import re
import time
from typing import Dict, Any, List

from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------------ CONFIG ------------------
API_ID = 20877162                 # <-- change this
API_HASH = "6dfa90f0624d13f591753174e2c56e8a"     # <-- change this
BOT_TOKEN = "8062798241:AAFDiWLjuh6ec-t7nrbUzeRs8rMuvK-3YFU"   # <-- change this

SESSIONS_DIR = "sessions"
RULES_FILE = "rules.json"

os.makedirs(SESSIONS_DIR, exist_ok=True)

# ------------------ UTILITY FUNCTIONS ------------------
def session_path_for(uid: int) -> str:
    return os.path.join(SESSIONS_DIR, f"user_{uid}")

def is_user_logged_in(uid: int) -> bool:
    return os.path.exists(session_path_for(uid) + ".session")

def parse_id_list(text: str) -> List[int]:
    """Parse comma-separated list of chat IDs or usernames"""
    items = [item.strip() for item in text.split(",")]
    result = []
    for item in items:
        try:
            # Try to convert to integer (for IDs)
            result.append(int(item))
        except ValueError:
            # If it's a username (starts with @), keep it as is
            if item.startswith('@'):
                result.append(item)
            else:
                # Try to handle string IDs (with minus sign)
                try:
                    result.append(int(item))
                except ValueError:
                    # If it's a username without @, add @
                    result.append('@' + item)
    return result

# ------------------ RULES ------------------
def load_rules() -> Dict[str, Any]:
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                rules_data = json.load(f)
                
                # Migrate old format to new format
                for user_id, user_rules in rules_data.items():
                    if "rules" not in user_rules:
                        # This is the old format, migrate to new format
                        rules_data[user_id] = {
                            "current_rule": 0,
                            "rules": [
                                {
                                    "name": "Rule 1",
                                    "sources": user_rules.get("sources", []),
                                    "destinations": user_rules.get("destinations", []),
                                    "keywords": user_rules.get("keywords", []),
                                    "skip_media": user_rules.get("skip_media", False),
                                    "prefix": user_rules.get("prefix", ""),
                                    "suffix": user_rules.get("suffix", ""),
                                    "temp_sources_list": user_rules.get("temp_sources_list", []),
                                    "selected_sources": user_rules.get("selected_sources", []),
                                    "temp_dest_list": user_rules.get("temp_dest_list", []),
                                    "selected_destinations": user_rules.get("selected_destinations", [])
                                }
                            ]
                        }
                
                return rules_data
        except:
            return {}
    return {}

def save_rules(rules_data: Dict[str, Any]):
    with open(RULES_FILE, "w") as f:
        json.dump(rules_data, f, indent=2)

rules = load_rules()

def ensure_user_rule(uid: int):
    key = str(uid)
    if key not in rules:
        rules[key] = {
            "current_rule": 0,  # Index of currently selected rule
            "rules": [  # List of rules
                {
                    "name": "Rule 1",
                    "sources": [],
                    "destinations": [],
                    "keywords": [],
                    "skip_media": False,
                    "prefix": "",
                    "suffix": ""
                }
            ]
        }
        save_rules(rules)

def get_current_rule(uid: int) -> Dict[str, Any]:
    key = str(uid)
    if key not in rules:
        ensure_user_rule(uid)
    
    # Ensure the structure is correct
    if "rules" not in rules[key]:
        # Migrate old format to new format
        old_rules = rules[key]
        rules[key] = {
            "current_rule": 0,
            "rules": [
                {
                    "name": "Rule 1",
                    "sources": old_rules.get("sources", []),
                    "destinations": old_rules.get("destinations", []),
                    "keywords": old_rules.get("keywords", []),
                    "skip_media": old_rules.get("skip_media", False),
                    "prefix": old_rules.get("prefix", ""),
                    "suffix": old_rules.get("suffix", ""),
                    "temp_sources_list": old_rules.get("temp_sources_list", []),
                    "selected_sources": old_rules.get("selected_sources", []),
                    "temp_dest_list": old_rules.get("temp_dest_list", []),
                    "selected_destinations": old_rules.get("selected_destinations", [])
                }
            ]
        }
        save_rules(rules)
    
    return rules[key]["rules"][rules[key]["current_rule"]]

# ------------------ STATE ------------------
user_states: Dict[int, str] = {}
pending_clients: Dict[int, Client] = {}
pending_codes: Dict[int, Dict[str, Any]] = {}

active_user_clients: Dict[int, Client] = {}
forward_tasks: Dict[int, asyncio.Task] = {}

# ------------------ MANAGER BOT ------------------
manager_bot = Client("manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------ CLEANUP TASK ------------------
async def cleanup_pending_logins():
    """Clean up pending login attempts that are older than 5 minutes"""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        current_time = time.time()
        
        # Clean up expired login attempts
        for uid in list(pending_codes.keys()):
            if current_time - pending_codes[uid].get("timestamp", 0) > 300:  # 5 minutes
                try:
                    if uid in pending_clients:
                        temp_client = pending_clients.pop(uid)
                        await temp_client.disconnect()
                except:
                    pass
                pending_codes.pop(uid, None)
                user_states.pop(uid, None)
                
                # Notify user about expired login attempt
                try:
                    await manager_bot.send_message(uid, "❌ Login session expired. Please start over with /login")
                except:
                    pass

# Remove the @manager_bot.on_start() decorator and replace it with this:
@manager_bot.on_message(filters.command("start"))
async def cmd_start(c: Client, m: Message):
    # Start the cleanup task if it's not already running
    if "cleanup_task" not in globals():
        global cleanup_task
        cleanup_task = asyncio.create_task(cleanup_pending_logins())
    
    text = (
        "👋 *Welcome to Hybrid Forwarder Bot*\n\n"
        "📌 Commands:\n"
        "/login - Login with your Telegram account\n"
        "/logout - Logout & remove session\n"
        "/source - Set source chats\n"
        "/destination - Set destination chats\n"
        "/set_options - Configure options\n"
        "/rules - Manage multiple rules\n"
        "/start_forwarding - Start forwarding\n"
        "/stop_forwarding - Stop forwarding\n"
        "/status - Show current status\n"
        "/debug - Debug information\n"
    )
    await m.reply_text(text)

# ------------------ RULES MANAGEMENT ------------------
@manager_bot.on_message(filters.command("rules"))
async def cmd_rules(c: Client, m: Message):
    uid = m.from_user.id
    ensure_user_rule(uid)
    
    user_rules = rules[str(uid)]["rules"]
    current_idx = rules[str(uid)]["current_rule"]
    
    text = "📋 **Your Rules**\n\n"
    for i, rule in enumerate(user_rules):
        status = "✅" if i == current_idx else "◻️"
        text += f"{status} Rule {i+1}: {rule['name']}\n"
        text += f"   Sources: {len(rule['sources'])} | Destinations: {len(rule['destinations'])}\n\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add New Rule", callback_data="add_rule")],
        [InlineKeyboardButton("🔄 Switch Rule", callback_data="switch_rule")],
        [InlineKeyboardButton("✏️ Rename Rule", callback_data="rename_rule")],
        [InlineKeyboardButton("🗑️ Delete Rule", callback_data="delete_rule")]
    ])
    
    await m.reply_text(text, reply_markup=keyboard)

@manager_bot.on_callback_query(filters.regex("add_rule"))
async def cb_add_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    ensure_user_rule(uid)
    user_rules = rules[str(uid)]["rules"]
    
    # Create a new rule
    new_rule = {
        "name": f"Rule {len(user_rules) + 1}",
        "sources": [],
        "destinations": [],
        "keywords": [],
        "skip_media": False,
        "prefix": "",
        "suffix": ""
    }
    
    user_rules.append(new_rule)
    rules[str(uid)]["current_rule"] = len(user_rules) - 1
    save_rules(rules)
    
    await q.message.edit_text(f"✅ Added new rule: {new_rule['name']}")

@manager_bot.on_callback_query(filters.regex("switch_rule"))
async def cb_switch_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    ensure_user_rule(uid)
    user_rules = rules[str(uid)]["rules"]
    
    if len(user_rules) <= 1:
        await q.answer("You only have one rule.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Rule {i+1}: {rule['name']}", callback_data=f"switch_to_{i}")]
        for i, rule in enumerate(user_rules)
    ])
    
    await q.message.edit_text("Select a rule to switch to:", reply_markup=keyboard)

@manager_bot.on_callback_query(filters.regex(r"^switch_to_"))
async def cb_switch_to_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    try:
        rule_idx = int(q.data.split("_")[2])
        rules[str(uid)]["current_rule"] = rule_idx
        save_rules(rules)
        
        await q.message.edit_text(f"✅ Switched to Rule {rule_idx+1}")
    except (ValueError, IndexError):
        await q.answer("Invalid selection", show_alert=True)

@manager_bot.on_callback_query(filters.regex("rename_rule"))
async def cb_rename_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    user_states[uid] = "awaiting_rule_name"
    await q.message.edit_text("Please send the new name for this rule:")

@manager_bot.on_callback_query(filters.regex("delete_rule"))
async def cb_delete_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    ensure_user_rule(uid)
    user_rules = rules[str(uid)]["rules"]
    
    if len(user_rules) <= 1:
        await q.answer("You must have at least one rule.", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Rule {i+1}: {rule['name']}", callback_data=f"delete_rule_{i}")]
        for i, rule in enumerate(user_rules)
    ])
    
    await q.message.edit_text("Select a rule to delete:", reply_markup=keyboard)

@manager_bot.on_callback_query(filters.regex(r"^delete_rule_"))
async def cb_delete_specific_rule(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    try:
        rule_idx = int(q.data.split("_")[2])
        ensure_user_rule(uid)
        user_rules = rules[str(uid)]["rules"]
        
        if len(user_rules) <= 1:
            await q.answer("You must have at least one rule.", show_alert=True)
            return
        
        deleted_rule = user_rules.pop(rule_idx)
        
        # Adjust current rule index if needed
        if rules[str(uid)]["current_rule"] >= rule_idx:
            rules[str(uid)]["current_rule"] = max(0, rules[str(uid)]["current_rule"] - 1)
        
        save_rules(rules)
        
        await q.message.edit_text(f"✅ Deleted rule: {deleted_rule['name']}")
    except (ValueError, IndexError):
        await q.answer("Invalid selection", show_alert=True)

# ------------------ LOGIN FLOW ------------------
@manager_bot.on_message(filters.command("login"))
async def cmd_login(c: Client, m: Message):
    uid = m.from_user.id
    
    # Check if user already has a pending login attempt
    if uid in pending_clients:
        await m.reply_text("❌ You already have a pending login attempt. Please complete it or wait for it to timeout.")
        return
        
    if is_user_logged_in(uid):
        await m.reply_text("✅ Already logged in.\nUse /logout to remove session.")
        return
        
    user_states[uid] = "awaiting_phone"
    await m.reply_text(
        "⚠️ *Note:* Include the `+` and country code.\n\n"
        "📱 Example: `+919876543210`\n\n"
        "⏰ You have 5 minutes to complete the login process.",
        disable_web_page_preview=True
    )

@manager_bot.on_message(filters.command("logout"))
async def cmd_logout(c: Client, m: Message):
    uid = m.from_user.id
    await stop_forwarding_for(uid)
    session_file = session_path_for(uid) + ".session"
    if os.path.exists(session_file):
        os.remove(session_file)
        await m.reply_text("✅ Logged out & session removed.")
    else:
        await m.reply_text("❌ No active session found.")

# ------------------ GET PINNED CHATS ------------------
async def get_pinned_chats(user_client: Client):
    """Get all pinned chats for a user"""
    try:
        # Get all dialogs and check which ones are pinned
        dialogs = []
        async for dialog in user_client.get_dialogs():
            dialogs.append(dialog)
        
        # Filter pinned chats
        pinned_chats = []
        for dialog in dialogs:
            try:
                # Check if chat is pinned by trying to access the pinned status
                if hasattr(dialog, 'is_pinned') and dialog.is_pinned:
                    pinned_chats.append(dialog)
                # Also check folder pinned status (for newer Telegram versions)
                elif hasattr(dialog, 'folder') and hasattr(dialog.folder, 'pinned') and dialog.folder.pinned:
                    pinned_chats.append(dialog)
            except:
                continue
        
        return pinned_chats
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            # Wait a bit and retry
            await asyncio.sleep(0.5)
            return await get_pinned_chats(user_client)
        else:
            raise e
    except Exception as e:
        print(f"Error getting pinned chats: {e}")
        return []

# ------------------ SOURCE ------------------
@manager_bot.on_message(filters.command("source"))
async def cmd_source(c: Client, m: Message):
    uid = m.from_user.id
    
    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await m.reply_text("❌ Please stop forwarding first using /stop_forwarding before changing sources.")
        return
        
    user_states[uid] = "awaiting_sources_pinned"

    text = (
        "## Follow these steps:\n"
        "1. Go to the chats from which you want to copy messages.\n"
        "2. Press and hold the chats.\n"
        "3. Tap on the pin icon to pin it at the top.\n\n"
        "Then press the button below."
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ I have pinned the chats", callback_data="confirm_pinned_sources")]]
    )
    await m.reply_text(text, reply_markup=keyboard)

@manager_bot.on_callback_query(filters.regex("confirm_pinned_sources"))
async def cb_confirm_sources(c: Client, q):
    uid = q.from_user.id
    await q.answer()

    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await q.message.edit_text("❌ Please stop forwarding first using /stop_forwarding before changing sources.")
        return

    if not is_user_logged_in(uid):
        await q.message.edit_text("⚠️ Please login first using /login")
        return

    # Show waiting message
    await q.message.edit_text("⏳ Loading your pinned chats, please wait...")

    try:
        user_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH)
        await user_client.start()

        # Get pinned chats using our improved function
        pinned_chats = await get_pinned_chats(user_client)

        if not pinned_chats:
            await q.message.edit_text("❌ No pinned chats found. Please pin chats first and try again.")
            await user_client.stop()
            return

        user_states[uid] = "awaiting_source_selection"
        temp_sources = []
        
        # Create a formatted list of pinned chats
        text_lines = [
            "## Select the number to copy the post from the source:\n"
        ]
        
        for i, d in enumerate(pinned_chats, start=1):
            title = d.chat.title or d.chat.first_name or d.chat.username or str(d.chat.id)
            
            # Always store the chat ID, not the username
            temp_sources.append(d.chat.id)
            if d.chat.username:
                text_lines.append(f"{i}. {title} (@{d.chat.username}) [ID: {d.chat.id}]")
            else:
                text_lines.append(f"{i}. {title} (ID: {d.chat.id})")

        # Create number buttons
        buttons = []
        row = []
        for i in range(1, len(pinned_chats) + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"source_{i}"))
            if len(row) == 5 or i == len(pinned_chats):
                buttons.append(row)
                row = []
        
        # Add "Select All" and "Done" buttons
        buttons.append([
            InlineKeyboardButton("Select All", callback_data="source_all"),
            InlineKeyboardButton("Done", callback_data="source_done")
        ])

        keyboard = InlineKeyboardMarkup(buttons)
        
        # Store temporary sources in the current rule
        current_rule = get_current_rule(uid)
        current_rule["temp_sources_list"] = temp_sources
        current_rule["selected_sources"] = []
        save_rules(rules)

        await q.message.edit_text("\n".join(text_lines), reply_markup=keyboard)
        
    except Exception as e:
        await q.message.edit_text(f"❌ Error loading pinned chats: {str(e)}")
    finally:
        if 'user_client' in locals():
            await user_client.stop()

# ------------------ DESTINATION ------------------
@manager_bot.on_message(filters.command("destination"))
async def cmd_destination(c: Client, m: Message):
    uid = m.from_user.id
    
    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await m.reply_text("❌ Please stop forwarding first using /stop_forwarding before changing destinations.")
        return
        
    user_states[uid] = "awaiting_dest_pinned"

    text = (
        "## Follow these steps:\n"
        "1. Go to the chats where you want to forward messages.\n"
        "2. Press and hold the chats.\n"
        "3. Tap on the pin icon to pin it at the top.\n\n"
        "Then press the button below."
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ I have pinned the chats", callback_data="confirm_pinned_destinations")]]
    )
    await m.reply_text(text, reply_markup=keyboard)

@manager_bot.on_callback_query(filters.regex("confirm_pinned_destinations"))
async def cb_confirm_destinations(c: Client, q):
    uid = q.from_user.id
    await q.answer()

    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await q.message.edit_text("❌ Please stop forwarding first using /stop_forwarding before changing destinations.")
        return

    if not is_user_logged_in(uid):
        await q.message.edit_text("⚠️ Please login first using /login")
        return
  
   # Show waiting message
    await q.message.edit_text("⏳ Loading your pinned chats, please wait...")

    try:
        user_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH)
        await user_client.start()

        # Get pinned chats using our improved function
        pinned_chats = await get_pinned_chats(user_client)

        if not pinned_chats:
            await q.message.edit_text("❌ No pinned chats found. Please pin chats first and try again.")
            await user_client.stop()
            return

        user_states[uid] = "awaiting_dest_selection"
        temp_dests = []
        
        # Create a formatted list of pinned chats
        text_lines = [
            "## Select the number to forward posts to destination:\n"
        ]
        
        for i, d in enumerate(pinned_chats, start=1):
            title = d.chat.title or d.chat.first_name or d.chat.username or str(d.chat.id)
            
            # For destinations, we can store usernames for bots, but IDs for other chats
            if d.chat.type == "bot" and d.chat.username:
                temp_dests.append("@" + d.chat.username)
                text_lines.append(f"{i}. {title} (@{d.chat.username}) [BOT]")
            elif d.chat.username:
                temp_dests.append("@" + d.chat.username)
                text_lines.append(f"{i}. {title} (@{d.chat.username})")
            else:
                temp_dests.append(d.chat.id)
                text_lines.append(f"{i}. {title} (ID: {d.chat.id})")

        # Create number buttons
        buttons = []
        row = []
        for i in range(1, len(pinned_chats) + 1):
            row.append(InlineKeyboardButton(str(i), callback_data=f"dest_{i}"))
            if len(row) == 5 or i == len(pinned_chats):
                buttons.append(row)
                row = []
        
        # Add "Select All" and "Done" buttons
        buttons.append([
            InlineKeyboardButton("Select All", callback_data="dest_all"),
            InlineKeyboardButton("Done", callback_data="dest_done")
        ])

        keyboard = InlineKeyboardMarkup(buttons)
        
        # Store temporary destinations in the current rule
        current_rule = get_current_rule(uid)
        current_rule["temp_dest_list"] = temp_dests
        current_rule["selected_destinations"] = []
        save_rules(rules)

        await q.message.edit_text("\n".join(text_lines), reply_markup=keyboard)
        
    except Exception as e:
        await q.message.edit_text(f"❌ Error loading pinned chats: {str(e)}")
    finally:
        if 'user_client' in locals():
            await user_client.stop()

@manager_bot.on_callback_query(filters.regex(r"^source_"))
async def cb_source_selection(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    data = q.data
    current_rule = get_current_rule(uid)
    
    if data == "source_all":
        # Select all sources
        temp_list = current_rule.get("temp_sources_list", [])
        current_rule["selected_sources"] = list(range(1, len(temp_list) + 1))
        await q.answer("All sources selected. Press 'Done' to confirm.")
        return
        
    if data == "source_done":
        # Finalize selection
        selected = current_rule.get("selected_sources", [])
        temp_list = current_rule.get("temp_sources_list", [])
        
        if not selected:
            await q.answer("Please select at least one source.", show_alert=True)
            return
            
        chosen = [temp_list[n - 1] for n in selected]
        current_rule["sources"] = chosen
        current_rule.pop("selected_sources", None)
        current_rule.pop("temp_sources_list", None)
        save_rules(rules)
        user_states.pop(uid, None)
        
        await q.message.edit_text(f"✅ Sources saved: {len(chosen)} chats selected")
        return
    
    # Handle individual number selection
    try:
        num = int(data.split("_")[1])
        selected = current_rule.get("selected_sources", [])
        
        if num in selected:
            selected.remove(num)
            await q.answer(f"Removed source {num}")
        else:
            selected.append(num)
            await q.answer(f"Added source {num}")
            
        current_rule["selected_sources"] = selected
        save_rules(rules)
        
    except (ValueError, IndexError):
        await q.answer("Invalid selection", show_alert=True)

@manager_bot.on_callback_query(filters.regex(r"^dest_"))
async def cb_dest_selection(c: Client, q):
    uid = q.from_user.id
    await q.answer()
    
    data = q.data
    current_rule = get_current_rule(uid)
    
    if data == "dest_all":
        # Select all destinations
        temp_list = current_rule.get("temp_dest_list", [])
        current_rule["selected_destinations"] = list(range(1, len(temp_list) + 1))
        await q.answer("All destinations selected. Press 'Done' to confirm.")
        return
        
    if data == "dest_done":
        # Finalize selection
        selected = current_rule.get("selected_destinations", [])
        temp_list = current_rule.get("temp_dest_list", [])
        
        if not selected:
            await q.answer("Please select at least one destination.", show_alert=True)
            return
            
        chosen = [temp_list[n - 1] for n in selected]
        current_rule["destinations"] = chosen
        current_rule.pop("selected_destinations", None)
        current_rule.pop("temp_dest_list", None)
        save_rules(rules)
        user_states.pop(uid, None)
        
        await q.message.edit_text(f"✅ Destinations saved: {len(chosen)} chats selected")
        return
    
    # Handle individual number selection
    try:
        num = int(data.split("_")[1])
        selected = current_rule.get("selected_destinations", [])
        
        if num in selected:
            selected.remove(num)
            await q.answer(f"Removed destination {num}")
        else:
            selected.append(num)
            await q.answer(f"Added destination {num}")
            
        current_rule["selected_destinations"] = selected
        save_rules(rules)
        
    except (ValueError, IndexError):
        await q.answer("Invalid selection", show_alert=True)

# ------------------ HANDLE TEXT ------------------
@manager_bot.on_message(filters.private & filters.text)
async def handle_text(c: Client, m: Message):
    uid = m.from_user.id
    text = m.text.strip()
    state = user_states.get(uid)

    if state == "awaiting_phone":
        # Validate phone number format
        if not re.match(r'^\+\d{10,15}$', text):
            await m.reply_text("❌ Invalid phone number format. Please use format like +919876543210")
            return
            
        phone = text
        
        # Send waiting message
        wait_msg = await m.reply_text("📨 Sending OTP, please wait...")
        
        temp_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH)
        try:
            await temp_client.connect()
            sent = await temp_client.send_code(phone)
            
            # Delete waiting message
            await wait_msg.delete()
            
            pending_clients[uid] = temp_client
            pending_codes[uid] = {
                "phone": phone, 
                "hash": sent.phone_code_hash,
                "timestamp": time.time()  # Add timestamp for timeout handling
            }
            user_states[uid] = "awaiting_otp"
            
            await m.reply_text(
                "✅ *OTP sent successfully!*\n\n"
                "📩 Please enter the code like: `BEST12345`\n\n"
                "_Do not share this code with anyone._\n"
                "⏰ You have 5 minutes to enter the code.",
                disable_web_page_preview=True
            )
        except Exception as e:
            # Delete waiting message on error
            await wait_msg.delete()
            await m.reply_text(f"❌ Error: {str(e)}")
            try:
                await temp_client.disconnect()
            except:
                pass
        return

    if state == "awaiting_otp":
        # Validate OTP format (typically 5-7 characters)
        if not re.match(r'^[A-Za-z0-9]{9}$', text):
            await m.reply_text("❌ Invalid OTP format. Please enter the code exactly as received.")
            return
            
        otp = text
        info = pending_codes.get(uid)
        temp_client = pending_clients.get(uid)
        
        if not info or not temp_client:
            await m.reply_text("❌ Login session expired. Please start over with /login")
            user_states.pop(uid, None)
            return
            
        try:
            await temp_client.sign_in(info["phone"], info["hash"], otp)
        except SessionPasswordNeeded:
            user_states[uid] = "awaiting_2fa"
            await m.reply_text("🔐 2FA enabled. Please send your password.")
            return
        except Exception as e:
            await m.reply_text(f"❌ Error: {str(e)}")
            try:
                await temp_client.disconnect()
            except:
                pass
            pending_clients.pop(uid, None)
            pending_codes.pop(uid, None)
            user_states.pop(uid, None)
            return
            
        await temp_client.disconnect()
        pending_clients.pop(uid, None)
        pending_codes.pop(uid, None)
        user_states.pop(uid, None)
        ensure_user_rule(uid)
        await m.reply_text("✅ *Login successful!*")
        return

    if state == "awaiting_2fa":
        pwd = text
        temp_client = pending_clients.get(uid)
        
        if not temp_client:
            await m.reply_text("❌ Login session expired. Please start over with /login")
            user_states.pop(uid, None)
            return
            
        try:
            await temp_client.check_password(pwd)
        except Exception as e:
            await m.reply_text(f"❌ Error: {str(e)}")
            try:
                await temp_client.disconnect()
            except:
                pass
            pending_clients.pop(uid, None)
            pending_codes.pop(uid, None)
            user_states.pop(uid, None)
            return
            
        await temp_client.disconnect()
        pending_clients.pop(uid, None)
        pending_codes.pop(uid, None)
        user_states.pop(uid, None)
        ensure_user_rule(uid)
        await m.reply_text("✅ *2FA login successful!*")
        return

    if state == "awaiting_rule_name":
        ensure_user_rule(uid)
        current_rule = get_current_rule(uid)
        current_rule["name"] = text
        save_rules(rules)
        user_states.pop(uid, None)
        await m.reply_text(f"✅ Rule renamed to: {text}")
        return

    if state == "awaiting_options":
        ensure_user_rule(uid)
        current_rule = get_current_rule(uid)
        
        # Parse the options text
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "keywords":
                    # Split by pipe | and strip each keyword
                    current_rule["keywords"] = [k.strip() for k in value.split('|') if k.strip()]
                elif key == "skip_media":
                    # Convert to boolean
                    current_rule["skip_media"] = value.lower() in ("1", "true", "yes", "on")
                elif key == "prefix":
                    current_rule["prefix"] = value
                elif key == "suffix":
                    current_rule["suffix"] = value
        
        save_rules(rules)
        user_states.pop(uid, None)
        
        # Show confirmation with current settings
        response = "✅ Options saved:\n"
        response += f"Keywords: {current_rule['keywords'] or 'None'}\n"
        response += f"Skip Media: {current_rule['skip_media']}\n"
        response += f"Prefix: '{current_rule['prefix'] or 'None'}'\n"
        response += f"Suffix: '{current_rule['suffix'] or 'None'}'\n"
        
        await m.reply_text(response)
        return

    # Commands typed as text
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
    if text.startswith("/status"):
        await cmd_status(c, m)
        return
    if text.startswith("/rules"):
        await cmd_rules(c, m)
        return
    if text.startswith("/debug"):
        await cmd_debug(c, m)
        return

# ------------------ DEBUG ------------------
@manager_bot.on_message(filters.command("debug"))
async def cmd_debug(c: Client, m: Message):
    uid = m.from_user.id
    ensure_user_rule(uid)
    
    user_data = rules[str(uid)]
    current_rule = get_current_rule(uid)
    
    text = f"👤 User ID: {uid}\n"
    text += f"🔐 Session exists: {is_user_logged_in(uid)}\n"
    text += f"🔄 Forwarding running: {uid in forward_tasks and not forward_tasks[uid].done()}\n\n"
    
    text += "📋 Rules:\n"
    for i, rule in enumerate(user_data["rules"]):
        text += f"Rule {i+1}: {rule['name']}\n"
        text += f"  Sources: {rule['sources']}\n"
        text += f"  Destinations: {rule['destinations']}\n\n"
    
    await m.reply_text(text, disable_web_page_preview=True)

# ------------------ STATUS ------------------
@manager_bot.on_message(filters.command("status"))
async def cmd_status(c: Client, m: Message):
    uid = m.from_user.id
   
   # Send waiting message
    wait_msg = await m.reply_text("⏳ Getting status, please wait...")

    ensure_user_rule(uid)
    user_data = rules[str(uid)]
    current_rule = get_current_rule(uid)
    running = uid in forward_tasks and not forward_tasks[uid].done()

    # Function to get chat names
    async def get_chat_names(chat_ids):
        names = []
        if not chat_ids:
            return ["Not set"]
        
        if not is_user_logged_in(uid):
            return [str(chat_id) for chat_id in chat_ids]
        
        try:
            user_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH)
            await user_client.start()
            
            for chat_id in chat_ids:
                try:
                    if isinstance(chat_id, str) and chat_id.startswith('@'):
                        # This is a username
                        names.append(chat_id)
                    else:
                        # This is an ID
                        chat = await user_client.get_chat(chat_id)
                        name = chat.title or chat.first_name or chat.username or str(chat_id)
                        names.append(f"{name} ({chat_id})")
                except:
                    names.append(str(chat_id))
            
            await user_client.stop()
        except:
            names = [str(chat_id) for chat_id in chat_ids]
        
        return names

    # Get source and destination names
    source_names = await get_chat_names(current_rule['sources'])
    dest_names = await get_chat_names(current_rule['destinations'])

    text = (
        f"👤 *User ID:* `{uid}`\n"
        f"🔐 *Session:* {'✅ Logged in' if is_user_logged_in(uid) else '❌ Not logged in'}\n"
        f"🔄 *Forwarding:* {'✅ Running' if running else '❌ Stopped'}\n"
        f"📋 *Current Rule:* {current_rule['name']} (Rule {user_data['current_rule'] + 1}/{len(user_data['rules'])})\n"
        f"📥 *Sources:* {', '.join(source_names)}\n"
        f"📤 *Destinations:* {', '.join(dest_names)}\n"
        f"🔍 *Keywords:* {current_rule['keywords'] or 'None'}\n"
        f"📷 *Skip Media:* {current_rule['skip_media']}\n"
        f"📝 *Prefix:* {current_rule['prefix'] or '-'}\n"
        f"📝 *Suffix:* {current_rule['suffix'] or '-'}\n"
    )
    await wait_msg.delete()  # Delete the waiting message
    await m.reply_text(text, disable_web_page_preview=True)

# ------------------ FORWARDING ------------------
async def run_forward_client(uid: int):
    key = str(uid)
    ensure_user_rule(uid)
    user_data = rules[key]
    
    # Check if any rule has sources and destinations
    has_active_rules = any(
        rule["sources"] and rule["destinations"] 
        for rule in user_data["rules"]
    )
    
    if not has_active_rules:
        await manager_bot.send_message(uid, "❌ No active rules with both sources and destinations.")
        return

    try:
        user_client = Client(session_path_for(uid), api_id=API_ID, api_hash=API_HASH, workers=3)
        await user_client.start()
        
        # Collect all sources from all rules
        all_sources = []
        for rule in user_data["rules"]:
            if rule["sources"] and rule["destinations"]:
                all_sources.extend(rule["sources"])

        if not all_sources:
            await manager_bot.send_message(uid, "❌ No valid sources found in any rule.")
            await user_client.stop()
            return

        # Create message handler
        @user_client.on_message(filters.chat(all_sources) & ~filters.service)
        async def _forward_handler(cli, m: Message):
            try:
                # Check all rules to see if this message matches any
                for rule in user_data["rules"]:
                    if not rule["sources"] or not rule["destinations"]:
                        continue
                    
                    # Check if message is from a source in this rule
                    if m.chat.id not in rule["sources"]:
                        continue
                    
                    # Check keywords if any are set
                    if rule["keywords"]:
                        text = m.text or m.caption or ""
                        if not any(keyword.lower() in text.lower() for keyword in rule["keywords"]):
                            continue
                    
                    # Skip media if configured
                    if rule["skip_media"] and (m.photo or m.video or m.audio or m.document):
                        continue
                    
                    # Add prefix/suffix if configured
                    modified_message = m
                    if rule["prefix"] or rule["suffix"]:
                        text = m.text or m.caption or ""
                        new_text = f"{rule['prefix']}{text}{rule['suffix']}"
                        
                        if m.text:
                            modified_message = m.copy()
                            modified_message.text = new_text
                        elif m.caption:
                            modified_message = m.copy()
                            modified_message.caption = new_text
                    
                    # Forward to all destinations in this rule
                    for dest in rule["destinations"]:
                        try:
                            # Use different approach for bots vs regular chats
                            if isinstance(dest, str) and dest.startswith('@'):
                                # This is a bot username, use send_message method
                                if m.text:
                                    await cli.send_message(dest, m.text)
                                elif m.caption:
                                    # For media with caption
                                    if m.photo:
                                        await cli.send_photo(dest, m.photo.file_id, caption=m.caption)
                                    elif m.video:
                                        await cli.send_video(dest, m.video.file_id, caption=m.caption)
                                    elif m.document:
                                        await cli.send_document(dest, m.document.file_id, caption=m.caption)
                                    # Add other media types as needed
                                else:
                                    # For media without caption
                                    if m.photo:
                                        await cli.send_photo(dest, m.photo.file_id)
                                    elif m.video:
                                        await cli.send_video(dest, m.video.file_id)
                                    elif m.document:
                                        await cli.send_document(dest, m.document.file_id)
                                    # Add other media types as needed
                            else:
                                # For non-bot destinations, use the regular copy method
                                await modified_message.copy(dest)
                                
                            print(f"Forwarded message from {m.chat.id} to {dest}")
                        except Exception as e:
                            print(f"Error forwarding to {dest}: {e}")
                            await manager_bot.send_message(uid, f"⚠️ Error forwarding to {dest}: {e}")
                        
            except Exception as e:
                print(f"Error in forward handler: {e}")
                await manager_bot.send_message(uid, f"⚠️ Error in forward handler: {e}")

        active_user_clients[uid] = user_client
        me = await user_client.get_me()
        await manager_bot.send_message(uid, f"🚀 Forwarding started as {me.first_name} ({me.id})")
        
        # Keep the client running
        while uid in forward_tasks and not forward_tasks[uid].done():
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error in run_forward_client: {e}")
        await manager_bot.send_message(uid, f"❌ Forwarding crashed: {e}")
    finally:
        if uid in active_user_clients:
            try:
                await active_user_clients[uid].stop()
                active_user_clients.pop(uid)
            except:
                pass

# ------------------ START / STOP ------------------
@manager_bot.on_message(filters.command("start_forwarding"))
async def cmd_start_forwarding(c: Client, m: Message):
    await start_forwarding_for(m.from_user.id, m)

@manager_bot.on_message(filters.command("stop_forwarding"))
async def cmd_stop_forwarding(c: Client, m: Message):
    await stop_forwarding_for_uid_and_reply(m.from_user.id, m)

async def start_forwarding_for(uid: int, reply_target: Message = None):
    key = str(uid)
    if not os.path.exists(session_path_for(uid) + ".session"):
        await reply_target.reply_text("❌ Not logged in. Use /login first.")
        return
        
    ensure_user_rule(uid)
    user_data = rules[key]
    
    # Check if any rule has sources and destinations
    has_active_rules = any(
        rule["sources"] and rule["destinations"] 
        for rule in user_data["rules"]
    )
    
    if not has_active_rules:
        await reply_target.reply_text("❌ No active rules with both sources and destinations.")
        return
        
    if uid in forward_tasks and not forward_tasks[uid].done():
        await reply_target.reply_text("⚠️ Already running.")
        return
        
    task = asyncio.create_task(run_forward_client(uid))
    forward_tasks[uid] = task
    await reply_target.reply_text("🚀 Forwarding starting...")

async def stop_forwarding_for(uid: int):
    client = active_user_clients.pop(uid, None)
    if client:
        try:
            await client.stop()
            await manager_bot.send_message(uid, "🛑 Forwarding stopped manually.")
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
    print("🤖 Hybrid Forwarder Manager Bot Running...")
    manager_bot.run()