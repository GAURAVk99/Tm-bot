import os
import json
import asyncio
import re
import time
from typing import Dict, Any, List

from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, FloodWaitError, ChatForbiddenError, UserNotParticipantError
from telethon.tl.types import Message, InputPeerChannel, InputPeerChat, InputPeerUser
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputDialogPeer, DialogPeer

# ------------------ CONFIG ------------------
API_ID = 20877162                 # <-- change this
API_HASH = "6dfa90f0624d13f591753174e2c56e8a"     # <-- change this
BOT_TOKEN = "8427659504:AAFAJlwP41s2o5BxT9EoWXM8jsH57VxM0dA"   # <-- change this

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
pending_clients: Dict[int, TelegramClient] = {}
pending_codes: Dict[int, Dict[str, Any]] = {}

active_user_clients: Dict[int, TelegramClient] = {}
forward_tasks: Dict[int, asyncio.Task] = {}

# ------------------ MANAGER BOT ------------------
manager_bot = TelegramClient("manager_bot", API_ID, API_HASH)

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

# ------------------ CHANNEL ACCESS VERIFICATION ------------------
async def verify_channel_access(user_client: TelegramClient, chat_id) -> bool:
    """Verify if user can access a channel/chat"""
    try:
        await user_client.get_entity(chat_id)
        return True
    except (ChatForbiddenError, UserNotParticipantError):
        return False
    except Exception:
        return False

async def check_all_sources_access(uid: int, user_client: TelegramClient, sources: List) -> List[str]:
    """Check access to all sources and return inaccessible ones"""
    inaccessible = []
    for source in sources:
        if not await verify_channel_access(user_client, source):
            inaccessible.append(str(source))
    return inaccessible

# ------------------ COMMAND HANDLERS ------------------
@manager_bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
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
    await event.reply(text)

# ------------------ RULES MANAGEMENT ------------------
@manager_bot.on(events.NewMessage(pattern='/rules'))
async def cmd_rules(event):
    uid = event.sender_id
    ensure_user_rule(uid)
    
    user_rules = rules[str(uid)]["rules"]
    current_idx = rules[str(uid)]["current_rule"]
    
    text = "📋 **Your Rules**\n\n"
    for i, rule in enumerate(user_rules):
        status = "✅" if i == current_idx else "◻️"
        text += f"{status} Rule {i+1}: {rule['name']}\n"
        text += f"   Sources: {len(rule['sources'])} | Destinations: {len(rule['destinations'])}\n\n"
    
    keyboard = [
        [Button.inline("➕ Add New Rule", "add_rule")],
        [Button.inline("🔄 Switch Rule", "switch_rule")],
        [Button.inline("✏️ Rename Rule", "rename_rule")],
        [Button.inline("🗑️ Delete Rule", "delete_rule")]
    ]
    
    await event.reply(text, buttons=keyboard)

@manager_bot.on(events.CallbackQuery(pattern='add_rule'))
async def cb_add_rule(event):
    uid = event.sender_id
    await event.answer()
    
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
    
    await event.edit(f"✅ Added new rule: {new_rule['name']}")

@manager_bot.on(events.CallbackQuery(pattern='switch_rule'))
async def cb_switch_rule(event):
    uid = event.sender_id
    await event.answer()
    
    ensure_user_rule(uid)
    user_rules = rules[str(uid)]["rules"]
    
    if len(user_rules) <= 1:
        await event.answer("You only have one rule.", alert=True)
        return
    
    keyboard = [
        [Button.inline(f"Rule {i+1}: {rule['name']}", f"switch_to_{i}")]
        for i, rule in enumerate(user_rules)
    ]
    
    await event.edit("Select a rule to switch to:", buttons=keyboard)

@manager_bot.on(events.CallbackQuery(pattern=r'^switch_to_'))
async def cb_switch_to_rule(event):
    uid = event.sender_id
    await event.answer()
    
    try:
        rule_idx = int(event.data.decode().split("_")[2])
        rules[str(uid)]["current_rule"] = rule_idx
        save_rules(rules)
        
        await event.edit(f"✅ Switched to Rule {rule_idx+1}")
    except (ValueError, IndexError):
        await event.answer("Invalid selection", alert=True)

@manager_bot.on(events.CallbackQuery(pattern='rename_rule'))
async def cb_rename_rule(event):
    uid = event.sender_id
    await event.answer()
    
    user_states[uid] = "awaiting_rule_name"
    await event.edit("Please send the new name for this rule:")

@manager_bot.on(events.CallbackQuery(pattern='delete_rule'))
async def cb_delete_rule(event):
    uid = event.sender_id
    await event.answer()
    
    ensure_user_rule(uid)
    user_rules = rules[str(uid)]["rules"]
    
    if len(user_rules) <= 1:
        await event.answer("You must have at least one rule.", alert=True)
        return
    
    keyboard = [
        [Button.inline(f"Rule {i+1}: {rule['name']}", f"delete_rule_{i}")]
        for i, rule in enumerate(user_rules)
    ]
    
    await event.edit("Select a rule to delete:", buttons=keyboard)

@manager_bot.on(events.CallbackQuery(pattern=r'^delete_rule_'))
async def cb_delete_specific_rule(event):
    uid = event.sender_id
    await event.answer()
    
    try:
        rule_idx = int(event.data.decode().split("_")[2])
        ensure_user_rule(uid)
        user_rules = rules[str(uid)]["rules"]
        
        if len(user_rules) <= 1:
            await event.answer("You must have at least one rule.", alert=True)
            return
        
        deleted_rule = user_rules.pop(rule_idx)
        
        # Adjust current rule index if needed
        if rules[str(uid)]["current_rule"] >= rule_idx:
            rules[str(uid)]["current_rule"] = max(0, rules[str(uid)]["current_rule"] - 1)
        
        save_rules(rules)
        
        await event.edit(f"✅ Deleted rule: {deleted_rule['name']}")
    except (ValueError, IndexError):
        await event.answer("Invalid selection", alert=True)

# ------------------ LOGIN FLOW ------------------
@manager_bot.on(events.NewMessage(pattern='/login'))
async def cmd_login(event):
    uid = event.sender_id
    
    # Check if user already has a pending login attempt
    if uid in pending_clients:
        await event.reply("❌ You already have a pending login attempt. Please complete it or wait for it to timeout.")
        return
        
    if is_user_logged_in(uid):
        await event.reply("✅ Already logged in.\nUse /logout to remove session.")
        return
        
    user_states[uid] = "awaiting_phone"
    await event.reply(
        "⚠️ *Note:* Include the `+` and country code.\n\n"
        "📱 Example: `+919876543210`\n\n"
        "⏰ You have 5 minutes to complete the login process.",
        link_preview=False
    )

@manager_bot.on(events.NewMessage(pattern='/logout'))
async def cmd_logout(event):
    uid = event.sender_id
    await stop_forwarding_for(uid)
    session_file = session_path_for(uid) + ".session"
    if os.path.exists(session_file):
        os.remove(session_file)
        await event.reply("✅ Logged out & session removed.")
    else:
        await event.reply("❌ No active session found.")

# ------------------ GET PINNED CHATS ------------------
async def get_pinned_chats(user_client: TelegramClient):
    """Get all pinned chats for a user"""
    try:
        # Get all dialogs
        dialogs = await user_client.get_dialogs()
        
        # Filter pinned chats
        pinned_chats = []
        for dialog in dialogs:
            try:
                if dialog.pinned:
                    pinned_chats.append(dialog)
            except:
                continue
        
        return pinned_chats
    except Exception as e:
        print(f"Error getting pinned chats: {e}")
        return []

# ------------------ SOURCE ------------------
@manager_bot.on(events.NewMessage(pattern='/source'))
async def cmd_source(event):
    uid = event.sender_id
    
    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await event.reply("❌ Please stop forwarding first using /stop_forwarding before changing sources.")
        return
        
    user_states[uid] = "awaiting_sources_pinned"

    text = (
        "## Follow these steps:\n"
        "1. Go to the chats from which you want to copy messages.\n"
        "2. Press and hold the chats.\n"
        "3. Tap on the pin icon to pin it at the top.\n\n"
        "Then press the button below."
    )
    keyboard = [[Button.inline("✅ I have pinned the chats", "confirm_pinned_sources")]]
    await event.reply(text, buttons=keyboard)

@manager_bot.on(events.CallbackQuery(pattern='confirm_pinned_sources'))
async def cb_confirm_sources(event):
    uid = event.sender_id
    await event.answer()

    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await event.edit("❌ Please stop forwarding first using /stop_forwarding before changing sources.")
        return

    if not is_user_logged_in(uid):
        await event.edit("⚠️ Please login first using /login")
        return

    # Show waiting message
    await event.edit("⏳ Loading your pinned chats, please wait...")

    try:
        user_client = TelegramClient(session_path_for(uid), API_ID, API_HASH)
        await user_client.connect()

        # Get pinned chats using our improved function
        pinned_chats = await get_pinned_chats(user_client)

        if not pinned_chats:
            await event.edit("❌ No pinned chats found. Please pin chats first and try again.")
            await user_client.disconnect()
            return

        user_states[uid] = "awaiting_source_selection"
        temp_sources = []
        
        # Create a formatted list of pinned chats
        text_lines = [
            "## Select the number to copy the post from the source:\n"
        ]
        
        for i, d in enumerate(pinned_chats, start=1):
            entity = d.entity
            title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(entity, 'username', None) or str(entity.id)
            
            # Always store the chat ID, not the username
            temp_sources.append(entity.id)
            if getattr(entity, 'username', None):
                text_lines.append(f"{i}. {title} (@{entity.username}) [ID: {entity.id}]")
            else:
                text_lines.append(f"{i}. {title} (ID: {entity.id})")

        # Create number buttons
        buttons = []
        row = []
        for i in range(1, len(pinned_chats) + 1):
            row.append(Button.inline(str(i), f"source_{i}"))
            if len(row) == 5 or i == len(pinned_chats):
                buttons.append(row)
                row = []
        
        # Add "Select All" and "Done" buttons
        buttons.append([
            Button.inline("Select All", "source_all"),
            Button.inline("Done", "source_done")
        ])

        # Store temporary sources in the current rule
        current_rule = get_current_rule(uid)
        current_rule["temp_sources_list"] = temp_sources
        current_rule["selected_sources"] = []
        save_rules(rules)

        await event.edit("\n".join(text_lines), buttons=buttons)
        
    except Exception as e:
        await event.edit(f"❌ Error loading pinned chats: {str(e)}")
    finally:
        if 'user_client' in locals():
            await user_client.disconnect()

# ------------------ DESTINATION ------------------
@manager_bot.on(events.NewMessage(pattern='/destination'))
async def cmd_destination(event):
    uid = event.sender_id
    
    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await event.reply("❌ Please stop forwarding first using /stop_forwarding before changing destinations.")
        return
        
    user_states[uid] = "awaiting_dest_pinned"

    text = (
        "## Follow these steps:\n"
        "1. Go to the chats where you want to forward messages.\n"
        "2. Press and hold the chats.\n"
        "3. Tap on the pin icon to pin it at the top.\n\n"
        "Then press the button below."
    )
    keyboard = [[Button.inline("✅ I have pinned the chats", "confirm_pinned_destinations")]]
    await event.reply(text, buttons=keyboard)

@manager_bot.on(events.CallbackQuery(pattern='confirm_pinned_destinations'))
async def cb_confirm_destinations(event):
    uid = event.sender_id
    await event.answer()

    # Check if forwarding is active
    if uid in forward_tasks and not forward_tasks[uid].done():
        await event.edit("❌ Please stop forwarding first using /stop_forwarding before changing destinations.")
        return

    if not is_user_logged_in(uid):
        await event.edit("⚠️ Please login first using /login")
        return
  
   # Show waiting message
    await event.edit("⏳ Loading your pinned chats, please wait...")

    try:
        user_client = TelegramClient(session_path_for(uid), API_ID, API_HASH)
        await user_client.connect()

        # Get pinned chats using our improved function
        pinned_chats = await get_pinned_chats(user_client)

        if not pinned_chats:
            await event.edit("❌ No pinned chats found. Please pin chats first and try again.")
            await user_client.disconnect()
            return

        user_states[uid] = "awaiting_dest_selection"
        temp_dests = []
        
        # Create a formatted list of pinned chats
        text_lines = [
            "## Select the number to forward posts to destination:\n"
        ]
        
        for i, d in enumerate(pinned_chats, start=1):
            entity = d.entity
            title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(entity, 'username', None) or str(entity.id)
            
            # For destinations, we can store usernames for bots, but IDs for other chats
            if getattr(entity, 'bot', False) and getattr(entity, 'username', None):
                temp_dests.append("@" + entity.username)
                text_lines.append(f"{i}. {title} (@{entity.username}) [BOT]")
            elif getattr(entity, 'username', None):
                temp_dests.append("@" + entity.username)
                text_lines.append(f"{i}. {title} (@{entity.username})")
            else:
                temp_dests.append(entity.id)
                text_lines.append(f"{i}. {title} (ID: {entity.id})")

        # Create number buttons
        buttons = []
        row = []
        for i in range(1, len(pinned_chats) + 1):
            row.append(Button.inline(str(i), f"dest_{i}"))
            if len(row) == 5 or i == len(pinned_chats):
                buttons.append(row)
                row = []
        
        # Add "Select All" and "Done" buttons
        buttons.append([
            Button.inline("Select All", "dest_all"),
            Button.inline("Done", "dest_done")
        ])

        # Store temporary destinations in the current rule
        current_rule = get_current_rule(uid)
        current_rule["temp_dest_list"] = temp_dests
        current_rule["selected_destinations"] = []
        save_rules(rules)

        await event.edit("\n".join(text_lines), buttons=buttons)
        
    except Exception as e:
        await event.edit(f"❌ Error loading pinned chats: {str(e)}")
    finally:
        if 'user_client' in locals():
            await user_client.disconnect()

@manager_bot.on(events.CallbackQuery(pattern=r'^source_'))
async def cb_source_selection(event):
    uid = event.sender_id
    await event.answer()
    
    data = event.data.decode()
    current_rule = get_current_rule(uid)
    
    if data == "source_all":
        # Select all sources
        temp_list = current_rule.get("temp_sources_list", [])
        current_rule["selected_sources"] = list(range(1, len(temp_list) + 1))
        await event.answer("All sources selected. Press 'Done' to confirm.")
        return
        
    if data == "source_done":
        # Finalize selection
        selected = current_rule.get("selected_sources", [])
        temp_list = current_rule.get("temp_sources_list", [])
        
        if not selected:
            await event.answer("Please select at least one source.", alert=True)
            return
            
        chosen = [temp_list[n - 1] for n in selected]
        current_rule["sources"] = chosen
        current_rule.pop("selected_sources", None)
        current_rule.pop("temp_sources_list", None)
        save_rules(rules)
        user_states.pop(uid, None)
        
        await event.edit(f"✅ Sources saved: {len(chosen)} chats selected")
        return
    
    # Handle individual number selection
    try:
        num = int(data.split("_")[1])
        selected = current_rule.get("selected_sources", [])
        
        if num in selected:
            selected.remove(num)
            await event.answer(f"Removed source {num}")
        else:
            selected.append(num)
            await event.answer(f"Added source {num}")
            
        current_rule["selected_sources"] = selected
        save_rules(rules)
        
    except (ValueError, IndexError):
        await event.answer("Invalid selection", alert=True)

@manager_bot.on(events.CallbackQuery(pattern=r'^dest_'))
async def cb_dest_selection(event):
    uid = event.sender_id
    await event.answer()
    
    data = event.data.decode()
    current_rule = get_current_rule(uid)
    
    if data == "dest_all":
        # Select all destinations
        temp_list = current_rule.get("temp_dest_list", [])
        current_rule["selected_destinations"] = list(range(1, len(temp_list) + 1))
        await event.answer("All destinations selected. Press 'Done' to confirm.")
        return
        
    if data == "dest_done":
        # Finalize selection
        selected = current_rule.get("selected_destinations", [])
        temp_list = current_rule.get("temp_dest_list", [])
        
        if not selected:
            await event.answer("Please select at least one destination.", alert=True)
            return
            
        chosen = [temp_list[n - 1] for n in selected]
        current_rule["destinations"] = chosen
        current_rule.pop("selected_destinations", None)
        current_rule.pop("temp_dest_list", None)
        save_rules(rules)
        user_states.pop(uid, None)
        
        await event.edit(f"✅ Destinations saved: {len(chosen)} chats selected")
        return
    
    # Handle individual number selection
    try:
        num = int(data.split("_")[1])
        selected = current_rule.get("selected_destinations", [])
        
        if num in selected:
            selected.remove(num)
            await event.answer(f"Removed destination {num}")
        else:
            selected.append(num)
            await event.answer(f"Added destination {num}")
            
        current_rule["selected_destinations"] = selected
        save_rules(rules)
        
    except (ValueError, IndexError):
        await event.answer("Invalid selection", alert=True)

# ------------------ HANDLE TEXT ------------------
@manager_bot.on(events.NewMessage())
async def handle_text(event):
    # Ignore commands that are already handled
    if event.text.startswith('/'):
        return
        
    uid = event.sender_id
    text = event.text.strip()
    state = user_states.get(uid)

    if state == "awaiting_phone":
        # Validate phone number format
        if not re.match(r'^\+\d{10,15}$', text):
            await event.reply("❌ Invalid phone number format. Please use format like +919876543210")
            return
            
        phone = text
        
        # Send waiting message
        wait_msg = await event.reply("📨 Sending OTP, please wait...")
        
        temp_client = TelegramClient(session_path_for(uid), API_ID, API_HASH)
        try:
            await temp_client.connect()
            sent = await temp_client.send_code_request(phone)
            
            # Delete waiting message
            await wait_msg.delete()
            
            pending_clients[uid] = temp_client
            pending_codes[uid] = {
                "phone": phone, 
                "hash": sent.phone_code_hash,
                "timestamp": time.time()  # Add timestamp for timeout handling
            }
            user_states[uid] = "awaiting_otp"
            
            await event.reply(
                "✅ *OTP sent successfully!*\n\n"
                "📩 Please enter the code like: `BEST12345`\n\n"
                "_Do not share this code with anyone._\n"
                "⏰ You have 5 minutes to enter the code.",
                link_preview=False
            )
        except Exception as e:
            # Delete waiting message on error
            await wait_msg.delete()
            await event.reply(f"❌ Error: {str(e)}")
            try:
                await temp_client.disconnect()
            except:
                pass
        return

    if state == "awaiting_otp":
        # Validate OTP format (typically 5-7 characters)
        if not re.match(r'^[A-Za-z0-9]{9}$', text):
            await event.reply("❌ Invalid OTP format. Please enter the code exactly as received.")
            return
            
        otp = text
        info = pending_codes.get(uid)
        temp_client = pending_clients.get(uid)
        
        if not info or not temp_client:
            await event.reply("❌ Login session expired. Please start over with /login")
            user_states.pop(uid, None)
            return
            
        try:
            # Telethon's sign_in method takes code as a keyword argument
            await temp_client.sign_in(phone=info["phone"], code=otp, phone_code_hash=info["hash"])
        except SessionPasswordNeededError:
            user_states[uid] = "awaiting_2fa"
            await event.reply("🔐 2FA enabled. Please send your password.")
            return
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
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
        await event.reply("✅ *Login successful!*")
        return

    if state == "awaiting_2fa":
        pwd = text
        temp_client = pending_clients.get(uid)
        
        if not temp_client:
            await event.reply("❌ Login session expired. Please start over with /login")
            user_states.pop(uid, None)
            return
            
        try:
            await temp_client.sign_in(password=pwd)
        except Exception as e:
            await event.reply(f"❌ Error: {str(e)}")
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
        await event.reply("✅ *2FA login successful!*")
        return

    if state == "awaiting_rule_name":
        ensure_user_rule(uid)
        current_rule = get_current_rule(uid)
        current_rule["name"] = text
        save_rules(rules)
        user_states.pop(uid, None)
        await event.reply(f"✅ Rule renamed to: {text}")
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
        
        await event.reply(response)
        return

# ------------------ DEBUG ------------------
@manager_bot.on(events.NewMessage(pattern='/debug'))
async def cmd_debug(event):
    uid = event.sender_id
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
    
    await event.reply(text, link_preview=False)

# ------------------ STATUS ------------------
@manager_bot.on(events.NewMessage(pattern='/status'))
async def cmd_status(event):
    uid = event.sender_id
   
   # Send waiting message
    wait_msg = await event.reply("⏳ Getting status, please wait...")

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
            user_client = TelegramClient(session_path_for(uid), API_ID, API_HASH)
            await user_client.connect()
            
            for chat_id in chat_ids:
                try:
                    if isinstance(chat_id, int):
                        entity = await user_client.get_entity(chat_id)
                    elif chat_id.startswith('@'):
                        entity = await user_client.get_entity(chat_id)
                    else:
                        names.append(str(chat_id))
                        continue
                    
                    title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or getattr(entity, 'username', None) or str(chat_id)
                    names.append(title)
                except Exception as e:
                    names.append(f"{chat_id} (Error: {str(e)})")
            
            await user_client.disconnect()
        except Exception as e:
            names = [str(chat_id) for chat_id in chat_ids]
        
        return names

    # Get source and destination names
    source_names = await get_chat_names(current_rule["sources"])
    dest_names = await get_chat_names(current_rule["destinations"])

    # Delete waiting message
    await wait_msg.delete()

    text = f"📊 **Status for Rule: {current_rule['name']}**\n\n"
    text += f"🔄 Forwarding: {'✅ RUNNING' if running else '❌ STOPPED'}\n\n"
    
    text += "📥 Sources:\n"
    for i, name in enumerate(source_names):
        text += f"  {i+1}. {name}\n"
    
    text += "\n📤 Destinations:\n"
    for i, name in enumerate(dest_names):
        text += f"  {i+1}. {name}\n"
    
    text += f"\n🔑 Keywords: {current_rule['keywords'] or 'All messages'}\n"
    text += f"📷 Skip Media: {current_rule['skip_media']}\n"
    text += f"🔖 Prefix: '{current_rule['prefix'] or 'None'}'\n"
    text += f"🔖 Suffix: '{current_rule['suffix'] or 'None'}'\n"
    
    await event.reply(text, link_preview=False)

# ------------------ SET OPTIONS ------------------
@manager_bot.on(events.NewMessage(pattern='/set_options'))
async def cmd_set_options(event):
    uid = event.sender_id
    user_states[uid] = "awaiting_options"
    
    ensure_user_rule(uid)
    current_rule = get_current_rule(uid)
    
    text = (
        "⚙️ *Send options in this format:*\n\n"
        "`keywords: word1|word2|word3`\n"
        "`skip_media: true`\n"
        "`prefix: [INFO]`\n"
        "`suffix: ~END`\n\n"
        "*Current settings:*\n"
        f"Keywords: {current_rule['keywords'] or 'None'}\n"
        f"Skip Media: {current_rule['skip_media']}\n"
        f"Prefix: '{current_rule['prefix'] or 'None'}'\n"
        f"Suffix: '{current_rule['suffix'] or 'None'}'"
    )
    
    await event.reply(text)

# ------------------ START FORWARDING ------------------
@manager_bot.on(events.NewMessage(pattern='/start_forwarding'))
async def cmd_start_forwarding(event):
    await start_forwarding_for(event.sender_id, event)

async def start_forwarding_for(uid, event=None):
    # Check if forwarding is already running
    if uid in forward_tasks and not forward_tasks[uid].done():
        if event:
            await event.reply("❌ Forwarding is already running.")
        return
    
    # Check if user is logged in
    if not is_user_logged_in(uid):
        if event:
            await event.reply("⚠️ Please login first using /login")
        return
    
    ensure_user_rule(uid)
    current_rule = get_current_rule(uid)
    
    # Validate sources and destinations
    if not current_rule["sources"]:
        if event:
            await event.reply("❌ No sources set. Use /source first.")
        return
        
    if not current_rule["destinations"]:
        if event:
            await event.reply("❌ No destinations set. Use /destination first.")
        return
    
    # Send waiting message
    if event:
        wait_msg = await event.reply("⏳ Starting forwarding, please wait...")
    
    try:
        # Create user client
        user_client = TelegramClient(session_path_for(uid), API_ID, API_HASH)
        await user_client.connect()
        
        # Check access to sources
        inaccessible_sources = await check_all_sources_access(uid, user_client, current_rule["sources"])
        if inaccessible_sources:
            await user_client.disconnect()
            if event:
                await wait_msg.delete()
                await event.reply(
                    f"❌ Cannot access these sources:\n{', '.join(inaccessible_sources)}\n"
                    "Please check if you have joined these chats."
                )
            return
        
        # Start forwarding task
        task = asyncio.create_task(forward_messages(uid, user_client, current_rule))
        forward_tasks[uid] = task
        active_user_clients[uid] = user_client
        
        if event:
            await wait_msg.delete()
            await event.reply(
                f"✅ *Forwarding started!*\n\n"
                f"📥 Sources: {len(current_rule['sources'])}\n"
                f"📤 Destinations: {len(current_rule['destinations'])}\n"
                f"🔑 Keywords: {current_rule['keywords'] or 'All messages'}\n\n"
                f"Use /stop_forwarding to stop."
            )
            
    except Exception as e:
        if event:
            await wait_msg.delete()
            await event.reply(f"❌ Error starting forwarding: {str(e)}")
        try:
            await user_client.disconnect()
        except:
            pass

# ------------------ STOP FORWARDING ------------------
@manager_bot.on(events.NewMessage(pattern='/stop_forwarding'))
async def cmd_stop_forwarding(event):
    await stop_forwarding_for_uid_and_reply(event.sender_id, event)

async def stop_forwarding_for_uid_and_reply(uid, event=None):
    await stop_forwarding_for(uid)
    if event:
        await event.reply("🛑 Forwarding stopped.")

async def stop_forwarding_for(uid):
    if uid in forward_tasks:
        task = forward_tasks[uid]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        del forward_tasks[uid]
    
    if uid in active_user_clients:
        user_client = active_user_clients[uid]
        try:
            await user_client.disconnect()
        except:
            pass
        del active_user_clients[uid]

# ------------------ FORWARDING LOGIC ------------------
async def forward_messages(uid, user_client, rule_config):
    """Main forwarding loop"""
    sources = rule_config["sources"]
    destinations = rule_config["destinations"]
    keywords = rule_config["keywords"]
    skip_media = rule_config["skip_media"]
    prefix = rule_config["prefix"]
    suffix = rule_config["suffix"]
    
    # Convert source IDs to entities
    source_entities = []
    for source in sources:
        try:
            entity = await user_client.get_entity(source)
            source_entities.append(entity)
        except Exception as e:
            print(f"Error getting entity for source {source}: {e}")
    
    if not source_entities:
        print("No valid source entities found")
        return
    
    try:
        # Start listening to new messages
        @user_client.on(events.NewMessage(chats=source_entities))
        async def handler(event):
            try:
                # Check if message matches keywords
                message_text = event.message.text or event.message.caption or ""
                
                if keywords:
                    # If keywords are specified, check if any keyword is in the message
                    if not any(keyword.lower() in message_text.lower() for keyword in keywords):
                        return
                
                # Skip media if configured
                if skip_media and (event.message.media and not event.message.text):
                    return
                
                # Prepare message text with prefix and suffix
                final_text = message_text
                if prefix and final_text:
                    final_text = prefix + " " + final_text
                if suffix and final_text:
                    final_text = final_text + " " + suffix
                
                # Forward to all destinations
                for dest in destinations:
                    try:
                        if event.message.media:
                            # Send media with caption (if there's text)
                            if final_text and final_text != message_text:
                                # Media with modified caption
                                await user_client.send_file(
                                    dest,
                                    file=event.message.media,
                                    caption=final_text
                                )
                            elif final_text:
                                # Media with original caption
                                await user_client.send_file(
                                    dest,
                                    file=event.message.media,
                                    caption=final_text
                                )
                            else:
                                # Media without caption
                                await user_client.send_file(
                                    dest,
                                    file=event.message.media
                                )
                        else:
                            # Send text message only if there's text
                            if final_text:
                                await user_client.send_message(dest, final_text)
                    except Exception as e:
                        print(f"Error forwarding to {dest}: {e}")
                        # Try to notify user about the error
                        try:
                            await manager_bot.send_message(uid, f"⚠️ Error forwarding to {dest}: {str(e)}")
                        except:
                            pass
                        
            except Exception as e:
                print(f"Error processing message: {e}")
        
        # Notify user that forwarding has started
        try:
            await manager_bot.send_message(uid, "✅ Forwarding is now active and listening for messages...")
        except:
            pass
        
        # Keep the client running
        await user_client.run_until_disconnected()
        
    except asyncio.CancelledError:
        print("Forwarding task cancelled")
        try:
            await manager_bot.send_message(uid, "🛑 Forwarding stopped by user")
        except:
            pass
    except Exception as e:
        print(f"Error in forwarding task: {e}")
        try:
            await manager_bot.send_message(uid, f"❌ Forwarding error: {str(e)}")
        except:
            pass
    finally:
        try:
            await user_client.disconnect()
        except:
            pass

# ------------------ MAIN ------------------
async def main():
    print("🚀 Starting Hybrid Forwarder Bot...")
    
    # Start the bot with proper event loop handling
    await manager_bot.start(bot_token=BOT_TOKEN)
    print("✅ Manager bot started!")
    
    # Start cleanup task
    global cleanup_task
    cleanup_task = asyncio.create_task(cleanup_pending_logins())
    
    # Keep the bot running
    print("🤖 Bot is now running. Press Ctrl+C to stop.")
    await manager_bot.run_until_disconnected()

if __name__ == "__main__":
    # Create a new event loop and set it as the current loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        if not loop.is_closed():
            loop.close()