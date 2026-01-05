import asyncio

try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from telethon import TelegramClient
import logging
import os
import json
import asyncpg
from datetime import datetime, timedelta  # Add this import
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, ChatWriteForbiddenError, ChannelPrivateError, FloodWaitError
from telethon.tl.types import MessageEntityMentionName, KeyboardButtonCallback
from telethon import types
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.tl.types import InputMediaPhoto, InputMediaDocument
from telethon.tl.types import DocumentAttributeSticker, DocumentAttributeCustomEmoji
from telethon.errors import (
    SessionPasswordNeededError, 
    PhoneCodeInvalidError, 
    PhoneCodeExpiredError,
    PhoneNumberInvalidError, 
    PhoneNumberBannedError,
    PhoneNumberFloodError,
    PhoneNumberUnoccupiedError,
    PasswordHashInvalidError
)

# ---------------- SUBSCRIPTION CONFIG ----------------
SUBSCRIPTION_LIMITS = {
    'free': {
        'max_rules': 1,
        'max_sources_per_rule': 1,
        'max_destinations_per_rule': 1
    },
    'premium': {
        'max_rules': 20,
        'max_sources_per_rule': 50,
        'max_destinations_per_rule': 50
    },
    'enterprise': {
        'max_rules': 100,
        'max_sources_per_rule': 500,
        'max_destinations_per_rule': 500
    }
}

PAYMENT_BOT_USERNAME = "@advance_forwarder_payment_bot"

# ---------------- CONFIG ----------------
API_ID = int(os.getenv("API_ID", "20877162"))
API_HASH = os.getenv("API_HASH", "6dfa90f0624d13f591753174e2c56e8a")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8346709989:AAGJpSgJG3KgrQV3fFQ0jh4P4W3vd4N2gAY")
BOT_USERNAME = "@advauto_messege_forwarder_bot"  # Your bot's username

# Add this line for payment bot ID
PAYMENT_BOT_ID = "8366789774"  # Replace with your payment bot's actual ID

DB_URL = os.getenv("DATABASE_URL", "postgresql://telegram_user:password@localhost:5432/telegram_forwarder2")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_CHANNEL = "@amfbot_help"  # Channel users must join

# ---------------- DB INIT ----------------
async def init_db():
    conn = await asyncpg.connect(DB_URL)
    
   
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id BIGINT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            expires_at TIMESTAMP,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create users table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            phone TEXT,
            session TEXT,
            options JSONB DEFAULT '{}'::jsonb
        );
    """)
    
    # Create rules table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            user_id BIGINT,
            rule_id TEXT,
            name TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            PRIMARY KEY(user_id, rule_id)
        );
    """)
    
    # Create sources table with rule_id
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            user_id BIGINT,
            chat_id BIGINT,
            title TEXT,
            rule_id TEXT DEFAULT 'default',
            PRIMARY KEY(user_id, chat_id, rule_id)
        );
    """)
    
    # Create destinations table with rule_id and username
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS destinations (
            user_id BIGINT,
            chat_id BIGINT,
            title TEXT,
            username TEXT,
            rule_id TEXT DEFAULT 'default',
            PRIMARY KEY(user_id, chat_id, rule_id)
        );
    """)
    
    # Create keyword_filters table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS keyword_filters (
            user_id BIGINT,
            rule_id TEXT,
            type TEXT CHECK (type IN ('whitelist', 'blacklist')),
            keywords TEXT[] DEFAULT '{}',
            PRIMARY KEY(user_id, rule_id, type)
        );
    """)
    
    # Add current_rule column to users table
    await conn.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS current_rule TEXT DEFAULT 'default'
    """)
    
    # Add username column to sources table if it doesn't exist
    await conn.execute("""
        ALTER TABLE sources 
        ADD COLUMN IF NOT EXISTS username TEXT
    """)
    
    # Add this to your init_db() function
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS forwarding_status (
            user_id BIGINT PRIMARY KEY,
            is_active BOOLEAN DEFAULT FALSE,
            last_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Add user_activity table for tracking usage
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id BIGINT PRIMARY KEY,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            command_count INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Add this to the DB INIT section in init_db() function
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS forwarding_delays (
            user_id BIGINT,
            rule_id TEXT,
            delay_seconds INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, rule_id)
        );
    """)
    
    # Add options column to rules table
    await conn.execute("""
        ALTER TABLE rules 
        ADD COLUMN IF NOT EXISTS options JSONB DEFAULT '{}'::jsonb
    """)
    
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS channel_verification (
        user_id BIGINT PRIMARY KEY,
        has_joined BOOLEAN DEFAULT FALSE,
        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
    
    # Add this to your init_db() function
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS subscription_notifications (
            user_id BIGINT PRIMARY KEY,
            last_expiry_notification TIMESTAMP,
            notified_for_plan TEXT
        );
    """)
    
    # Add this to your init_db() function
    await conn.execute("""
        ALTER TABLE rules 
        ADD COLUMN IF NOT EXISTS manually_disabled BOOLEAN DEFAULT FALSE
    """)
    
    await conn.close()
    logger.info("Database tables created with correct schema")

db_pool = None

async def get_db():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DB_URL, min_size=10, max_size=90)
    return db_pool

# ---------------- BOT INIT ----------------
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_clients = {}   # {user_id: TelegramClient}
forwarding_tasks = {}  # {user_id: task}
user_states = {}  # {user_id: state_data}
last_message_ids = {}  # {user_id: {source_id: last_message_id}}

# Add this with other global variables
user_operation_mode = {}  # {user_id: 'login', 'source_selection', etc.}

# Helper function to wait for user response
async def wait_for_user_response(user_id, timeout=60, operation_mode=None):
    """Wait for a message from a specific user, with command detection"""
    future = asyncio.Future()
    handler = None
    
    @bot.on(events.NewMessage(from_users=user_id))
    async def inner_handler(response_event):
        message_text = response_event.raw_text.strip()
        
        # Check if user sent a command instead of expected response
        if message_text.startswith('/'):
            logger.info(f"User {user_id} sent command during {operation_mode}: {message_text}")
            
            # Only set exception if future is not already done
            if not future.done():
                future.set_exception(ValueError("COMMAND_DETECTED"))
            
            # Clean up the handler immediately
            if handler:
                try:
                    bot.remove_event_handler(handler)
                except:
                    pass
            
            # Clear the user's operation state
            if user_id in user_operation_mode:
                del user_operation_mode[user_id]
            
            if user_id in user_states:
                del user_states[user_id]
            
            # Let the command handler process the new command
            return
        elif not future.done():
            future.set_result(response_event)
            # Clean up the handler after getting a valid response
            if handler:
                try:
                    bot.remove_event_handler(handler)
                except:
                    pass
    
    handler = inner_handler
    
    try:
        if operation_mode:
            user_operation_mode[user_id] = operation_mode
        
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        logger.info(f"Timeout waiting for response from user {user_id}")
        # Clean up tracking and handler
        if user_id in user_operation_mode:
            del user_operation_mode[user_id]
        if handler:
            try:
                bot.remove_event_handler(handler)
            except:
                pass
        raise
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled {operation_mode} with a command")
            # Handler already cleaned up in inner_handler
            raise
        # Clean up handler on other ValueErrors
        if handler:
            try:
                bot.remove_event_handler(handler)
            except:
                pass
        raise
    except Exception as e:
        # Clean up handler on any other exception
        if handler:
            try:
                bot.remove_event_handler(handler)
            except:
                pass
        raise

# Helper to get chat info
async def get_chat_info(client, chat_input):
    try:
        if chat_input.startswith('@'):
            chat = await client.get_entity(chat_input)
        else:
            chat = await client.get_entity(int(chat_input))
        return chat.id, chat.title
    except Exception as e:
        return None, None

# ----------------- SUBSCRIPTION STATUS ---------------
async def get_user_subscription(user_id):
    """Get user's subscription plan and normalize it to standard keys"""
    db = await get_db()
    row = await db.fetchrow("SELECT * FROM subscriptions WHERE user_id=$1", user_id)
    
    if row and row['plan']:
        # Check if subscription is still valid
        if row['expires_at'] and row['expires_at'] > datetime.now():
            plan = row['plan'].lower()
            
            # Normalize plan names to match SUBSCRIPTION_LIMITS keys
            if any(keyword in plan for keyword in ['month', 'premium', 'pro', 'paid']):
                return 'premium'
            elif any(keyword in plan for keyword in ['year', 'enterprise', 'business']):
                return 'enterprise'
            elif plan in ['free', 'basic']:
                return 'free'
            else:
                # Default to free for any unrecognized plan
                return 'free'
        else:
            # Subscription expired
            return 'free'
    
    # No subscription found or expired
    return 'free'

async def get_subscription_display_name(user_id):
    """Get the actual plan name from database for display purposes"""
    db = await get_db()
    row = await db.fetchrow("SELECT * FROM subscriptions WHERE user_id=$1", user_id)
    
    if row and row['plan'] and row['expires_at'] and row['expires_at'] > datetime.now():
        return row['plan']
    return 'free'

@bot.on(events.NewMessage(pattern="/subscription"))
async def subscription_cmd(event):
    user_id = event.sender_id
    subscription_plan = await get_user_subscription(user_id)
    display_plan = await get_subscription_display_name(user_id)
    
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    
    db = await get_db()
    
    # Get current usage
    rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    
    # Get current rule to check sources/destinations for this rule
    rule_id, rule_name = await get_current_rule(user_id)
    sources_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    destinations_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    # Check if subscription has expiry
    sub_info = await db.fetchrow("SELECT * FROM subscriptions WHERE user_id=$1", user_id)
    expiry_info = ""
    if sub_info and sub_info['expires_at']:
        expiry_date = sub_info['expires_at'].strftime("%Y-%m-%d")
        expiry_info = f"\n⏰ Expires on: {expiry_date}"
    
    response = f"📋 **Your Subscription Plan:** {display_plan.upper()}{expiry_info}\n\n"
    response += f"📊 **Current Usage:**\n"
    response += f"• Rules: {rules_count}/{limits['max_rules']}\n"
    response += f"• Sources (current rule): {sources_count}/{limits['max_sources_per_rule']}\n"
    response += f"• Destinations (current rule): {destinations_count}/{limits['max_destinations_per_rule']}\n\n"
    
    response += "💎 **Premium Features:**\n"
    response += "• Unlimited rules\n" if subscription_plan != 'free' else "• Up to 20 rules\n"
    response += "• Up to 50 sources per rule\n" if subscription_plan != 'free' else "• Up to 5 sources per rule\n"
    response += "• Up to 50 destinations per rule\n" if subscription_plan != 'free' else "• Up to 5 destinations per rule\n"
    response += "• Priority support\n\n" if subscription_plan != 'free' else "• Standard support\n\n"
    
    # Add upgrade button for free users
    if subscription_plan == 'free':
        buttons = [[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
        await event.respond(response, buttons=buttons)
    else:
        await event.respond(response)

@bot.on(events.NewMessage(pattern="/verify_payment"))
async def verify_payment_cmd(event):
    # This command should be used by your payment bot to verify payments
    # For security, you might want to add authentication for this command
    
    if str(event.sender_id) != PAYMENT_BOT_ID:  # You should set PAYMENT_BOT_ID
        await event.respond("❌ Unauthorized")
        return
        
    try:
        # Parse command: /verify_payment user_id plan duration_days
        parts = event.raw_text.split()
        if len(parts) < 4:
            await event.respond("❌ Usage: /verify_payment user_id plan duration_days")
            return
            
        user_id = int(parts[1])
        plan = parts[2]
        duration_days = int(parts[3])
        
        # Calculate expiry date - datetime is now imported
        expires_at = datetime.now() + timedelta(days=duration_days)
        
        db = await get_db()
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET plan=$2, expires_at=$3
        """, user_id, plan, expires_at)
        
        # Notify user
        try:
            await bot.send_message(
                user_id, 
                f"✅ Payment successful! Your {plan} plan is now active.\n"
                f"⏰ Expires on: {expires_at.strftime('%Y-%m-%d')}\n\n"
                "Thank you for upgrading! 🎉"
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")
            
        await event.respond(f"✅ Payment verified for user {user_id}")
        
    except Exception as e:
        await event.respond(f"❌ Error: {str(e)}")

async def check_subscription_limit(user_id, limit_type):
    """Check if user has reached a subscription limit"""
    subscription_plan = await get_user_subscription(user_id)  # This now returns normalized plan
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    
    db = await get_db()
    
    if limit_type == 'rules':
        count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
        return count < limits['max_rules'], limits['max_rules']
    
    elif limit_type == 'sources':
        # Get current rule to check sources for this rule
        rule_id, _ = await get_current_rule(user_id)
        count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        return count < limits['max_sources_per_rule'], limits['max_sources_per_rule']
    
    elif limit_type == 'destinations':
        # Get current rule to check destinations for this rule
        rule_id, _ = await get_current_rule(user_id)
        count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        return count < limits['max_destinations_per_rule'], limits['max_destinations_per_rule']
    
    return True, 0  # Default to no limit

async def check_and_notify_subscription_limit(user_id, limit_type, action_name):
    can_add, max_limit = await check_subscription_limit(user_id, limit_type)
    if not can_add:
        db = await get_db()
        
        if limit_type == 'rules':
            current_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
        elif limit_type == 'sources':
            rule_id, _ = await get_current_rule(user_id)
            current_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        elif limit_type == 'destinations':
            rule_id, _ = await get_current_rule(user_id)
            current_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        
        # Get the actual plan name for display
        display_plan = await get_subscription_display_name(user_id)
        
        message = (
            f"❌ You've reached the limit of {max_limit} {limit_type} on your {display_plan} plan.\n\n"
            f"Current: {current_count}/{max_limit}\n"
            f"Cannot {action_name}.\n\n"
            "💎 Upgrade to a higher plan for more!"
        )
        
        return False, message
    
    return True, ""

# Add this function to track user activity
async def track_user_activity(user_id):
    """Track when a user last used the bot"""
    try:
        db = await get_db()
        await db.execute("""
            INSERT INTO user_activity (user_id, last_activity, command_count)
            VALUES ($1, CURRENT_TIMESTAMP, 1)
            ON CONFLICT (user_id) DO UPDATE SET 
            last_activity = EXCLUDED.last_activity,
            command_count = user_activity.command_count + 1
        """, user_id)
    except Exception as e:
        logger.error(f"Error tracking user activity: {e}")


# Add this after the SUBSCRIPTION_LIMITS configuration
SUBSCRIPTION_WARNING_DAYS = 3  # Notify users 3 days before expiry

async def enforce_subscription_limits(user_id):
    """Enforce subscription limits - prevent reactivation of disabled rules"""
    subscription_plan = await get_user_subscription(user_id)
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    db = await get_db()
    
    issues = []
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    # For free plan: keep only first rule active
    if subscription_plan == 'free' and len(rules) > 1:
        first_rule_kept = False
        disabled_rules = []
        
        for i, rule in enumerate(rules):
            if not first_rule_kept:
                # Keep the first rule active
                await db.execute(
                    "UPDATE rules SET is_active=TRUE WHERE user_id=$1 AND rule_id=$2",
                    user_id, rule['rule_id']
                )
                first_rule_kept = True
                logger.info(f"Kept rule active: {rule['name']} (first rule)")
            else:
                # Disable all subsequent rules and ensure they STAY disabled
                await db.execute(
                    "UPDATE rules SET is_active=FALSE WHERE user_id=$1 AND rule_id=$2",
                    user_id, rule['rule_id']
                )
                disabled_rules.append(rule['rule_id'])
                issues.append(f"Disabled rule: {rule['name']}")
                logger.info(f"Disabled rule: {rule['name']} (exceeds free plan limit)")
        
        # Stop forwarding for disabled rules
        if disabled_rules:
            await stop_forwarding_for_disabled_rules(user_id, disabled_rules)
    
    # For premium plans, only activate rules that were manually activated
    # Don't auto-activate rules that were manually deactivated
    if subscription_plan in ['premium', 'enterprise']:
        # Only activate rules that have sources/destinations and weren't manually disabled
        for rule in rules:
            # Check if rule has configurations
            sources_count = await db.fetchval(
                "SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", 
                user_id, rule['rule_id']
            )
            destinations_count = await db.fetchval(
                "SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", 
                user_id, rule['rule_id']
            )
            
            # Only auto-activate if rule has configurations
            if sources_count > 0 and destinations_count > 0:
                # But don't reactivate rules that were manually disabled
                # We need to track manual deactivation separately
                current_status = rule['is_active']
                if not current_status:
                    logger.info(f"Rule {rule['name']} remains inactive (manual setting)")
            else:
                # No configurations, keep inactive
                await db.execute(
                    "UPDATE rules SET is_active=FALSE WHERE user_id=$1 AND rule_id=$2",
                    user_id, rule['rule_id']
                )
    
    return issues

async def stop_forwarding_for_disabled_rules(user_id, disabled_rule_ids):
    """Stop forwarding for disabled rules by restarting forwarding session"""
    if user_id in forwarding_tasks:
        try:
            logger.info(f"Stopping forwarding for user {user_id} to apply rule changes...")
            
            # Cancel current forwarding task
            forwarding_tasks[user_id].cancel()
            await asyncio.sleep(2)  # Allow cancellation to complete
            
            # Remove from tracking
            if user_id in forwarding_tasks:
                del forwarding_tasks[user_id]
            
            # Check if user still has active rules and sources/destinations
            db = await get_db()
            active_rules = await db.fetch(
                "SELECT * FROM rules WHERE user_id=$1 AND is_active=TRUE", 
                user_id
            )
            
            if active_rules:
                sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
                destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
                
                if sources and destinations:
                    # Wait a moment before restarting
                    await asyncio.sleep(3)
                    
                    # Restart forwarding with updated rules
                    task = asyncio.create_task(forward_messages(user_id))
                    forwarding_tasks[user_id] = task
                    
                    # Update database status
                    await db.execute("""
                        UPDATE forwarding_status SET is_active=TRUE, last_started=CURRENT_TIMESTAMP 
                        WHERE user_id=$1
                    """, user_id)
                    
                    logger.info(f"Restarted forwarding for user {user_id} with updated rules")
                    
                    # Notify user about the changes
                    await notify_user_about_rule_changes(user_id, disabled_rule_ids)
                else:
                    logger.info(f"User {user_id} has no sources/destinations, not restarting forwarding")
                    await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
            else:
                logger.info(f"User {user_id} has no active rules, not restarting forwarding")
                await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
                
        except Exception as e:
            logger.error(f"Error stopping/restarting forwarding for user {user_id}: {e}")

async def notify_user_about_rule_changes(user_id, disabled_rule_ids):
    """Notify user about rule changes due to subscription limits"""
    if not disabled_rule_ids:
        return
    
    db = await get_db()
    
    # Get rule names for the disabled rules
    rule_names = []
    for rule_id in disabled_rule_ids:
        rule = await db.fetchrow(
            "SELECT name FROM rules WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule_id
        )
        if rule:
            rule_names.append(rule['name'])
    
    if rule_names:
        # Get current active rule info
        current_rule_id, current_rule_name = await get_current_rule(user_id)
        
        # Get sources and destinations for the active rule
        sources = await db.fetch(
            "SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2 ORDER BY chat_id", 
            user_id, current_rule_id
        )
        destinations = await db.fetch(
            "SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2 ORDER BY chat_id", 
            user_id, current_rule_id
        )
        
        first_source = sources[0]['title'] if sources else "No sources"
        first_destination = destinations[0]['title'] if destinations else "No destinations"
        
        message = (
            "🔧 **Auto-Adjusted to Free Plan Limits**\n\n"
            "Your configuration has been automatically adjusted to comply with free plan limits:\n\n"
        )
        
        for rule_name in rule_names:
            message += f"• ❌ Disabled rule: {rule_name}\n"
        
        message += (
            f"\n✅ **Active Rule:** {current_rule_name}\n"
            f"📥 **Using Source:** {first_source}\n"
            f"📤 **Using Destination:** {first_destination}\n\n"
            f"💡 **Note:** All your {len(sources)} sources and {len(destinations)} destinations are preserved in the database.\n"
            f"Only the first source and first destination are used during forwarding on the free plan.\n\n"
            "🔄 **Forwarding has been restarted** with limited configuration.\n\n"
            "💎 Upgrade to Premium to use all sources and destinations simultaneously!"
        )
        
        buttons = [
            [Button.inline("💎 Upgrade Plan", data="upgrade_subscription")],
            [Button.inline("📋 View Rules", data="view_rules_after_limit")],
            [Button.inline("📊 Check Usage", data="check_compliance")]
        ]
        
        try:
            await bot.send_message(user_id, message, buttons=buttons)
        except Exception as e:
            logger.warning(f"Could not send rule change notification to user {user_id}: {e}")

async def check_if_exceeds_free_limits(user_id):
    """Check if user exceeds free plan limits (more than 1 rule OR more than 1 source/destination per rule)"""
    db = await get_db()
    
    # Check rules count
    rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    if rules_count > 1:
        return f"Too many rules: {rules_count}/1"
    
    # Check each rule's sources and destinations
    rules = await db.fetch("SELECT rule_id, name FROM rules WHERE user_id=$1", user_id)
    for rule in rules:
        sources_count = await db.fetchval(
            "SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule['rule_id']
        )
        destinations_count = await db.fetchval(
            "SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule['rule_id']
        )
        
        if sources_count > 1:
            return f"Rule '{rule['name']}' has too many sources: {sources_count}/1"
        if destinations_count > 1:
            return f"Rule '{rule['name']}' has too many destinations: {destinations_count}/1"
    
    return None  # User is within free plan limits

async def check_subscription_compliance(user_id):
    """Check if user complies with their current plan limits"""
    subscription_plan = await get_user_subscription(user_id)
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    
    db = await get_db()
    
    # Check rules count
    rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    if rules_count > limits['max_rules']:
        return False, f"Too many rules: {rules_count}/{limits['max_rules']}"
    
    # Check each rule's sources and destinations
    rules = await db.fetch("SELECT rule_id, name FROM rules WHERE user_id=$1", user_id)
    for rule in rules:
        sources_count = await db.fetchval(
            "SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule['rule_id']
        )
        destinations_count = await db.fetchval(
            "SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule['rule_id']
        )
        
        if sources_count > limits['max_sources_per_rule']:
            return False, f"Rule '{rule['name']}' has too many sources: {sources_count}/{limits['max_sources_per_rule']}"
        if destinations_count > limits['max_destinations_per_rule']:
            return False, f"Rule '{rule['name']}' has too many destinations: {destinations_count}/{limits['max_destinations_per_rule']}"
    
    return True, "Compliant"

async def check_expiring_subscriptions():
    """Check and notify users about expiring subscriptions (only once per expiry period)"""
    db = await get_db()
    
    # Notify users 3 days before expiry
    warning_date = datetime.now() + timedelta(days=SUBSCRIPTION_WARNING_DAYS)
    expiring_subs = await db.fetch("""
        SELECT s.*, n.last_expiry_notification 
        FROM subscriptions s 
        LEFT JOIN subscription_notifications n ON s.user_id = n.user_id 
        WHERE s.expires_at BETWEEN $1 AND $2
        AND s.expires_at > CURRENT_TIMESTAMP
    """, datetime.now(), warning_date)
    
    for sub in expiring_subs:
        try:
            user_id = sub['user_id']
            days_left = (sub['expires_at'] - datetime.now()).days
            
            # Check if we've notified this user recently (in the last 7 days)
            last_notified = sub.get('last_expiry_notification')
            should_notify = True
            
            if last_notified:
                # Don't notify if we already notified in the last 7 days
                days_since_notification = (datetime.now() - last_notified).days
                if days_since_notification < 7:
                    should_notify = False
            
            if should_notify and days_left <= SUBSCRIPTION_WARNING_DAYS:
                await bot.send_message(
                    user_id,
                    f"⚠️ **Subscription Expiry Notice**\n\n"
                    f"Your {sub['plan']} plan expires in {days_left} days.\n"
                    f"Expiry date: {sub['expires_at'].strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                    "Renew now to avoid service interruption and automatic downgrade to free plan!",
                    buttons=[[Button.inline("💎 Renew Plan", data="upgrade_subscription")]]
                )
                
                # Record this notification
                await db.execute("""
                    INSERT INTO subscription_notifications (user_id, last_expiry_notification, notified_for_plan) 
                    VALUES ($1, CURRENT_TIMESTAMP, $2) 
                    ON CONFLICT (user_id) DO UPDATE SET 
                    last_expiry_notification = EXCLUDED.last_expiry_notification, 
                    notified_for_plan = EXCLUDED.notified_for_plan
                """, user_id, f"expiring_{sub['plan']}")
                
                logger.info(f"Sent expiry warning to user {user_id} ({days_left} days left)")
                
        except Exception as e:
            logger.error(f"Could not notify user {sub['user_id']}: {e}")

async def check_expired_subscriptions():
    """Check and downgrade expired subscriptions (run less frequently)"""
    db = await get_db()
    
    # Only process users we haven't handled in the last hour
    expired_subs = await db.fetch("""
        SELECT s.* FROM subscriptions s 
        JOIN users u ON s.user_id = u.id
        WHERE s.expires_at <= $1
        AND u.session IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM subscription_notifications 
            WHERE user_id = s.user_id 
            AND last_expiry_notification > (CURRENT_TIMESTAMP - INTERVAL '1 hour')
        )
    """, datetime.now())
    
    for sub in expired_subs:
        user_id = sub['user_id']
        try:
            # Check if user was previously on a paid plan
            was_premium = sub['plan'].lower() in ['premium', 'enterprise', 'pro', 'paid']
            
            if was_premium:
                # Store current forwarding status before making changes
                was_forwarding_active = user_id in forwarding_tasks
                
                # Enforce free plan limits
                issues = await enforce_subscription_limits(user_id)
                
                # Disable premium features
                disabled_features = await disable_premium_features_on_downgrade(user_id)
                
                # Stop existing forwarding if running
                if was_forwarding_active:
                    try:
                        forwarding_tasks[user_id].cancel()
                        del forwarding_tasks[user_id]
                    except Exception as e:
                        logger.warning(f"Error stopping forwarding for user {user_id}: {e}")
                
                # Update database status
                await db.execute("""
                    UPDATE forwarding_status SET is_active=FALSE 
                    WHERE user_id=$1
                """, user_id)
                
                # Prepare the single notification message
                message = (
                    "🔧 **Auto-Adjusted to Free Plan Limits**\n\n"
                    "Your configuration has been automatically adjusted:\n\n"
                )
                
                if issues:
                    message += "**Auto-adjustments made:**\n"
                    for issue in issues:
                        message += f"• {issue}\n"
                    message += "\n"
                
                # Check if user has sources and destinations to restart forwarding
                sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
                destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
                
                if sources and destinations:
                    # Wait a moment before restarting
                    await asyncio.sleep(2)
                    
                    # Restart forwarding with new limits
                    task = asyncio.create_task(forward_messages(user_id))
                    forwarding_tasks[user_id] = task
                    
                    # Update database status
                    await db.execute("""
                        UPDATE forwarding_status SET is_active=TRUE, last_started=CURRENT_TIMESTAMP 
                        WHERE user_id=$1
                    """, user_id)
                    
                    message += (
                        "🔄 **Forwarding RESTARTED with limited configuration.**\n\n"
                        "Now using only:\n"
                        "• 1 active rule (first rule)\n"
                        "• 1 source per rule\n"
                        "• 1 destination per rule\n\n"
                    )
                else:
                    message += (
                        "❌ **Forwarding not started** - no sources/destinations configured.\n\n"
                        "Please set up sources and destinations first.\n\n"
                    )
                
                # Add disabled features info if any were disabled
                if disabled_features:
                    message += "**Premium features disabled:**\n"
                    for feature_info in disabled_features:
                        message += f"• {feature_info}\n"
                    message += "\n"
                
                message += "💎 Upgrade to restore full functionality!"
                
                buttons = [
                    [Button.inline("💎 Upgrade Subscription", data="upgrade_subscription")],
                    [Button.inline("📊 Check Usage", data="check_compliance")]
                ]
                
                # Add start button only if forwarding was restarted
                if sources and destinations:
                    buttons.insert(1, [Button.inline("🚀 Start Forwarding", data="start_after_fix")])
                
                # Send the single comprehensive message
                await bot.send_message(user_id, message, buttons=buttons)
                
                logger.info(f"User {user_id} subscription expired, downgraded to free plan. Issues: {issues}")
            
            # Mark as processed
            await db.execute("""
                INSERT INTO subscription_notifications (user_id, last_expiry_notification, notified_for_plan)
                VALUES ($1, CURRENT_TIMESTAMP, $2)
                ON CONFLICT (user_id) DO UPDATE SET 
                last_expiry_notification = EXCLUDED.last_expiry_notification,
                notified_for_plan = EXCLUDED.notified_for_plan
            """, user_id, f"expired_{sub['plan']}")
            
        except Exception as e:
            logger.error(f"Could not process expired subscription for user {user_id}: {e}")

async def disable_premium_features_on_downgrade(user_id):
    """Disable all premium features when user is downgraded to free plan"""
    db = await get_db()
    
    # Get all rules for this user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1", user_id)
    
    disabled_features = []
    
    for rule in rules:
        rule_id = rule['rule_id']
        
        # Get current options
        rule_options = await db.fetchrow(
            "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
            user_id, rule_id
        )
        
        if not rule_options or not rule_options['options']:
            continue
            
        options = {}
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            continue
        
        # Check and disable premium features
        features_disabled = []
        
        # Disable remove_links feature
        if options.get('remove_links', False):
            options['remove_links'] = False
            features_disabled.append('remove_links')
        
        # Disable text replacement features
        if options.get('text_replacements'):
            del options['text_replacements']
            features_disabled.append('text_replacements')
        
        if options.get('replace_all_text', {}).get('enabled', False):
            options['replace_all_text'] = {'enabled': False, 'replacement': ''}
            features_disabled.append('replace_all_text')
        
        # Save updated options if any features were disabled
        if features_disabled:
            await db.execute(
                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                json.dumps(options), user_id, rule_id
            )
            disabled_features.append(f"Rule '{rule['name']}': {', '.join(features_disabled)}")
    
    return disabled_features

async def consolidated_subscription_enforcement():
    """Consolidated subscription enforcement with proper cooldown handling"""
    # Track recently processed users in memory
    recently_processed = set()
    
    while True:
        try:
            logger.info("Running consolidated subscription enforcement...")
            
            # Check every 5 minutes
            await asyncio.sleep(300)
            
            db = await get_db()
            
            # 1. First, handle expired subscriptions (downgrade to free)
            await process_expired_subscriptions(db)
            
            # 2. Then, handle expiring subscriptions (notifications)
            await check_expiring_subscriptions()
            
            # 3. Finally, enforce limits for active users
            await enforce_limits_for_active_users(db, recently_processed)
            
            # Clean up memory tracking
            if len(recently_processed) > 1000:
                recently_processed.clear()
                
        except Exception as e:
            logger.error(f"Error in consolidated subscription enforcement: {e}")

async def process_expired_subscriptions(db):
    """Process users with expired subscriptions"""
    expired_users = await db.fetch("""
        SELECT DISTINCT u.id as user_id, s.plan, s.expires_at
        FROM users u 
        JOIN subscriptions s ON u.id = s.user_id 
        WHERE s.expires_at <= $1
        AND u.session IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM subscription_notifications 
            WHERE user_id = s.user_id 
            AND last_expiry_notification > (CURRENT_TIMESTAMP - INTERVAL '4 hours')
            AND notified_for_plan LIKE 'expired_%'
        )
        AND s.expires_at > (CURRENT_TIMESTAMP - INTERVAL '30 days')
    """, datetime.now())
    
    for user_record in expired_users:
        user_id = user_record['user_id']
        try:
            # Check if user was previously on a paid plan
            was_premium = user_record['plan'].lower() in ['premium', 'enterprise', 'pro', 'paid']
            
            if was_premium:
                logger.info(f"Processing expired subscription for user {user_id}")
                
                # Stop forwarding first
                await stop_user_forwarding(user_id)
                
                # Enforce free plan limits
                issues = await enforce_subscription_limits(user_id)
                
                # Disable premium features
                disabled_features = await disable_premium_features_on_downgrade(user_id)
                
                # Send notification to user
                await send_expiry_notification(user_id, issues, disabled_features, user_record['plan'])
                
            # Mark as processed for 4 hours
            await db.execute("""
                INSERT INTO subscription_notifications (user_id, last_expiry_notification, notified_for_plan)
                VALUES ($1, CURRENT_TIMESTAMP, $2)
                ON CONFLICT (user_id) DO UPDATE SET 
                last_expiry_notification = EXCLUDED.last_expiry_notification,
                notified_for_plan = EXCLUDED.notified_for_plan
            """, user_id, f"expired_{user_record['plan']}")
            
        except Exception as e:
            logger.error(f"Error processing expired subscription for user {user_id}: {e}")

async def enforce_limits_for_active_users(db, recently_processed):
    """Enforce limits for users with active forwarding"""
    active_users = await db.fetch("""
        SELECT 
            fs.user_id,
            COALESCE(
                CASE 
                    WHEN s.expires_at > CURRENT_TIMESTAMP THEN s.plan 
                    ELSE 'free' 
                END, 
                'free'
            ) as raw_plan
        FROM forwarding_status fs
        LEFT JOIN subscriptions s ON fs.user_id = s.user_id
        WHERE fs.is_active = TRUE
        AND fs.user_id NOT IN (
            SELECT user_id FROM subscription_notifications 
            WHERE last_expiry_notification > (CURRENT_TIMESTAMP - INTERVAL '1 hour')
            AND notified_for_plan = 'limit_enforcement'
        )
    """)
    
    for user_record in active_users:
        user_id = user_record['user_id']
        raw_plan = user_record['raw_plan'].lower() if user_record['raw_plan'] else 'free'
        
        # Skip if processed recently
        if user_id in recently_processed:
            continue
            
        try:
            subscription_plan = 'free'
            if any(keyword in raw_plan for keyword in ['month', 'premium', 'pro', 'paid']):
                subscription_plan = 'premium'
            elif any(keyword in raw_plan for keyword in ['year', 'enterprise', 'business']):
                subscription_plan = 'enterprise'
            elif raw_plan in ['free', 'basic']:
                subscription_plan = 'free'
            
            # Only check free users for compliance
            if subscription_plan == 'free':
                # Check if user exceeds free limits
                exceeds_limits = await check_if_exceeds_free_limits(user_id)
                
                if exceeds_limits:
                    logger.info(f"Free user {user_id} exceeds limits: {exceeds_limits}")
                    
                    # Enforce limits but DON'T stop forwarding
                    issues = await enforce_subscription_limits(user_id)
                    
                    if issues:
                        # Send notification about auto-adjustment
                        await send_limit_enforcement_notification(user_id, issues, exceeds_limits)
                        
                        # Mark as processed in memory for 30 minutes
                        recently_processed.add(user_id)
                        
                        # Mark in database for 1 hour
                        await db.execute("""
                            INSERT INTO subscription_notifications (user_id, last_expiry_notification, notified_for_plan)
                            VALUES ($1, CURRENT_TIMESTAMP, $2)
                            ON CONFLICT (user_id) DO UPDATE SET 
                            last_expiry_notification = EXCLUDED.last_expiry_notification,
                            notified_for_plan = EXCLUDED.notified_for_plan
                        """, user_id, "limit_enforcement")
                        
        except Exception as e:
            logger.error(f"Error enforcing limits for user {user_id}: {e}")

async def stop_user_forwarding(user_id):
    """Stop forwarding for a user"""
    if user_id in forwarding_tasks:
        try:
            forwarding_tasks[user_id].cancel()
            await asyncio.sleep(2)  # Allow cancellation to complete
            if user_id in forwarding_tasks:
                del forwarding_tasks[user_id]
            logger.info(f"Stopped forwarding for user {user_id}")
        except Exception as e:
            logger.warning(f"Error stopping forwarding for user {user_id}: {e}")
    
    # Update database status
    db = await get_db()
    await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)

async def send_expiry_notification(user_id, issues, disabled_features, plan_name):
    """Send expiry notification to user"""
    message = (
        "📋 **Subscription Expired - Downgraded to Free Plan**\n\n"
        f"Your {plan_name} subscription has expired and you've been automatically downgraded to the free plan.\n\n"
        "**Free Plan Limits Applied:**\n"
        "• Only 1 rule enabled (others disabled)\n"
        "• Only 1 source per rule used\n" 
        "• Only 1 destination per rule used\n\n"
    )
    
    if issues:
        message += "**Auto-adjustments made:**\n"
        for issue in issues:
            message += f"• {issue}\n"
        message += "\n"
    
    if disabled_features:
        message += "**Premium features disabled:**\n"
        for feature_info in disabled_features:
            message += f"• {feature_info}\n"
        message += "\n"
    
    message += (
        "❌ **Forwarding has been stopped.**\n\n"
        "Please use /start_forwarding to restart with free plan limits.\n\n"
        "💎 Upgrade to restore full functionality!"
    )
    
    buttons = [
        [Button.inline("💎 Upgrade Subscription", data="upgrade_subscription")],
        [Button.inline("🚀 Start Forwarding", data="start_after_fix")],
        [Button.inline("📊 Check Usage", data="check_compliance")]
    ]
    
    try:
        await bot.send_message(user_id, message, buttons=buttons)
    except Exception as e:
        logger.warning(f"Could not send expiry notification to user {user_id}: {e}")

async def send_limit_enforcement_notification(user_id, issues, exceeds_limits):
    """Send limit enforcement notification to user"""
    message = (
        f"🔧 **Auto-Adjusted to Free Plan Limits**\n\n"
        f"Your account configuration has been automatically adjusted:\n\n"
    )
    
    if issues:
        message += "\n".join([f"• {issue}" for issue in issues]) + "\n\n"
    
    message += (
        f"🔄 **Forwarding continues** with limited configuration.\n\n"
        f"Now using only:\n"
        f"• 1 active rule (first rule)\n"
        f"• 1 source per rule\n"
        f"• 1 destination per rule\n\n"
        f"💎 Upgrade for more capacity!"
    )
    
    buttons = [
        [Button.inline("💎 Upgrade Plan", data="upgrade_subscription")],
        [Button.inline("📊 Check Usage", data="check_compliance")]
    ]
    
    try:
        await bot.send_message(user_id, message, buttons=buttons)
    except Exception as e:
        logger.warning(f"Could not send limit notification to user {user_id}: {e}")

async def periodic_subscription_checks():
    """Periodically check for expired subscriptions and stop forwarding"""
    while True:
        try:
            # Check every 10 minutes
            await asyncio.sleep(5)
            
            logger.info("Running periodic subscription checks...")
            
            # Check and process expired subscriptions
            await check_expired_subscriptions()
            
            # Check and notify about expiring subscriptions
            await check_expiring_subscriptions()
            
            # Check all active forwarding users for compliance
            await check_active_forwarding_compliance()
            
        except Exception as e:
            logger.error(f"Error in periodic subscription checks: {e}")

async def check_active_forwarding_compliance():
    """Check all users with active forwarding but DON'T stop forwarding"""
    db = await get_db()
    
    # Get all users with active forwarding
    active_users = await db.fetch("""
        SELECT user_id FROM forwarding_status 
        WHERE is_active = TRUE
    """)
    
    for user_record in active_users:
        user_id = user_record['user_id']
        try:
            # Get user's current subscription plan
            subscription_plan = await get_user_subscription(user_id)
            
            # Only check free users for compliance with free plan limits
            if subscription_plan == 'free':
                # First disable any premium features they shouldn't have
                disabled_features = await disable_premium_features_on_downgrade(user_id)
                
                exceeds_limits = await check_if_exceeds_free_limits(user_id)
                
                if exceeds_limits:
                    logger.info(f"Free user {user_id} exceeds limits: {exceeds_limits}")
                    
                    # DON'T stop forwarding, just notify user
                    message = (
                        f"📋 **Free Plan Limits Applied**\n\n"
                        f"Your account exceeds free plan limits:\n"
                        f"• {exceeds_limits}\n\n"
                    )
                    
                    # Add disabled features info if any were disabled
                    if disabled_features:
                        message += "**Premium features disabled:**\n"
                        for feature_info in disabled_features:
                            message += f"• {feature_info}\n"
                        message += "\n"
                    
                    message += (
                        "**Free Plan Limits:**\n"
                        "• 1 rule total\n"
                        "• 1 source per rule\n" 
                        "• 1 destination per rule\n\n"
                        "🔄 **Forwarding continues with limited configuration**\n\n"
                        "Your configuration has been automatically adjusted to comply with free plan limits.\n\n"
                        "💎 Upgrade for more capacity and premium features!"
                    )
                    
                    await bot.send_message(
                        user_id,
                        message,
                        buttons=[
                            [Button.inline("💎 Upgrade Plan", data="upgrade_subscription")],
                            [Button.inline("📊 Check Usage", data="check_compliance")],
                            [Button.inline("📋 View Rules", data="view_rules_after_limit")]
                        ]
                    )
                elif disabled_features:
                    # User is within limits but had premium features disabled
                    message = (
                        "🔧 **Premium Features Auto-Disabled**\n\n"
                        "The following premium features have been disabled for your free plan:\n"
                    )
                    for feature_info in disabled_features:
                        message += f"• {feature_info}\n"
                    
                    message += (
                        "\n✅ Your forwarding continues normally with free plan features.\n\n"
                        "💎 Upgrade to restore premium features!"
                    )
                    
                    await bot.send_message(
                        user_id,
                        message,
                        buttons=[[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
                    )
                    
        except Exception as e:
            logger.error(f"Error checking compliance for user {user_id}: {e}")

# ---------------- HELPERS ----------------
async def cancel_ongoing_operation(user_id):
    """Cancel any ongoing operation for the user"""
    if user_id in user_operation_mode:
        operation = user_operation_mode[user_id]
        logger.info(f"Cancelling ongoing operation for user {user_id}: {operation}")
        
        # Clear user state for that operation
        if user_id in user_states:
            del user_states[user_id]
        
        # Cancel the operation mode
        del user_operation_mode[user_id]
        
        # Try to notify the user
        try:
            await bot.send_message(user_id, f"❌ Operation cancelled: {operation}")
        except:
            pass
        
        return True
    return False

async def ask_user_to_stop_forwarding(user_id, configuration_type):
    """Ask user to stop forwarding before configuration changes"""
    if user_id in forwarding_tasks:
        try:
            await bot.send_message(
                user_id,
                f"Please **Stop Forwarding** Before changing **{configuration_type}**\n\n"
                f"1. Use /stop_forwarding to stop the current session\n"
                f"2. Then configure your {configuration_type}\n"
                f"3. Use /start_forwarding to restart with new configurations \n\n"
                
            )
            return True  # Forwarding is running, user needs to stop it
        except Exception as e:
            logger.warning(f"Could not ask user {user_id} to stop forwarding: {e}")
    return False  # No forwarding running

def replace_links_in_text(text, link_replacements):
    """Replace links in text according to the replacement rules"""
    if not text or not link_replacements:
        return text
    
    replaced_text = text
    for original_link, new_link in link_replacements.items():
        replaced_text = replaced_text.replace(original_link, new_link)
    
    return replaced_text

async def get_forwarding_delay(user_id, rule_id):
    """Get forwarding delay for a rule"""
    db = await get_db()
    row = await db.fetchrow(
        "SELECT delay_seconds FROM forwarding_delays WHERE user_id=$1 AND rule_id=$2",
        user_id, rule_id
    )
    return row['delay_seconds'] if row else 0

async def set_forwarding_delay(user_id, rule_id, delay_seconds):
    """Set forwarding delay for a rule"""
    db = await get_db()
    await db.execute("""
        INSERT INTO forwarding_delays (user_id, rule_id, delay_seconds)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, rule_id) DO UPDATE SET delay_seconds = $3
    """, user_id, rule_id, delay_seconds)

async def resolve_entity_safe(client, chat_id):
    """Safely resolve entity with multiple fallbacks"""
    try:
        # Try direct entity resolution first
        return await client.get_entity(chat_id)
    except (ValueError, TypeError):
        try:
            # Try input entity resolution
            return await client.get_input_entity(chat_id)
        except Exception as e:
            logger.warning(f"Could not resolve entity {chat_id}: {e}")
            return None
    except Exception as e:
        logger.warning(f"Error resolving entity {chat_id}: {e}")
        return None

async def get_user_client(user_id, force_refresh=False):
    """Load user client from DB or cache"""
    # If force refresh or user not in cache, create new client
    if force_refresh or user_id not in user_clients:
        db = await get_db()
        row = await db.fetchrow("SELECT session FROM users WHERE id=$1", user_id)
        if row and row["session"]:
            try:
                client = TelegramClient(StringSession(row["session"]), API_ID, API_HASH)
                await client.connect()
                
                # More reliable authorization check
                try:
                    # Try a simple operation to check authorization
                    me = await client.get_me()
                    if me:
                        user_clients[user_id] = client
                        logger.info(f"Client loaded for user {user_id}: {me.id}")
                        return client
                    else:
                        logger.warning(f"Client get_me returned None for user {user_id}")
                except Exception as auth_error:
                    logger.warning(f"Client not authorized for user {user_id}: {auth_error}")
                
                # If authorization fails, clean up cache
                await client.disconnect()
                if user_id in user_clients:
                    del user_clients[user_id]
                return None
                    
            except Exception as e:
                logger.error(f"Error creating client for user {user_id}: {e}")
                # Clean up cache
                if user_id in user_clients:
                    del user_clients[user_id]
                return None
        return None
    
    # Get client from cache
    client = user_clients[user_id]
    
    # Verify if cached client is still valid
    try:
        # Try a simple operation to check connection
        await client.get_me()
        return client
    except Exception as e:
        logger.warning(f"Cached client for user {user_id} is invalid: {e}")
        # Clean up invalid cache
        try:
            await client.disconnect()
        except:
            pass
        del user_clients[user_id]
        
        # Recursively call to create new client
        return await get_user_client(user_id, force_refresh=True)

async def check_client_health(client):
    """Check if client connection is healthy"""
    try:
        me = await client.get_me()
        return me is not None
    except Exception as e:
        logger.warning(f"Client health check failed: {e}")
        return False

async def refresh_user_client(user_id):
    """Force refresh user's client session"""
    if user_id in user_clients:
        try:
            await user_clients[user_id].disconnect()
        except:
            pass
        del user_clients[user_id]
    
    return await get_user_client(user_id, force_refresh=True)

async def get_bot_chat(client, bot_username):
    """Get the bot chat entity directly"""
    try:
        # Remove @ symbol if present
        if bot_username.startswith('@'):
            bot_username = bot_username[1:]
        
        bot_entity = await client.get_entity(bot_username)
        return {
            'id': bot_entity.id,
            'title': bot_entity.first_name or bot_entity.title or bot_username,
            'username': bot_entity.username,
            'is_bot': getattr(bot_entity, 'bot', False),
            'pinned': False
        }
    except Exception as e:
        logging.error(f"Error getting bot entity: {e}")
        return None

async def get_user_dialogs(user_id):
    """Get user's dialogs (chats, channels, groups, and private chats)"""
    client = await get_user_client(user_id)
    if not client:
        return None
    
    dialogs = []
    try:
        async for dialog in client.iter_dialogs():
            # Include channels, groups, AND private chats (including bots)
            if dialog.is_channel or dialog.is_group or dialog.is_user:
                title = dialog.title or dialog.name or "Unknown"
                if dialog.is_user and dialog.entity:
                    title = getattr(dialog.entity, 'first_name', None) or title
                
                dialogs.append({
                    'id': dialog.id,
                    'name': dialog.name,
                    'title': title,
                    'pinned': dialog.pinned,
                    'is_user': dialog.is_user,
                    'is_bot': getattr(dialog.entity, 'bot', False) if dialog.entity else False
                })
    except Exception as e:
        logger.error(f"Error getting dialogs for user {user_id}: {e}")
    
    return dialogs

async def create_numbered_keyboard(items, page=0, items_per_page=10, include_done=True):
    """Create a numbered keyboard for selection"""
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    keyboard = []
    row = []
    
    for i, item in enumerate(page_items, start=1):
        btn_text = f"{i}. {item['title'][:15]}"
        # Use KeyboardButtonCallback for callback handling
        row.append(KeyboardButtonCallback(btn_text, data=str(i)))
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(KeyboardButtonCallback("⬅️ Previous", data="prev"))
    if end_idx < len(items):
        nav_row.append(KeyboardButtonCallback("➡️ Next", data="next"))
    if nav_row:
        keyboard.append(nav_row)
    
    if include_done:
        keyboard.append([KeyboardButtonCallback("✅ Done Selecting", data="done")])
    
    return keyboard, page_items

async def get_current_rule(user_id):
    """Get the current rule for a user from database"""
    db = await get_db()
    
    # First try to get from database
    user_row = await db.fetchrow("SELECT current_rule FROM users WHERE id=$1", user_id)
    if user_row and user_row['current_rule']:
        # Get the rule name
        rule = await db.fetchrow(
            "SELECT name FROM rules WHERE user_id=$1 AND rule_id=$2", 
            user_id, user_row['current_rule']
        )
        rule_name = rule['name'] if rule else user_row['current_rule']
        return user_row['current_rule'], rule_name
    
    # Fallback to state (temporary)
    if user_id in user_states and 'current_rule' in user_states[user_id]:
        return user_states[user_id]['current_rule'], user_states[user_id].get('rule_name', 'default')
    
    # Get the first active rule or default
    rule = await db.fetchrow("SELECT * FROM rules WHERE user_id=$1 AND is_active=TRUE ORDER BY rule_id LIMIT 1", user_id)
    if rule:
        return rule['rule_id'], rule['name']
    
    return 'default', 'default'

async def check_keyword_filter(message, user_id, rule_id):
    """Check if message passes keyword filtering"""
    db = await get_db()
    
    # Get whitelist and blacklist keywords
    whitelist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
        user_id, rule_id
    )
    
    blacklist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
        user_id, rule_id
    )
    
    whitelist_keywords = whitelist['keywords'] if whitelist else []
    blacklist_keywords = blacklist['keywords'] if blacklist else []
    
    # If no filters are set, allow all messages
    if not whitelist_keywords and not blacklist_keywords:
        return True
    
    message_text = message.text or ""
    message_caption = getattr(message, 'caption', '') or ""
    full_text = f"{message_text} {message_caption}".lower().strip()
    
    # Check blacklist first - if any blacklist keyword is found, reject
    for keyword in blacklist_keywords:
        if keyword.lower() in full_text:
            logger.info(f"Message rejected due to blacklist keyword: {keyword}")
            return False
    
    # Check whitelist - if whitelist exists but no keywords match, reject
    if whitelist_keywords:
        for keyword in whitelist_keywords:
            if keyword.lower() in full_text:
                logger.info(f"Message accepted due to whitelist keyword: {keyword}")
                return True
        # If we have whitelist but no keywords matched
        logger.info("Message rejected - no whitelist keywords matched")
        return False
    
    # If only blacklist exists and no blacklist keywords matched
    return True

async def save_selected_sources(user_id, rule_id, source_ids):
    """Save selected sources for a rule, storing username for bots"""
    db = await get_db()
    # First get existing sources for this rule to preserve them
    existing_sources = await db.fetch(
        "SELECT chat_id FROM sources WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    existing_source_ids = {source['chat_id'] for source in existing_sources}
    
    # Add new sources (don't delete existing ones)
    for source_id in source_ids:
        if source_id not in existing_source_ids:
            # Get the dialog title and username
            client = await get_user_client(user_id)
            title = f"Chat {source_id}"
            username = None
            
            if client:
                try:
                    entity = await resolve_entity_safe(client, source_id)
                    if entity:
                        title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or title
                        # Store username if it's a bot
                        if getattr(entity, 'bot', False):
                            username = getattr(entity, 'username', None)
                except Exception as e:
                    logger.error(f"Error getting entity for source {source_id}: {e}")
            
            await db.execute(
                "INSERT INTO sources (user_id, rule_id, chat_id, title, username) VALUES ($1, $2, $3, $4, $5)",
                user_id, rule_id, source_id, title, username
            )

async def save_selected_destinations(user_id, rule_id, destination_ids):
    """Save selected destinations for a rule, storing username for bots"""
    db = await get_db()
    # First get existing destinations for this rule to preserve them
    existing_destinations = await db.fetch(
        "SELECT chat_id FROM destinations WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    existing_destination_ids = {dest['chat_id'] for dest in existing_destinations}
    
    # Add new destinations (don't delete existing ones)
    for dest_id in destination_ids:
        if dest_id not in existing_destination_ids:
            # Get the dialog title and username
            client = await get_user_client(user_id)
            title = f"Chat {dest_id}"
            username = None
            
            if client:
                try:
                    entity = await resolve_entity_safe(client, dest_id)
                    if entity:
                        title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or title
                        # Store username if it's a bot
                        if getattr(entity, 'bot', False):
                            username = getattr(entity, 'username', None)
                except Exception as e:
                    logger.error(f"Error getting entity for destination {dest_id}: {e}")
            
            await db.execute(
                "INSERT INTO destinations (user_id, rule_id, chat_id, title, username) VALUES ($1, $2, $3, $4, $5)",
                user_id, rule_id, dest_id, title, username
            )

async def update_source_selection_message(event):
    user_id = event.sender_id
    if user_id not in user_states:
        return
        
    state = user_states[user_id]
    dialogs = state['dialogs']
    page = state.get('page', 0)
    selected = state.get('selected', [])
    current_count = state.get('current_count', 0)
    max_limit = state.get('max_limit', 5)
    
    # Create message text with safe key access
    rule_name = state.get('rule_name', 'Default Rule')
    current_rule = state.get('current_rule', 'default')
    subscription_plan = await get_user_subscription(user_id)
    
    rule_info = f" for rule '{rule_name}'" if current_rule != 'default' else ''
    message_text = f"**Select sources to copy from{rule_info}:**\n\n"
    
    # Add subscription info
    message_text += f"📊 **Subscription:** {subscription_plan.upper()} ({current_count + len(selected)}/{max_limit} sources)\n\n"
    
    if selected:
        message_text += f"✅ Selected: {len(selected)} source(s)\n\n"
    
    # Show top 15 chats only (no pagination)
    dialogs_to_show = dialogs[:15]
    
    for i, dialog in enumerate(dialogs_to_show, 1):
        # Add checkmark for selected items
        check = "✅ " if dialog['id'] in selected else ""
        # Add pin emoji for pinned chats
        pin_emoji = "📌 " if dialog.get('pinned') else ""
        # Truncate long names
        title = dialog['title']
        if len(title) > 25:
            title = title[:22] + "..."
        message_text += f"{i}. {check}{pin_emoji}{title}\n"
    
    # Add subscription limit warning
    if current_count + len(selected) >= max_limit and subscription_plan == 'free':
        message_text += f"\n❌ **Free plan limit:** {max_limit} sources per rule\n"
        message_text += "💎 Upgrade to Premium for more sources!\n"
    
    # Create buttons for first 10 chats
    buttons = []
    
    # First row: numbers 1-5 for current page
    row1 = []
    for i in range(1, 6):
        if i <= len(dialogs_to_show):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10 for current page
    row2 = []
    for i in range(6, 11):
        if i <= len(dialogs_to_show):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: numbers 11-15 (if available)
    row3 = []
    for i in range(11, 16):
        if i <= len(dialogs_to_show):
            row3.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row3.append(Button.inline(" ", data="none"))
    
    # Fourth row: Done button only (no navigation buttons)
    row4 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2]
    if row3:  # Only add third row if there are items
        buttons.append(row3)
    buttons.append(row4)
    
    # Add upgrade button if user is on free plan and near limit
    if subscription_plan == 'free' and current_count + len(selected) >= max_limit - 2:
        buttons.append([Button.inline("💎 Upgrade Plan", data="upgrade_subscription")])
    
    # Edit the message
    await event.edit(message_text, buttons=buttons)

async def update_destination_selection_message(event):
    user_id = event.sender_id
    if user_id not in user_states:
        return
        
    state = user_states[user_id]
    dialogs = state['dialogs']
    page = state.get('page', 0)
    selected = state.get('selected', [])
    current_count = state.get('current_count', 0)
    max_limit = state.get('max_limit', 5)
    
    # Create message text with safe key access
    rule_name = state.get('rule_name', 'Default Rule')
    current_rule = state.get('current_rule', 'default')
    subscription_plan = await get_user_subscription(user_id)
    
    rule_info = f" for rule '{rule_name}'" if current_rule != 'default' else ''
    message_text = f"**Select destinations to forward to{rule_info}:**\n\n"
    
    # Add subscription info
    message_text += f"📊 **Subscription:** {subscription_plan.upper()} ({current_count + len(selected)}/{max_limit} destinations)\n\n"
    
    if selected:
        message_text += f"✅ Selected: {len(selected)} destination(s)\n\n"
    
    # Show top 15 chats only (no pagination)
    dialogs_to_show = dialogs[:15]
    
    for i, dialog in enumerate(dialogs_to_show, 1):
        # Add checkmark for selected items
        check = "✅ " if dialog['id'] in selected else ""
        # Add pin emoji for pinned chats
        pin_emoji = "📌 " if dialog.get('pinned') else ""
        # Truncate long names
        title = dialog['title']
        if len(title) > 25:
            title = title[:22] + "..."
        message_text += f"{i}. {check}{pin_emoji}{title}\n"
    
    # Add subscription limit warning
    if current_count + len(selected) >= max_limit and subscription_plan == 'free':
        message_text += f"\n❌ **Free plan limit:** {max_limit} destinations per rule\n"
        message_text += "💎 Upgrade to Premium for more destinations!\n"
    
    # Create buttons for first 15 chats
    buttons = []
    
    # First row: numbers 1-5 for current page
    row1 = []
    for i in range(1, 6):
        if i <= len(dialogs_to_show):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10 for current page
    row2 = []
    for i in range(6, 11):
        if i <= len(dialogs_to_show):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: numbers 11-15 (if available)
    row3 = []
    for i in range(11, 16):
        if i <= len(dialogs_to_show):
            row3.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row3.append(Button.inline(" ", data="none"))
    
    # Fourth row: Done button only (no navigation buttons)
    row4 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2]
    if row3:  # Only add third row if there are items
        buttons.append(row3)
    buttons.append(row4)
    
    # Add upgrade button if user is on free plan and near limit
    if subscription_plan == 'free' and current_count + len(selected) >= max_limit - 2:
        buttons.append([Button.inline("💎 Upgrade Plan", data="upgrade_subscription")])
    
    # Edit the message
    await event.edit(message_text, buttons=buttons)

async def update_rule_selection_message(event, state, rules, action):
    page = state.get('page', 0)
    items_per_page = 10
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(rules))
    page_rules = rules[start_idx:end_idx]
    
    if action == 'edit':
        title = "Select a rule to edit:"
    elif action == 'delete':
        title = "Select a rule to delete:"
    elif action == 'toggle':
        title = "Select a rule to toggle:"
    elif action == 'set_current':
        title = "Select a rule to configure:"
    else:
        title = "Select a rule:"
    
    message = f"📝 {title}\n\n"
    
    for i, rule in enumerate(page_rules, 1):
        if action == 'toggle':
            status = "✅ Active" if rule.get('active', False) else "❌ Inactive"
            message += f"{i}. {rule['title']} - {status}\n"
        else:
            message += f"{i}. {rule['title']}\n"
    
    # Create navigation buttons
    buttons = []
    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("⬅️ Previous", data="prev"))
    if end_idx < len(rules):
        nav_row.append(Button.inline("➡️ Next", data="next"))
    if nav_row:
        buttons.append(nav_row)
    
    # Create number buttons
    number_buttons = []
    for i in range(1, len(page_rules) + 1):
        if len(number_buttons) == 0 or len(number_buttons[-1]) >= 5:
            number_buttons.append([])
        number_buttons[-1].append(Button.inline(str(i), data=str(i)))
    
    buttons = number_buttons + buttons
    
    await event.edit(message, buttons=buttons)

@bot.on(events.NewMessage(pattern="/remove_source"))
async def remove_source_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "source removal"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get sources for the current rule
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    if not sources:
        await event.respond(f"❌ No sources found for rule '{rule_name}'. Use /source to add sources first.")
        return
    
    # Create a list of sources for selection
    sources_list = [{'id': source['chat_id'], 'title': source['title']} for source in sources]
    
    # Create inline buttons with numbers 1-10
    buttons = []
    row1 = []
    row2 = []
    
    # First row: numbers 1-5
    for i in range(1, 6):
        if i <= len(sources_list):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10
    for i in range(6, 11):
        if i <= len(sources_list):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: Done button only
    row3 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2, row3]
    
    # Create response message
    response = f"🗑️ Select sources to remove from rule '{rule_name}':\n\n"
    
    for i, source in enumerate(sources_list[:10], 1):  # Show first 10 only
        response += f"{i}. {source['title']}\n"
    
    if len(sources_list) > 10:
        response += f"\n... and {len(sources_list) - 10} more sources (use navigation if needed)"
    
    # Save state
    user_states[user_id] = {
        'mode': 'remove_source_selection',
        'items': sources_list,
        'page': 0,
        'selected': [],
        'current_rule': rule_id,
        'rule_name': rule_name
    }
    
    await event.respond(response, buttons=buttons)

@bot.on(events.NewMessage(pattern="/remove_destination"))
async def remove_destination_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "destination removal"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get destinations for the current rule
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    if not destinations:
        await event.respond(f"❌ No destinations found for rule '{rule_name}'. Use /destination to add destinations first.")
        return
    
    # Create a list of destinations for selection
    destinations_list = [{'id': dest['chat_id'], 'title': dest['title']} for dest in destinations]
    
    # Create inline buttons with numbers 1-10
    buttons = []
    row1 = []
    row2 = []
    
    # First row: numbers 1-5
    for i in range(1, 6):
        if i <= len(destinations_list):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10
    for i in range(6, 11):
        if i <= len(destinations_list):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: Done button only
    row3 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2, row3]
    
    # Create response message
    response = f"🗑️ Select destinations to remove from rule '{rule_name}':\n\n"
    
    for i, dest in enumerate(destinations_list[:10], 1):  # Show first 10 only
        response += f"{i}. {dest['title']}\n"
    
    if len(destinations_list) > 10:
        response += f"\n... and {len(destinations_list) - 10} more destinations (use navigation if needed)"
    
    # Save state
    user_states[user_id] = {
        'mode': 'remove_destination_selection',
        'items': destinations_list,
        'page': 0,
        'selected': [],
        'current_rule': rule_id,
        'rule_name': rule_name
    }
    
    await event.respond(response, buttons=buttons)

async def update_remove_selection_message(event, item_type):
    user_id = event.sender_id
    if user_id not in user_states:
        return
        
    state = user_states[user_id]
    items = state['items']
    page = state.get('page', 0)
    selected = state.get('selected', [])
    
    rule_name = state.get('rule_name', 'Default Rule')
    message_text = f"🗑️ Select {item_type} to remove from rule '{rule_name}':\n\n"
    
    if selected:
        message_text += f"✅ Selected: {len(selected)} {item_type}(s) to remove\n\n"
    
    # Show items per page
    items_per_page = 10
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(items))
    
    for i in range(start_idx, end_idx):
        item = items[i]
        # Add checkmark for selected items
        check = "✅ " if item['id'] in selected else ""
        # Truncate long names
        title = item['title']
        if len(title) > 25:
            title = title[:22] + "..."
        message_text += f"{i+1}. {check}{title}\n"
    
    # Create buttons
    buttons = []
    
    # First row: numbers 1-5 for current page
    row1 = []
    for i in range(1, 6):
        if start_idx + i <= len(items):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10 for current page
    row2 = []
    for i in range(6, 11):
        if start_idx + i <= len(items):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    buttons.append(row1)
    buttons.append(row2)
    
    # Add navigation buttons if needed
    nav_row = []
    if page > 0:
        nav_row.append(Button.inline("⬅️ Back", data="nav_prev"))
    if end_idx < len(items):
        nav_row.append(Button.inline("➡️ Next", data="nav_next"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Add done button
    buttons.append([Button.inline("✅ Remove Selected", data="done_sel")])
    
    # Edit the message
    await event.edit(message_text, buttons=buttons)

# ---------------- COMMANDS ----------------
@bot.on(events.NewMessage(pattern="/start$"))
async def start_cmd(event):
    await track_user_activity(event.sender_id)
    await event.respond(
        "👋 **Welcome to Advance Auto Message Forwarder Bot!** 🤖\n\n"
        "🚀 **Automate your message forwarding with advanced features:**\n\n"
        "✨ **What you can do:**\n"
        "• *Create multiple forwarding rules*\n"
        "• *Filter messages by keywords*\n"
        "• *Forward from channels, groups & private chats*\n"
        "• *Handle both media and text messages*\n"
        "• *Choose subscription plans that fit your needs*\n\n"
        "🎯 **Get started in 3 simple steps:**\n"
        "1. Use /login to connect your account\n"
        "2. Create your first rule with /add_rule\n"
        "3. Set up sources & destinations\n\n"
        "💡 **Pro Tip:** Start with /add_rule to create your first forwarding rule!\n\n"
        "Need help? Use /help for support information."
    )

@bot.on(events.NewMessage(pattern="/delay"))
async def delay_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "forwarding delay"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current delay
    current_delay = await get_forwarding_delay(user_id, rule_id)
    
    await event.respond(
        f"⏰ **Set Forwarding Delay for Rule: {rule_name}**\n\n"
        f"Current delay: {current_delay} seconds\n\n"
        "Send the delay in seconds (0-3600):\n"
        "• 0 = No delay (forward immediately)\n"
        "• 60 = 1 minute delay\n"
        "• 300 = 5 minutes delay\n"
        "• 1800 = 30 minutes delay\n\n"
        "Maximum delay: 3600 seconds (1 hour)\n\n"
        "Or send 'clear' to remove delay"
    )
    
    try:
        response = await wait_for_user_response(user_id, timeout=60)
        delay_text = response.raw_text.strip()
        
        if delay_text.lower() == 'clear':
            await set_forwarding_delay(user_id, rule_id, 0)
            await event.respond("✅ Delay cleared! Messages will be forwarded immediately.")
        else:
            try:
                delay_seconds = int(delay_text)
                if delay_seconds < 0 or delay_seconds > 3600:
                    await event.respond("❌ Delay must be between 0 and 3600 seconds (1 hour).")
                    return
                
                await set_forwarding_delay(user_id, rule_id, delay_seconds)
                
                if delay_seconds == 0:
                    await event.respond("✅ Delay set to 0 seconds. Messages will be forwarded immediately.")
                else:
                    minutes = delay_seconds // 60
                    seconds = delay_seconds % 60
                    time_str = f"{minutes} minute(s) {seconds} second(s)" if minutes > 0 else f"{delay_seconds} second(s)"
                    await event.respond(f"✅ Delay set to {time_str} for rule '{rule_name}'")
                    
            except ValueError:
                await event.respond("❌ Please enter a valid number (0-3600) or 'clear'.")
                
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /delay again.")
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled delay setting with a command")
            return
        raise

@bot.on(events.NewMessage(pattern="/whitelist_keywords"))
async def whitelist_keywords_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Cancel any ongoing operation
    await cancel_ongoing_operation(user_id)
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "whitelist keywords"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing whitelist keywords
    existing = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
        user_id, rule_id
    )
    
    existing_keywords = existing['keywords'] if existing else []
    
    await event.respond(
        f"📝 **Whitelist Keywords for Rule: {rule_name}**\n\n"
        f"Current keywords: {', '.join(existing_keywords) if existing_keywords else 'None'}\n\n"
        "Send keywords separated by commas (e.g., HELLO,WORLD,EXAMPLE):\n"
        "Or send 'clear' to remove all whitelist keywords\n\n"
        "**Note-** For Apply keywords Filter /stop_forwarding and /start_forwarding again"
    )
    
    try:
        response = await wait_for_user_response(user_id, timeout=60)
        keywords_text = response.raw_text.strip()
        
        if keywords_text.lower() == 'clear':
            await db.execute(
                "DELETE FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
                user_id, rule_id
            )
            await event.respond("✅ Whitelist keywords cleared!")
        else:
            keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
            
            if keywords:
                await db.execute("""
                    INSERT INTO keyword_filters (user_id, rule_id, type, keywords)
                    VALUES ($1, $2, 'whitelist', $3)
                    ON CONFLICT (user_id, rule_id, type) 
                    DO UPDATE SET keywords = $3
                """, user_id, rule_id, keywords)
                
                await event.respond(f"✅ Whitelist keywords set: {', '.join(keywords)}")
            else:
                await event.respond("❌ No valid keywords provided.")
                
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /whitelist_keywords again.")
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled whitelist keywords setting with a command")
            return
        raise

@bot.on(events.NewMessage(pattern="/blacklist_keywords"))
async def blacklist_keywords_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "blacklist_keywords"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing blacklist keywords
    existing = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
        user_id, rule_id
    )
    
    existing_keywords = existing['keywords'] if existing else []
    
    await event.respond(
        f"📝 **Blacklist Keywords for Rule: {rule_name}**\n\n"
        f"Current keywords: {', '.join(existing_keywords) if existing_keywords else 'None'}\n\n"
        "Send keywords separated by commas (e.g., SPAM,ADVERT,BLOCK):\n"
        "Or send 'clear' to remove all blacklist keywords\n\n"
        "**Note-** For Apply keywords Filter /stop_forwarding and /start_forwarding again"
    )
    
    try:
        response = await wait_for_user_response(user_id, timeout=60)
        keywords_text = response.raw_text.strip()
        
        if keywords_text.lower() == 'clear':
            await db.execute(
                "DELETE FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
                user_id, rule_id
            )
            await event.respond("✅ Blacklist keywords cleared!")
        else:
            keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
            
            if keywords:
                await db.execute("""
                    INSERT INTO keyword_filters (user_id, rule_id, type, keywords)
                    VALUES ($1, $2, 'blacklist', $3)
                    ON CONFLICT (user_id, rule_id, type) 
                    DO UPDATE SET keywords = $3
                """, user_id, rule_id, keywords)
                
                await event.respond(f"✅ Blacklist keywords set: {', '.join(keywords)}")
            else:
                await event.respond("❌ No valid keywords provided.")
                
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /blacklist_keywords again.")
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled blacklist keywords setting with a command")
            return
        raise

@bot.on(events.NewMessage(pattern="/debug_forwarding"))
async def debug_forwarding_cmd(event):
    user_id = event.sender_id
    
    response = f"🔍 **Forwarding Debug Info:**\n\n"
    response += f"User ID: {user_id}\n"
    response += f"User client loaded: {'✅' if user_id in user_clients else '❌'}\n"
    response += f"Forwarding task running: {'✅' if user_id in forwarding_tasks else '❌'}\n"
    
    if user_id in forwarding_tasks:
        task = forwarding_tasks[user_id]
        response += f"Task status: {task.done() if hasattr(task, 'done') else 'Unknown'}\n"
    
    # Check database configuration
    db = await get_db()
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
    response += f"Active rules: {len(rules)}\n"
    
    for rule in rules:
        sources = await db.fetch("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule['rule_id'])
        destinations = await db.fetch("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule['rule_id'])
        
        # Get keyword filters
        whitelist = await db.fetchrow(
            "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
            user_id, rule['rule_id']
        )
        blacklist = await db.fetchrow(
            "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
            user_id, rule['rule_id']
        )
        
        whitelist_count = len(whitelist['keywords']) if whitelist else 0
        blacklist_count = len(blacklist['keywords']) if blacklist else 0
        
        response += f"Rule '{rule['name']}': {sources[0]['count']} sources, {destinations[0]['count']} destinations\n"
        response += f"  Keywords: {whitelist_count} whitelist, {blacklist_count} blacklist\n"
    
    # Show last message IDs if available
    if user_id in last_message_ids:
        response += f"\n📋 Last message IDs: {last_message_ids[user_id]}\n"
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/debug_destinations"))
async def debug_destinations_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Get all destinations for this user
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
    
    response = "🔍 **Debug - Your Destinations:**\n\n"
    
    if not destinations:
        response += "❌ No destinations found!\n\n"
        response += "Make sure to:\n"
        response += "1. Use /destination to select destination chats\n"
        response += "2. Select chats from the list\n"
        response += "3. Click '✅ Done Selecting' when finished\n"
    else:
        for dest in destinations:
            username_info = f" (@{dest['username']})" if dest['username'] else ""
            response += f"📤 {dest['title']}{username_info} (ID: {dest['chat_id']}, Rule: {dest['rule_id']})\n"
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/debug_sources"))
async def debug_sources_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Get all sources for this user
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
    
    response = "🔍 **Debug - Your Sources:**\n\n"
    
    if not sources:
        response += "❌ No sources found!\n\n"
        response += "Make sure to:\n"
        response += "1. Use /source to select source chats\n"
        response += "2. Select chats from the list\n"
        response += "3. Click '✅ Done Selecting' when finished\n"
    else:
        for source in sources:
            response += f"📥 {source['title']} (ID: {source['chat_id']}, Rule: {source['rule_id']})\n"
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/test_chats"))
async def test_chats_cmd(event):
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Please /login first.")
        return

    try:
        dialogs = await get_user_dialogs(user_id)
        if not dialogs:
            await event.respond("❌ No chats found!")
            return
        
        response = "📋 **Available Chats:**\n\n"
        for i, dialog in enumerate(dialogs[:10], 1):  # Show first 10
            bot_info = " 🤖" if dialog.get('is_bot') else ""
            response += f"{i}. {dialog['title']}{bot_info} (ID: {dialog['id']})\n"
        
        if len(dialogs) > 10:
            response += f"\n... and {len(dialogs) - 10} more chats"
        
        await event.respond(response)
        
    except Exception as e:
        await event.respond(f"❌ Error: {e}")

@bot.on(events.NewMessage(pattern="/set_rule"))
async def set_rule_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "current rule selection"):
        return  # Stop command execution until user stops forwarding
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    if not rules:
        await event.respond("❌ No rules found. Use /add_rule to create a new rule first.")
        return
    
    # Create a list of rules for selection
    rules_list = [{'id': rule['rule_id'], 'title': rule['name']} for rule in rules]
    
    user_states[user_id] = {
        'mode': 'rule_selection',
        'rules': rules_list,
        'page': 0,
        'action': 'set_current'
    }
    
    keyboard, page_items = await create_numbered_keyboard(rules_list, page=0, include_done=False)
    response = "📝 Select a rule to configure:\n\n"
    
    for i, rule in enumerate(page_items, 1):
        response += f"{i}. {rule['title']}\n"
    
    response += "\n💡 This rule will be used for subsequent /source and /destination commands"
    
    await event.respond(response, buttons=keyboard)

@bot.on(events.NewMessage(pattern="/rules"))
async def rules_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    response = "📋 **Your Forwarding Rules:**\n\n"
    
    if not rules:
        response += "No rules created yet. Use /add_rule to create a new rule.\n\n"
    else:
        for rule in rules:
            status = "✅ Active" if rule['is_active'] else "❌ Inactive"
            response += f"📝 **{rule['name']}** ({rule['rule_id']}) - {status}\n"
            
            # Get sources and destinations for this rule
            sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule['rule_id'])
            destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule['rule_id'])
            
            # Get keyword filters
            whitelist = await db.fetchrow(
                "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
                user_id, rule['rule_id']
            )
            blacklist = await db.fetchrow(
                "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
                user_id, rule['rule_id']
            )
            
            whitelist_count = len(whitelist['keywords']) if whitelist else 0
            blacklist_count = len(blacklist['keywords']) if blacklist else 0
            
            response += f"   📥 Sources: {len(sources)}\n"
            response += f"   📤 Destinations: {len(destinations)}\n"
            response += f"   🔤 Keywords: {whitelist_count} whitelist, {blacklist_count} blacklist\n\n"
    
    # Get current rule
    current_rule_id, current_rule_name = await get_current_rule(user_id)
    response += f"🔧 **Current Rule:** {current_rule_name} ({current_rule_id})\n\n"
    
    response += "Available actions:\n"
    response += "/add_rule - Create a new rule\n"
    response += "/edit_rule - Edit an existing rule\n"
    response += "/delete_rule - Delete a rule\n"
    response += "/toggle_rule - Activate/deactivate a rule\n"
    response += "/set_rule - Set current rule for configuration\n"
    response += "/whitelist_keywords - Set whitelist keywords\n"
    response += "/blacklist_keywords - Set blacklist keywords\n"
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/add_rule"))
async def add_rule_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Cancel any ongoing operation
    await cancel_ongoing_operation(user_id)
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "rules"):
        return  # Stop command execution until user stops forwarding
    
    # Check subscription limit for rules
    subscription_plan = await get_user_subscription(user_id)
    max_rules = SUBSCRIPTION_LIMITS[subscription_plan]['max_rules']
    
    rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    
    if rules_count >= max_rules:
        if subscription_plan == 'free':
            await event.respond(
                f"❌ You've reached the limit of {max_rules} rules on the free plan.\n\n"
                f"💎 Upgrade to Premium for unlimited rules!",
                buttons=[[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
            )
            return
        else:
            await event.respond(
                f"❌ You've reached the limit of {max_rules} rules on your {subscription_plan} plan.\n\n"
                "Please contact support for enterprise options."
            )
            return
    
    # Show subscription info
    subscription_info = f"📋 **Your Plan:** {subscription_plan.upper()} ({rules_count}/{max_rules} rules used)"
    
    await event.respond(
        f"{subscription_info}\n\n"
        "📝 Creating a new rule\n\nPlease send a name for this rule:"
    )
    
    try:
        name_msg = await wait_for_user_response(user_id, timeout=60)
        rule_name = name_msg.raw_text.strip()
        
        if not rule_name:
            await event.respond("❌ Rule name cannot be empty.")
            return
        
        # Check if rule name already exists
        existing_rule = await db.fetchrow(
            "SELECT * FROM rules WHERE user_id=$1 AND name=$2", 
            user_id, rule_name
        )
        
        if existing_rule:
            await event.respond("❌ A rule with this name already exists. Please choose a different name.")
            return
        
        # Generate a rule ID
        rule_id = f"rule_{int(asyncio.get_event_loop().time())}"
        
        # Save the rule to database
        await db.execute("""
            INSERT INTO rules (user_id, rule_id, name, is_active)
            VALUES ($1, $2, $3, $4)
        """, user_id, rule_id, rule_name, True)

        # Set this as the current rule in database (permanent)
        await db.execute("""
            UPDATE users SET current_rule=$1 WHERE id=$2
        """, rule_id, user_id)

        # Also set in user state (temporary)
        user_states[user_id] = {
            'current_rule': rule_id,
            'rule_name': rule_name
        }
        
        # Update rules count
        rules_count += 1
        
        # Create success message with subscription info
        success_message = (
            f"✅ Rule '{rule_name}' created successfully!\n\n"
            f"📊 **Subscription Status:** {subscription_plan.upper()} ({rules_count}/{max_rules} rules)\n\n"
            f"🔧 **This rule is now set as your current rule**\n\n"
        )
        
        if subscription_plan == 'free' and rules_count >= max_rules - 1:
            success_message += (
                "⚠️ **You're approaching your free plan limit!**\n"
                f"Only {max_rules - rules_count} rule(s) remaining.\n\n"
                "💎 Upgrade to Premium for unlimited rules!\n\n"
            )
        
        success_message += (
            "Now you can set sources and destinations for this rule using:\n"
            "/source - Set sources\n"
            "/destination - Set destinations"
        )
        
        # Add upgrade button if user is on free plan and near limit
        if subscription_plan == 'free' and rules_count >= max_rules - 1:
            buttons = [[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
            await event.respond(success_message, buttons=buttons)
        else:
            await event.respond(success_message)
        
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /add_rule again.")
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            # User sent a command instead of rule name, just return
            logger.info(f"User {user_id} cancelled rule creation with a command")
            return
        # Re-raise other ValueErrors
        raise

@bot.on(events.NewMessage(pattern="/edit_rule"))
async def edit_rule_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "rule settings "):
        return  # Stop command execution until user stops forwarding
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    if not rules:
        await event.respond("❌ No rules found. Use /add_rule to create a new rule.")
        return
    
    # Create a list of rules for selection
    rules_list = [{'id': rule['rule_id'], 'title': rule['name']} for rule in rules]
    
    user_states[user_id] = {
        'mode': 'rule_selection',
        'rules': rules_list,
        'page': 0,
        'action': 'edit'
    }
    
    keyboard, page_items = await create_numbered_keyboard(rules_list, page=0, include_done=False)
    response = "📝 Select a rule to edit:\n\n"
    
    for i, rule in enumerate(page_items, 1):
        response += f"{i}. {rule['title']}\n"
    
    await event.respond(response, buttons=keyboard)

@bot.on(events.NewMessage(pattern="/delete_rule"))
async def delete_rule_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "rule deletion"):
        return  # Stop command execution until user stops forwarding
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    if not rules:
        await event.respond("❌ No rules found. Use /add_rule to create a new rule.")
        return
    
    # Create a list of rules for selection
    rules_list = [{'id': rule['rule_id'], 'title': rule['name']} for rule in rules]
    
    user_states[user_id] = {
        'mode': 'rule_selection',
        'rules': rules_list,
        'page': 0,
        'action': 'delete'
    }
    
    keyboard, page_items = await create_numbered_keyboard(rules_list, page=0, include_done=False)
    response = "🗑️ Select a rule to delete:\n\n"
    
    for i, rule in enumerate(page_items, 1):
        response += f"{i}. {rule['title']}\n"
    
    await event.respond(response, buttons=keyboard)

@bot.on(events.NewMessage(pattern="/toggle_rule"))
async def toggle_rule_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "rule activation status"):
        return  # Stop command execution until user stops forwarding
    
    # Get all rules for the user
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    if not rules:
        await event.respond("❌ No rules found. Use /add_rule to create a new rule.")
        return
    
    # Create a list of rules for selection
    rules_list = [{'id': rule['rule_id'], 'title': rule['name'], 'active': rule['is_active']} for rule in rules]
    
    user_states[user_id] = {
        'mode': 'rule_selection',
        'rules': rules_list,
        'page': 0,
        'action': 'toggle'
    }
    
    keyboard, page_items = await create_numbered_keyboard(rules_list, page=0, include_done=False)
    response = "🔧 Select a rule to toggle (activate/deactivate):\n\n"
    
    for i, rule in enumerate(page_items, 1):
        status = "✅ Active" if rule['active'] else "❌ Inactive"
        response += f"{i}. {rule['title']} - {status}\n"
    
    await event.respond(response, buttons=keyboard)

@bot.on(events.NewMessage(pattern="/login"))
async def login_cmd(event):
    await track_user_activity(event.sender_id)
    user_id = event.sender_id
    db = await get_db()
    
    # Cancel any ongoing operation
    await cancel_ongoing_operation(user_id)

    # Check if user is already logged in
    client = await get_user_client(user_id)
    if client:
        try:
            # Verify the client is still authorized
            if await client.is_user_authorized():
                # Get user info for the message
                me = await client.get_me()
                username = f"@{me.username}" if me.username else "No username"
                account_name = me.first_name or ""
                if me.last_name:
                    account_name = f"{account_name} {me.last_name}".strip()
                account_name = account_name or "No name"
                
                await event.respond(
                    f"✅ **You are already logged in!**\n\n"
                    f"👤 **Logged as:** {account_name}\n"
                    f"📧 **Username:** {username}\n\n"
                )
                return
        except Exception as e:
            logger.warning(f"Existing client check failed for user {user_id}: {e}")
            # If check fails, continue with normal login process
            pass
    
    await track_user_activity(event.sender_id)
    db = await get_db()

    await event.respond(
        "📱**Enter Your Phone Number**\n\n"
        "Please send your phone number in international format:\n\n"
        "**Examples:**\n"
        "• `+919876543210` (India)\n"
        "• `+1234567890` (US/Canada)\n"
        "• `+441234567890` (UK)\n\n"
        "⚠️ **Important:**\n"
        "• Include country code with `+` sign\n"
        "• No spaces or special characters\n"
        "• Use the number linked to your Telegram account\n\n"
    )
    
    try:
        phone_msg = await wait_for_user_response(user_id, timeout=60, operation_mode="login_phone")
        phone = phone_msg.raw_text.strip()
        
        # Basic phone number validation
        if not phone.startswith('+'):
            await event.respond("❌ **Invalid phone number format!** Please include the country code with `+` sign (e.g., `+919876543210`).\n\nPlease try /login again.")
            return
            
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /login again.")
        return
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled phone number input with a command")
            return
        raise

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        # Add waiting message after entering mobile number
        waiting_msg = await event.respond("📨 Sending OTP... Please wait")
        
        await client.send_code_request(phone)
        
        # Edit the waiting message to show OTP sent
        await waiting_msg.edit(
            "🔑 **OTP Sent** to your Telegram account.\n\n"
            "Please enter your OTP in this format:\n"
            "`HELLO12345`\n\n"
            "If your OTP is `12345`, type it as `HELLO12345`."
        )
        
        try:
            otp_msg = await wait_for_user_response(user_id, timeout=60, operation_mode="login_otp")
            otp = otp_msg.raw_text.strip()
            
            # Remove the "HELLO" prefix if user included it
            if otp.upper().startswith("HELLO"):
                otp = otp[5:]  # Remove "HELLO" prefix
            
            await client.sign_in(phone=phone, code=otp)
            
        except asyncio.TimeoutError:
            await event.respond("❌ OTP timeout. Please try /login again.")
            await client.disconnect()
            return
        except ValueError as e:
            if str(e) == "COMMAND_DETECTED":
                logger.info(f"User {user_id} cancelled OTP input with a command")
                await client.disconnect()
                return
            raise
        except PhoneCodeInvalidError:
            await event.respond("❌ **Invalid OTP!** The code you entered is incorrect.\n\nPlease try /login again with the correct OTP.")
            await client.disconnect()
            return
        except PhoneCodeExpiredError:
            await event.respond("❌ **OTP expired!** The code has expired.\n\nPlease try /login again to get a new OTP.")
            await client.disconnect()
            return

    except SessionPasswordNeededError:
        await event.respond("🔒 2FA password enabled. Send your password:")
        
        try:
            pwd_msg = await wait_for_user_response(user_id, timeout=60, operation_mode="login_password")
            pwd = pwd_msg.raw_text.strip()
            await client.sign_in(password=pwd)
        except asyncio.TimeoutError:
            await event.respond("❌ Password timeout. Please try /login again.")
            await client.disconnect()
            return
        except ValueError as e:
            if str(e) == "COMMAND_DETECTED":
                logger.info(f"User {user_id} cancelled password input with a command")
                await client.disconnect()
                return
            raise
        except PasswordHashInvalidError:
            await event.respond("❌ **Invalid password!** The 2FA password you entered is incorrect.\n\nPlease try /login again.")
            await client.disconnect()
            return
            
    except PhoneNumberInvalidError:
        await event.respond("❌ **Invalid phone number!** The phone number you entered is not valid.\n\nPlease check the number and try /login again with the correct format (e.g., `+919876543210`).")
        await client.disconnect()
        return
    except PhoneNumberBannedError:
        await event.respond("❌ **Phone number banned!** This phone number has been banned by Telegram.\n\nPlease use a different phone number.")
        await client.disconnect()
        return
    except PhoneNumberFloodError:
        await event.respond("❌ **Too many attempts!** This phone number has been temporarily blocked due to too many login attempts.\n\nPlease wait for some time before trying again.")
        await client.disconnect()
        return
    except PhoneNumberUnoccupiedError:
        await event.respond("❌ **Phone number not registered!** This phone number is not registered on Telegram.\n\nPlease check the number or use a different phone number.")
        await client.disconnect()
        return
    except Exception as e:
        await event.respond(f"❌ Error during login: {str(e)}\n\nPlease try /login again.")
        await client.disconnect()
        return

    # Save session
    session_str = client.session.save()
    await db.execute("""
        INSERT INTO users (id, phone, session)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO UPDATE SET session=$3
    """, user_id, phone, session_str)

    user_clients[user_id] = client
    
    # Get user info for success message
    try:
        me = await client.get_me()
        username = f"@{me.username}" if me.username else "No username"
        # Get account name (first name + last name if available)
        account_name = me.first_name or ""
        if me.last_name:
            account_name = f"{account_name} {me.last_name}".strip()
        account_name = account_name or "No name"
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        username = "Unknown"
        account_name = "Unknown"
    
    await event.respond(
        f"✅ **Login successful!**\n\n"
        f"👤 **Logged as:** {account_name}\n"
        f"📧 **Username:** {username}\n\n"
        "Before adding Source and Destination channels,\n"
        "you must add a Rule using /add_rule"
    )
    
@bot.on(events.NewMessage(pattern="/logout"))
async def logout_cmd(event):
    user_id = event.sender_id
    
    if user_id in user_clients:
        await user_clients[user_id].disconnect()
        del user_clients[user_id]
    
    if user_id in forwarding_tasks:
        forwarding_tasks[user_id].cancel()
        del forwarding_tasks[user_id]
    
    db = await get_db()
    await db.execute("DELETE FROM users WHERE id=$1", user_id)
    await db.execute("DELETE FROM sources WHERE user_id=$1", user_id)
    await db.execute("DELETE FROM destinations WHERE user_id=$1", user_id)
    await db.execute("DELETE FROM rules WHERE user_id=$1", user_id)
    await db.execute("DELETE FROM keyword_filters WHERE user_id=$1", user_id)
    
    user_states.pop(user_id, None)
    last_message_ids.pop(user_id, None)
    
    await event.respond("✅ Logged out successfully. All data has been removed.")

@bot.on(events.NewMessage(pattern="/source"))
async def source_cmd(event):
    await track_user_activity(event.sender_id)
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Please /login first.")
        return
        
     # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "sources"):
        return  # Stop command execution until user stops forwarding   

    try:
        # Get current rule
        rule_id, rule_name = await get_current_rule(user_id)
        
        # Check subscription limit for sources
        subscription_plan = await get_user_subscription(user_id)
        max_sources = SUBSCRIPTION_LIMITS[subscription_plan]['max_sources_per_rule']  # ✅ Get the correct limit
        
        db = await get_db()
        current_sources_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        
        # Check if user has reached the limit
        if current_sources_count >= max_sources and subscription_plan == 'free':
            await event.respond(
                f"❌ You've reached the limit of {max_sources} sources per rule on the free plan.\n\n"
                f"💎 Upgrade to Premium for more sources!",
                buttons=[[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
            )
            return
        
        # First show instructional message with button
        instructional_message = (
            "** To add a source, tap the “I Have Pinned Chats” button.**\n" 
            "**Follow These Steps to Set Source Channels**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "1. Go to the Chats From Which You Want to Copy Messages.\n"
            "2. Press and Hold the Source Channel.\n"
            "3. Tap on the Pin Icon to Pin it At the Top.\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ **Note:** Make Sure You Have Admin or Forward enabled in Channel/Group."
        )
        
        buttons = [[Button.inline("✅ I have pinned chats", data="show_source_chats")]]
        
        # Store state for callback
        user_states[user_id] = {
            'mode': 'source_instruction',
            'rule_id': rule_id,
            'rule_name': rule_name,
            'current_count': current_sources_count,
            'max_limit': max_sources
        }
        
        # Send instructional message
        await event.respond(instructional_message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error in source command: {e}")
        await event.respond("❌ Error loading your chats. Please try again.")

@bot.on(events.NewMessage(pattern="/destination"))
async def destination_cmd(event):
    await track_user_activity(event.sender_id)
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Please /login first.")
        return

    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "destinations"):
        return  # Stop command execution until user stops forwarding

    try:
        # Get current rule
        rule_id, rule_name = await get_current_rule(user_id)
        
        # Check subscription limit for destinations
        subscription_plan = await get_user_subscription(user_id)
        max_destinations = SUBSCRIPTION_LIMITS[subscription_plan]['max_destinations_per_rule']
        
        db = await get_db()
        current_destinations_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        
        # Check if user has reached the limit
        if current_destinations_count >= max_destinations and subscription_plan == 'free':
            await event.respond(
                f"❌ You've reached the limit of {max_destinations} destinations per rule on the free plan.\n\n"
                f"💎 Upgrade to Premium for more destinations!",
                buttons=[[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
            )
            return
        
        # First show instructional message with button
        instructional_message = (
            "**To add a Destination, tap the “I Have Pinned Chats” button.**\n"
            "**Follow These Steps to Set Target Channels**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "1. Go to the Chats From Which You Want to Copy Messages.\n"
            "2. Press and Hold the Destination Channel.\n"
            "3. Tap on the Pin Icon to Pin it At the Top.\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ **Note:** Make Sure You Have Admin or Send Message Permission In Destination Channel/Group."
        )
        
        buttons = [[Button.inline("✅ I have pinned chats", data="show_destination_chats")]]
        
        # Store state for callback
        user_states[user_id] = {
            'mode': 'destination_instruction',
            'rule_id': rule_id,
            'rule_name': rule_name,
            'current_count': current_destinations_count,
            'max_limit': max_destinations
        }
        
        # Send instructional message
        await event.respond(instructional_message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error in destination command: {e}")
        await event.respond("❌ Error loading your chats. Please try again.")

@bot.on(events.CallbackQuery(pattern=b"show_source_chats"))
async def show_source_chats_callback(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'source_instruction':
        await event.answer("Session expired. Please use /source again.")
        return
    
    state = user_states[user_id]
    rule_id = state['rule_id']
    rule_name = state['rule_name']
    current_sources_count = state['current_count']
    max_sources = state['max_limit']
    
    # Get user client
    client = await get_user_client(user_id)
    if not client:
        await event.answer("❌ Please /login first.", alert=True)
        return
    
    # Get user's dialogs (pinned chats will appear first)
    dialogs = await get_user_dialogs(user_id)
    if not dialogs:
        await event.edit("❌ No chats found. Please join some channels/groups first.")
        return
    
    # Create the selection message
    rule_info = f" for rule '{rule_name}'" if rule_id != 'default' else ''
    message_text = f"**Select sources to copy from{rule_info}:**\n\n"
    
    # Add subscription info
    subscription_plan = await get_user_subscription(user_id)
    message_text += f"📊 **Subscription:** {subscription_plan.upper()} ({current_sources_count}/{max_sources} sources)\n\n"
    
    if current_sources_count >= max_sources and subscription_plan == 'free':
        message_text += "❌ **You've reached the free plan limit!**\n"
        message_text += "💎 Upgrade to Premium for more sources!\n\n"
    
    # Show top 15 dialogs (pinned ones will appear first)
    for i, dialog in enumerate(dialogs[:15], 1):
        # Add pin emoji for pinned chats
        pin_emoji = "📌 " if dialog.get('pinned') else ""
        # Truncate long names if needed
        title = dialog['title']
        if len(title) > 25:
            title = title[:22] + "..."
        message_text += f"{i}. {pin_emoji}{title}\n"
    
    # Create buttons for first 15 chats
    buttons = []
    
    # First row: numbers 1-5
    row1 = []
    for i in range(1, 6):
        if i <= 15 and i <= len(dialogs):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10
    row2 = []
    for i in range(6, 11):
        if i <= 15 and i <= len(dialogs):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: numbers 11-15 (if available)
    row3 = []
    for i in range(11, 16):
        if i <= 15 and i <= len(dialogs):
            row3.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row3.append(Button.inline(" ", data="none"))
    
    # Fourth row: Done button only (no navigation buttons)
    row4 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2]
    if any(btn.text != " " for btn in row3):  # Only add third row if there are actual buttons
        buttons.append(row3)
    buttons.append(row4)
    
    # Add upgrade button if user is on free plan and near limit
    if subscription_plan == 'free' and current_sources_count >= max_sources - 2:
        buttons.append([Button.inline("💎 Upgrade Plan", data="upgrade_subscription")])
    
    # Update state for callback handling
    user_states[user_id] = {
        'mode': 'source_selection',
        'dialogs': dialogs,
        'selected': [],
        'page': 0,
        'current_rule': rule_id,
        'rule_name': rule_name,
        'current_count': current_sources_count,
        'max_limit': max_sources
    }
    
    # Edit the message to show chat selection
    await event.edit(message_text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"show_destination_chats"))
async def show_destination_chats_callback(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'destination_instruction':
        await event.answer("Session expired. Please use /destination again.")
        return
    
    state = user_states[user_id]
    rule_id = state['rule_id']
    rule_name = state['rule_name']
    current_destinations_count = state['current_count']
    max_destinations = state['max_limit']
    
    # Get user client
    client = await get_user_client(user_id)
    if not client:
        await event.answer("❌ Please /login first.", alert=True)
        return
    
    # Get user's dialogs (pinned chats will appear first)
    dialogs = await get_user_dialogs(user_id)
    if not dialogs:
        await event.edit("❌ No chats found. Please join some channels/groups first.")
        return
    
    # Create the selection message
    rule_info = f" for rule '{rule_name}'" if rule_id != 'default' else ''
    message_text = f"**Select destinations to forward to{rule_info}:**\n\n"
    
    # Add subscription info
    subscription_plan = await get_user_subscription(user_id)
    message_text += f"📊 **Subscription:** {subscription_plan.upper()} ({current_destinations_count}/{max_destinations} destinations)\n\n"
    
    if current_destinations_count >= max_destinations and subscription_plan == 'free':
        message_text += "❌ **You've reached the free plan limit!**\n"
        message_text += "💎 Upgrade to Premium for more destinations!\n\n"
    
    # Show top 15 dialogs (pinned ones will appear first)
    for i, dialog in enumerate(dialogs[:15], 1):
        # Add pin emoji for pinned chats
        pin_emoji = "📌 " if dialog.get('pinned') else ""
        # Truncate long names if needed
        title = dialog['title']
        if len(title) > 25:
            title = title[:22] + "..."
        message_text += f"{i}. {pin_emoji}{title}\n"
    
    # Create buttons for first 15 chats
    buttons = []
    
    # First row: numbers 1-5
    row1 = []
    for i in range(1, 6):
        if i <= 15 and i <= len(dialogs):
            row1.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row1.append(Button.inline(" ", data="none"))
    
    # Second row: numbers 6-10
    row2 = []
    for i in range(6, 11):
        if i <= 15 and i <= len(dialogs):
            row2.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row2.append(Button.inline(" ", data="none"))
    
    # Third row: numbers 11-15 (if available)
    row3 = []
    for i in range(11, 16):
        if i <= 15 and i <= len(dialogs):
            row3.append(Button.inline(str(i), data=f"sel_{i}"))
        else:
            row3.append(Button.inline(" ", data="none"))
    
    # Fourth row: Done button only (no navigation buttons)
    row4 = [Button.inline("✅ Done", data="done_sel")]
    
    buttons = [row1, row2]
    if any(btn.text != " " for btn in row3):  # Only add third row if there are actual buttons
        buttons.append(row3)
    buttons.append(row4)
    
    # Add upgrade button if user is on free plan and near limit
    if subscription_plan == 'free' and current_destinations_count >= max_destinations - 2:
        buttons.append([Button.inline("💎 Upgrade Plan", data="upgrade_subscription")])
    
    # Update state for callback handling
    user_states[user_id] = {
        'mode': 'destination_selection',
        'dialogs': dialogs,
        'selected': [],
        'page': 0,
        'current_rule': rule_id,
        'rule_name': rule_name,
        'current_count': current_destinations_count,
        'max_limit': max_destinations
    }
    
    # Edit the message to show chat selection
    await event.edit(message_text, buttons=buttons)

@bot.on(events.NewMessage(pattern="/add_bot"))
async def add_bot_cmd(event):
    user_id = event.sender_id
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Please /login first.")
        return
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get the bot chat entity
    bot_chat = await get_bot_chat(client, BOT_USERNAME)
    if not bot_chat:
        await event.respond("❌ Could not find the bot. Make sure you've started a chat with the bot.")
        return
    
    db = await get_db()
    
    # Add to sources
    await db.execute("""
        INSERT INTO sources (user_id, chat_id, title, rule_id)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, chat_id, rule_id) DO NOTHING
    """, user_id, bot_chat['id'], f"🤖 {bot_chat['title']}", rule_id)
    
    # Add to destinations (with username)
    await db.execute("""
        INSERT INTO destinations (user_id, chat_id, title, username, rule_id)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, chat_id, rule_id) DO NOTHING
    """, user_id, bot_chat['id'], f"🤖 {bot_chat['title']}", bot_chat['username'], rule_id)
    
    await event.respond(f"✅ Added {BOT_USERNAME} to both sources and destinations for rule: {rule_name}")

@bot.on(events.NewMessage(pattern="/config"))
async def config_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Get user info
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row:
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # Get all rules
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY rule_id", user_id)
    
    if not rules:
        await event.respond("❌ No rules configured yet. Use /add_rule to create one.")
        return
    
    # Show first rule by default
    await show_rule_config(event, rules, 0)

async def show_rule_config(event, rules, current_index):
    """Show configuration for a specific rule with all settings"""
    user_id = event.sender_id
    db = await get_db()
    
    rule = rules[current_index]
    rule_id = rule['rule_id']
    rule_name = rule['name']
    
    # Get the user's username from their Telegram account
    client = await get_user_client(user_id)
    username = "Unknown"
    if client:
        try:
            me = await client.get_me()
            username = f"@{me.username}" if me.username else "No username"
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
    
    # Build response for this specific rule
    response = f"⚙️ **Configuration - Rule {current_index + 1}/{len(rules)}**\n\n"
    response += f"👤 **Logged as:** {username}\n"
    response += f"📝 **Rule:** {rule_name} ({rule_id})\n"
    response += f"🔧 **Status:** {'✅ Active' if rule['is_active'] else '❌ Inactive'}\n\n"
    
    # Get sources and destinations for this rule
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    # Get keyword filters
    whitelist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
        user_id, rule_id
    )
    blacklist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
        user_id, rule_id
    )
    
    # Get delay
    delay = await get_forwarding_delay(user_id, rule_id)
    
    # Get options for this specific rule
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse rule options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
  
    # --- SOURCES & DESTINATIONS ---
    response += "📋 **Sources & Destinations**\n"
    response += "────────────────\n"
    
    # Show first few sources and destinations
    if sources:
        response += "**📤 Sources:**\n"
        for i, source in enumerate(sources[:100]):
            response += f"  {i+1}. {source['title']}\n"
        
    if destinations:
        response += "\n**📥 Destinations:**\n"
        for i, dest in enumerate(destinations[:100]):
            response += f"  {i+1}. {dest['title']}\n\n"
  
    # --- BASIC SETTINGS ---
    response += "🔧 **Basic Settings**\n"
    response += "────────────────\n"
    
    # Forwarding mode
    forward_media_only = options.get('forward_media_only', False)
    forward_text_only = options.get('forward_text_only', False)
    
    if forward_media_only:
        option_setting = "📷 Forward media only"
    elif forward_text_only:
        option_setting = "📝 Forward text only"
    else:
        option_setting = "📬 Forward all messages"
    
    response += f"• **Forwarding Mode:** {option_setting}\n"
    
    # Delay
    response += f"• **Delay:** {delay} seconds\n"
    
    # URL Preview
    url_preview_enabled = options.get('url_preview', True)
    response += f"• **URL Preview:** {'✅ Enabled' if url_preview_enabled else '❌ Disabled'}\n\n"
        
    # --- KEYWORD FILTERS ---
    response += "🔤 **Keyword Filters**\n"
    response += "────────────────\n"
    
    whitelist_keywords = whitelist['keywords'] if whitelist else []
    blacklist_keywords = blacklist['keywords'] if blacklist else []
    
    response += f"• **Whitelist:** {len(whitelist_keywords)} keywords\n"
    
    # Show sample keywords
    if whitelist_keywords:
        response += f" {', '.join(whitelist_keywords[:3])}"
        if len(whitelist_keywords) > 3:
            response += f" ..."
        response += "\n\n"
    
    response += f"• **Blacklist:** {len(blacklist_keywords)} keywords\n"
     
    if blacklist_keywords:
        response += f" {', '.join(blacklist_keywords[:3])}"
        if len(blacklist_keywords) > 3:
            response += f" ..."
        response += "\n"
    response += "\n"
    
    # --- PREMIUM FEATURES ---
    subscription_plan = await get_user_subscription(user_id)
    response += f"💎 **Premium Features** ({subscription_plan.upper()})\n"
    response += "────────────────\n"
    
    # Remove Links
    remove_links_enabled = options.get('remove_links', False)
    remove_links_status = "✅ Enabled" if remove_links_enabled else "❌ Disabled"
    if subscription_plan == 'free' and remove_links_enabled:
        remove_links_status = "🔄 (Will be disabled - Free plan)"
    response += f"• **Remove Links:** {remove_links_status}\n"
    
    # Text Replacements
    text_replacements = options.get('text_replacements', {})
    active_text_replacements = len([k for k, v in text_replacements.items() if v])
    text_replace_status = f"✅ {active_text_replacements} active" if active_text_replacements > 0 else "❌ Disabled"
    if subscription_plan == 'free' and active_text_replacements > 0:
        text_replace_status = "🔄 (Will be disabled - Free plan)"
    response += f"• **Text Replacements:** {text_replace_status}\n"
    
    # Replace All Text
    replace_all_text = options.get('replace_all_text', {'enabled': False})
    replace_all_status = "✅ Enabled" if replace_all_text.get('enabled') else "❌ Disabled"
    if subscription_plan == 'free' and replace_all_text.get('enabled'):
        replace_all_status = "🔄 (Will be disabled - Free plan)"
    response += f"• **Replace All Text:** {replace_all_status}\n"
    
    if replace_all_text.get('enabled'):
        replacement_text = replace_all_text.get('replacement', '')
        if replacement_text:
            display_text = replacement_text[:30] + "..." if len(replacement_text) > 30 else replacement_text
            response += f"  Replacement: `{display_text}`\n"
    
    # Channel Converter
    channel_converter = options.get('channel_converter', {'enabled': False})
    channel_convert_status = "✅ Enabled" if channel_converter.get('enabled') else "❌ Disabled"
    response += f"• **Channel Converter:** {channel_convert_status}\n"
    
    if channel_converter.get('enabled') and channel_converter.get('my_channel'):
        response += f"  Target: `{channel_converter['my_channel']}`\n"
    
    # Link Replacements
    link_replacements = options.get('link_replacements', {})
    active_link_replacements = len([k for k, v in link_replacements.items() if v])
    link_replace_status = f"✅ {active_link_replacements} active" if active_link_replacements > 0 else "❌ Disabled"
    response += f"• **Link Replacements:** {link_replace_status}\n"
    
    # Show sample link replacements
    if active_link_replacements > 0:
        sample_count = min(2, active_link_replacements)
        sample_items = list(link_replacements.items())[:sample_count]
        for original, replacement in sample_items:
            display_original = original[:15] + "..." if len(original) > 15 else original
            display_replacement = replacement[:15] + "..." if len(replacement) > 15 else replacement
            response += f"  `{display_original}` → `{display_replacement}`\n"
        if active_link_replacements > sample_count:
            response += f"  ... and {active_link_replacements - sample_count} more\n"
    
    response += "\n"
    
     # Get current rule
    current_rule_id, current_rule_name = await get_current_rule(user_id)
    response += f"🔧 **Current Rule**: {current_rule_name} ({current_rule_id})\n\n"
    
    response += "🔄 **Forwarding status**: "
    if user_id in forwarding_tasks:
        task = forwarding_tasks[user_id]
        if task.done():
            response += "❌ Stopped (task completed)\n"
        else:
            response += "✅ Running\n"
    else:
        response += "❌ Not started\n"
        
    # Create navigation buttons
    buttons = []
    
    # Rule name quick navigation buttons (max 3 per row)
    rule_buttons = []
    for i, rule_item in enumerate(rules):
        # Truncate long rule names
        display_name = rule_item['name']
        if len(display_name) > 12:
            display_name = display_name[:10] + "..."
        
        # Add emoji for current rule and status
        prefix = "📍" if i == current_index else "📝"
        status_emoji = "✅" if rule_item['is_active'] else "❌"
        button_text = f"{prefix}{status_emoji} {display_name}"
        
        rule_buttons.append(Button.inline(button_text, data=f"config_rule_{i}"))
        
        # Start new row after every 3 buttons
        if len(rule_buttons) == 3:
            buttons.append(rule_buttons)
            rule_buttons = []
    
    # Add remaining rule buttons if any
    if rule_buttons:
        buttons.append(rule_buttons)
    
    # Navigation row
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(Button.inline("⬅️ Previous", data=f"config_prev_{current_index}"))
    
    nav_buttons.append(Button.inline(f"📊 {current_index + 1}/{len(rules)}", data="config_current"))
    
    if current_index < len(rules) - 1:
        nav_buttons.append(Button.inline("Next ➡️", data=f"config_next_{current_index}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)

    
    # Close button
    buttons.append([Button.inline("❌ Close", data="config_close")])
    
    # Check if this is an edit or new message
    if hasattr(event, 'data') and event.data:
        await event.edit(response, buttons=buttons)
    else:
        # Store the current state for callback handling
        user_states[user_id] = {
            'mode': 'config_view',
            'rules': rules,
            'current_index': current_index
        }
        await event.respond(response, buttons=buttons)

# Add new callback handlers for feature management
@bot.on(events.CallbackQuery(pattern=b"config_"))
async def config_callback_handler(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'config_view':
        await event.answer("Session expired. Please use /config again.")
        return
    
    state = user_states[user_id]
    rules = state['rules']
    current_index = state['current_index']
    
    if data.startswith("config_prev_"):
        # Go to previous rule
        new_index = int(data.split("_")[2]) - 1
        if new_index >= 0:
            state['current_index'] = new_index
            await show_rule_config(event, rules, new_index)
        else:
            await event.answer("This is the first rule.")
    
    elif data.startswith("config_next_"):
        # Go to next rule
        new_index = int(data.split("_")[2]) + 1
        if new_index < len(rules):
            state['current_index'] = new_index
            await show_rule_config(event, rules, new_index)
        else:
            await event.answer("This is the last rule.")
    
    elif data.startswith("config_rule_"):
        # Jump to specific rule by index
        rule_index = int(data.split("_")[2])
        if 0 <= rule_index < len(rules):
            state['current_index'] = rule_index
            await show_rule_config(event, rules, rule_index)
        else:
            await event.answer("Invalid rule selection.")
    
    elif data == "config_close":
        await event.delete()
        if user_id in user_states:
            del user_states[user_id]
    
    # Handle management callbacks (from previous implementation)
    elif data.startswith("manage_") or data.startswith("confirm_delete_"):
        await handle_management_callbacks(event, data, rules, state)
    
    await event.answer()

@bot.on(events.NewMessage(pattern="/set_options"))
async def set_options_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "forwarding options"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options for this rule
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse current options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    await event.respond(
        f"⚙️ **Setting Options for Rule: {rule_name}**\n\n"
        "Available Options:\n\n"
        "1. Forward media only\n"
        "2. Forward text only\n"
        "3. Forward all messages\n\n"
        "Please select an option (1-3):"
    )
    
    try:
        response = await wait_for_user_response(user_id, timeout=60)
        choice = response.raw_text.strip()
        
        if choice == "1":
            options['forward_media_only'] = True
            options['forward_text_only'] = False
            message = f"✅ Rule '{rule_name}' set to forward media only"
        elif choice == "2":
            options['forward_media_only'] = False
            options['forward_text_only'] = True
            message = f"✅ Rule '{rule_name}' set to forward text only"
        elif choice == "3":
            options['forward_media_only'] = False
            options['forward_text_only'] = False
            message = f"✅ Rule '{rule_name}' set to forward all messages"
        else:
            await event.respond("❌ Invalid choice. Please use /set_options again.")
            return
        
        # Save to database for this specific rule
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        await event.respond(message)
        
    except asyncio.TimeoutError:
        await event.respond("❌ Timeout. Please try /set_options again.")
    except ValueError as e:
        if str(e) == "COMMAND_DETECTED":
            logger.info(f"User {user_id} cancelled options setting with a command")
            return
        raise

# Add this helper function to check if user has joined the channel
async def check_channel_membership(user_id):
    """Reliable channel membership check using get_permissions"""
    try:
        # Get the channel entity
        channel = await bot.get_entity(REQUIRED_CHANNEL)
        
        # Try to get user permissions in the channel
        # This will raise ChannelPrivateError if user hasn't joined
        permissions = await bot.get_permissions(channel, user_id)
        
        # If we get here without error, user is a member
        logger.info(f"User {user_id} is a channel member")
        return True
        
    except (ChannelPrivateError, ChatWriteForbiddenError) as e:
        logger.info(f"User {user_id} is NOT a channel member: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking channel membership for user {user_id}: {e}")
        return False

# Modify the start_forwarding_cmd function
@bot.on(events.NewMessage(pattern="/start_forwarding$"))
async def start_forwarding_cmd(event):
    await track_user_activity(event.sender_id)
    user_id = event.sender_id
    
    # STRICT CHECK: User MUST join channel before starting forwarding
    logger.info(f"Checking channel membership for user {user_id}")
    is_member = await check_channel_membership(user_id)
    
    if not is_member:
        logger.info(f"User {user_id} tried to start forwarding but is not channel member")
        
        channel_buttons = [
            [Button.url("📢 Join Our Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [Button.inline("🔄 Check Again", "verify_channel_join")]
        ]
        
        await event.respond(
            "🔒 **CHANNEL MEMBERSHIP REQUIRED**\n\n"
            "❌ **You must join our channel to use forwarding features!**\n\n"
            f"**Required Channel:** {REQUIRED_CHANNEL}\n\n"
            "**Steps to continue:**\n"
            "1. Click 'Join Our Channel' below\n"
            "2. Wait to be redirected to Telegram\n" 
            "3. Press the **JOIN** button in the channel\n"
            "4. Come back here and click 'Check Again'\n\n"
            "🚫 **Forwarding is disabled until you join the channel**",
            buttons=channel_buttons
        )
        return
    
    # Auto-enforce subscription limits but DON'T block forwarding
    issues = await enforce_subscription_limits(user_id)
    
    if issues:
        await event.respond(
            f"🔧 **Auto-Adjusted to Your Plan Limits**\n\n"
            f"Your configuration has been automatically adjusted:\n\n"
            + "\n".join([f"• {issue}" for issue in issues]) +
            f"\n\n✅ **Forwarding started with limited configuration**\n\n"
            f"💎 Upgrade for more capacity!",
            buttons=[[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
        )
    
    # Check if user has sources and destinations
    db = await get_db()
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
    
    if not sources:
        await event.respond("❌ No sources configured. Use /source first.")
        return
    if not destinations:
        await event.respond("❌ No destinations configured. Use /destination first.")
        return
    
    # Start forwarding task (ALWAYS start, even if over limits)
    task = asyncio.create_task(forward_messages(user_id))
    forwarding_tasks[user_id] = task
    
    # Store forwarding status in database
    await db.execute("""
        INSERT INTO forwarding_status (user_id, is_active, last_started)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE SET is_active=$2, last_started=CURRENT_TIMESTAMP
    """, user_id, True)
    
    if not issues:
        await event.respond(
            "✅ Forwarding Started Successfully! 🚀\n\n"
            "Use /stop_forwarding to stop when needed."
        )

@bot.on(events.CallbackQuery(pattern=b"verify_channel_join"))
async def verify_channel_join_callback(event):
    user_id = event.sender_id
    
    await event.answer("🔄 Checking channel membership...")
    
    is_member = await check_channel_membership(user_id)
    
    if is_member:
        await event.edit(
            "✅ **Success! Channel Membership Verified!**\n\n"
            "Thank you for joining our channel! You can now start forwarding.\n\n"
            "Click the button below to start:",
            buttons=[[Button.inline("🚀 Start Forwarding", "start_after_verify")]]
        )
    else:
        channel_buttons = [
            [Button.url("📢 Join Our Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [Button.inline("🔄 Check Again", "verify_channel_join")]
        ]
        
        await event.edit(
            "❌ **Still Not Verified**\n\n"
            "We still can't verify your channel membership.\n\n"
            "**Please make sure you:**\n"
            "1. Actually pressed the **JOIN** button in the channel\n"
            "2. Didn't just open the channel and leave\n"
            "3. Are not banned from the channel\n\n"
            "Join the channel and check again:",
            buttons=channel_buttons
        )


@bot.on(events.CallbackQuery(pattern=b"start_after_verify"))
async def start_after_verify_callback(event):
    user_id = event.sender_id
    
    # Double-check membership
    is_member = await check_channel_membership(user_id)
    
    if not is_member:
        await event.answer("❌ Channel membership lost. Please join again.", alert=True)
        return
    
    # Check if user has sources and destinations
    db = await get_db()
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
    
    if not sources or not destinations:
        await event.edit(
            "❌ **Setup Required**\n\n"
            "You need to configure sources and destinations first:\n\n"
            "1. Use /source to add source chats\n"
            "2. Use /destination to add destination chats\n"
            "3. Then use /start_forwarding\n\n"
            "Get started with /add_rule if you haven't created a rule yet."
        )
        return
    
    # Start forwarding task
    task = asyncio.create_task(forward_messages(user_id))
    forwarding_tasks[user_id] = task
    
    # Store forwarding status in database
    await db.execute("""
        INSERT INTO forwarding_status (user_id, is_active, last_started)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) DO UPDATE SET is_active=$2, last_started=CURRENT_TIMESTAMP
    """, user_id, True)
    
    await event.edit(
        "✅ Forwarding Started Successfully! 🚀\n\n"
        "Use /stop_forwarding to stop when needed."
    )

# Add a pre-check command to test channel membership
@bot.on(events.NewMessage(pattern="/check_join"))
async def check_join_cmd(event):
    user_id = event.sender_id
    
    await event.respond("🔄 Checking your channel membership...")
    
    is_member = await check_channel_membership(user_id)
    
    if is_member:
        await event.respond(
            f"✅ **You are a member of {REQUIRED_CHANNEL}**\n\n"
            "You can now use /start_forwarding to begin message forwarding."
        )
    else:
        channel_buttons = [
            [Button.url("📢 Join Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [Button.inline("🔄 Check Again", "verify_channel_join")]
        ]
        
        await event.respond(
            f"❌ **You are NOT a member of {REQUIRED_CHANNEL}**\n\n"
            "Please join the channel to use forwarding features:",
            buttons=channel_buttons
        )

@bot.on(events.NewMessage(pattern="/channel_status"))
async def channel_status_cmd(event):
    user_id = event.sender_id
    
    is_member = await check_channel_membership(user_id)
    
    if is_member:
        await event.respond(
            f"✅ **Channel Status: JOINED**\n\n"
            f"You are a member of {REQUIRED_CHANNEL}\n\n"
            "You can use /start_forwarding to begin message forwarding."
        )
    else:
        channel_buttons = [
            [Button.url("📢 Join Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [Button.inline("🔄 Verify Now", "verify_channel_join")]
        ]
        
        await event.respond(
            f"❌ **Channel Status: NOT JOINED**\n\n"
            f"You need to join {REQUIRED_CHANNEL} to use forwarding features.\n\n"
            "Click below to join and verify:",
            buttons=channel_buttons
        )

@bot.on(events.NewMessage(pattern="/stop_forwarding"))
async def stop_forwarding_cmd(event):
    user_id = event.sender_id
    
    if user_id in forwarding_tasks:
        forwarding_tasks[user_id].cancel()
        del forwarding_tasks[user_id]
        
        # Update database status
        db = await get_db()
        await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
        
        await event.respond("✅ Forwarding stopped.")
    else:
        await event.respond("❌ No forwarding task is running.")

async def stop_forwarding_if_over_limit(user_id):
    """Stop forwarding if user exceeds subscription limits"""
    if user_id in forwarding_tasks:
        task = forwarding_tasks[user_id]
        if not task.done():
            # Cancel the task
            task.cancel()
            
            # Wait a bit for task to cancel properly
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            
            # Remove from tracking
            del forwarding_tasks[user_id]
            
            # Update database status
            db = await get_db()
            await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
            
            logger.info(f"Auto-stopped forwarding for user {user_id} due to subscription limits")
            return True
    
    # Also update database status even if no active task
    db = await get_db()
    await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
    
    return False
    
async def restart_forwarding_for_all_users():
    """Restart forwarding for all users who had active sessions"""
    db = await get_db()
    
    # Get all users who had active forwarding
    users = await db.fetch("""
        SELECT fs.user_id 
        FROM forwarding_status fs
        JOIN users u ON fs.user_id = u.id
        WHERE fs.is_active = TRUE
        AND u.session IS NOT NULL
    """)
    
    logger.info(f"Restarting forwarding for {len(users)} users...")
    
    for user_record in users:
        user_id = user_record['user_id']  # Changed from 'id' to 'user_id'
        await asyncio.sleep(0.02)
        
        try:
            # Check if user still has sources and destinations
            sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
            destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
            
            if sources and destinations:
                # Start forwarding only if not already running
                if user_id not in forwarding_tasks:
                    task = asyncio.create_task(forward_messages(user_id))
                    forwarding_tasks[user_id] = task
                    logger.info(f"Auto-started forwarding for user {user_id}")
                    
                    # Notify user that forwarding has been restarted
                    try:
                        message = await bot.send_message(
                            user_id, 
                            "🔄 **Forwarding Auto-Restarted**\n\n"
                            "Your message forwarding has been automatically restarted after bot maintenance and restart bot server.\n\n"
                            
                        )
                        
                        # Delete the message after 10 seconds
                        await asyncio.sleep(5)
                        await message.delete()
                        
                    except Exception as e:
                        logger.warning(f"Could not notify user {user_id}: {e}")
            else:
                # User no longer has sources/destinations, update status
                await db.execute("UPDATE forwarding_status SET is_active=FALSE WHERE user_id=$1", user_id)
                logger.info(f"User {user_id} has no sources/destinations, forwarding marked as inactive")
                
        except Exception as e:
            logger.error(f"Error restarting forwarding for user {user_id}: {e}")
    
    logger.info("Auto-restart forwarding completed")

@bot.on(events.NewMessage(pattern="/status"))
async def status_cmd(event):
    user_id = event.sender_id
    
    response = "📊 **Status:**\n\n"
    
    # Check login status
    db = await get_db()
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        response += "❌ Not logged in\n"
    else:
        response += "✅ Logged in\n"
    
    # Check sources and destinations
    sources = await db.fetch("SELECT COUNT(*) FROM sources WHERE user_id=$1", user_id)
    destinations = await db.fetch("SELECT COUNT(*) FROM destinations WHERE user_id=$1", user_id)
    
    response += f"📥 Sources: {sources[0]['count']}\n"
    response += f"📤 Destinations: {destinations[0]['count']}\n"
    
    # Check forwarding status
    if user_id in forwarding_tasks:
        task = forwarding_tasks[user_id]
        if task.done():
            response += "🔄 Forwarding: ❌ Stopped (task completed)\n"
        else:
            response += "🔄 Forwarding: ✅ Running\n"
    else:
        response += "🔄 Forwarding: ❌ Not started\n"
    
    await event.respond(response)
    
@bot.on(events.NewMessage(pattern="/current_rule"))
async def current_rule_cmd(event):
    user_id = event.sender_id
    rule_id, rule_name = await get_current_rule(user_id)
    await event.respond(f"🔧 **Current Rule:** {rule_name} ({rule_id})")    

@bot.on(events.NewMessage(pattern="/help"))
async def help_cmd(event):
    help_message = (
        "🤖 **Advance Message Forwarder Bot Help**\n\n"
        "📚 **Documentation & Support:**\n"
        "• Help Channel: https://t.me/amfbot_help\n"
        "• Admin Contact: @amfbot_admin\n\n"
        "💡 **Need more help?**\n"
        "Visit our help channel or contact admin for assistance!"
    )
    
    await event.respond(help_message)

@bot.on(events.NewMessage(pattern="/convert_channellink"))
async def convert_channellink_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "channel link converter"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing converter settings for this rule
    existing_settings = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse existing options
    options = {}
    if existing_settings and existing_settings['options']:
        try:
            if isinstance(existing_settings['options'], dict):
                options = existing_settings['options']
            else:
                options = json.loads(existing_settings['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get converter settings
    converter_settings = options.get('channel_converter', {
        'my_channel': '',
        'enabled': False
    })
    
    my_channel = converter_settings.get('my_channel', '')
    enabled = converter_settings.get('enabled', False)
    
    status = "✅ **ACTIVE**" if enabled and my_channel else "❌ **INACTIVE**"
    
    message = f"🔗 **Auto Channel Link Converter**\n\n"
    message += f"**Rule:** {rule_name}\n"
    message += f"**Status:** {status}\n\n"
    
    if my_channel:
        message += f"🎯 **Your Channel:** {my_channel}\n\n"
        message += "**How it works:**\n"
        message += "• Bot will auto-detect ANY channel links in messages\n"
        message += "• Convert ALL other channel links to your channel\n"
        message += "• Preserves post IDs and message structure\n\n"
        # In the /convert_channellink_cmd function, update the examples section:
        message += "**Examples:**\n"
        message += f"`t.me/otherchannel/123` → `{my_channel}/123`\n"
        message += f"`https://t.me/competitor` → `https://{my_channel}`\n"
        message += f"`@username` → `@{my_channel.replace('t.me/', '')}`\n"
        message += f"`t.me/+abc123` → `{my_channel}`\n"  # Add private link example
        message += f"`https://t.me/+xyz789` → `https://{my_channel}`\n"  # Add private link example
    else:
        message += "❌ **No channel set!**\n\n"
        message += "Set your channel link to activate auto-conversion:\n"
        message += "• Any other channel links will be converted to yours\n"
        message += "• Works with all channel link formats\n"
        message += "• Automatic detection and replacement\n"
    
    buttons = []
    if my_channel:
        if enabled:
            buttons.append([Button.inline("🛑 Disable Converter", data="convert_toggle")])
        else:
            buttons.append([Button.inline("🚀 Enable Converter", data="convert_toggle")])
        buttons.append([Button.inline("✏️ Change My Channel", data="convert_set_channel")])
        buttons.append([Button.inline("🧹 Clear Settings", data="convert_clear")])
    else:
        buttons.append([Button.inline("🎯 Set My Channel", data="convert_set_channel")])
    
    buttons.append([Button.inline("❌ Close", data="convert_close")])
    
    await event.respond(message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"convert_"))
async def convert_channellink_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options
    existing_settings = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    options = {}
    if existing_settings and existing_settings['options']:
        try:
            if isinstance(existing_settings['options'], dict):
                options = existing_settings['options']
            else:
                options = json.loads(existing_settings['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Initialize converter settings if not exists
    if 'channel_converter' not in options:
        options['channel_converter'] = {
            'my_channel': '',
            'enabled': False
        }
    
    converter_settings = options['channel_converter']
    
    if data == "convert_set_channel":
        current_channel = converter_settings.get('my_channel', '')
        
        await event.edit(
            "🎯 **Set Your Channel Link**\n\n"
            "Enter your channel link that ALL other channel links will be converted to:\n\n"
            f"**Current:** {current_channel if current_channel else 'Not set'}\n\n"
            "**Supported formats:**\n"
            "• `t.me/yourchannel`\n"
            "• `https://t.me/yourchannel`\n"
            "• `@yourusername`\n\n"
            "**Examples:**\n"
            "t.me/mychannel\n"
            "https://t.me/myawesomechannel\n"
            "@myusername\n\n"
            "Send your channel link now, or 'cancel' to go back:"
        )
        
        user_states[user_id] = {
            'mode': 'convert_set_channel',
            'rule_id': rule_id,
            'options': options
        }
        
    elif data == "convert_toggle":
        if not converter_settings.get('my_channel'):
            await event.answer("❌ Set your channel first!", alert=True)
            return
            
        converter_settings['enabled'] = not converter_settings['enabled']
        options['channel_converter'] = converter_settings
        
        # Save to database
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        status = "enabled ✅" if converter_settings['enabled'] else "disabled 🛑"
        await event.answer(f"Channel converter {status}!")
        
        # Refresh the view
        await convert_channellink_cmd(event)
        
    elif data == "convert_clear":
        if not converter_settings.get('my_channel'):
            await event.answer("❌ Nothing to clear!", alert=True)
            return
            
        buttons = [
            [Button.inline("✅ Yes, Clear", data="convert_confirm_clear")],
            [Button.inline("❌ Cancel", data="convert_back")]
        ]
        
        await event.edit(
            "🗑️ **Clear Channel Settings**\n\n"
            f"Are you sure you want to remove your channel?\n\n"
            f"**Your Channel:** {converter_settings['my_channel']}\n\n"
            "This will disable the auto-converter.",
            buttons=buttons
        )
        
    elif data == "convert_confirm_clear":
        options['channel_converter'] = {
            'my_channel': '',
            'enabled': False
        }
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.edit(
            "✅ Channel settings cleared!\n\n"
            "Auto-converter has been disabled.",
            buttons=[[Button.inline("⬅️ Back", data="convert_back")]]
        )
        
    elif data == "convert_close":
        await event.delete()
        
    elif data == "convert_back":
        # Return to main menu
        await convert_channellink_cmd(event)

@bot.on(events.NewMessage)
async def handle_channel_converter_input(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'convert_set_channel':
        return
    
    state = user_states[user_id]
    text = event.raw_text.strip()
    
    if text.lower() == 'cancel':
        await event.respond("❌ Cancelled channel setup.")
        del user_states[user_id]
        return
    
    # Validate and normalize channel link
    my_channel = normalize_channel_link(text)
    
    if not my_channel:
        await event.respond(
            "❌ Invalid channel link!\n\n"
            "Please enter a valid channel link:\n"
            "• t.me/yourchannel\n"
            "• https://t.me/yourchannel\n"
            "• @yourusername\n\n"
            "Try again or send 'cancel' to go back."
        )
        return
    
    # Get current options
    options = state['options']
    converter_settings = options.get('channel_converter', {
        'my_channel': '',
        'enabled': True
    })
    
    # Update with new channel
    old_channel = converter_settings.get('my_channel', '')
    converter_settings['my_channel'] = my_channel
    converter_settings['enabled'] = True  # Auto-enable when setting channel
    
    options['channel_converter'] = converter_settings
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Save to database
    await db.execute(
        "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
        json.dumps(options), user_id, rule_id
    )
    
    # Prepare success response
    response = f"✅ **Auto Channel Converter Activated!**\n\n"
    response += f"**Your Channel:** {my_channel}\n\n"
    response += "**Now active for rule:** {rule_name}\n\n"
    response += "🔄 **The bot will now automatically:**\n"
    response += "• Detect ANY channel links in messages\n"
    response += "• Convert ALL other channels to your channel\n"
    response += "• Preserve post IDs and message structure\n\n"
    response += "**Examples of conversion:**\n"
    response += f"• `t.me/anychannel/123` → `{my_channel}/123`\n"
    response += f"• `https://t.me/competitor` → `https://{my_channel}`\n"
    response += f"• `@anyusername` → `@{my_channel.replace('t.me/', '')}`\n"
    response += f"• `telegram.me/somechannel` → `{my_channel}`\n\n"
    response += "🚀 **Ready to convert!** Messages will be auto-processed."
    
    buttons = [
        [Button.inline("⚙️ Manage Settings", data="convert_back")],
        [Button.inline("❌ Close", data="convert_close")]
    ]
    
    await event.respond(response, buttons=buttons)
    del user_states[user_id]

def normalize_channel_link(link):
    """Normalize channel link to standard t.me format"""
    link = link.strip()
    
    if not link:
        return None
    
    # Remove @ symbol if present at start
    if link.startswith('@'):
        link = link[1:]
    
    # Handle different formats
    if link.startswith('https://t.me/'):
        channel_name = link[13:].rstrip('/')
    elif link.startswith('t.me/'):
        channel_name = link[5:].rstrip('/')
    elif link.startswith('https://telegram.me/'):
        channel_name = link[20:].rstrip('/')
    elif link.startswith('telegram.me/'):
        channel_name = link[12:].rstrip('/')
    else:
        # Assume it's just a username/channel name
        channel_name = link.rstrip('/')
    
    # Remove any additional path (like /123 post IDs)
    channel_name = channel_name.split('/')[0]
    
    # Remove + from private links for normalization
    if channel_name.startswith('+'):
        channel_name = channel_name[1:]
    
    if not channel_name or ' ' in channel_name:
        return None
    
    return f"t.me/{channel_name}"

def convert_all_channel_links(text, my_channel):
    """Convert ALL channel links in text to user's channel"""
    if not text or not my_channel:
        return text
    
    # Extract clean channel name (without t.me/)
    my_channel_name = my_channel.replace('t.me/', '')
    
    import re
    
    # Patterns to match various channel link formats - including private links
    patterns = [
        # Private channel links (t.me/+ format)
        r't\.me/\+([a-zA-Z0-9_-]+)',
        # Private channel links (https://t.me/+ format)
        r'https://t\.me/\+([a-zA-Z0-9_-]+)',
        # t.me format with post ID
        r't\.me/([a-zA-Z0-9_]+)/\d+',
        # t.me format without post ID  
        r't\.me/([a-zA-Z0-9_]+)(?!/)',
        # https://t.me format with post ID
        r'https://t\.me/([a-zA-Z0-9_]+)/\d+',
        # https://t.me format without post ID
        r'https://t\.me/([a-zA-Z0-9_]+)(?!/)',
        # telegram.me format
        r'telegram\.me/([a-zA-Z0-9_]+)',
        # https://telegram.me format
        r'https://telegram\.me/([a-zA-Z0-9_]+)',
        # @username format
        r'@([a-zA-Z0-9_]+)'
    ]
    
    converted_text = text
    
    for pattern in patterns:
        matches = re.finditer(pattern, converted_text)
        for match in matches:
            original_link = match.group(0)
            original_channel = match.group(1)
            
            # Don't convert if it's already the user's channel
            if original_channel.lower() == my_channel_name.lower():
                continue
            
            # Determine replacement based on pattern type
            if pattern.startswith('@'):
                # @username format
                replacement = f"@{my_channel_name}"
            elif 't.me/+' in original_link:
                # Private channel link format - convert to regular channel link
                if pattern.startswith('https://'):
                    replacement = f"https://t.me/{my_channel_name}"
                else:
                    replacement = f"t.me/{my_channel_name}"
            elif pattern.startswith('https://'):
                # https format
                if r'/\d+' in pattern:  # With post ID
                    post_id = original_link.split('/')[-1]
                    replacement = f"https://t.me/{my_channel_name}/{post_id}"
                else:  # Without post ID
                    replacement = f"https://t.me/{my_channel_name}"
            else:
                # t.me format
                if r'/\d+' in pattern:  # With post ID
                    post_id = original_link.split('/')[-1]
                    replacement = f"t.me/{my_channel_name}/{post_id}"
                else:  # Without post ID
                    replacement = f"t.me/{my_channel_name}"
            
            # Replace the link
            converted_text = converted_text.replace(original_link, replacement)
    
    return converted_text

# Add this command handler after the other command handlers
@bot.on(events.NewMessage(pattern="/replace_link"))
async def replace_link_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "link replacement"):
        return  # Stop command execution until user stops forwarding
        
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing link replacements for this rule
    existing_replacements = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse existing options
    options = {}
    if existing_replacements and existing_replacements['options']:
        try:
            if isinstance(existing_replacements['options'], dict):
                options = existing_replacements['options']
            else:
                options = json.loads(existing_replacements['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get link replacements from options
    link_replacements = options.get('link_replacements', {})
    
    # Create a more interactive menu with buttons
    buttons = [
        [Button.inline("➕ Add Replacement", data="link_add")],
        [Button.inline("🗑️ Remove Replacement", data="link_remove")],
        [Button.inline("🧹 Clear All", data="link_clear")],
        [Button.inline("📋 View Current", data="link_view")],
        [Button.inline("❌ Close", data="link_close")]
    ]
    
    status_message = f"🔗 **Link Replacement Manager**\n\n**Rule:** {rule_name}\n\n"
    
    if link_replacements:
        status_message += f"📊 **Active Replacements:** {len(link_replacements)}\n"
        # Show a few examples
        count = 0
        for original, new in list(link_replacements.items())[:3]:
            status_message += f"• `{original}` → `{new}`\n"
            count += 1
        if len(link_replacements) > 3:
            status_message += f"• ... and {len(link_replacements) - 3} more\n"
    else:
        status_message += "❌ No link replacements configured\n"
    
    status_message += "\n💡 **Features:**\n• Replace links in text & captions\n• Support for multiple replacements\n• Case-sensitive matching\n• Works with all message types"
    
    await event.respond(status_message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"link_"))
async def link_replacement_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options
    existing_replacements = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    options = {}
    if existing_replacements and existing_replacements['options']:
        try:
            if isinstance(existing_replacements['options'], dict):
                options = existing_replacements['options']
            else:
                options = json.loads(existing_replacements['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    link_replacements = options.get('link_replacements', {})
    
    if data == "link_add":
        await event.edit(
            "🔗 **Add Link Replacement**\n\n"
            "Please send the replacement in one of these formats:\n\n"
            "**Format 1:** Simple replacement\n"
            "`original_link -> new_link`\n\n"
            "**Format 2:** Multiple replacements\n"
            "`link1->new1, link2->new2, link3->new3`\n\n"
            "**Format 3:** Bulk import\n"
            "Send a text file with one replacement per line:\n"
            "`original1 -> new1`\n"
            "`original2 -> new2`\n\n"
            "**Examples:**\n"
            "`https://old.com -> https://new.com`\n"
            "`t.me/oldchannel -> t.me/newchannel`\n"
            "`example.com/page -> alternative.com/page`\n\n"
            "📝 **Notes:**\n"
            "• Links should include http:// or https://\n"
            "• Use `->` as separator\n"
            "• For multiple, separate with commas\n\n"
            "Send 'cancel' to go back.",
            buttons=[Button.inline("⬅️ Back", data="link_back")]
        )
        
        user_states[user_id] = {
            'mode': 'link_replacement_add',
            'rule_id': rule_id,
            'options': options
        }
        
    elif data == "link_remove":
        if not link_replacements:
            await event.answer("❌ No replacements to remove", alert=True)
            return
        
        # Create paginated removal interface
        replacements_list = list(link_replacements.items())
        user_states[user_id] = {
            'mode': 'link_replacement_remove',
            'replacements': replacements_list,
            'page': 0,
            'rule_id': rule_id,
            'options': options
        }
        
        await show_replacements_page(event, replacements_list, 0)
        
    elif data == "link_clear":
        if not link_replacements:
            await event.answer("❌ No replacements to clear", alert=True)
            return
        
        buttons = [
            [Button.inline("✅ Yes, Clear All", data="link_confirm_clear")],
            [Button.inline("❌ Cancel", data="link_back")]
        ]
        await event.edit(
            "🗑️ **Clear All Replacements**\n\n"
            f"Are you sure you want to remove all {len(link_replacements)} link replacements?\n\n"
            "This action cannot be undone!",
            buttons=buttons
        )
        
    elif data == "link_confirm_clear":
        if 'link_replacements' in options:
            del options['link_replacements']
            
            await db.execute(
                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                json.dumps(options), user_id, rule_id
            )
            
            await event.edit(
                f"✅ All link replacements cleared for rule '{rule_name}'!",
                buttons=[Button.inline("⬅️ Back to Manager", data="link_back")]
            )
        else:
            await event.answer("❌ No replacements to clear", alert=True)
            
    elif data == "link_view":
        if not link_replacements:
            await event.answer("❌ No replacements to view", alert=True)
            return
            
        replacements_list = list(link_replacements.items())
        user_states[user_id] = {
            'mode': 'link_replacement_view',
            'replacements': replacements_list,
            'page': 0
        }
        
        await show_replacements_page(event, replacements_list, 0, view_mode=True)
        
    elif data == "link_close":
        await event.delete()
        
    elif data == "link_back":
        # Return to main menu
        await replace_link_cmd(event)
        
    elif data.startswith("link_page_"):
        # Handle pagination
        page = int(data.split("_")[2])
        mode = user_states[user_id].get('mode')
        replacements_list = user_states[user_id].get('replacements', [])
        
        if mode == 'link_replacement_remove':
            await show_replacements_page(event, replacements_list, page)
        elif mode == 'link_replacement_view':
            await show_replacements_page(event, replacements_list, page, view_mode=True)
            
    elif data.startswith("link_remove_"):
        # Handle individual removal
        index = int(data.split("_")[2])
        replacements_list = user_states[user_id].get('replacements', [])
        page = user_states[user_id].get('page', 0)
        
        if 0 <= index < len(replacements_list):
            original_link, new_link = replacements_list[index]
            
            # Remove from replacements
            del link_replacements[original_link]
            options['link_replacements'] = link_replacements
            
            # Save to database
            await db.execute(
                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                json.dumps(options), user_id, rule_id
            )
            
            await event.answer(f"✅ Removed: {original_link} → {new_link}")
            
            # Update the list and show current page
            replacements_list = list(link_replacements.items())
            user_states[user_id]['replacements'] = replacements_list
            
            if replacements_list:
                await show_replacements_page(event, replacements_list, page)
            else:
                await event.edit(
                    "✅ All replacements removed!",
                    buttons=[Button.inline("⬅️ Back to Manager", data="link_back")]
                )

async def show_replacements_page(event, replacements_list, page, view_mode=False):
    """Show a paginated list of replacements"""
    items_per_page = 5
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(replacements_list))
    page_items = replacements_list[start_idx:end_idx]
    
    if view_mode:
        title = "📋 Current Link Replacements"
    else:
        title = "🗑️ Select Replacement to Remove"
    
    message = f"**{title}**\n\n"
    message += f"Page {page + 1}/{(len(replacements_list) + items_per_page - 1) // items_per_page}\n\n"
    
    buttons = []
    
    for i, (original, new) in enumerate(page_items):
        idx = start_idx + i
        # Truncate long URLs for display
        display_original = original[:30] + "..." if len(original) > 30 else original
        display_new = new[:30] + "..." if len(new) > 30 else new
        
        message += f"**{idx + 1}. {display_original}**\n→ {display_new}\n\n"
        
        if not view_mode:
            buttons.append([Button.inline(f"🗑️ Remove #{idx + 1}", data=f"link_remove_{idx}")])
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(Button.inline("⬅️ Previous", data=f"link_page_{page - 1}"))
    if end_idx < len(replacements_list):
        nav_buttons.append(Button.inline("➡️ Next", data=f"link_page_{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([Button.inline("⬅️ Back to Manager", data="link_back")])
    
    await event.edit(message, buttons=buttons)

@bot.on(events.NewMessage)
async def handle_link_replacement_input(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'link_replacement_add':
        return
    
    state = user_states[user_id]
    text = event.raw_text.strip()
    
    if text.lower() == 'cancel':
        await event.respond("❌ Cancelled adding link replacement.")
        del user_states[user_id]
        return
    
    # Check if it's a file (bulk import)
    if event.message.media and event.message.document:
        try:
            file = await event.download_media()
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            os.remove(file)
            
            replacements = parse_bulk_replacements(content)
            
        except Exception as e:
            await event.respond(f"❌ Error reading file: {e}")
            return
    else:
        # Parse text input
        replacements = parse_replacements_text(text)
    
    if not replacements:
        await event.respond(
            "❌ Invalid format. Please use:\n"
            "• `original -> replacement`\n"
            "• `link1->new1, link2->new2`\n"
            "Or send a text file with one replacement per line."
        )
        return
    
    # Get current replacements
    options = state['options']
    link_replacements = options.get('link_replacements', {})
    
    # Add new replacements
    added_count = 0
    duplicate_count = 0
    
    for original, new in replacements.items():
        if original in link_replacements:
            duplicate_count += 1
        else:
            link_replacements[original] = new
            added_count += 1
    
    # Save to database
    options['link_replacements'] = link_replacements
    db = await get_db()
    await db.execute(
        "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
        json.dumps(options), user_id, state['rule_id']
    )
    
    # Prepare response message
    rule_id, rule_name = await get_current_rule(user_id)
    response = f"✅ **Link Replacements Updated for '{rule_name}'**\n\n"
    
    if added_count > 0:
        response += f"➕ **Added:** {added_count} new replacement(s)\n"
    if duplicate_count > 0:
        response += f"⚠️ **Skipped:** {duplicate_count} duplicate(s)\n"
    
    response += f"\n📊 **Total Active:** {len(link_replacements)} replacement(s)\n\n"
    
    # Show some of the added replacements
    if added_count > 0:
        response += "**Recently Added:**\n"
        count = 0
        for original, new in replacements.items():
            if original in link_replacements and link_replacements[original] == new:
                response += f"• `{original}` → `{new}`\n"
                count += 1
                if count >= 3:  # Show max 3 examples
                    break
        if added_count > 3:
            response += f"• ... and {added_count - 3} more\n"
    
    buttons = [
        [Button.inline("📋 View All", data="link_view")],
        [Button.inline("⬅️ Back to Manager", data="link_back")]
    ]
    
    await event.respond(response, buttons=buttons)
    del user_states[user_id]

def parse_replacements_text(text):
    """Parse replacement text input"""
    replacements = {}
    
    # Check for multiple replacements separated by commas
    if ',' in text:
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if '->' in part:
                original, new = part.split('->', 1)
                original = original.strip()
                new = new.strip()
                if original and new:
                    replacements[original] = new
    else:
        # Single replacement
        if '->' in text:
            original, new = text.split('->', 1)
            original = original.strip()
            new = new.strip()
            if original and new:
                replacements[original] = new
    
    return replacements

def parse_bulk_replacements(content):
    """Parse bulk replacements from file content"""
    replacements = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if line and '->' in line:
            original, new = line.split('->', 1)
            original = original.strip()
            new = new.strip()
            if original and new:
                replacements[original] = new
    
    return replacements

# Add this after the other command handlers

@bot.on(events.NewMessage(pattern="/more_settings"))
async def more_settings_cmd(event):
    """Show additional settings commands"""
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current settings for this rule
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse current options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    
    settings_message = (
        f"⚙️ ****More Settings for Rule: {rule_name}****\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔧 **Available Settings Commands**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    settings_message += "🔹 **/delay** - Set a delay for forwarding\n\n"
    settings_message += "🔹 **/url_preview** - Turn URL previews on or off\n\n"
    settings_message += "🔹 **/convert_channellink** - Convert a channel link to your channel link\n\n"
    settings_message += "🔹 **/remove_links** - Remove all links from messages 💎 PREMIUM\n\n"
    settings_message += "🔹 **/replace_link** - Replace links with your own links\n\n"
    settings_message += "🔹 **/replace_text** - Replace text with custom text 💎 PREMIUM\n\n"
    settings_message += "🔹 **/forward_old** - Forward old messages 💎 PREMIUM\n\n"
    
    settings_message += "💡 **Usage:** Use the commands above to configure each setting individually."
    
    await event.respond(settings_message)

@bot.on(events.NewMessage(pattern="/forward_old"))
async def forward_old_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # Check if user is on premium plan
    subscription_plan = await get_user_subscription(user_id)
    if subscription_plan == 'free':
        await event.respond(
            "❌ **Premium Feature Required**\n\n"
            "The **Forward Old Messages** feature is only available for premium users.\n\n"
            "💎 **Upgrade to Premium to unlock:**\n"
            "• Forward old messages from sources\n"
            "• Copy mode (not forward mode)\n"
            "• Album/media group support\n"
            "• Advanced message processing\n\n"
            "Click below to upgrade:",
            buttons=[[Button.inline("💎 Upgrade to Premium", data="upgrade_subscription")]]
        )
        return
    
    # Check if user has joined the required channel
    is_member = await check_channel_membership(user_id)
    if not is_member:
        channel_buttons = [
            [Button.url("📢 Join Our Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
            [Button.inline("🔄 Check Again", "verify_channel_join")]
        ]
        await event.respond(
            "🔒 **CHANNEL MEMBERSHIP REQUIRED**\n\n"
            f"❌ **You must join {REQUIRED_CHANNEL} to use this feature!**\n\n"
            "Join the channel and verify to continue.",
            buttons=channel_buttons
        )
        return
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get sources for the current rule
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    if not sources:
        await event.respond(f"❌ No sources found for rule '{rule_name}'. Use /source to add sources first.")
        return
    
    # Get destinations for the current rule
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
    
    if not destinations:
        await event.respond(f"❌ No destinations found for rule '{rule_name}'. Use /destination to add destinations first.")
        return
    
    # Show options for forwarding old messages
    message = (
        f"📚 **Forward Old Messages** 💎 PREMIUM\n\n"
        f"**Rule:** {rule_name}\n\n"
        "**Features:**\n"
        "• 📝 Copy mode (not forward)\n"
        "• 🖼️ Album/media group support\n"
        "• ⚡ All filters applied\n"
        "• 🔄 Batch processing\n\n"
        "**Important:**\n"
        "• ⏰ Rate limiting to avoid bans\n"
        "• 🛑 Auto-pause on flood waits\n"
        "• 📊 Progress tracking\n\n"
        "**Options:**\n"
        "1. Copy last 10 messages\n"
        "2. Copy last 50 messages\n"
        "3. Copy last 100 messages\n"
        "4. Copy ALL messages (from beginning)\n"
        "5. Custom number of messages\n"
        "6. 📊 Message Range (e.g., 1-1000, 1000-2000)\n\n"
        "Choose an option:"
    )
    
    buttons = [
        [Button.inline("1️⃣ Last 10", data="old_10")],
        [Button.inline("2️⃣ Last 50", data="old_50")],
        [Button.inline("3️⃣ Last 100", data="old_100")],
        [Button.inline("4️⃣ 🚀 ALL Messages", data="old_all")],
        [Button.inline("5️⃣ Custom", data="old_custom")],
        [Button.inline("6️⃣ 📊 Message Range", data="old_range")],
        [Button.inline("❌ Cancel", data="old_cancel")]
    ]
    
    user_states[user_id] = {
        'mode': 'forward_old_selection',
        'rule_id': rule_id,
        'rule_name': rule_name,
        'sources': sources,
        'destinations': destinations
    }
    
    await event.respond(message, buttons=buttons)

# Handler for range selection
@bot.on(events.CallbackQuery(pattern=b"old_range"))
async def old_range_handler(event):
    user_id = event.sender_id
    
    if user_id not in user_states:
        await event.respond("❌ Session expired. Please use /forward_old again.")
        return
    
    user_states[user_id]['mode'] = 'awaiting_range_input'
    
    await event.edit(
        "📊 **Message Range Selection**\n\n"
        "Please enter the message range in the format:\n"
        "`start-end`\n\n"
        "**Examples:**\n"
        "• `1-1000` - Messages 1 to 1000\n"
        "• `1000-2000` - Messages 1000 to 2000\n"
        "• `2000-3000` - Messages 2000 to 3000\n\n"
        "**Note:**\n"
        "• Message 1 is the oldest message\n"
        "• Higher numbers are newer messages\n"
        "• Range is inclusive (both start and end included)\n"
        "• Maximum range: 10,000 messages\n\n"
        "Enter your range:"
    )

# Handler for range input
@bot.on(events.NewMessage(pattern=r"^(\d+)-(\d+)$"))
async def range_input_handler(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'awaiting_range_input':
        return
    
    try:
        match = event.pattern_match
        start_msg = int(match.group(1))
        end_msg = int(match.group(2))
        
        if start_msg <= 0 or end_msg <= 0:
            await event.respond("❌ Range values must be positive numbers.")
            return
        
        if start_msg >= end_msg:
            await event.respond("❌ Start value must be less than end value.")
            return
        
        # Calculate the limit (number of messages to fetch)
        limit = end_msg - start_msg + 1
        
        if limit > 10000:
            await event.respond("❌ Range too large. Maximum 10,000 messages per range.")
            return
        
        state = user_states[user_id]
        state['mode'] = 'processing_range'
        state['range_start'] = start_msg
        state['range_end'] = end_msg
        state['range_limit'] = limit
        state['offset'] = start_msg - 1  # Telegram uses 0-based offset
        
        await event.respond(
            f"✅ **Range Accepted**\n\n"
            f"**Range:** {start_msg}-{end_msg}\n"
            f"**Total Messages:** {limit}\n"
            f"**Offset:** {state['offset']}\n\n"
            "Starting message copying process..."
        )
        
        # Start the forwarding process with range
        await start_old_forwarding_with_range(event, user_id, state, start_msg, end_msg, limit)
        
    except Exception as e:
        logger.error(f"Error processing range input: {e}")
        await event.respond("❌ Invalid range format. Please use format: `start-end` (e.g., 1-1000)")

async def start_old_forwarding_with_range(event, user_id, state, start_msg, end_msg, limit):
    """Start copying messages in a specific range"""
    rule_id = state['rule_id']
    rule_name = state['rule_name']
    sources = state['sources']
    destinations = state['destinations']
    offset = state['offset']
    
    # Get user client
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Client not available. Please /login again.")
        if user_id in user_states:
            del user_states[user_id]
        return
    
    db = await get_db()
    
    # Get rule options for filtering
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse rule options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get keyword filters
    whitelist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
        user_id, rule_id
    )
    blacklist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
        user_id, rule_id
    )
    
    whitelist_keywords = whitelist['keywords'] if whitelist else []
    blacklist_keywords = blacklist['keywords'] if blacklist else []
    
    # Start forwarding process
    progress_msg = await event.respond(
        f"🔄 Starting to copy messages {start_msg}-{end_msg} in COPY mode...\n"
        f"📊 Range: {start_msg} to {end_msg} ({limit} messages)\n"
        f"⏰ This may take a while..."
    )
    
    total_copied = 0
    total_skipped = 0
    album_groups_processed = set()
    
    # Rate limiting variables
    messages_sent = 0
    start_time = asyncio.get_event_loop().time()
    
    try:
        for source_idx, source in enumerate(sources):
            try:
                # Get source entity
                if source['username']:
                    source_entity = await resolve_entity_safe(client, f"@{source['username']}")
                else:
                    source_entity = await resolve_entity_safe(client, source['chat_id'])
                
                if not source_entity:
                    logger.warning(f"Could not resolve source entity: {source['title']}")
                    continue
                
                # Update progress
                await progress_msg.edit(
                    f"📥 Processing range {start_msg}-{end_msg} from: {source['title']}\n"
                    f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
                    f"🔄 Fetching messages {start_msg} to {end_msg}...\n"
                    f"📋 Source {source_idx + 1}/{len(sources)}\n"
                    f"⏰ Rate limiting: {messages_sent} messages sent"
                )
                
                # Get messages from the source with specific range
                messages = []
                try:
                    # Fetch messages with offset and limit
                    async for message in client.iter_messages(
                        source_entity, 
                        limit=limit,
                        offset_id=offset,
                        reverse=True  # Get from oldest to newest in the range
                    ):
                        messages.append(message)
                    
                    # Reverse to process from newest to oldest in the range
                    messages.reverse()
                    
                    logger.info(f"Fetched {len(messages)} messages from {source['title']} (range {start_msg}-{end_msg})")
                    
                    if len(messages) < limit:
                        await progress_msg.edit(
                            f"⚠️ **Range Notice**\n\n"
                            f"Source: {source['title']}\n"
                            f"Requested: {limit} messages ({start_msg}-{end_msg})\n"
                            f"Available: {len(messages)} messages\n"
                            f"Continuing with available messages..."
                        )
                    
                except Exception as e:
                    logger.error(f"Error fetching messages from {source['title']}: {e}")
                    await progress_msg.edit(
                        f"❌ Error fetching messages from {source['title']}: {str(e)}"
                    )
                    continue
                
                # Process messages with album grouping and rate limiting
                i = 0
                while i < len(messages):
                    message = messages[i]
                    current_message_number = start_msg + i
                    
                    # Check if this message is part of an album that we've already processed
                    if hasattr(message, 'grouped_id') and message.grouped_id:
                        album_id = f"{source_entity.id}_{message.grouped_id}"
                        if album_id in album_groups_processed:
                            i += 1
                            continue
                        
                        # Process entire album as a group
                        album_messages = await get_album_messages(messages, i, message.grouped_id)
                        if album_messages:
                            # Mark this album as processed
                            album_groups_processed.add(album_id)
                            
                            # Process album group with rate limiting
                            copied_count = await process_album_group(
                                client, album_messages, destinations,
                                whitelist_keywords, blacklist_keywords, options,
                                progress_msg, source_idx, len(sources), total_copied, total_skipped,
                                range_info=f"Range: {start_msg}-{end_msg}"
                            )
                            
                            if copied_count > 0:
                                total_copied += len(album_messages)
                                messages_sent += len(album_messages)
                            else:
                                total_skipped += len(album_messages)
                            
                            i += len(album_messages)
                            continue
                    
                    # Process single message
                    try:
                        # Check if message should be copied based on filters
                        if not await should_forward_message(
                            message, whitelist_keywords, blacklist_keywords, options
                        ):
                            total_skipped += 1
                            i += 1
                            continue
                        
                        # Apply rate limiting
                        await apply_rate_limiting(messages_sent, start_time, progress_msg)
                        
                        # Copy to all destinations
                        success = await copy_message_to_destinations(
                            client, message, destinations, options
                        )
                        
                        if success:
                            total_copied += 1
                            messages_sent += 1
                        else:
                            total_skipped += 1
                        
                        # Update progress every 5 messages
                        if total_copied % 5 == 0:
                            await update_progress_with_range(
                                progress_msg, source['title'], source_idx, len(sources),
                                total_copied, total_skipped, i, len(messages),
                                messages_sent, start_msg, end_msg, current_message_number
                            )
                        
                    except Exception as e:
                        logger.error(f"Error processing message {current_message_number} from {source['title']}: {e}")
                        total_skipped += 1
                    
                    i += 1
                
                # Source completed
                await progress_msg.edit(
                    f"✅ Completed range {start_msg}-{end_msg}: {source['title']}\n"
                    f"📊 Total: {total_copied} copied, {total_skipped} skipped\n"
                    f"⏰ Messages sent: {messages_sent}\n"
                    f"🔄 Moving to next source...\n"
                    f"📋 Source {source_idx + 1}/{len(sources)}"
                )
                
            except Exception as e:
                logger.error(f"Error processing source {source['title']}: {e}")
                continue
        
        # All sources completed
        completion_message = await generate_range_completion_message(
            rule_name, total_copied, total_skipped, 
            len(album_groups_processed), start_msg, end_msg
        )
        await progress_msg.edit(completion_message)
        
    except Exception as e:
        logger.error(f"Error in range message copying: {e}")
        await progress_msg.edit(f"❌ Error during range message copying: {str(e)}")
    
    # Clean up
    if user_id in user_states:
        del user_states[user_id]

async def update_progress_with_range(progress_msg, source_title, source_idx, total_sources,
                                   total_copied, total_skipped, current, total,
                                   messages_sent, start_msg, end_msg, current_message_number):
    """Update progress message for range processing"""
    message = (
        f"📥 Processing range {start_msg}-{end_msg} from: {source_title}\n"
        f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
        f"📈 Current: Message {current_message_number} ({current + 1}/{total})\n"
        f"⏰ Messages sent: {messages_sent}\n"
        f"📋 Source {source_idx + 1}/{total_sources}"
    )
    
    await progress_msg.edit(message)

async def generate_range_completion_message(rule_name, total_copied, total_skipped, albums_processed, start_msg, end_msg):
    """Generate completion message for range processing"""
    return (
        f"✅ **Range Copying Completed!** 💎\n\n"
        f"**Rule:** {rule_name}\n"
        f"**Range Processed:** {start_msg}-{end_msg}\n"
        f"**Total Messages:** {end_msg - start_msg + 1}\n"
        f"**Successfully Copied:** {total_copied}\n"
        f"**Skipped:** {total_skipped}\n"
        f"**Albums Processed:** {albums_processed}\n\n"
        f"📝 **Copy Mode:** Messages were copied (not forwarded)\n"
        f"🖼️ **Album Support:** Media groups preserved\n"
        f"⏰ **Rate Limited:** Protected from flood waits\n\n"
        "Use /start_forwarding to begin real-time forwarding."
    )

# Original start_old_forwarding function (updated with range support)
async def start_old_forwarding(event, user_id, state, limit):
    """Start copying old messages in copy mode with album support and rate limiting"""
    rule_id = state['rule_id']
    rule_name = state['rule_name']
    sources = state['sources']
    destinations = state['destinations']
    
    # Get user client
    client = await get_user_client(user_id)
    if not client:
        await event.respond("❌ Client not available. Please /login again.")
        if user_id in user_states:
            del user_states[user_id]
        return
    
    db = await get_db()
    
    # Get rule options for filtering
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse rule options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get keyword filters
    whitelist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
        user_id, rule_id
    )
    blacklist = await db.fetchrow(
        "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
        user_id, rule_id
    )
    
    whitelist_keywords = whitelist['keywords'] if whitelist else []
    blacklist_keywords = blacklist['keywords'] if blacklist else []
    
    # Start forwarding process
    if limit is None:
        progress_msg = await event.respond("🔄 Starting to copy ALL messages from the beginning in COPY mode...")
    else:
        progress_msg = await event.respond(f"🔄 Starting to copy last {limit} messages in COPY mode...")
    
    total_copied = 0
    total_skipped = 0
    album_groups_processed = set()
    
    # Rate limiting variables
    messages_sent = 0
    start_time = asyncio.get_event_loop().time()
    
    try:
        for source_idx, source in enumerate(sources):
            try:
                # Get source entity
                if source['username']:
                    source_entity = await resolve_entity_safe(client, f"@{source['username']}")
                else:
                    source_entity = await resolve_entity_safe(client, source['chat_id'])
                
                if not source_entity:
                    logger.warning(f"Could not resolve source entity: {source['title']}")
                    continue
                
                # Update progress
                if limit is None:
                    await progress_msg.edit(
                        f"📥 Processing ALL messages from: {source['title']}\n"
                        f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
                        f"🔄 Fetching ALL messages (this may take a while)...\n"
                        f"📋 Source {source_idx + 1}/{len(sources)}\n"
                        f"⏰ Rate limiting: {messages_sent} messages sent"
                    )
                else:
                    await progress_msg.edit(
                        f"📥 Processing source: {source['title']}\n"
                        f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
                        f"🔄 Fetching last {limit} messages...\n"
                        f"📋 Source {source_idx + 1}/{len(sources)}\n"
                        f"⏰ Rate limiting: {messages_sent} messages sent"
                    )
                
                # Get messages from the source
                messages = []
                try:
                    if limit is None:
                        # Get ALL messages from the beginning
                        async for message in client.iter_messages(
                            source_entity, 
                            reverse=True  # Get from oldest to newest, no limit
                        ):
                            messages.append(message)
                    else:
                        # Get limited number of messages
                        async for message in client.iter_messages(
                            source_entity, 
                            limit=limit,
                            reverse=True  # Get from oldest to newest
                        ):
                            messages.append(message)
                    
                    # Reverse to process from newest to oldest
                    messages.reverse()
                    
                    logger.info(f"Fetched {len(messages)} messages from {source['title']}")
                    
                except Exception as e:
                    logger.error(f"Error fetching messages from {source['title']}: {e}")
                    await progress_msg.edit(
                        f"❌ Error fetching messages from {source['title']}: {str(e)}"
                    )
                    continue
                
                # Process messages with album grouping and rate limiting
                i = 0
                while i < len(messages):
                    message = messages[i]
                    
                    # Check if this message is part of an album that we've already processed
                    if hasattr(message, 'grouped_id') and message.grouped_id:
                        album_id = f"{source_entity.id}_{message.grouped_id}"
                        if album_id in album_groups_processed:
                            i += 1
                            continue
                        
                        # Process entire album as a group
                        album_messages = await get_album_messages(messages, i, message.grouped_id)
                        if album_messages:
                            # Mark this album as processed
                            album_groups_processed.add(album_id)
                            
                            # Process album group with rate limiting
                            copied_count = await process_album_group(
                                client, album_messages, destinations,
                                whitelist_keywords, blacklist_keywords, options,
                                progress_msg, source_idx, len(sources), total_copied, total_skipped
                            )
                            
                            if copied_count > 0:
                                total_copied += len(album_messages)
                                messages_sent += len(album_messages)
                            else:
                                total_skipped += len(album_messages)
                            
                            i += len(album_messages)
                            continue
                    
                    # Process single message
                    try:
                        # Check if message should be copied based on filters
                        if not await should_forward_message(
                            message, whitelist_keywords, blacklist_keywords, options
                        ):
                            total_skipped += 1
                            i += 1
                            continue
                        
                        # Apply rate limiting
                        await apply_rate_limiting(messages_sent, start_time, progress_msg)
                        
                        # Copy to all destinations
                        success = await copy_message_to_destinations(
                            client, message, destinations, options
                        )
                        
                        if success:
                            total_copied += 1
                            messages_sent += 1
                        else:
                            total_skipped += 1
                        
                        # Update progress every 5 messages
                        if total_copied % 5 == 0:
                            await update_progress(
                                progress_msg, source['title'], source_idx, len(sources),
                                total_copied, total_skipped, i, len(messages),
                                messages_sent, limit
                            )
                        
                    except Exception as e:
                        logger.error(f"Error processing message {i} from {source['title']}: {e}")
                        total_skipped += 1
                    
                    i += 1
                
                # Source completed
                await progress_msg.edit(
                    f"✅ Completed: {source['title']}\n"
                    f"📊 Total: {total_copied} copied, {total_skipped} skipped\n"
                    f"⏰ Messages sent: {messages_sent}\n"
                    f"🔄 Moving to next source...\n"
                    f"📋 Source {source_idx + 1}/{len(sources)}"
                )
                
            except Exception as e:
                logger.error(f"Error processing source {source['title']}: {e}")
                continue
        
        # All sources completed
        completion_message = await generate_completion_message(
            rule_name, total_copied, total_skipped, 
            len(album_groups_processed), limit
        )
        await progress_msg.edit(completion_message)
        
    except Exception as e:
        logger.error(f"Error in old message copying: {e}")
        await progress_msg.edit(f"❌ Error during old message copying: {str(e)}")
    
    # Clean up
    if user_id in user_states:
        del user_states[user_id]

async def apply_rate_limiting(messages_sent, start_time, progress_msg):
    """Apply rate limiting to avoid flood waits"""
    current_time = asyncio.get_event_loop().time()
    elapsed_time = current_time - start_time
    
    # More conservative rate limiting
    if messages_sent >= 20 and elapsed_time < 60:
        # If we sent 20 messages in less than 60 seconds, wait
        wait_time = 60 - elapsed_time
        if wait_time > 0:
            logger.warning(f"Rate limiting: Sent {messages_sent} messages in {elapsed_time:.1f}s, waiting {wait_time:.1f}s")
            await progress_msg.edit(
                f"⏰ **Rate Limiting Active**\n\n"
                f"Sent {messages_sent} messages in {elapsed_time:.1f} seconds.\n"
                f"Waiting {wait_time:.1f} seconds to avoid flood wait...\n\n"
                "This protects your account from being limited."
            )
            await asyncio.sleep(wait_time)
    
    # Always have a small delay between messages
    await asyncio.sleep(1.0)  # Increased from 0.2 to 1.0 seconds

async def update_progress(progress_msg, source_title, source_idx, total_sources,
                         total_copied, total_skipped, current, total,
                         messages_sent, limit):
    """Update progress message"""
    if limit is None:
        message = (
            f"📥 Processing ALL messages from: {source_title}\n"
            f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
            f"📈 Current: {current + 1}/{total} messages\n"
            f"⏰ Messages sent: {messages_sent}\n"
            f"📋 Source {source_idx + 1}/{total_sources}"
        )
    else:
        message = (
            f"📥 Processing source: {source_title}\n"
            f"📊 Progress: {total_copied} copied, {total_skipped} skipped\n"
            f"📈 Current: {current + 1}/{total} messages\n"
            f"⏰ Messages sent: {messages_sent}\n"
            f"📋 Source {source_idx + 1}/{total_sources}"
        )
    
    await progress_msg.edit(message)

async def process_album_group(client, album_messages, destinations, 
                            whitelist_keywords, blacklist_keywords, options,
                            progress_msg, source_idx, total_sources, total_copied, total_skipped,
                            range_info=None):
    """Process an entire album group with rate limiting"""
    if not album_messages:
        return 0
    
    # Check if any message in the album passes filters
    album_passes_filter = False
    for message in album_messages:
        if await should_forward_message(message, whitelist_keywords, blacklist_keywords, options):
            album_passes_filter = True
            break
    
    if not album_passes_filter:
        return 0
    
    success_count = 0
    
    for destination in destinations:
        try:
            # Apply rate limiting for albums (albums count as multiple messages)
            current_time = asyncio.get_event_loop().time()
            await apply_rate_limiting(success_count, current_time, progress_msg)
            
            # Get destination entity
            if destination['username']:
                dest_entity = await resolve_entity_safe(client, f"@{destination['username']}")
            else:
                dest_entity = await resolve_entity_safe(client, destination['chat_id'])
            
            if not dest_entity:
                continue
            
            # Prepare files and caption
            files = []
            caption = None
            caption_entities = None
            caption_applied = False
            
            for msg in album_messages:
                # Safe attribute access
                message_text = getattr(msg, 'text', '') or ''
                message_caption = getattr(msg, 'caption', '') or ''
                message_entities = getattr(msg, 'entities', None)
                message_caption_entities = getattr(msg, 'caption_entities', None)
                has_media = hasattr(msg, 'media') and msg.media is not None
                
                if not has_media:
                    continue
                
                # Apply transformations
                transformed_text, transformed_text_entities = await apply_text_transformations(message_text, options, message_entities)
                transformed_caption, transformed_caption_entities = await apply_text_transformations(message_caption, options, message_caption_entities)
                
                # Determine which caption to use
                final_caption = transformed_caption if transformed_caption.strip() else transformed_text
                final_entities = transformed_caption_entities if transformed_caption.strip() else transformed_text_entities
                
                # Set caption only once
                if not caption_applied and final_caption.strip():
                    caption = final_caption
                    caption_entities = final_entities
                    caption_applied = True
                
                # Add media to files list
                files.append(msg.media)
            
            if files:
                # Send as album
                await client.send_file(
                    dest_entity,
                    files,
                    caption=caption,
                    caption_entities=caption_entities
                )
                success_count += 1
            
            # Additional delay for albums
            await asyncio.sleep(2.0)
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait error for album: {e.seconds} seconds")
            await progress_msg.edit(
                f"⏳ **Flood Wait Detected**\n\n"
                f"Telegram requires us to wait {e.seconds} seconds.\n"
                f"Waiting and then continuing automatically..."
            )
            await asyncio.sleep(e.seconds)
            continue
        except Exception as e:
            logger.error(f"Error copying album to {destination['title']}: {e}")
            continue
    
    return success_count

async def copy_message_to_destinations(client, message, destinations, options):
    """Copy a single message to all destinations with flood wait protection"""
    success_count = 0
    
    for destination in destinations:
        try:
            # Get destination entity
            if destination['username']:
                dest_entity = await resolve_entity_safe(client, f"@{destination['username']}")
            else:
                dest_entity = await resolve_entity_safe(client, destination['chat_id'])
            
            if not dest_entity:
                continue
            
            success = await copy_single_message_to_destination(client, message, dest_entity, options)
            
            if success:
                success_count += 1
            
            # Increased delay between destinations
            await asyncio.sleep(0.5)
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait error for {destination['title']}: {e.seconds} seconds")
            # This will be handled by the rate limiting
            raise
        except Exception as e:
            logger.error(f"Error copying to {destination['title']}: {e}")
            continue
    
    return success_count > 0

async def copy_single_message_to_destination(client, message, dest_entity, options, reply_to=None):
    """Copy a single message to a specific destination with flood wait handling"""
    try:
        # Safe attribute access
        message_text = getattr(message, 'text', '') or ''
        message_caption = getattr(message, 'caption', '') or ''
        message_entities = getattr(message, 'entities', None)
        message_caption_entities = getattr(message, 'caption_entities', None)
        has_media = hasattr(message, 'media') and message.media is not None
        
        # Check if message has any content
        has_content = has_media or message_text.strip() or message_caption.strip()
        if not has_content:
            logger.warning("Skipping empty message (no media, text, or caption)")
            return False
        
        # Apply transformations to text/caption
        transformed_text, transformed_text_entities = await apply_text_transformations(message_text, options, message_entities)
        transformed_caption, transformed_caption_entities = await apply_text_transformations(message_caption, options, message_caption_entities)
        
        # Copy message (not forward)
        if has_media:
            # For media messages, use the original media but with transformed caption
            final_caption = transformed_caption if transformed_caption.strip() else transformed_text
            final_entities = transformed_caption_entities if transformed_caption.strip() else transformed_text_entities
            
            await client.send_file(
                dest_entity,
                message.media,
                caption=final_caption if final_caption.strip() else None,
                caption_entities=final_entities,
                reply_to=reply_to
            )
        else:
            # For text messages, send as new message
            text_to_send = transformed_text if transformed_text.strip() else transformed_caption
            final_entities = transformed_text_entities if transformed_text.strip() else transformed_caption_entities
            
            if text_to_send.strip():  # Only send if not empty
                await client.send_message(
                    dest_entity,
                    text_to_send,
                    formatting_entities=final_entities,
                    link_preview=not options.get('remove_links', False),
                    reply_to=reply_to
                )
            else:
                logger.warning("Skipping empty text message after transformations")
                return False
        
        return True
        
    except FloodWaitError as e:
        logger.warning(f"Flood wait error in copy_single_message: {e.seconds} seconds")
        raise
    except Exception as e:
        logger.error(f"Error copying single message to destination: {e}")
        return False

async def generate_completion_message(rule_name, total_copied, total_skipped, albums_processed, limit):
    """Generate completion message"""
    if limit is None:
        return (
            f"✅ **All Messages Copying Completed!** 💎\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Messages Processed:** ALL messages from each source\n"
            f"**Successfully Copied:** {total_copied}\n"
            f"**Skipped:** {total_skipped}\n"
            f"**Albums Processed:** {albums_processed}\n\n"
            f"📝 **Copy Mode:** Messages were copied (not forwarded)\n"
            f"🖼️ **Album Support:** Media groups preserved\n"
            f"⏰ **Rate Limited:** Protected from flood waits\n\n"
            "Use /start_forwarding to begin real-time forwarding."
        )
    else:
        return (
            f"✅ **Old Messages Copying Completed!** 💎\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Messages Processed:** {limit} per source\n"
            f"**Successfully Copied:** {total_copied}\n"
            f"**Skipped:** {total_skipped}\n"
            f"**Albums Processed:** {albums_processed}\n\n"
            f"📝 **Copy Mode:** Messages were copied (not forwarded)\n"
            f"🖼️ **Album Support:** Media groups preserved\n"
            f"⏰ **Rate Limited:** Protected from flood waits\n\n"
            "Use /start_forwarding to begin real-time forwarding."
        )

# Add helper functions for album processing
async def get_album_messages(messages, start_index, grouped_id):
    """Get all messages that belong to the same album group"""
    album_messages = []
    
    for i in range(start_index, len(messages)):
        message = messages[i]
        if hasattr(message, 'grouped_id') and message.grouped_id == grouped_id:
            album_messages.append(message)
        else:
            break
    
    return album_messages

async def should_forward_message(message, whitelist_keywords, blacklist_keywords, options):
    """Check if a message should be forwarded based on filters"""
    # Get message text/caption
    message_text = getattr(message, 'text', '') or ''
    message_caption = getattr(message, 'caption', '') or ''
    full_text = (message_text + ' ' + message_caption).strip().lower()
    
    # Check blacklist first
    if blacklist_keywords:
        for keyword in blacklist_keywords:
            if keyword.lower() in full_text:
                return False
    
    # Check whitelist
    if whitelist_keywords:
        for keyword in whitelist_keywords:
            if keyword.lower() in full_text:
                return True
        # If whitelist exists but no matches, don't forward
        return False
    
    return True

async def apply_text_transformations(text, options, entities=None):
    """Apply text transformations based on rule options"""
    import copy

    if not text:
        return text, entities
    
    transformed = text
    new_entities = copy.deepcopy(entities) if entities else []
    
    # Remove links if option is set
    if options.get('remove_links', False) and new_entities:
        # Simple link removal - in practice you'd parse entities and remove links
        pass
    
    # Add prefix/suffix if specified
    prefix = options.get('prefix', '')
    suffix = options.get('suffix', '')
    
    if prefix:
        transformed = prefix + transformed
        # Shift entity offsets
        if new_entities:
            for entity in new_entities:
                if hasattr(entity, 'offset'):
                    entity.offset += len(prefix)

    if suffix:
        transformed = transformed + suffix
    
    return transformed, new_entities

# Add callback handlers for other options
@bot.on(events.CallbackQuery(pattern=b"old_10"))
async def old_10_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        await event.edit("🔄 Starting to copy last 10 messages...")
        await start_old_forwarding(event, user_id, user_states[user_id], 10)

@bot.on(events.CallbackQuery(pattern=b"old_50"))
async def old_50_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        await event.edit("🔄 Starting to copy last 50 messages...")
        await start_old_forwarding(event, user_id, user_states[user_id], 50)

@bot.on(events.CallbackQuery(pattern=b"old_100"))
async def old_100_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        await event.edit("🔄 Starting to copy last 100 messages...")
        await start_old_forwarding(event, user_id, user_states[user_id], 100)

@bot.on(events.CallbackQuery(pattern=b"old_all"))
async def old_all_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        await event.edit("🔄 Starting to copy ALL messages from the beginning...")
        await start_old_forwarding(event, user_id, user_states[user_id], None)

@bot.on(events.CallbackQuery(pattern=b"old_custom"))
async def old_custom_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        user_states[user_id]['mode'] = 'awaiting_custom_input'
        await event.edit(
            "🔢 **Custom Number Selection**\n\n"
            "Please enter the number of messages you want to copy:\n\n"
            "**Examples:**\n"
            "• `500` - Last 500 messages\n"
            "• `1000` - Last 1000 messages\n"
            "• `5000` - Last 5000 messages\n\n"
            "**Maximum:** 10,000 messages\n\n"
            "Enter the number:"
        )

@bot.on(events.CallbackQuery(pattern=b"old_cancel"))
async def old_cancel_handler(event):
    user_id = event.sender_id
    if user_id in user_states:
        del user_states[user_id]
    await event.edit("❌ Old message forwarding cancelled.")

# Handler for custom number input
@bot.on(events.NewMessage(pattern=r"^\d+$"))
async def custom_input_handler(event):
    user_id = event.sender_id
    
    if user_id not in user_states or user_states[user_id].get('mode') != 'awaiting_custom_input':
        return
    
    try:
        limit = int(event.text.strip())
        
        if limit <= 0:
            await event.respond("❌ Number must be positive.")
            return
        
        if limit > 10000:
            await event.respond("❌ Maximum limit is 10,000 messages.")
            return
        
        state = user_states[user_id]
        state['mode'] = 'processing_custom'
        
        await event.respond(f"✅ Starting to copy last {limit} messages...")
        await start_old_forwarding(event, user_id, state, limit)
        
    except ValueError:
        await event.respond("❌ Please enter a valid number.")


# Add this command handler after the other command handlers
@bot.on(events.NewMessage(pattern="/url_preview"))
async def url_preview_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "URL preview settings"):
        return  # Stop command execution until user stops forwarding
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current URL preview setting for this rule
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse current options
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get URL preview setting (default to True if not set)
    url_preview_enabled = options.get('url_preview', True)
    
    status = "✅ ENABLED" if url_preview_enabled else "❌ DISABLED"
    
    message = (
        f"🔗 **URL Preview Settings**\n\n"
        f"**Rule:** {rule_name}\n"
        f"**Current Status:** {status}\n\n"
        "**What this does:**\n"
        "• ✅ **Enabled**: Links will show previews (default)\n"
        "• ❌ **Disabled**: Links will show as plain text\n\n"
        "**Affects:**\n"
        "• Website links in messages\n"
        "• YouTube/Instagram/Twitter links\n"
        "• All other link previews\n\n"
        "Choose your preference:"
    )
    
    buttons = [
        [Button.inline("✅ Enable URL Previews", data="url_preview_enable")],
        [Button.inline("❌ Disable URL Previews", data="url_preview_disable")],
        [Button.inline("❌ Close", data="url_preview_close")]
    ]
    
    await event.respond(message, buttons=buttons)

# Add this callback handler after the other callback handlers
@bot.on(events.CallbackQuery(pattern=b"url_preview_"))
async def url_preview_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    if data == "url_preview_enable":
        options['url_preview'] = True
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.answer("✅ URL previews enabled!")
        
        # Show updated status
        message = (
            f"🔗 **URL Preview Settings**\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Current Status:** ✅ ENABLED\n\n"
            "Links will now show previews when forwarded."
        )
        
        buttons = [
            [Button.inline("❌ Disable URL Previews", data="url_preview_disable")],
            [Button.inline("❌ Close", data="url_preview_close")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    elif data == "url_preview_disable":
        options['url_preview'] = False
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.answer("❌ URL previews disabled!")
        
        # Show updated status
        message = (
            f"🔗 **URL Preview Settings**\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Current Status:** ❌ DISABLED\n\n"
            "Links will now be sent as plain text without previews."
        )
        
        buttons = [
            [Button.inline("✅ Enable URL Previews", data="url_preview_enable")],
            [Button.inline("❌ Close", data="url_preview_close")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    elif data == "url_preview_close":
        await event.delete()

@bot.on(events.NewMessage(pattern="/remove_links"))
async def remove_links_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "link removal settings"):
        return  # Stop command execution until user stops forwarding
    
    # Check if user is on free plan
    subscription_plan = await get_user_subscription(user_id)
    if subscription_plan == 'free':
        await event.respond(
            "❌ **Premium Feature Required**\n\n"
            "The **Remove Links** feature is only available for premium users.\n\n"
            "💎 **Upgrade to Premium to unlock:**\n"
            "• Remove all links from messages\n"
            "• Advanced message filtering\n"
            "• Higher limits and more features\n\n"
            "Click below to upgrade:",
            buttons=[[Button.inline("💎 Upgrade to Premium", data="upgrade_subscription")]]
        )
        return
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing remove_links setting for this rule
    existing_settings = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse existing options
    options = {}
    if existing_settings and existing_settings['options']:
        try:
            if isinstance(existing_settings['options'], dict):
                options = existing_settings['options']
            else:
                options = json.loads(existing_settings['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get remove_links setting
    remove_links_enabled = options.get('remove_links', False)
    
    status = "✅ **ENABLED**" if remove_links_enabled else "❌ **DISABLED**"
    
    message = (
        f"🔗 **Remove All Links Settings**\n\n"
        f"**Rule:** {rule_name}\n"
        f"**Current Status:** {status}\n\n"
        "**What this does:**\n"
        "• ✅ **Enabled**: All links will be removed from messages before forwarding\n"
        "• ❌ **Disabled**: Links will be preserved (default)\n\n"
        "**Affects:**\n"
        "• Website links (http://, https://)\n"
        "• Telegram links (t.me, telegram.me)\n"
        "• Email addresses\n"
        "• All other URLs in text and captions\n\n"
        "**Examples:**\n"
        "• `Check this: https://example.com` → `Check this: `\n"
        "• `Join @channel and visit t.me/group` → `Join @channel and visit `\n"
        "• `Contact: email@example.com` → `Contact: `\n\n"
        "💎 **Premium Feature** - Thank you for being a premium user!\n\n"
        "Choose your preference:"
    )
    
    buttons = [
        [Button.inline("✅ Enable Remove Links", data="remove_links_enable")],
        [Button.inline("❌ Disable Remove Links", data="remove_links_disable")],
        [Button.inline("❌ Close", data="remove_links_close")]
    ]
    
    await event.respond(message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"remove_links_"))
async def remove_links_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    # Check if user is on free plan (in case they somehow bypassed the command check)
    subscription_plan = await get_user_subscription(user_id)
    if subscription_plan == 'free':
        await event.answer("❌ This feature requires a premium subscription!", alert=True)
        return
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    if data == "remove_links_enable":
        options['remove_links'] = True
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.answer("✅ Remove links enabled!")
        
        # Show updated status
        message = (
            f"🔗 **Remove All Links Settings**\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Current Status:** ✅ ENABLED\n\n"
            "All links will now be removed from messages before forwarding.\n\n"
            "**Note:** For Apply Remove Links Filter /stop_forwarding and /start_forwarding again\n\n"
            "💎 **Premium Feature Active**"
        )
        
        buttons = [
            [Button.inline("❌ Disable Remove Links", data="remove_links_disable")],
            [Button.inline("❌ Close", data="remove_links_close")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    elif data == "remove_links_disable":
        options['remove_links'] = False
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.answer("❌ Remove links disabled!")
        
        # Show updated status
        message = (
            f"🔗 **Remove All Links Settings**\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Current Status:** ❌ DISABLED\n\n"
            "Links will be preserved in forwarded messages.\n\n"
            "💎 **Premium Feature Available**"
        )
        
        buttons = [
            [Button.inline("✅ Enable Remove Links", data="remove_links_enable")],
            [Button.inline("❌ Close", data="remove_links_close")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    elif data == "remove_links_close":
        await event.delete()

def remove_all_links(text):
    """Remove all links from text"""
    if not text:
        return text
    
    import re
    
    # More comprehensive link patterns
    patterns = [
        # URLs with http/https
        r'https?://[^\s]+',
        # URLs without protocol
        r'www\.[^\s]+',
        # Telegram links
        r't\.me/[^\s]+',
        r'telegram\.me/[^\s]+',
        r't\.me/\+[^\s]+',  # Private links
        # Email addresses
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        # Generic URL patterns
        r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*'
    ]
    
    cleaned_text = text
    
    for pattern in patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    
    return cleaned_text.strip()

@bot.on(events.NewMessage(pattern="/replace_text"))
async def replace_text_cmd(event):
    user_id = event.sender_id
    db = await get_db()
    
    # Check if user is logged in
    user_row = await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user_row or not user_row.get("session"):
        await event.respond("❌ Not logged in. Use /login first.")
        return
    
    # ASK USER TO STOP FORWARDING BEFORE RULE CREATION
    if await ask_user_to_stop_forwarding(user_id, "text replacement settings"):
        return  # Stop command execution until user stops forwarding
    
    # Check if user is on free plan
    subscription_plan = await get_user_subscription(user_id)
    if subscription_plan == 'free':
        await event.respond(
            "❌ **Premium Feature Required**\n\n"
            "The **Text Replacement** feature is only available for premium users.\n\n"
            "💎 **Upgrade to Premium to unlock:**\n"
            "• Replace specific text in messages\n"
            "• Replace all text in messages\n"
            "• Advanced text processing\n\n"
            "Click below to upgrade:",
            buttons=[[Button.inline("💎 Upgrade to Premium", data="upgrade_subscription")]]
        )
        return
    
    # Get current rule
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get existing text replacement settings for this rule
    existing_settings = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    # Parse existing options
    options = {}
    if existing_settings and existing_settings['options']:
        try:
            if isinstance(existing_settings['options'], dict):
                options = existing_settings['options']
            else:
                options = json.loads(existing_settings['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    # Get text replacement settings
    text_replacements = options.get('text_replacements', {})
    replace_all_text = options.get('replace_all_text', {'enabled': False, 'replacement': ''})
    
    # Count active replacements
    active_specific = len([k for k, v in text_replacements.items() if v])  # Only count non-empty replacements
    
    status_message = (
        f"🔤 **Text Replacement Settings**\n\n"
        f"**Rule:** {rule_name}\n\n"
        f"📊 **Current Status:**\n"
        f"• Specific Text Replacements: {active_specific} active\n"
        f"• Replace All Text: {'✅ ENABLED' if replace_all_text.get('enabled') else '❌ DISABLED'}\n\n"
    )
    
    if replace_all_text.get('enabled'):
        status_message += f"🔁 **Replace All Text With:** `{replace_all_text.get('replacement', '')}`\n\n"
    
    if active_specific > 0:
        status_message += "📝 **Active Specific Replacements:**\n"
        count = 0
        for original, replacement in list(text_replacements.items())[:3]:
            if replacement:  # Only show non-empty replacements
                status_message += f"• `{original}` → `{replacement}`\n"
                count += 1
                if count >= 3:
                    break
        if active_specific > 3:
            status_message += f"• ... and {active_specific - 3} more\n"
        status_message += "\n"
    
    status_message += (
        "💡 **Available Options:**\n\n"
        "1. **Replace Specific Text**\n"
        "   • Replace specific words/phrases with custom text\n"
        "   • Multiple replacements can be configured\n"
        "   • Case-sensitive matching\n\n"
        "2. **Replace All Text**\n"
        "   • Replace ALL text in messages with custom text\n"
        "   • Useful for forwarding only media with custom captions\n"
        "   • Overrides specific text replacements\n\n"
        "💎 **Premium Feature** - Thank you for being a premium user!"
    )
    
    buttons = [
        [Button.inline("🔤 Replace Specific Text", data="text_specific")],
        [Button.inline("🔄 Replace All Text", data="text_all")],
        [Button.inline("🧹 Clear All Settings", data="text_clear")],
        [Button.inline("📋 View Current", data="text_view")],
        [Button.inline("❌ Close", data="text_close")]
    ]
    
    await event.respond(status_message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"text_"))
async def text_replacement_callback(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    # Check if user is on free plan
    subscription_plan = await get_user_subscription(user_id)
    if subscription_plan == 'free':
        await event.answer("❌ This feature requires a premium subscription!", alert=True)
        return
    
    db = await get_db()
    rule_id, rule_name = await get_current_rule(user_id)
    
    # Get current options
    rule_options = await db.fetchrow(
        "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
        user_id, rule_id
    )
    
    options = {}
    if rule_options and rule_options['options']:
        try:
            if isinstance(rule_options['options'], dict):
                options = rule_options['options']
            else:
                options = json.loads(rule_options['options'])
        except (json.JSONDecodeError, TypeError):
            options = {}
    
    if data == "text_specific":
        await event.edit(
            "🔤 **Replace Specific Text**\n\n"
            "Please send the text replacement in one of these formats:\n\n"
            "**Format 1:** Simple replacement\n"
            "`original_text -> replacement_text`\n\n"
            "**Format 2:** Multiple replacements\n"
            "`text1->new1, text2->new2, text3->new3`\n\n"
            "**Format 3:** Bulk import\n"
            "Send a text file with one replacement per line:\n"
            "`original1 -> new1`\n"
            "`original2 -> new2`\n\n"
            "**Examples:**\n"
            "`hello -> hi`\n"
            "`world -> earth`\n"
            "`example.com -> mysite.com`\n\n"
            "📝 **Notes:**\n"
            "• Use `->` as separator\n"
            "• For multiple, separate with commas\n"
            "• Case-sensitive matching\n\n"
            "Send 'cancel' to go back.",
            buttons=[Button.inline("⬅️ Back", data="text_back")]
        )
        
        user_states[user_id] = {
            'mode': 'text_replacement_specific',
            'rule_id': rule_id,
            'options': options,
            'rule_name': rule_name  # ADD THIS LINE
        }
        
    elif data == "text_all":
        current_setting = options.get('replace_all_text', {'enabled': False, 'replacement': ''})
        current_text = current_setting.get('replacement', '')
        
        if current_setting.get('enabled'):
            status = "✅ Currently replacing ALL text with"
            buttons = [
                [Button.inline("✏️ Change Replacement Text", data="text_change_all")],
                [Button.inline("🛑 Disable Replace All", data="text_disable_all")],
                [Button.inline("⬅️ Back", data="text_back")]
            ]
        else:
            status = "❌ Currently not replacing all text"
            buttons = [
                [Button.inline("🚀 Enable Replace All", data="text_enable_all")],
                [Button.inline("⬅️ Back", data="text_back")]
            ]
        
        await event.edit(
            f"🔄 **Replace All Text**\n\n"
            f"**Status:** {status}\n"
            f"**Current Text:** `{current_text}`\n\n"
            "**What this does:**\n"
            "• Replaces ALL text in messages with your custom text\n"
            "• Useful for forwarding only media with custom captions\n"
            "• Overrides specific text replacements\n"
            "• Works with both text messages and media captions\n\n"
            "**Examples:**\n"
            "• Original: `Hello world!` → New: `Check this out!`\n"
            "• Original: `Long caption text...` → New: `Posted by my channel`\n"
            "• Media with caption → Media with your custom caption\n\n"
            "Choose an option:",
            buttons=buttons
        )
        
    elif data == "text_enable_all":
        await event.edit(
            "🔄 **Enable Replace All Text**\n\n"
            "Please send the text that ALL messages will be replaced with:\n\n"
            "**Examples:**\n"
            "• `Posted by my channel`\n"
            "• `Check this out!`\n"
            "• `Follow for more content`\n\n"
            "You can use emojis and formatting.\n\n"
            "Send the replacement text now, or 'cancel' to go back:"
        )
        
        # In the text_enable_all and text_change_all sections:
        user_states[user_id] = {
            'mode': 'text_enable_all',  # or 'text_change_all'
            'rule_id': rule_id,
            'options': options,
            'rule_name': rule_name  # ADD THIS LINE
        }
        
    elif data == "text_change_all":
        current_setting = options.get('replace_all_text', {'enabled': False, 'replacement': ''})
        current_text = current_setting.get('replacement', '')
        
        await event.edit(
            f"✏️ **Change Replacement Text**\n\n"
            f"Current replacement text: `{current_text}`\n\n"
            "Send the new text that ALL messages will be replaced with:\n\n"
            "Send the new text now, or 'cancel' to go back:"
        )
        
        user_states[user_id] = {
            'mode': 'text_change_all',
            'rule_id': rule_id,
            'options': options
        }
        
    elif data == "text_disable_all":
        if 'replace_all_text' in options:
            options['replace_all_text']['enabled'] = False
            
            await db.execute(
                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                json.dumps(options), user_id, rule_id
            )
            
            await event.answer("🛑 Replace All Text disabled!")
            
            # Return to main menu
            await replace_text_cmd(event)
        else:
            await event.answer("❌ Replace All Text is not enabled!", alert=True)
            
    elif data == "text_clear":
        text_replacements = options.get('text_replacements', {})
        replace_all_text = options.get('replace_all_text', {'enabled': False})
        
        has_settings = text_replacements or replace_all_text.get('enabled')
        
        if not has_settings:
            await event.answer("❌ No text replacement settings to clear!", alert=True)
            return
            
        buttons = [
            [Button.inline("✅ Yes, Clear All", data="text_confirm_clear")],
            [Button.inline("❌ Cancel", data="text_back")]
        ]
        
        message = "🗑️ **Clear All Text Replacement Settings**\n\n"
        
        if text_replacements:
            message += f"• {len(text_replacements)} specific text replacement(s)\n"
        if replace_all_text.get('enabled'):
            message += f"• Replace All Text setting\n"
            
        message += "\nAre you sure you want to clear ALL text replacement settings?\nThis action cannot be undone!"
        
        await event.edit(message, buttons=buttons)
        
    elif data == "text_confirm_clear":
        # Clear all text replacement settings
        if 'text_replacements' in options:
            del options['text_replacements']
        if 'replace_all_text' in options:
            options['replace_all_text'] = {'enabled': False, 'replacement': ''}
            
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        await event.edit(
            "✅ All text replacement settings cleared!\n\n"
            "Text replacement has been disabled for this rule.",
            buttons=[[Button.inline("⬅️ Back to Manager", data="text_back")]]
        )
        
    elif data == "text_view":
        text_replacements = options.get('text_replacements', {})
        replace_all_text = options.get('replace_all_text', {'enabled': False, 'replacement': ''})
        
        if not text_replacements and not replace_all_text.get('enabled'):
            await event.answer("❌ No text replacements to view!", alert=True)
            return
            
        message = "📋 **Current Text Replacements**\n\n"
        
        if replace_all_text.get('enabled'):
            message += f"🔄 **Replace All Text:**\n"
            message += f"• ALL text → `{replace_all_text.get('replacement', '')}`\n\n"
        
        if text_replacements:
            active_replacements = {k: v for k, v in text_replacements.items() if v}
            if active_replacements:
                message += f"🔤 **Specific Replacements ({len(active_replacements)}):**\n"
                for original, replacement in list(active_replacements.items())[:10]:
                    message += f"• `{original}` → `{replacement}`\n"
                if len(active_replacements) > 10:
                    message += f"• ... and {len(active_replacements) - 10} more\n"
        
        buttons = [[Button.inline("⬅️ Back", data="text_back")]]
        await event.edit(message, buttons=buttons)
        
    elif data == "text_close":
        await event.delete()
        
    elif data == "text_back":
        # Return to main menu
        await replace_text_cmd(event)

@bot.on(events.NewMessage)
@bot.on(events.NewMessage)
async def handle_text_replacement_input(event):
    user_id = event.sender_id
    
    if user_id not in user_states:
        return
        
    state = user_states[user_id]
    mode = state.get('mode')
    text = event.raw_text.strip()
    
    if text.lower() == 'cancel':
        await event.respond("❌ Cancelled text replacement setup.")
        del user_states[user_id]
        return
    
    # Safely get rule_id with fallback
    rule_id = state.get('rule_id')
    if not rule_id:
        # If rule_id is missing, get current rule
        rule_id, rule_name = await get_current_rule(user_id)
        state['rule_id'] = rule_id  # Store it for future use
    
    db = await get_db()
    options = state.get('options', {})
    
    # Get the rule name for the response
    rule_id_from_db, rule_name = await get_current_rule(user_id)
    
    if mode == 'text_replacement_specific':
        # Check if it's a file (bulk import)
        if event.message.media and event.message.document:
            try:
                file = await event.download_media()
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                os.remove(file)
                
                replacements = parse_bulk_text_replacements(content)
                
            except Exception as e:
                await event.respond(f"❌ Error reading file: {e}")
                return
        else:
            # Parse text input
            replacements = parse_text_replacements_text(text)
        
        if not replacements:
            await event.respond(
                "❌ Invalid format. Please use:\n"
                "• `original -> replacement`\n"
                "• `text1->new1, text2->new2`\n"
                "Or send a text file with one replacement per line."
            )
            return
        
        # Get current replacements
        text_replacements = options.get('text_replacements', {})
        
        # Add new replacements
        added_count = 0
        updated_count = 0
        
        for original, replacement in replacements.items():
            if original in text_replacements:
                updated_count += 1
            else:
                added_count += 1
            text_replacements[original] = replacement
        
        # Save to database
        options['text_replacements'] = text_replacements
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        # Prepare response message
        response = f"✅ **Text Replacements Updated for '{rule_name}'**\n\n"
        
        if added_count > 0:
            response += f"➕ **Added:** {added_count} new replacement(s)\n"
        if updated_count > 0:
            response += f"✏️ **Updated:** {updated_count} replacement(s)\n"
        
        response += f"\n📊 **Total Active:** {len(text_replacements)} replacement(s)\n\n"
        
        # Show some of the added replacements
        if added_count > 0 or updated_count > 0:
            response += "**Recent Changes:**\n"
            count = 0
            for original, replacement in replacements.items():
                response += f"• `{original}` → `{replacement}`\n"
                count += 1
                if count >= 3:
                    break
            if (added_count + updated_count) > 3:
                response += f"• ... and {(added_count + updated_count) - 3} more\n"
        
        buttons = [
            [Button.inline("📋 View All", data="text_view")],
            [Button.inline("⬅️ Back to Manager", data="text_back")]
        ]
        
        await event.respond(response, buttons=buttons)
        del user_states[user_id]
        
    elif mode in ['text_enable_all', 'text_change_all']:
        if not text.strip():
            await event.respond("❌ Replacement text cannot be empty. Please try again or send 'cancel'.")
            return
        
        # Enable or update replace all text
        options['replace_all_text'] = {
            'enabled': True,
            'replacement': text
        }
        
        await db.execute(
            "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
            json.dumps(options), user_id, rule_id
        )
        
        if mode == 'text_enable_all':
            action = "enabled"
        else:
            action = "updated"
        
        response = (
            f"✅ **Replace All Text {action}!**\n\n"
            f"**Rule:** {rule_name}\n"
            f"**Replacement Text:** `{text}`\n\n"
            "Now ALL text in forwarded messages will be replaced with your custom text.\n\n"
            "**Note:** For Apply Text Replace Filter /stop_forwarding and /start_forwarding again\n\n"
            "💎 **Premium Feature Active**"
        )
        
        buttons = [
            [Button.inline("⚙️ Manage Settings", data="text_back")],
            [Button.inline("❌ Close", data="text_close")]
        ]
        
        await event.respond(response, buttons=buttons)
        del user_states[user_id]

def parse_text_replacements_text(text):
    """Parse text replacement text input"""
    replacements = {}
    
    # Check for multiple replacements separated by commas
    if ',' in text:
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if '->' in part:
                original, replacement = part.split('->', 1)
                original = original.strip()
                replacement = replacement.strip()
                if original:
                    replacements[original] = replacement
    else:
        # Single replacement
        if '->' in text:
            original, replacement = text.split('->', 1)
            original = original.strip()
            replacement = replacement.strip()
            if original:
                replacements[original] = replacement
    
    return replacements

def parse_bulk_text_replacements(content):
    """Parse bulk text replacements from file content"""
    replacements = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if line and '->' in line:
            original, replacement = line.split('->', 1)
            original = original.strip()
            replacement = replacement.strip()
            if original:
                replacements[original] = replacement
    
    return replacements

def replace_text_in_message(message_text, text_replacements, replace_all_text):
    """Apply text replacements to message text"""
    if not message_text:
        return message_text
    
    # If replace all text is enabled, return the replacement text
    if replace_all_text.get('enabled'):
        return replace_all_text.get('replacement', '')
    
    # Apply specific text replacements
    replaced_text = message_text
    for original, replacement in text_replacements.items():
        if original and replacement:
            replaced_text = replaced_text.replace(original, replacement)
    
    return replaced_text

@bot.on(events.NewMessage(pattern="/fix_limits"))
async def fix_limits_cmd(event):
    """Command to automatically fix subscription limit issues"""
    user_id = event.sender_id
    
    # Check compliance first
    is_compliant, message = await check_subscription_compliance(user_id)
    
    if is_compliant:
        await event.respond("✅ Your account is already compliant with your subscription limits.")
        return
    
    # Fix the issues
    issues = await enforce_subscription_limits(user_id)
    
    if issues:
        response = "🔧 **Fixed the following limit issues:**\n\n"
        for issue in issues:
            response += f"• {issue}\n"
        response += "\n✅ Your account is now compliant with your subscription plan."
        
        # Show current status
        subscription_plan = await get_user_subscription(user_id)
        limits = SUBSCRIPTION_LIMITS[subscription_plan]
        
        db = await get_db()
        rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
        active_rules = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
        
        response += f"\n\n📊 **Current Status:**\n"
        response += f"• Plan: {subscription_plan.upper()}\n"
        response += f"• Rules: {active_rules}/{rules_count} active ({limits['max_rules']} allowed)\n"
        
    else:
        response = "❌ No issues found to fix. Your account appears to be compliant."
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/check_compliance"))
async def check_compliance_cmd(event):
    """Check if account is compliant with subscription limits"""
    user_id = event.sender_id
    
    is_compliant, message = await check_subscription_compliance(user_id)
    subscription_plan = await get_user_subscription(user_id)
    
    if is_compliant:
        response = f"✅ **Compliant with {subscription_plan.upper()} Plan**\n\n"
        response += "Your account configuration meets all subscription limits."
    else:
        response = f"❌ **Not Compliant with {subscription_plan.upper()} Plan**\n\n"
        response += f"**Issue:** {message}\n\n"
        response += "Use /fix_limits to automatically resolve these issues."
    
    # Add current usage summary
    db = await get_db()
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    
    total_rules = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    active_rules = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
    
    response += f"\n📊 **Current Usage:**\n"
    response += f"• Rules: {active_rules}/{total_rules} active ({limits['max_rules']} allowed)\n"
    
    # Check subscription expiry
    sub_info = await db.fetchrow("SELECT * FROM subscriptions WHERE user_id=$1", user_id)
    if sub_info and sub_info['expires_at']:
        days_until_expiry = (sub_info['expires_at'] - datetime.now()).days
        if days_until_expiry <= SUBSCRIPTION_WARNING_DAYS:
            if days_until_expiry > 0:
                response += f"⏰ **Expires in:** {days_until_expiry} days\n"
            else:
                response += f"❌ **Expired:** {abs(days_until_expiry)} days ago\n"
    
    await event.respond(response)

@bot.on(events.NewMessage(pattern="/usage"))
async def usage_cmd(event):
    """Show detailed usage analytics"""
    user_id = event.sender_id
    subscription_plan = await get_user_subscription(user_id)
    limits = SUBSCRIPTION_LIMITS[subscription_plan]
    
    db = await get_db()
    
    # Get usage stats
    total_rules = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
    active_rules = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
    
    # Get sources/destinations per rule
    rules_usage = []
    rules = await db.fetch("SELECT * FROM rules WHERE user_id=$1 ORDER BY is_active DESC, rule_id", user_id)
    
    for rule in rules:
        sources_count = await db.fetchval(
            "SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2",
            user_id, rule['rule_id']
        )
        destinations_count = await db.fetchval(
            "SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2",
            user_id, rule['rule_id']
        )
        
        rules_usage.append({
            'name': rule['name'],
            'sources': sources_count,
            'destinations': destinations_count,
            'active': rule['is_active']
        })
    
    # Get activity stats
    activity = await db.fetchrow("SELECT * FROM user_activity WHERE user_id=$1", user_id)
    
    response = f"📊 **Usage Analytics**\n\n"
    response += f"📋 **Plan:** {subscription_plan.upper()}\n"
    response += f"📈 **Rules:** {active_rules}/{total_rules} active ({limits['max_rules']} allowed)\n\n"
    
    response += "🔧 **Per Rule Usage:**\n"
    for usage in rules_usage:
        status = "✅" if usage['active'] else "❌"
        response += f"{status} **{usage['name']}:** {usage['sources']} sources, {usage['destinations']} destinations\n"
    
    if activity:
        last_active = activity['last_activity'].strftime("%Y-%m-%d %H:%M")
        response += f"\n📅 **Last Active:** {last_active}\n"
        response += f"🔄 **Commands Used:** {activity['command_count']}\n"
        response += f"👀 **First Seen:** {activity['first_seen'].strftime('%Y-%m-%d')}\n"
    
    # Check compliance
    is_compliant, compliance_msg = await check_subscription_compliance(user_id)
    if not is_compliant:
        response += f"\n⚠️ **Compliance Issue:** {compliance_msg}\n"
        response += "Use /fix_limits to resolve automatically.\n"
    
    # Add upgrade suggestion if near limits
    if subscription_plan == 'free' and (total_rules >= limits['max_rules'] - 1):
        response += "\n💡 **You're approaching free plan limits!**\n"
        response += "Consider upgrading for more capacity.\n"
    
    await event.respond(response)
   
# ---------------- CALLBACK HANDLER ----------------
@bot.on(events.CallbackQuery(pattern=b"check_compliance"))
async def check_compliance_callback(event):
    """Callback for checking compliance"""
    user_id = event.sender_id
    await event.answer("Checking compliance...")
    await check_compliance_cmd(event)

@bot.on(events.CallbackQuery(pattern=b"start_after_fix"))
async def start_after_fix_callback(event):
    """Callback to start forwarding after fixing limits"""
    user_id = event.sender_id
    
    # Check compliance first
    is_compliant, compliance_msg = await check_subscription_compliance(user_id)
    
    if not is_compliant:
        await event.answer(f"Still not compliant: {compliance_msg}", alert=True)
        return
    
    # Check if user has sources and destinations
    db = await get_db()
    sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1", user_id)
    destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1", user_id)
    
    if not sources or not destinations:
        await event.answer("Please configure sources and destinations first", alert=True)
        return
    
    # Start forwarding
    if user_id in forwarding_tasks:
        task = forwarding_tasks[user_id]
        if not task.done():
            await event.answer("Forwarding is already running", alert=True)
            return
    
    task = asyncio.create_task(forward_messages(user_id))
    forwarding_tasks[user_id] = task
    
    # Update database status
    await db.execute("""
        UPDATE forwarding_status SET is_active=TRUE, last_started=CURRENT_TIMESTAMP 
        WHERE user_id=$1
    """, user_id)
    
    await event.edit("✅ Forwarding Started Successfully! 🚀")

@bot.on(events.CallbackQuery(pattern=b"view_rules_after_limit"))
async def view_rules_after_limit_callback(event):
    user_id = event.sender_id
    await event.answer("Showing your current rules...")
    await rules_cmd(event)
    
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    if user_id not in user_states and not data.startswith(('upgrade_', 'back_to_')):
        await event.answer("Session expired. Please start again.")
        return
    
    # Handle subscription upgrade
    if data == "upgrade_subscription":
        await event.answer("Redirecting to payment bot...")
        
        # Create a deep link to your payment bot with user ID
        deep_link = f"https://t.me/{PAYMENT_BOT_USERNAME[1:]}?start=user_{user_id}"
        
        # Send message with payment options
        payment_message = (
            "💎 **Upgrade Your Plan**\n\n"
            "Choose your payment method:\n\n"
            "🇮🇳 **UPI Payment**\n"
            "• PhonePe/GPay/PayTM:\n\n"
            "📱 **Scan QR Code**\n"
            "🌎 **PayPal**\n"
            "Click the button below to proceed with payment:"
        )
        
        buttons = [
            [Button.url("💳 Proceed to Payment", deep_link)],
            [Button.inline("⬅️ Back", data="back_to_subscription")]
        ]
        
        await event.edit(payment_message, buttons=buttons)
        return
    
    # Handle back to subscription
    elif data == "back_to_subscription":
        # Go back to subscription info
        subscription_plan = await get_user_subscription(user_id)
        limits = SUBSCRIPTION_LIMITS[subscription_plan]
        
        db = await get_db()
        rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1", user_id)
        rule_id, rule_name = await get_current_rule(user_id)
        sources_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        destinations_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
        
        sub_info = await db.fetchrow("SELECT * FROM subscriptions WHERE user_id=$1", user_id)
        expiry_info = ""
        if sub_info and sub_info['expires_at']:
            expiry_date = sub_info['expires_at'].strftime("%Y-%m-%d")
            expiry_info = f"\n⏰ Expires on: {expiry_date}"
        
        response = f"📋 **Your Subscription Plan:** {subscription_plan.upper()}{expiry_info}\n\n"
        response += f"📊 **Current Usage:**\n"
        response += f"• Rules: {rules_count}/{limits['max_rules']}\n"
        response += f"• Sources (current rule): {sources_count}/{limits['max_sources_per_rule']}\n"
        response += f"• Destinations (current rule): {destinations_count}/{limits['max_destinations_per_rule']}\n\n"
        
        response += "💎 **Premium Features:**\n"
        response += "• Unlimited rules\n" if subscription_plan != 'free' else "• Up to 20 rules\n"
        response += "• Up to 50 sources per rule\n" if subscription_plan != 'free' else "• Up to 5 sources per rule\n"
        response += "• Up to 50 destinations per rule\n" if subscription_plan != 'free' else "• Up to 5 destinations per rule\n"
        response += "• Priority support\n\n" if subscription_plan != 'free' else "• Standard support\n\n"
        
        if subscription_plan == 'free':
            buttons = [[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
            await event.edit(response, buttons=buttons)
        else:
            await event.edit(response)
        return
    
    state = user_states[user_id]
    
    # Handle source selection
    if state.get('mode') == 'source_selection':
        if data.startswith('sel_'):
            # Handle number selection for sources
            idx = int(data.split('_')[1]) - 1
            dialogs = state['dialogs']
            page = state.get('page', 0)
            
            # Calculate actual index based on page
            actual_idx = page * 10 + idx
            
            if 0 <= actual_idx < len(dialogs):
                dialog = dialogs[actual_idx]
                # Initialize selected list if not exists
                if 'selected' not in state:
                    state['selected'] = []
                # Toggle selection (multiple sources allowed)
                if dialog['id'] in state['selected']:
                    state['selected'].remove(dialog['id'])
                    await event.answer(f"Unselected {dialog['title']}")
                else:
                    # Check subscription limit before adding
                    db = await get_db()
                    rule_id, rule_name = await get_current_rule(user_id)
                    current_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
                    
                    subscription_plan = await get_user_subscription(user_id)
                    max_limit = SUBSCRIPTION_LIMITS[subscription_plan]['max_sources_per_rule']
                    
                    if current_count >= max_limit:
                        await event.answer(
                            f"❌ Limit reached! Free plan allows only {max_limit} sources per rule. Upgrade to add more.",
                            alert=True
                        )
                        return
                    
                    state['selected'].append(dialog['id'])
                    await event.answer(f"Selected {dialog['title']}")
                
                # Update message to show selection status
                await update_source_selection_message(event)
                
        elif data == 'nav_prev':
            # Go to previous page
            if state.get('page', 0) > 0:
                state['page'] = state.get('page', 0) - 1
                await update_source_selection_message(event)
            else:
                await event.answer("You're on the first page")
                
        elif data == 'nav_next':
            # Go to next page
            total_pages = (len(state['dialogs']) + 9) // 10
            if state.get('page', 0) < total_pages - 1:
                state['page'] = state.get('page', 0) + 1
                await update_source_selection_message(event)
            else:
                await event.answer("You're on the last page")
                
        elif data == 'done_sel':
            # Process selected sources
            selected = state.get('selected', [])
            if not selected:
                await event.answer("No sources selected!")
            else:
                # Check subscription limit before saving
                db = await get_db()
                rule_id = state.get('current_rule', 'default')
                rule_name = state.get('rule_name', 'Default Rule')
                
                current_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
                subscription_plan = await get_user_subscription(user_id)
                max_limit = SUBSCRIPTION_LIMITS[subscription_plan]['max_sources_per_rule']
                
                if current_count + len(selected) > max_limit:
                    await event.answer(
                        f"❌ Cannot add {len(selected)} sources. Free plan allows only {max_limit} sources per rule. "
                        f"Current: {current_count}, Limit: {max_limit}",
                        alert=True
                    )
                    
                    # Show upgrade button
                    buttons = [[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
                    await event.edit(
                        f"❌ **Subscription Limit Reached**\n\n"
                        f"You're trying to add {len(selected)} sources, but your free plan only allows {max_limit} sources per rule.\n\n"
                        f"Current: {current_count}/{max_limit}\n\n"
                        f"💎 Upgrade to Premium for up to 50 sources per rule!",
                        buttons=buttons
                    )
                    return
                
                # Save selections and proceed
                await save_selected_sources(user_id, rule_id, selected)
                await event.edit(f"✅ {len(selected)} sources saved for rule '{rule_name}'!")
                del user_states[user_id]
    
    # Handle destination selection (multiple selection like sources)
    elif state.get('mode') == 'destination_selection':
        if data.startswith('sel_'):
            # Handle number selection for destinations
            idx = int(data.split('_')[1]) - 1
            dialogs = state['dialogs']
            page = state.get('page', 0)
            
            # Calculate actual index based on page
            actual_idx = page * 10 + idx
            
            if 0 <= actual_idx < len(dialogs):
                dialog = dialogs[actual_idx]
                # Initialize selected list if not exists
                if 'selected' not in state:
                    state['selected'] = []
                # Toggle selection (multiple destinations allowed)
                if dialog['id'] in state['selected']:
                    state['selected'].remove(dialog['id'])
                    await event.answer(f"Unselected {dialog['title']}")
                else:
                    # Check subscription limit before adding
                    db = await get_db()
                    rule_id, rule_name = await get_current_rule(user_id)
                    current_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
                    
                    subscription_plan = await get_user_subscription(user_id)
                    max_limit = SUBSCRIPTION_LIMITS[subscription_plan]['max_destinations_per_rule']
                    
                    if current_count >= max_limit:
                        await event.answer(
                            f"❌ Limit reached! Free plan allows only {max_limit} destinations per rule. Upgrade to add more.",
                            alert=True
                        )
                        return
                    
                    state['selected'].append(dialog['id'])
                    await event.answer(f"Selected {dialog['title']}")
                
                # Update message to show selection status
                await update_destination_selection_message(event)
                
        elif data == 'nav_prev':
            # Go to previous page
            if state.get('page', 0) > 0:
                state['page'] = state.get('page', 0) - 1
                await update_destination_selection_message(event)
            else:
                await event.answer("You're on the first page")
                
        elif data == 'nav_next':
            # Go to next page
            total_pages = (len(state['dialogs']) + 9) // 10
            if state.get('page', 0) < total_pages - 1:
                state['page'] = state.get('page', 0) + 1
                await update_destination_selection_message(event)
            else:
                await event.answer("You're on the last page")
                
        elif data == 'done_sel':
            # Process selected destinations
            selected = state.get('selected', [])
            if not selected:
                await event.answer("No destinations selected!")
            else:
                # Check subscription limit before saving
                db = await get_db()
                rule_id = state.get('current_rule', 'default')
                rule_name = state.get('rule_name', 'Default Rule')
                
                current_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, rule_id)
                subscription_plan = await get_user_subscription(user_id)
                max_limit = SUBSCRIPTION_LIMITS[subscription_plan]['max_destinations_per_rule']
                
                if current_count + len(selected) > max_limit:
                    await event.answer(
                        f"❌ Cannot add {len(selected)} destinations. Free plan allows only {max_limit} destinations per rule. "
                        f"Current: {current_count}, Limit: {max_limit}",
                        alert=True
                    )
                    
                    # Show upgrade button
                    buttons = [[Button.inline("💎 Upgrade Plan", data="upgrade_subscription")]]
                    await event.edit(
                        f"❌ **Subscription Limit Reached**\n\n"
                        f"You're trying to add {len(selected)} destinations, but your free plan only allows {max_limit} destinations per rule.\n\n"
                        f"Current: {current_count}/{max_limit}\n\n"
                        f"💎 Upgrade to Premium for up to 50 destinations per rule!",
                        buttons=buttons
                    )
                    return
                
                # Save selections and proceed
                await save_selected_destinations(user_id, rule_id, selected)
                await event.edit(f"✅ {len(selected)} destinations saved for rule '{rule_name}'!")
                del user_states[user_id]
    
    # Handle rule selection for edit/delete/toggle/set_current
    elif state.get('mode') == 'rule_selection':
        rules = state['rules']
        action = state['action']
        
        if data == "prev":
            state['page'] = max(0, state.get('page', 0) - 1)
            await update_rule_selection_message(event, state, rules, action)
            
        elif data == "next":
            items_per_page = 10
            max_page = (len(rules) - 1) // items_per_page
            state['page'] = min(max_page, state.get('page', 0) + 1)
            await update_rule_selection_message(event, state, rules, action)
            
        else:
            # Handle rule selection
            try:
                index = int(data) - 1
                items_per_page = 10
                actual_index = state.get('page', 0) * items_per_page + index
                
                if 0 <= actual_index < len(rules):
                    selected_rule = rules[actual_index]
                    db = await get_db()
                    
                    if action == 'edit':
                        # Set this as the current rule
                        user_states[user_id] = {
                            'current_rule': selected_rule['id'],
                            'rule_name': selected_rule['title']
                        }
                        await event.respond(f"✅ Now editing rule: {selected_rule['title']}\n\nUse /source and /destination to configure this rule.")
                        
                    elif action == 'delete':
                        # Delete the rule and all associated sources/destinations
                        await db.execute("DELETE FROM rules WHERE user_id=$1 AND rule_id=$2", user_id, selected_rule['id'])
                        await db.execute("DELETE FROM sources WHERE user_id=$1 AND rule_id=$2", user_id, selected_rule['id'])
                        await db.execute("DELETE FROM destinations WHERE user_id=$1 AND rule_id=$2", user_id, selected_rule['id'])
                        await db.execute("DELETE FROM keyword_filters WHERE user_id=$1 AND rule_id=$2", user_id, selected_rule['id'])
                        await event.respond(f"✅ Rule '{selected_rule['title']}' deleted successfully!")
                        
                    elif action == 'toggle':
                        # Get current subscription info
                        subscription_plan = await get_user_subscription(user_id)
                        max_rules = SUBSCRIPTION_LIMITS[subscription_plan]['max_rules']
                        
                        # Get current active rules count and list
                        active_rules = await db.fetch("SELECT rule_id, name, is_active FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
                        active_rules_count = len(active_rules)
                        
                        # Get current status of the selected rule
                        current_status = await db.fetchval("SELECT is_active FROM rules WHERE user_id=$1 AND rule_id=$2", user_id, selected_rule['id'])
                        
                        # FREE PLAN LIMITATION: Only allow first rule to be active
                        if subscription_plan == 'free':
                            # If trying to activate a rule that's currently inactive
                            if not current_status:
                                # If there's already an active rule, block activation of any other rule
                                if active_rules_count >= 1:
                                    first_active_rule = active_rules[0] if active_rules else None
                                    
                                    await event.answer(
                                        f"❌ Free plan limitation! You can only have 1 active rule.\n"
                                        f"'{first_active_rule['name'] if first_active_rule else 'Unknown'}' is currently active.\n"
                                        "💎 Upgrade to Premium to activate multiple rules.",
                                        alert=True
                                    )
                                    
                                    # Show upgrade button
                                    buttons = [
                                        [Button.inline("💎 Upgrade Plan", data="upgrade_subscription")],
                                        
                                    ]
                                    await event.edit(
                                        f"❌ **Free Plan Limitation**\n\n"
                                        f"You're trying to activate '{selected_rule['title']}', but your free plan only allows 1 active rule.\n\n"
                                        f"**Currently Active:** {first_active_rule['name'] if first_active_rule else 'Unknown'}\n"
                                        f"**Rules Available:** {len(rules)}\n\n"
                                        f"💎 **Upgrade to Premium for:**\n"
                                        f"• Up to 20 active rules\n"
                                        f"• Multiple simultaneous forwarding rules\n"
                                        f"• Higher source/destination limits",
                                        buttons=buttons
                                    )
                                    return
                        
                        # For premium plans, check regular limits
                        if subscription_plan != 'free' and not current_status and active_rules_count >= max_rules:
                            await event.answer(
                                f"❌ You've reached your plan limit of {max_rules} active rules.\n"
                                "Deactivate another rule first.",
                                alert=True
                            )
                            return
                        
                        # Prevent deactivating the only active rule in free plan
                        if subscription_plan == 'free' and current_status and active_rules_count == 1:
                            await event.answer(
                                "❌ You cannot deactivate your only active rule.\n"
                                "Free plan requires at least 1 active rule.\n"
                                "Create and activate another rule first, or upgrade to Premium.",
                                alert=True
                            )
                            return
                        
                        # Toggle the rule status
                        new_status = not current_status
                        await db.execute("UPDATE rules SET is_active=$1 WHERE user_id=$2 AND rule_id=$3", new_status, user_id, selected_rule['id'])
                        
                        status_text = "activated" if new_status else "deactivated"
                        
                        # Update active rules count
                        active_rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id=$1 AND is_active=TRUE", user_id)
                        
                        response = f"✅ Rule '{selected_rule['title']}' {status_text} successfully!\n\n"
                        response += f"📊 **Active Rules:** {active_rules_count}/{max_rules}\n\n"
                        
                        # Add suggestion if near limit
                        if subscription_plan == 'free' and active_rules_count >= max_rules:
                            response += "⚠️ **You've reached the free plan limit!**\n"
                            response += "💎 Upgrade to Premium for more active rules!\n"
                        elif subscription_plan != 'free' and active_rules_count >= max_rules - 2:
                            response += "💡 **You're approaching your plan limit!**\n"
                        
                        await event.respond(response)
                    
                    elif action == 'set_current':
                        # Set this as the current rule for configuration
                        # Save to database permanently
                        await db.execute(
                            "UPDATE users SET current_rule=$1 WHERE id=$2",
                            selected_rule['id'], user_id
                        )
                        
                        # Also update state
                        user_states[user_id] = {
                            'current_rule': selected_rule['id'],
                            'rule_name': selected_rule['title']
                        }
                        
                        await event.respond(f"✅ Current rule set to: {selected_rule['title']}\n\nNow all /source and /destination commands will apply to this rule.")
                                          
                    # Clear the state
                    user_states.pop(user_id, None)
                    
                else:
                    await event.answer("Invalid selection.")
                    
            except ValueError:
                await event.answer("Invalid selection.")
    
    # Handle remove source selection
    elif state.get('mode') == 'remove_source_selection':
        if data.startswith('sel_'):
            # Handle number selection for removal
            idx = int(data.split('_')[1]) - 1
            items = state['items']
            page = state.get('page', 0)
            
            # Calculate actual index based on page
            actual_idx = page * 10 + idx
            
            if 0 <= actual_idx < len(items):
                item = items[actual_idx]
                # Initialize selected list if not exists
                if 'selected' not in state:
                    state['selected'] = []
                # Toggle selection
                if item['id'] in state['selected']:
                    state['selected'].remove(item['id'])
                    await event.answer(f"Unselected {item['title']}")
                else:
                    state['selected'].append(item['id'])
                    await event.answer(f"Selected {item['title']} for removal")
                
                # Update message to show selection status
                await update_remove_selection_message(event, "sources")
                
        elif data == 'nav_prev':
            # Go to previous page
            if state.get('page', 0) > 0:
                state['page'] = state.get('page', 0) - 1
                await update_remove_selection_message(event, "sources")
            else:
                await event.answer("You're on the first page")
                
        elif data == 'nav_next':
            # Go to next page
            total_pages = (len(state['items']) + 9) // 10
            if state.get('page', 0) < total_pages - 1:
                state['page'] = state.get('page', 0) + 1
                await update_remove_selection_message(event, "sources")
            else:
                await event.answer("You're on the last page")
                
        elif data == 'done_sel':
            # Process selected sources for removal
            selected = state.get('selected', [])
            if not selected:
                await event.answer("No sources selected for removal!")
            else:
                # Remove selected sources
                db = await get_db()
                rule_id = state.get('current_rule', 'default')
                rule_name = state.get('rule_name', 'Default Rule')
                
                for source_id in selected:
                    await db.execute(
                        "DELETE FROM sources WHERE user_id=$1 AND rule_id=$2 AND chat_id=$3",
                        user_id, rule_id, source_id
                    )
                
                await event.edit(f"✅ Removed {len(selected)} sources from rule '{rule_name}'!")
                del user_states[user_id]
    
    # Handle remove destination selection
    elif state.get('mode') == 'remove_destination_selection':
        if data.startswith('sel_'):
            # Handle number selection for removal
            idx = int(data.split('_')[1]) - 1
            items = state['items']
            page = state.get('page', 0)
            
            # Calculate actual index based on page
            actual_idx = page * 10 + idx
            
            if 0 <= actual_idx < len(items):
                item = items[actual_idx]
                # Initialize selected list if not exists
                if 'selected' not in state:
                    state['selected'] = []
                # Toggle selection
                if item['id'] in state['selected']:
                    state['selected'].remove(item['id'])
                    await event.answer(f"Unselected {item['title']}")
                else:
                    state['selected'].append(item['id'])
                    await event.answer(f"Selected {item['title']} for removal")
                
                # Update message to show selection status
                await update_remove_selection_message(event, "destinations")
                
        elif data == 'nav_prev':
            # Go to previous page
            if state.get('page', 0) > 0:
                state['page'] = state.get('page', 0) - 1
                await update_remove_selection_message(event, "destinations")
            else:
                await event.answer("You're on the first page")
                
        elif data == 'nav_next':
            # Go to next page
            total_pages = (len(state['items']) + 9) // 10
            if state.get('page', 0) < total_pages - 1:
                state['page'] = state.get('page', 0) + 1
                await update_remove_selection_message(event, "destinations")
            else:
                await event.answer("You're on the last page")
                
        elif data == 'done_sel':
            # Process selected destinations for removal
            selected = state.get('selected', [])
            if not selected:
                await event.answer("No destinations selected for removal!")
            else:
                # Remove selected destinations
                db = await get_db()
                rule_id = state.get('current_rule', 'default')
                rule_name = state.get('rule_name', 'Default Rule')
                
                for dest_id in selected:
                    await db.execute(
                        "DELETE FROM destinations WHERE user_id=$1 AND rule_id=$2 AND chat_id=$3",
                        user_id, rule_id, dest_id
                    )
                
                await event.edit(f"✅ Removed {len(selected)} destinations from rule '{rule_name}'!")
                del user_states[user_id]
    
    await event.answer()

# ---------------- FORWARDING LOGIC ----------------
async def forward_messages(user_id):
    client = await get_user_client(user_id)
    if not client:
        logger.error(f"No client for user {user_id}")
        return
    
    db = await get_db()
    
    # Get user's subscription plan
    subscription_plan = await get_user_subscription(user_id)
    
    # ONLY get ACTIVE rules for forwarding
    rules = await db.fetch("""
        SELECT * FROM rules WHERE user_id=$1 AND is_active=TRUE 
        ORDER BY rule_id
    """, user_id)
    
    if not rules:
        logger.info(f"No active rules found for user {user_id}")
        return
    
    # Track the last few forwarded messages to prevent loops
    forwarded_message_ids = set()
    MAX_TRACKED_MESSAGES = 100
    
    # Track album groups that have been processed to prevent duplicate forwarding
    processed_album_groups = set()
    
    # Create a handler for each rule
    handlers = []
    
    # Helper function for premium sticker handling
    async def forward_sticker_specially(client, dest_entity, event, caption=None, url_preview_enabled=True):
        """Special handling for stickers including premium stickers"""
        try:
            # Get the message from event
            message = event.message
            
            # Check if it's a sticker
            is_sticker = False
            custom_emoji_id = None
            
            if hasattr(message, 'media') and message.media:
                if hasattr(message.media, 'document'):
                    doc = message.media.document
                    if hasattr(doc, 'attributes'):
                        for attr in doc.attributes:
                            # Check for sticker attribute
                            if hasattr(attr, 'stickerset'):
                                is_sticker = True
                                logger.info(f"Detected sticker with stickerset: {attr.stickerset}")
                            # Check for custom emoji attribute
                            elif hasattr(attr, 'alt') and hasattr(attr, 'custom_emoji_id'):
                                custom_emoji_id = attr.custom_emoji_id
                                logger.info(f"Detected custom emoji with ID: {custom_emoji_id}")
            
            if is_sticker or custom_emoji_id:
                # For stickers and custom emoji, use send_file with allow_cache=False
                logger.info(f"Using special handling for {'sticker' if is_sticker else 'custom emoji'}")
                
                # Prepare file for sending
                file = message.media
                
                # Try different methods for premium stickers
                try:
                    # Method 1: Send as file with explicit sticker handling
                    # For stickers, we should not include caption in send_file
                    # Caption should be sent as a separate message if needed
                    result = await client.send_file(
                        dest_entity,
                        file,
                        allow_cache=False,  # Important for stickers
                        supports_streaming=False,
                        parse_mode=None
                    )
                    
                    # If there's a caption, send it as a separate message after the sticker
                    if caption:
                        await client.send_message(
                            dest_entity,
                            caption,
                            link_preview=url_preview_enabled
                        )
                    
                    logger.info(f"Successfully sent {'sticker' if is_sticker else 'custom emoji'} using send_file")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Method 1 failed for {'sticker' if is_sticker else 'custom emoji'}: {e}")
                    
                    # Method 2: Try with forward_messages as fallback
                    try:
                        result = await client.forward_messages(
                            dest_entity,
                            message,
                            drop_author=True
                        )
                        
                        # If there's a caption and forwarding preserved it, we're done
                        # Otherwise send caption as separate message
                        if caption and hasattr(message, 'text') and not message.text:
                            await client.send_message(
                                dest_entity,
                                caption,
                                link_preview=url_preview_enabled
                            )
                        
                        logger.info(f"Fallback: forwarded {'sticker' if is_sticker else 'custom emoji'} successfully")
                        return result
                    except Exception as e2:
                        logger.error(f"All methods failed for {'sticker' if is_sticker else 'custom emoji'}: {e2}")
                        raise
            
            # For non-sticker media, use regular forwarding
            return await client.send_file(
                dest_entity,
                message.media,
                caption=caption,
                link_preview=url_preview_enabled
            )
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait when sending sticker: {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            raise
        except Exception as e:
            logger.error(f"Error in forward_sticker_specially: {e}")
            raise
    
    # Helper for checking premium content
    def is_premium_sticker_or_emoji(event):
        """Check if message contains premium sticker or custom emoji"""
        message = event.message
        
        if not hasattr(message, 'media') or not message.media:
            return False
        
        if not hasattr(message.media, 'document'):
            return False
        
        doc = message.media.document
        if not hasattr(doc, 'attributes'):
            return False
        
        for attr in doc.attributes:
            # Check for sticker
            if hasattr(attr, 'stickerset'):
                # Check if it's a premium sticker (some indicators)
                premium_flags = [
                    hasattr(attr, 'premium_animation'),
                    hasattr(doc, 'premium') and doc.premium,
                    hasattr(doc, 'id') and str(doc.id).startswith('5')  # Some premium stickers have specific ID patterns
                ]
                
                if any(premium_flags):
                    logger.info(f"Detected premium sticker with stickerset ID: {attr.stickerset.id if hasattr(attr.stickerset, 'id') else 'unknown'}")
                    return True
                else:
                    logger.info(f"Detected regular sticker")
                    return True
            
            # Check for custom emoji (animated emoji)
            elif hasattr(attr, 'custom_emoji_id'):
                logger.info(f"Detected custom emoji with ID: {attr.custom_emoji_id}")
                return True
        
        return False
    
    # Dummy event class for album messages
    class DummyEvent:
        def __init__(self, message):
            self.message = message
    
    try:
        for rule in rules:
            rule_id = rule['rule_id']
            rule_name = rule['name']
            
            # Get delay for this rule
            delay_seconds = await get_forwarding_delay(user_id, rule_id)
            
            # Get sources and destinations for this rule
            sources = await db.fetch("SELECT * FROM sources WHERE user_id=$1 AND rule_id=$2 ORDER BY chat_id", user_id, rule_id)
            destinations = await db.fetch("SELECT * FROM destinations WHERE user_id=$1 AND rule_id=$2 ORDER BY chat_id", user_id, rule_id)
            
            if not sources or not destinations:
                logger.info(f"No sources or destinations for rule {rule_name}")
                continue
            
            # FOR FREE PLAN: Only use the first source and first destination
            if subscription_plan == 'free':
                sources = [sources[0]] if sources else []
                destinations = [destinations[0]] if destinations else []
                logger.info(f"Free plan: Using only 1st source and 1st destination for rule {rule_name}")
            
            # Convert source IDs to entities
            source_entities = []
            for source in sources:
                try:
                    # For bots with username, use username instead of chat ID
                    if source['username']:
                        entity = await resolve_entity_safe(client, f"@{source['username']}")
                    else:
                        entity = await resolve_entity_safe(client, source['chat_id'])
                    
                    if entity:
                        source_entities.append(entity)
                except Exception as e:
                    logger.error(f"Error getting entity for source {source['chat_id']}: {e}")
            
            if not source_entities:
                logger.info(f"No valid source entities for rule {rule_name}")
                continue
            
            # Get keyword filters for this rule
            whitelist = await db.fetchrow(
                "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='whitelist'",
                user_id, rule_id
            )
            blacklist = await db.fetchrow(
                "SELECT keywords FROM keyword_filters WHERE user_id=$1 AND rule_id=$2 AND type='blacklist'",
                user_id, rule_id
            )
            
            whitelist_keywords = whitelist['keywords'] if whitelist else []
            blacklist_keywords = blacklist['keywords'] if blacklist else []
            
            # Get rule options
            rule_options = await db.fetchrow(
                "SELECT options FROM rules WHERE user_id=$1 AND rule_id=$2", 
                user_id, rule_id
            )
            
            # Parse rule options
            options = {}
            if rule_options and rule_options['options']:
                try:
                    if isinstance(rule_options['options'], dict):
                        options = rule_options['options']
                    else:
                        options = json.loads(rule_options['options'])
                except (json.JSONDecodeError, TypeError):
                    options = {}
            
            # Get URL preview setting with proper fallback
            url_preview_enabled = True  # Default to True
            if 'url_preview' in options:
                url_preview_enabled = options.get('url_preview', True)
            
            # Create mode info for logging
            mode_info = ""
            if options.get('forward_media_only'):
                mode_info = " [MEDIA ONLY]"
            elif options.get('forward_text_only'):
                mode_info = " [TEXT ONLY]"

            # Add free plan limitation info
            if subscription_plan == 'free':
                mode_info += " [FREE PLAN: 1st SOURCE & DEST ONLY]"

            # Add remove_links info if enabled and user is premium
            remove_links_info = ""
            if options.get('remove_links', False):
                if subscription_plan != 'free':
                    remove_links_info = " [LINKS REMOVED]"

            # Add text replacement info if enabled and user is premium
            text_replacement_info = ""
            if options.get('text_replacements') or options.get('replace_all_text', {}).get('enabled'):
                if subscription_plan != 'free':
                    if options.get('replace_all_text', {}).get('enabled'):
                        text_replacement_info = " [ALL TEXT REPLACED]"
                    elif options.get('text_replacements'):
                        text_replacement_info = " [TEXT REPLACED]"

            mode_info = f"{mode_info}{remove_links_info}{text_replacement_info}"
            
            # Create handler for this rule
            @client.on(events.NewMessage(chats=source_entities))
            async def handler(
                event, rule_id=rule_id, rule_name=rule_name, 
                destinations=destinations, whitelist_keywords=whitelist_keywords,
                blacklist_keywords=blacklist_keywords, delay_seconds=delay_seconds,
                options=options, url_preview_enabled=url_preview_enabled,
                subscription_plan=subscription_plan  # Pass subscription plan to handler
            ):
                try:
                    # Check if this message was just forwarded by our bot to prevent loops
                    message_id = f"{event.chat_id}_{event.message.id}"
                    if message_id in forwarded_message_ids:
                        logger.info(f"Ignoring message {event.message.id} - was forwarded by this bot")
                        return
                    
                    # Check if this album group has already been processed
                    if event.message.grouped_id:
                        album_group_id = f"{event.chat_id}_{event.message.grouped_id}"
                        if album_group_id in processed_album_groups:
                            logger.info(f"Ignoring message {event.message.id} - album group {event.message.grouped_id} already processed")
                            return
                    
                    # Get message text for keyword checking
                    message_text = event.message.text or ""
                    message_caption = getattr(event.message, 'caption', '') or ""
                    full_text = f"{message_text} {message_caption}".lower().strip()
                    
                    # Check blacklist first
                    for keyword in blacklist_keywords:
                        if keyword.lower() in full_text:
                            logger.info(f"Message {event.message.id} rejected due to blacklist keyword: {keyword}")
                            return
                    
                    # Check whitelist if it exists
                    if whitelist_keywords:
                        whitelist_match = False
                        for keyword in whitelist_keywords:
                            if keyword.lower() in full_text:
                                whitelist_match = True
                                break
                        if not whitelist_match:
                            logger.info(f"Message {event.message.id} rejected - no whitelist keywords matched")
                            return
                    
                    # Apply channel link conversion if enabled
                    if 'channel_converter' in options:
                        converter_settings = options['channel_converter']
                        
                        if converter_settings.get('enabled') and converter_settings.get('my_channel'):
                            my_channel = converter_settings['my_channel']
                            
                            # Convert channel links in text
                            if event.message.text:
                                event.message.text = convert_all_channel_links(event.message.text, my_channel)
                            
                            # Convert channel links in caption  
                            if hasattr(event.message, 'caption') and event.message.caption:
                                event.message.caption = convert_all_channel_links(event.message.caption, my_channel)

                    # Apply link removal if enabled and user is premium
                    if options.get('remove_links', False):
                        # Double-check that user is premium before applying link removal
                        if subscription_plan != 'free':  # Only apply if user is premium
                            # Remove links from message text
                            if event.message.text:
                                original_text = event.message.text
                                event.message.text = remove_all_links(event.message.text)
                                if original_text != event.message.text:
                                    logger.info(f"Removed links from text for message {event.message.id}")
                            
                            # Remove links from message caption
                            message_caption = getattr(event.message, 'caption', '')
                            if message_caption:
                                original_caption = message_caption
                                event.message.caption = remove_all_links(message_caption)
                                if original_caption != event.message.caption:
                                    logger.info(f"Removed links from caption for message {event.message.id}")
                        else:
                            # If free user somehow has this enabled, disable it
                            options['remove_links'] = False
                            await db.execute(
                                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                                json.dumps(options), user_id, rule_id
                            )
                            logger.warning(f"Disabled remove_links for free user {user_id} in rule {rule_id}")
                    
                    # Apply text replacements if enabled and user is premium
                    if options.get('text_replacements') or options.get('replace_all_text', {}).get('enabled'):
                        # Double-check that user is premium before applying text replacement
                        if subscription_plan != 'free':  # Only apply if user is premium
                            text_replacements = options.get('text_replacements', {})
                            replace_all_text = options.get('replace_all_text', {'enabled': False})
                            
                            # Apply to message text
                            if event.message.text:
                                original_text = event.message.text
                                event.message.text = replace_text_in_message(event.message.text, text_replacements, replace_all_text)
                                if original_text != event.message.text:
                                    logger.info(f"Applied text replacement for message {event.message.id}")
                            
                            # Apply to message caption
                            message_caption = getattr(event.message, 'caption', '')
                            if message_caption:
                                original_caption = message_caption
                                event.message.caption = replace_text_in_message(message_caption, text_replacements, replace_all_text)
                                if original_caption != event.message.caption:
                                    logger.info(f"Applied text replacement to caption for message {event.message.id}")
                        else:
                            # If free user somehow has this enabled, disable it
                            if 'text_replacements' in options:
                                del options['text_replacements']
                            if 'replace_all_text' in options:
                                options['replace_all_text'] = {'enabled': False, 'replacement': ''}
                            await db.execute(
                                "UPDATE rules SET options=$1 WHERE user_id=$2 AND rule_id=$3", 
                                json.dumps(options), user_id, rule_id
                            )
                            logger.warning(f"Disabled text replacements for free user {user_id} in rule {rule_id}")
                                                                                                    
                    # Apply link replacements to text and captions
                    link_replacements = options.get('link_replacements', {})
                    if link_replacements:
                        # Replace links in message text
                        if event.message.text:
                            event.message.text = replace_links_in_text(event.message.text, link_replacements)
                        
                        # Replace links in message caption
                        message_caption = getattr(event.message, 'caption', '')
                        if message_caption:
                            event.message.caption = replace_links_in_text(message_caption, link_replacements)
                    
                    # Check if we should forward this message type based on options
                    forward_media_only = options.get('forward_media_only', False)
                    forward_text_only = options.get('forward_text_only', False)
                    
                    # Handle media-only mode
                    if forward_media_only:
                        if not event.message.media:
                            # Skip text-only messages in media-only mode
                            logger.info(f"Message {event.message.id} rejected - text message in media-only mode")
                            return
                        # In media-only mode, we'll forward media but without captions
                        logger.info(f"Message {event.message.id} - forwarding media only (without caption) in media-only mode")
                    
                    # Handle text-only mode
                    if forward_text_only:
                        if event.message.media and not (event.message.text or getattr(event.message, 'caption', '')):
                            # If it's media-only with no text/caption, skip it in text-only mode
                            logger.info(f"Message {event.message.id} rejected - media with no text in text-only mode")
                            return
                        elif event.message.media and (event.message.text or getattr(event.message, 'caption', '')):
                            # If it's media with text/caption, we'll forward only the text part
                            logger.info(f"Message {event.message.id} - extracting text from media message in text-only mode")
                            # Continue processing to extract and forward the text
                    
                    # Check if message contains premium sticker or custom emoji
                    is_premium_content = is_premium_sticker_or_emoji(event)
                    if is_premium_content:
                        logger.info(f"Message {event.message.id} contains premium sticker/custom emoji, using special handling")
                    
                    # Track this message to prevent re-forwarding
                    forwarded_message_ids.add(message_id)
                    # Keep the set size manageable
                    if len(forwarded_message_ids) > MAX_TRACKED_MESSAGES:
                        # Remove the oldest message (FIFO)
                        oldest_message = next(iter(forwarded_message_ids))
                        forwarded_message_ids.remove(oldest_message)
                    
                    # Apply delay if set
                    if delay_seconds > 0:
                        delay_info = f" (after {delay_seconds} second delay)"
                        await asyncio.sleep(delay_seconds)
                    else:
                        delay_info = ""
                    
                    # Check if this is part of a media group (album)
                    if event.message.grouped_id:
                        # This is part of an album - we need to collect all messages in the group
                        logger.info(f"Message {event.message.id} is part of album group {event.message.grouped_id}")
                        
                        # Mark this album group as being processed
                        album_group_id = f"{event.chat_id}_{event.message.grouped_id}"
                        
                        # If we're already processing this album, skip individual processing
                        if album_group_id in processed_album_groups:
                            logger.info(f"Album group {event.message.grouped_id} already being processed, skipping individual message")
                            return
                            
                        processed_album_groups.add(album_group_id)
                        
                        # Wait a bit to collect all album messages
                        await asyncio.sleep(2)
                        
                        # Get all messages in the album group
                        album_messages = []
                        async for album_msg in client.iter_messages(
                            event.chat_id, 
                            limit=10,
                            min_id=event.message.id - 10,
                            max_id=event.message.id + 10
                        ):
                            if (hasattr(album_msg, 'grouped_id') and 
                                album_msg.grouped_id == event.message.grouped_id and
                                album_msg.media):
                                # Track each album message individually to prevent duplicate processing
                                album_msg_id = f"{event.chat_id}_{album_msg.id}"
                                forwarded_message_ids.add(album_msg_id)
                                album_messages.append(album_msg)
                        
                        # Sort by message ID to maintain order
                        album_messages.sort(key=lambda x: x.id)
                        
                        if len(album_messages) > 1:
                            logger.info(f"Found {len(album_messages)} messages in album group {event.message.grouped_id}")
                            
                            # Find caption from the first message that has text or caption
                            final_caption = None
                            for msg in album_messages:
                                if hasattr(msg, 'text') and msg.text:
                                    final_caption = msg.text
                                    break
                                elif hasattr(msg, 'caption') and getattr(msg, 'caption', ''):
                                    final_caption = msg.caption
                                    break
                            
                            # Check if album contains premium stickers/emoji
                            album_has_premium = False
                            for msg in album_messages:
                                dummy_event = DummyEvent(msg)
                                if is_premium_sticker_or_emoji(dummy_event):
                                    album_has_premium = True
                                    break
                            
                            # Apply link removal to caption if enabled and user is premium
                            if options.get('remove_links', False):
                                if subscription_plan != 'free' and final_caption:
                                    original_caption = final_caption
                                    final_caption = remove_all_links(final_caption)
                                    if original_caption != final_caption:
                                        logger.info(f"Removed links from album caption for group {event.message.grouped_id}")
                            
                            # Apply text replacements to caption if enabled and user is premium
                            if options.get('text_replacements') or options.get('replace_all_text', {}).get('enabled'):
                                if subscription_plan != 'free' and final_caption:
                                    text_replacements = options.get('text_replacements', {})
                                    replace_all_text = options.get('replace_all_text', {'enabled': False})
                                    original_caption = final_caption
                                    final_caption = replace_text_in_message(final_caption, text_replacements, replace_all_text)
                                    if original_caption != final_caption:
                                        logger.info(f"Applied text replacement to album caption for group {event.message.grouped_id}")
                            
                            # Apply link replacements to caption
                            link_replacements = options.get('link_replacements', {})
                            if link_replacements and final_caption:
                                final_caption = replace_links_in_text(final_caption, link_replacements)
                            
                            # Forward as album to all destinations
                            for destination in destinations:
                                try:
                                    # For bots with username, use username instead of chat ID
                                    if destination['username']:
                                        dest_entity = await resolve_entity_safe(client, f"@{destination['username']}")
                                        dest_identifier = f"@{destination['username']}"
                                    else:
                                        dest_entity = await resolve_entity_safe(client, destination['chat_id'])
                                        dest_identifier = destination['chat_id']
                                    
                                    if not dest_entity:
                                        logger.warning(f"Cannot resolve destination entity: {dest_identifier}")
                                        continue
                                    
                                    if forward_text_only:
                                        # In text-only mode, only forward the caption
                                        if final_caption:
                                            await client.send_message(
                                                dest_entity,
                                                final_caption,
                                                link_preview=url_preview_enabled
                                            )
                                            logger.info(
                                                f"Copied text from album with {len(album_messages)} media files"
                                                f" to {destination['title']} for rule {rule_name}{delay_info}"
                                                f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                            )
                                    elif forward_media_only:
                                        # In media-only mode, forward album without captions
                                        # Prepare media files for album
                                        media_files = []
                                        for album_msg in album_messages:
                                            media_files.append(album_msg.media)
                                        
                                        # Special handling if album contains premium stickers
                                        if album_has_premium:
                                            logger.info(f"Album contains premium content, sending individually")
                                            # Send each premium sticker individually with special handling
                                            for album_msg in album_messages:
                                                try:
                                                    dummy_event = DummyEvent(album_msg)
                                                    if is_premium_sticker_or_emoji(dummy_event):
                                                        await forward_sticker_specially(
                                                            client, dest_entity, dummy_event, 
                                                            caption=None, url_preview_enabled=False
                                                        )
                                                    else:
                                                        await client.send_file(
                                                            dest_entity,
                                                            file=album_msg.media
                                                        )
                                                except Exception as e:
                                                    logger.error(f"Error sending album message individually: {e}")
                                        else:
                                            # Send as album without caption
                                            await client.send_file(
                                                dest_entity,
                                                file=media_files
                                            )
                                        
                                        logger.info(
                                            f"Copied album with {len(album_messages)} media files (no caption)"
                                            f" to {destination['title']} for rule {rule_name}{delay_info}"
                                        )
                                    else:
                                        # Normal mode - forward the album with caption
                                        # Prepare media files for album
                                        media_files = []
                                        for album_msg in album_messages:
                                            media_files.append(album_msg.media)
                                        
                                        # Special handling if album contains premium stickers
                                        if album_has_premium:
                                            logger.info(f"Album contains premium content, sending individually")
                                            # Send each message individually with special handling
                                            for album_msg in album_messages:
                                                try:
                                                    # Get individual caption if any
                                                    individual_caption = album_msg.text or getattr(album_msg, 'caption', '')
                                                    dummy_event = DummyEvent(album_msg)
                                                    
                                                    if is_premium_sticker_or_emoji(dummy_event):
                                                        await forward_sticker_specially(
                                                            client, dest_entity, dummy_event, 
                                                            caption=individual_caption, 
                                                            url_preview_enabled=url_preview_enabled
                                                        )
                                                    else:
                                                        await client.send_file(
                                                            dest_entity,
                                                            file=album_msg.media,
                                                            caption=individual_caption,
                                                            link_preview=url_preview_enabled
                                                        )
                                                except Exception as e:
                                                    logger.error(f"Error sending album message individually: {e}")
                                        else:
                                            # Send as album with caption and URL preview setting
                                            await client.send_file(
                                                dest_entity,
                                                file=media_files,
                                                caption=final_caption,
                                                link_preview=url_preview_enabled
                                            )
                                        
                                        logger.info(
                                            f"Copied album with {len(album_messages)} media files"
                                            f" to {destination['title']} for rule {rule_name}{delay_info}"
                                            f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                        )
                                        
                                except (ChatWriteForbiddenError, ChannelPrivateError) as e:
                                    logger.warning(f"Cannot send album to {destination['title']}: {e}")
                                except FloodWaitError as e:
                                    logger.warning(f"Flood wait for {destination['title']}: {e.seconds} seconds")
                                    await asyncio.sleep(e.seconds)
                                except Exception as e:
                                    logger.error(f"Error sending album to {destination['title']}: {e}")
                            
                            # CRITICAL: Return after processing album to prevent individual message forwarding
                            return
                        else:
                            # Album collection failed, remove from processed groups and fall back to single message
                            processed_album_groups.discard(album_group_id)
                            logger.warning(f"Failed to collect album group {event.message.grouped_id}, falling back to single message")
                    
                    # Single message forwarding (not part of album or album handling failed)
                    # Forward to all destinations without "forwarded from" header
                    for destination in destinations:
                        try:
                            # For bots with username, use username instead of chat ID
                            if destination['username']:
                                dest_entity = await resolve_entity_safe(client, f"@{destination['username']}")
                                dest_identifier = f"@{destination['username']}"
                            else:
                                dest_entity = await resolve_entity_safe(client, destination['chat_id'])
                                dest_identifier = destination['chat_id']
                            
                            if not dest_entity:
                                logger.warning(f"Cannot resolve destination entity: {dest_identifier}")
                                continue
                                                  
                            # Handle both text and media messages
                            if event.message.media:
                                # Check media type and handle accordingly
                                media_type = type(event.message.media).__name__
                                
                                # Skip unsupported media types
                                unsupported_media_types = ['MessageMediaWebPage', 'MessageMediaPoll', 'MessageMediaGame']
                                if media_type in unsupported_media_types:
                                    logger.info(f"Skipping unsupported media type: {media_type} for message {event.message.id}")
                                    
                                    # For web pages, you might want to forward the text content only
                                    if media_type == 'MessageMediaWebPage' and (event.message.text or getattr(event.message, 'caption', '')):
                                        # Forward only the text content with URL preview setting
                                        text_content = event.message.text or getattr(event.message, 'caption', '')
                                        await client.send_message(
                                            dest_entity, 
                                            text_content,
                                            link_preview=url_preview_enabled  # Apply URL preview setting
                                        )
                                        logger.info(
                                            f"Copied text from web page message {event.message.id}"
                                            f" to {destination['title']} for rule {rule_name}{delay_info}"
                                            f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                        )
                                    return
                                
                                # Media message (photo, video, document, etc.)
                                if forward_text_only:
                                    # In text-only mode, only forward the caption/text, not the media
                                    caption = event.message.text or getattr(event.message, 'caption', '')
                                    if caption:
                                        await client.send_message(
                                            dest_entity, 
                                            caption,
                                            link_preview=url_preview_enabled  # Apply URL preview setting
                                        )
                                        logger.info(
                                            f"Copied text from media message {event.message.id}"
                                            f" to {destination['title']} for rule {rule_name}{delay_info}"
                                            f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                        )
                                elif forward_media_only:
                                    # In media-only mode, forward media without caption
                                    if is_premium_content:
                                        # Use special handling for premium stickers
                                        await forward_sticker_specially(
                                            client, dest_entity, event, 
                                            caption=None, url_preview_enabled=False
                                        )
                                    else:
                                        await client.send_file(
                                            dest_entity, 
                                            file=event.message.media
                                        )
                                    logger.info(
                                        f"Copied {media_type} message {event.message.id}"
                                        f" to {destination['title']} for rule {rule_name}{delay_info}"
                                    )
                                else:
                                    # Normal mode - forward media with caption and URL preview setting
                                    caption = event.message.text or getattr(event.message, 'caption', '')
                                    
                                    if is_premium_content:
                                        # Use special handling for premium stickers with caption
                                        await forward_sticker_specially(
                                            client, dest_entity, event, 
                                            caption=caption, url_preview_enabled=url_preview_enabled
                                        )
                                    else:
                                        await client.send_file(
                                            dest_entity, 
                                            file=event.message.media,
                                            caption=caption,
                                            link_preview=url_preview_enabled  # Apply URL preview setting
                                        )
                                    logger.info(
                                        f"Copied {media_type} message {event.message.id}"
                                        f" to {destination['title']} for rule {rule_name}{delay_info}"
                                        f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                    )
                            else:
                                # Text-only message
                                if forward_media_only:
                                    # Skip text messages in media-only mode
                                    logger.info(f"Text message {event.message.id} skipped in media-only mode")
                                    continue
                                
                                # Send message with URL preview setting
                                await client.send_message(
                                    dest_entity, 
                                    event.message.text,
                                    link_preview=url_preview_enabled  # This applies the setting
                                )
                                logger.info(
                                    f"Copied text message {event.message.id}"
                                    f" to {destination['title']} for rule {rule_name}{delay_info}"
                                    f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
                                )
                                
                        except (ChatWriteForbiddenError, ChannelPrivateError) as e:
                            logger.warning(f"Cannot send to {destination['title']}: {e}")
                        except FloodWaitError as e:
                            logger.warning(f"Flood wait for {destination['title']}: {e.seconds} seconds")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            logger.error(f"Error sending message to {destination['title']}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
            
            handlers.append(handler)
            delay_info = f" with {delay_seconds}s delay" if delay_seconds > 0 else ""
            
            logger.info(
                f"Started forwarding for rule: {rule_name}{mode_info}{delay_info} "
                f"with {len(sources)} sources and {len(destinations)} destinations"
                f" [URL Preview: {'ON' if url_preview_enabled else 'OFF'}]"
            )
        
        # Notify user that forwarding has started
        try:
            message = await bot.send_message(user_id, "✅ Forwarding is now active and listening for new messages...")
            
            # Delete the message after 5 seconds
            await asyncio.sleep(5)
            await message.delete()
            
        except Exception as e:
            logger.warning(f"Cannot send notification to user {user_id}: {e}")
        
        # Keep the client running
        await client.run_until_disconnected()
        
    except asyncio.CancelledError:
        logger.info(f"Forwarding stopped for user {user_id}")
        try:
            await bot.send_message(user_id, "🛑 Forwarding stopped by user")
        except Exception as e:
            logger.warning(f"Cannot send stop notification to user {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in forwarding task for user {user_id}: {e}")
        try:
            await bot.send_message(user_id, f"❌ Forwarding error: {str(e)}")
        except Exception as e:
            logger.warning(f"Cannot send error notification to user {user_id}: {e}")
    finally:
        # Remove this task from forwarding_tasks
        if user_id in forwarding_tasks:
            del forwarding_tasks[user_id]
        
        # Disconnect client if it's still connected
        if user_id in user_clients:
            try:
                await user_clients[user_id].disconnect()
            except:
                pass
            del user_clients[user_id]

# ---------------- MAIN ----------------
async def main():
    await init_db()
    await bot.start()
    logger.info("Bot started!")
    
    # Auto-restart forwarding for all users
    await restart_forwarding_for_all_users()
    
    # Start consolidated subscription enforcement (replaces all previous periodic functions)
    asyncio.create_task(consolidated_subscription_enforcement())
    
    logger.info("Consolidated subscription enforcement started")
    
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # Use the proper event loop handling for Telethon
    bot.loop.run_until_complete(main())    
