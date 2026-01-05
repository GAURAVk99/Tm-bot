import os
import logging
import asyncio
import json
import asyncpg
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# Add these global variables at the top
active_plan_messages = {}  # {message_id: (chat_id, message_text)}
user_payment_screenshots = {}  # {user_id: (file_id, message_id, chat_id)}

async def update_specific_plan_message(chat_id, message_id):
    """Update a specific plan selection message"""
    try:
        # Generate updated message
        message = "💎 **Welcome to the Premium Upgrade Center!**\n\n"
        message += "**Choose a plan:**\n\n"
        
        for plan_id, plan_data in PLANS.items():
            message += f"• {plan_data['name']}\n"
            message += f"  💰 {plan_data['price_ton']} TON | ₹{plan_data['price_inr']} | ${plan_data['price_usd']}\n"
            message += f"  ⏰ {plan_data['days']} days"
            if 'discount' in plan_data:
                message += f" | {plan_data['discount']} OFF"
            message += "\n\n"
        
        message += "Select a plan below:"
        
        # Generate updated buttons
        buttons = generate_plan_buttons()
        
        # Edit the message - FIXED: Use correct method signature
        await bot.edit_message(chat_id, message_id, message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error updating message {message_id}: {e}")

# ---------------- CONFIG ----------------
API_ID = int(os.getenv("API_ID", "20877162"))
API_HASH = os.getenv("API_HASH", "6dfa90f0624d13f591753174e2c56e8a")
BOT_TOKEN = os.getenv("PAYMENT_BOT_TOKEN", "8366789774:AAHnPKKm-Zqs_VFi-Pk0JjvOgym9w3MXjNo")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://telegram_user:password@localhost:5432/telegram_forwarder2")

MAIN_BOT_USERNAME = "@advauto_messege_forwarder_bot"

# Payment methods
UPI_ID = "amfbot@ybl"
PAYPAL_LINK = "https://www.paypal.com/ncp/payment/NVQS97ZKT8Q54"
TON_WALLET_ADDRESS = "UQAUb8SnfYl7tEI4yFTS1JHp1qkwcwXB0ktxpiG257E8yG4p"  # Replace with your actual TON wallet

# QR Code configuration - use local files instead of URLs
QR_CODE_FILES = {
    "default": "qr99.png",  # Default QR code
    "ton": "ton_qr.png",  # TON QR code
    # You can also have specific QR codes for each plan:
    "1month": "https://pdf2imgs.site/phonepe/qrcode99.png",
    "3months": "https://pdf2imgs.site/phonepe/qrcode283.png",
    "6months": "https://pdf2imgs.site/phonepe/qrcode535.png",
    "1year": "https://pdf2imgs.site/phonepe/qrcode951.png"
}

# Subscription plans (in USD, INR, and TON)
PLANS = {
    "1month": {
        "price_usd": 2, 
        "price_inr": 99,
        "price_ton": 2,
        "days": 30, 
        "name": "1 Month Premium"
    },
    "3months": {
        "price_usd": 3.38,
        "price_inr": 283,
        "price_ton": 5.4,
        "days": 90, 
        "name": "3 Months Premium", 
        "discount": "10%"
    },
    "6months": {
        "price_usd": 7.27,
        "price_inr": 535,
        "price_ton": 9.6,
        "days": 180, 
        "name": "6 Months Premium", 
        "discount": "20%"
    },
    "1year": {
        "price_usd": 12.93,
        "price_inr": 951,
        "price_ton": 12,
        "days": 365, 
        "name": "1 Year Premium", 
        "discount": "50%"
    }
}

# Exchange rate for reference (can be updated periodically)
USD_TO_INR = 83.5  # Current approximate exchange rate

# Admin configuration
ADMIN_IDS = [1013148420]  # Replace with your Telegram user ID
ADMIN_NOTIFICATION_CHAT = 1013148420  # Where to send payment notifications

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

## ---------------- DATABASE SETUP ----------------
async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create subscriptions table that matches main bot's schema
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id BIGINT PRIMARY KEY,
                plan TEXT DEFAULT 'free',
                expires_at TIMESTAMP,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create payments table with screenshot field
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                plan_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                transaction_id TEXT,
                status TEXT DEFAULT 'pending',
                screenshot_message_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                admin_id BIGINT,
                notes TEXT,
                UNIQUE(user_id)
            );
        """)
        
        # Create admin users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                can_approve_payments BOOLEAN DEFAULT TRUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add default admin if not exists
        for admin_id in ADMIN_IDS:
            await conn.execute("""
                INSERT INTO admin_users (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO NOTHING
            """, admin_id, "Admin")
        
        await conn.close()
        logger.info("Payment database initialized with compatible schema")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Continue - tables might already exist

# Database connection pool
db_pool = None

async def get_db():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
    return db_pool

# Update the update_database_schema() function
async def update_database_schema():
    """Add missing columns to existing database"""
    try:
        db = await get_db()
        
        # Check if screenshot_message_id column exists
        try:
            await db.execute("SELECT screenshot_message_id FROM payments LIMIT 1")
        except Exception:
            # Column doesn't exist, add it
            await db.execute("ALTER TABLE payments ADD COLUMN screenshot_message_id BIGINT")
            logger.info("Added screenshot_message_id column to payments table")
        
        # Add notification flags to subscriptions table
        try:
            await db.execute("SELECT notified_about_expiry FROM subscriptions LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE subscriptions ADD COLUMN notified_about_expiry BOOLEAN DEFAULT FALSE")
            logger.info("Added notified_about_expiry column to subscriptions table")
            
        try:
            await db.execute("SELECT notified_about_expiry_soon FROM subscriptions LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE subscriptions ADD COLUMN notified_about_expiry_soon BOOLEAN DEFAULT FALSE")
            logger.info("Added notified_about_expiry_soon column to subscriptions table")
            
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")

# Add these functions to handle subscription expiry notifications
async def check_expired_subscriptions():
    """Check for expired subscriptions and notify users"""
    try:
        db = await get_db()
        
        # Find subscriptions that expired in the last 24 hours
        expired_subscriptions = await db.fetch("""
            SELECT user_id, plan, expires_at 
            FROM subscriptions 
            WHERE expires_at <= NOW() 
            AND expires_at >= NOW() - INTERVAL '24 hours'
            AND notified_about_expiry = FALSE
        """)
        
        for subscription in expired_subscriptions:
            user_id = subscription['user_id']
            plan_name = subscription['plan'] or "Premium"
            expiry_date = subscription['expires_at']
            
            try:
                # Send expiry notification
                message = (
                    "⚠️ **Your Subscription Has Expired** ⚠️\n\n"
                    f"Your **{plan_name}** plan expired on {expiry_date.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
                    "🔒 **What's changed:**\n"
                    "• Limited to 1 rules\n"
                    "• Limited to 1 sources & destinations\n"
                    "• Basic forwarding capabilities\n\n"
                    "💎 **Renew now to regain premium features:**\n"
                    "• 50 Sources + 50 Targets\n"
                    "• 20 Rules\n"
                    "• Auto-forwarding enabled\n"
                    "• Header control\n"
                    "• Media forwarding\n"
                    "• Blacklist/Whitelist keywords\n"
                    "• Unlimited forwards/day\n\n"
                    "Click below to renew your subscription!"
                )
                
                buttons = [
                    [Button.inline("💎 Renew Subscription", data="show_plans")],
                    [Button.inline("📋 Check My Plan", data="show_my_plan")],
                    [Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")]
                ]
                
                await bot.send_message(user_id, message, buttons=buttons)
                
                # Mark as notified
                await db.execute(
                    "UPDATE subscriptions SET notified_about_expiry = TRUE WHERE user_id = $1",
                    user_id
                )
                
                logger.info(f"Sent expiry notification to user {user_id}")
                
            except Exception as e:
                logger.error(f"Could not send expiry notification to user {user_id}: {e}")
        
        return len(expired_subscriptions)
        
    except Exception as e:
        logger.error(f"Error checking expired subscriptions: {e}")
        return 0

async def check_expiring_soon_subscriptions():
    """Check for subscriptions expiring soon (3 days before)"""
    try:
        db = await get_db()
        
        # Find subscriptions expiring in next 3 days that haven't been notified
        expiring_soon = await db.fetch("""
            SELECT user_id, plan, expires_at 
            FROM subscriptions 
            WHERE expires_at <= NOW() + INTERVAL '3 days'
            AND expires_at > NOW()
            AND notified_about_expiry_soon = FALSE
        """)
        
        for subscription in expiring_soon:
            user_id = subscription['user_id']
            plan_name = subscription['plan'] or "Premium"
            expiry_date = subscription['expires_at']
            days_remaining = (expiry_date - datetime.now()).days
            
            try:
                # Send expiry soon notification
                message = (
                    "🔔 **Subscription Expiring Soon** 🔔\n\n"
                    f"Your **{plan_name}** plan will expire in **{days_remaining} days** "
                    f"({expiry_date.strftime('%Y-%m-%d %H:%M UTC')}).\n\n"
                    "Renew now to continue enjoying premium features without interruption!\n\n"
                    "💎 **Premium Features:**\n"
                    "• 50 Sources + 50 Targets\n"
                    "• 20 Rules\n"
                    "• Auto-forwarding enabled\n"
                    "• Header control\n"
                    "• Media forwarding\n"
                    "• Blacklist/Whitelist keywords\n"
                    "• Unlimited forwards/day"
                )
                
                buttons = [
                    [Button.inline("💎 Renew Now", data="show_plans")],
                    [Button.inline("📋 Check Details", data="show_my_plan")],
                    [Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")]
                ]
                
                await bot.send_message(user_id, message, buttons=buttons)
                
                # Mark as notified
                await db.execute(
                    "UPDATE subscriptions SET notified_about_expiry_soon = TRUE WHERE user_id = $1",
                    user_id
                )
                
                logger.info(f"Sent expiry soon notification to user {user_id}")
                
            except Exception as e:
                logger.error(f"Could not send expiry soon notification to user {user_id}: {e}")
        
        return len(expiring_soon)
        
    except Exception as e:
        logger.error(f"Error checking expiring soon subscriptions: {e}")
        return 0

# Add this background task to run periodically
async def subscription_monitor_task():
    """Background task to monitor subscriptions and send notifications"""
    while True:
        try:
            # Check every hour
            await asyncio.sleep(300)  # 1 hour
            
            # Check for expiring soon subscriptions
            expiring_count = await check_expiring_soon_subscriptions()
            if expiring_count > 0:
                logger.info(f"Sent {expiring_count} expiring soon notifications")
            
            # Check for expired subscriptions
            expired_count = await check_expired_subscriptions()
            if expired_count > 0:
                logger.info(f"Sent {expired_count} expiry notifications")
                
        except Exception as e:
            logger.error(f"Error in subscription monitor task: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying
            
# Add more specific rejection reasons in the reject handler
detailed_rejection_reasons = {
    'invalid_screenshot': 'Payment screenshot is unclear, missing, or invalid',
    'wrong_amount': 'Payment amount does not match the selected plan',
    'no_payment_found': 'No payment transaction found for the provided details',
    'suspicious_activity': 'Payment appears suspicious or fraudulent',
    'duplicate_payment': 'This payment has already been processed',
    'test_transaction': 'Payment appears to be a test transaction',
    'bank_declined': 'Payment was declined by the bank',
    'user_cancelled': 'User requested cancellation',
    'system_error': 'Technical system error occurred',
    'other': 'Other reason (please specify)'
}

# ---------------- BOT INIT ----------------
bot = TelegramClient("payment_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ---------------- HELPER FUNCTIONS ----------------
async def is_admin(user_id):
    """Check if user is an admin"""
    try:
        db = await get_db()
        row = await db.fetchrow("SELECT * FROM admin_users WHERE user_id=$1 AND can_approve_payments=TRUE", user_id)
        return row is not None
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        # Fallback: check if user is in the hardcoded admin list
        return user_id in ADMIN_IDS

async def notify_admins(message, buttons=None):
    """Notify all admins about a new payment"""
    try:
        db = await get_db()
        admins = await db.fetch("SELECT user_id FROM admin_users WHERE can_approve_payments=TRUE")
        
        for admin in admins:
            try:
                if buttons:
                    await bot.send_message(admin['user_id'], message, buttons=buttons)
                else:
                    await bot.send_message(admin['user_id'], message)
            except Exception as e:
                logger.error(f"Could not notify admin {admin['user_id']}: {e}")
    except Exception as e:
        logger.error(f"Error notifying admins: {e}")
        # Fallback: notify hardcoded admin IDs
        for admin_id in ADMIN_IDS:
            try:
                if buttons:
                    await bot.send_message(admin_id, message, buttons=buttons)
                else:
                    await bot.send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Could not notify admin {admin_id}: {e}")

# Update the subscription renewal function to reset notification flags
async def update_subscription_in_main_bot(user_id, plan_id, days):
    """Update subscription in the shared database"""
    try:
        db = await get_db()
        
        # Calculate expiry date
        expires_at = datetime.now() + timedelta(days=days)
        
        # Update the subscriptions table (matching main bot's schema)
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at, purchased_at, notified_about_expiry, notified_about_expiry_soon)
            VALUES ($1, $2, $3, NOW(), FALSE, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET 
            plan = EXCLUDED.plan, 
            expires_at = EXCLUDED.expires_at,
            purchased_at = NOW(),
            notified_about_expiry = FALSE,
            notified_about_expiry_soon = FALSE
        """, user_id, plan_id, expires_at)
        
        logger.info(f"✅ Updated subscription for user {user_id}: {plan_id} for {days} days")
        
    except Exception as e:
        logger.error(f"❌ Error updating subscription for user {user_id}: {e}")
        # Don't re-raise, just log the error

async def get_payment_with_screenshot(payment_id):
    """Get payment details including screenshot if available"""
    try:
        db = await get_db()
        payment = await db.fetchrow(
            "SELECT * FROM payments WHERE id=$1",
            payment_id
        )
        
        if payment and payment.get('screenshot_message_id'):
            # Try to get the screenshot message
            try:
                screenshot_msg = await bot.get_messages(
                    payment['user_id'],
                    ids=payment['screenshot_message_id']
                )
                if screenshot_msg and screenshot_msg.media:
                    return payment, screenshot_msg
            except Exception as e:
                logger.error(f"Error fetching screenshot: {e}")
        
        return payment, None
    except Exception as e:
        logger.error(f"Error getting payment with screenshot: {e}")
        return None, None

# ---------------- PAYMENT HANDLERS ----------------

@bot.on(events.CallbackQuery(pattern=r'plan_(.+)'))
async def plan_handler(event):
    user_id = event.sender_id
    data_parts = event.data.decode('utf-8').split('_')
    plan_id = data_parts[1]
    
    # Check if discount code is included
    discount_code = data_parts[2] if len(data_parts) > 2 else None
    
    if plan_id not in PLANS:
        await event.answer("Invalid plan selection")
        return
    
    plans_to_show = get_discounted_plans(discount_code)
    plan = plans_to_show[plan_id]
    
    # Store the selected plan in database
    try:
        db = await get_db()
        notes = f"Discount: {discount_code} ({active_discounts[discount_code]['percentage']}% OFF)" if discount_code else None
        amount = plan['price_inr']  # Use discounted price if available
        
        await db.execute("""
            INSERT INTO payments (user_id, plan_id, amount, status, notes)
            VALUES ($1, $2, $3, 'selected', $4)
            ON CONFLICT (user_id) DO UPDATE SET 
                plan_id = EXCLUDED.plan_id, 
                amount = EXCLUDED.amount, 
                status = EXCLUDED.status,
                notes = EXCLUDED.notes
        """, user_id, plan_id, amount, notes)
    except Exception as e:
        logger.error(f"Error storing payment selection: {e}")
        await event.answer("Database error. Please try again.")
        return
    
    # Delete previous message if exists
    try:
        await event.delete()
    except:
        pass
    
    if discount_code:
        # Show discounted plan details
        percentage = active_discounts[discount_code]['percentage']
        original_plan = PLANS[plan_id]
        
        await event.respond(
            f"🎫 **{plan['name']} Plan with {percentage}% OFF**\n"
            f"💰 Original: {original_plan['price_ton']} TON | ₹{original_plan['price_inr']} | ${original_plan['price_usd']}\n"
            f"💰 **Discounted: {plan['price_ton']} TON | ₹{plan['price_inr']:.0f} | ${plan['price_usd']:.2f}**\n"
            f"⏰ Duration: {plan['days']} days\n"
            f"🎫 Discount Code: {discount_code}\n\n"
            "Please choose your payment method:",
            buttons=[
                [Button.inline("💰 TON Crypto", data=f"pay_ton_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("🇮🇳 UPI Payment (₹)", data=f"pay_upi_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("📱 Scan QR Code (₹)", data=f"pay_qr_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("🌎 PayPal ($)", data=f"pay_paypal_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("🔙 Back to Plans", data="show_plans" + (f"_{discount_code}" if discount_code else ""))]
            ]
        )
    else:
        # Show regular plan details
        await event.respond(
            f"💎 **{plan['name']} Plan**\n"
            f"💰 Price: {plan['price_ton']} TON | ₹{plan['price_inr']} | ${plan['price_usd']}\n"
            f"⏰ Duration: {plan['days']} days\n\n"
            "Please choose your payment method:",
            buttons=[
                [Button.inline("💰 TON Crypto", data=f"pay_ton_{plan_id}")],
                [Button.inline("🇮🇳 UPI Payment (₹)", data=f"pay_upi_{plan_id}")],
                [Button.inline("📱 Scan QR Code (₹)", data=f"pay_qr_{plan_id}")],
                [Button.inline("🌎 PayPal ($)", data=f"pay_paypal_{plan_id}")],
                [Button.inline("🔙 Back to Plans", data="back_to_plans")]
            ]
        )

@bot.on(events.NewMessage(pattern='/refresh_plans'))
async def refresh_plans_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
    
    try:
        count = 0
        for message_id, (chat_id, _) in list(active_plan_messages.items()):
            try:
                await update_specific_plan_message(chat_id, message_id)
                count += 1
            except Exception as e:
                logger.error(f"Error refreshing message {message_id}: {e}")
                # Remove invalid messages from tracking
                del active_plan_messages[message_id]
        
        await event.respond(f"✅ Refreshed {count} active plan messages with current prices.")
        
    except Exception as e:
        logger.error(f"Error refreshing plans: {e}")
        await event.respond("❌ Error refreshing plan messages.")

def has_media_but_not_webpage(event):
    """Check if message has media but is not a webpage"""
    if not event.media:
        return False
    # Check if media has webpage attribute and it's truthy
    if hasattr(event.media, 'webpage') and event.media.webpage:
        return False
    return True

@bot.on(events.NewMessage(func=has_media_but_not_webpage))
async def screenshot_handler(event):
    user_id = event.sender_id
    
    # Check if user has a pending payment
    try:
        db = await get_db()
        payment = await db.fetchrow(
            "SELECT * FROM payments WHERE user_id=$1 AND status IN ('pending', 'pending_approval')",
            user_id
        )
        
        if not payment:
            return  # Not in payment flow, ignore media
            
        # Check if media is an image or document (screenshot)
        if isinstance(event.media, (MessageMediaPhoto, MessageMediaDocument)):
            # Store the screenshot reference
            user_payment_screenshots[user_id] = {
                'file_id': event.media.photo.id if isinstance(event.media, MessageMediaPhoto) else event.media.document.id,
                'message_id': event.id,
                'chat_id': event.chat_id
            }
            
            # Update payment record with screenshot info
            await db.execute(
                "UPDATE payments SET screenshot_message_id=$1 WHERE user_id=$2",
                event.id, user_id
            )
            
            await event.reply(
                "📸 **Screenshot Received!**\n\n"
                "Thank you for sending your payment proof. Our team will review it shortly.\n\n"
                "Please click '✅ I've Paid' below to complete your submission.",
                buttons=[[Button.inline("✅ I've Paid", data=f"confirm_{payment['plan_id']}")]]
            )
            
    except Exception as e:
        logger.error(f"Error handling screenshot: {e}")

@bot.on(events.CallbackQuery(pattern=r'approve_'))
async def approve_callback_handler(event):
    """Handle approve button clicks from notifications"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    payment_id = int(event.data.decode('utf-8').split('_')[1])
    
    try:
        db = await get_db()
        
        # Get payment details with screenshot
        payment, screenshot_msg = await get_payment_with_screenshot(payment_id)
        
        if not payment:
            await event.answer("❌ Payment not found.")
            return
            
        if payment['status'] != 'pending_approval':
            await event.answer(f"❌ Payment is already {payment['status']}.")
            return
        
        # Get plan details
        plan = PLANS.get(payment['plan_id'])
        if not plan:
            await event.answer("❌ Invalid plan in payment record.")
            return
        
        # Update payment status FIRST
        await db.execute(
            "UPDATE payments SET status='approved', processed_at=NOW(), admin_id=$1 WHERE id=$2",
            user_id, payment_id
        )
        
        # THEN update the subscription in the shared database
        await update_subscription_in_main_bot(payment['user_id'], payment['plan_id'], plan['days'])
        
        # Notify user
        try:
            expires_at = datetime.now() + timedelta(days=plan['days'])
            await bot.send_message(
                payment['user_id'],
                f"🎉 **Your Premium Plan Has Been Activated!**\n\n"
                f"Plan: {plan['name']}\n"
                f"Purchase Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Expiry: {expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                "Thank you for your purchase! You can now enjoy enhanced forwarding capabilities.\n\n"
                "Return to your main bot to start using your premium features!"
            )
        except Exception as e:
            logger.error(f"Could not notify user {payment['user_id']}: {e}")
        
        await event.answer(f"✅ Payment #{payment_id} approved successfully!")
        await event.edit(f"✅ Payment #{payment_id} approved by admin!")
        
    except Exception as e:
        logger.error(f"Error approving payment via callback: {e}")
        await event.answer("❌ Error approving payment.")

@bot.on(events.NewMessage(pattern=r'/reject'))
async def reject_payment_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 3:
        await event.respond(
            "Usage: /reject <payment_id> <reason>\n\n"
            "**Common rejection reasons:**\n"
            "• invalid_screenshot - Screenshot unclear or missing\n"
            "• wrong_amount - Payment amount incorrect\n"
            "• no_payment_found - No payment received\n"
            "• suspicious_activity - Suspicious payment\n"
            "• duplicate_payment - Payment already processed\n"
            "• other - Other reasons (specify in notes)\n\n"
            "**Examples:**\n"
            "/reject 15 invalid_screenshot\n"
            "/reject 23 wrong_amount\n"
            "/reject 45 no_payment_found"
        )
        return
        
    try:
        payment_id = int(parts[1])
        reason_code = parts[2].lower()
        
        # Get additional notes if provided
        notes = ' '.join(parts[3:]) if len(parts) > 3 else ""
        
        # Validate reason code
        valid_reasons = {
            'invalid_screenshot': 'Invalid or unclear screenshot',
            'wrong_amount': 'Incorrect payment amount',
            'no_payment_found': 'No payment received',
            'suspicious_activity': 'Suspicious payment activity',
            'duplicate_payment': 'Duplicate payment detected',
            'other': 'Other reason'
        }
        
        if reason_code not in valid_reasons:
            await event.respond(
                f"❌ Invalid reason code. Available options:\n" +
                "\n".join([f"• {code} - {desc}" for code, desc in valid_reasons.items()])
            )
            return
        
        reason_description = valid_reasons[reason_code]
        if notes and reason_code == 'other':
            reason_description = notes
        elif notes:
            reason_description = f"{valid_reasons[reason_code]} - {notes}"
        
        await process_payment_rejection(payment_id, user_id, reason_description, event)
        
    except ValueError:
        await event.respond("❌ Invalid payment ID. Please provide a numeric payment ID.")
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        await event.respond("❌ Error rejecting payment.")

async def process_payment_rejection(payment_id, admin_id, reason, event=None):
    """Process payment rejection with proper notification"""
    try:
        db = await get_db()
        
        # Get payment details
        payment = await db.fetchrow(
            "SELECT * FROM payments WHERE id=$1",
            payment_id
        )
        
        if not payment:
            if event:
                await event.respond("❌ Payment not found.")
            return False
            
        if payment['status'] != 'pending_approval':
            if event:
                await event.respond(f"❌ Payment is already {payment['status']}.")
            return False
        
        # Update payment status with rejection reason
        await db.execute("""
            UPDATE payments 
            SET status='rejected', 
                processed_at=NOW(), 
                admin_id=$1,
                notes=$2
            WHERE id=$3
        """, admin_id, f"REJECTED: {reason}", payment_id)
        
        # Notify user about rejection
        try:
            plan = PLANS.get(payment['plan_id'], {'name': 'Unknown Plan'})
            
            rejection_message = (
                "❌ **Payment Rejected**\n\n"
                f"Your payment for **{plan['name']}** has been rejected.\n\n"
                f"**Reason:** {reason}\n\n"
            )
            
            # Add specific instructions based on rejection reason
            if 'screenshot' in reason.lower():
                rejection_message += (
                    "**What to do next:**\n"
                    "• Please send a clear screenshot of your payment\n"
                    "• Make sure transaction details are visible\n"
                    "• Resend the screenshot and click 'I've Paid' again\n"
                )
            elif 'amount' in reason.lower():
                rejection_message += (
                    "**What to do next:**\n"
                    "• Please verify the correct amount for your selected plan\n"
                    "• Make a new payment with the correct amount\n"
                    "• Send the new payment screenshot\n"
                )
            elif 'duplicate' in reason.lower():
                rejection_message += (
                    "**What to do next:**\n"
                    "• Your payment was already processed\n"
                    "• Check your subscription status with /my_plan\n"
                    "• Contact support if you believe this is an error\n"
                )
            else:
                rejection_message += (
                    "**What to do next:**\n"
                    "• Please contact support for assistance\n"
                    "• Or try making the payment again\n"
                )
            
            rejection_message += "\nIf you believe this is a mistake, please contact support."
            
            await bot.send_message(
                payment['user_id'],
                rejection_message,
                buttons=[
                    [Button.inline("🔄 Try Again", data="show_plans")],
                    [Button.inline("📋 Check Status", data="show_my_plan")]
                ]
            )
            
        except Exception as e:
            logger.error(f"Could not notify user {payment['user_id']} about rejection: {e}")
        
        # Notify admins about the rejection
        admin_message = (
            f"❌ **Payment Rejected**\n\n"
            f"Payment ID: `{payment_id}`\n"
            f"User ID: `{payment['user_id']}`\n"
            f"Admin: `{admin_id}`\n"
            f"Reason: {reason}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        await notify_admins(admin_message)
        
        if event:
            await event.respond(
                f"✅ Payment #{payment_id} rejected successfully!\n"
                f"Reason: {reason}\n\n"
                "User has been notified about the rejection."
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Error in process_payment_rejection: {e}")
        if event:
            await event.respond("❌ Error processing payment rejection.")
        return False

@bot.on(events.CallbackQuery(pattern=r'reject_reason_(\d+)_(.+)'))
async def reject_reason_handler(event):
    """Handle specific rejection reason selection"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    # Extract payment_id and reason_code using regex groups
    payment_id = int(event.pattern_match.group(1))
    reason_code = event.pattern_match.group(2)
    
    # Map reason codes to descriptions
    reason_descriptions = {
        'invalid_screenshot': 'Invalid or unclear screenshot',
        'wrong_amount': 'Incorrect payment amount',
        'no_payment_found': 'No payment received',
        'suspicious_activity': 'Suspicious payment activity',
        'duplicate_payment': 'Duplicate payment detected',
        'other': 'Other reason'
    }
    
    reason_description = reason_descriptions.get(reason_code, 'Unknown reason')
    
    # Process immediate rejection with single reason
    success = await process_payment_rejection(payment_id, user_id, reason_description, event)
    if success:
        await event.answer(f"✅ Payment #{payment_id} rejected!")
    else:
        await event.answer("❌ Failed to reject payment")

# Add a new handler for multiple reason selection
@bot.on(events.CallbackQuery(pattern=r'reject_multiple_(\d+)'))
async def reject_multiple_handler(event):
    """Handle multiple rejection reason selection"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    payment_id = int(event.pattern_match.group(1))
    
    # Store selected reasons
    if not hasattr(event, 'selected_reasons'):
        event.selected_reasons = set()
    
    # Get the button text to determine which reason was clicked
    button_text = event.data.decode('utf-8')
    
    # Map button patterns to reasons
    reason_mapping = {
        'invalid_screenshot': 'Invalid or unclear screenshot',
        'wrong_amount': 'Incorrect payment amount', 
        'no_payment_found': 'No payment received',
        'suspicious_activity': 'Suspicious payment activity',
        'duplicate_payment': 'Duplicate payment detected'
    }
    
    # Find which reason was selected
    selected_reason = None
    for reason_code in reason_mapping.keys():
        if reason_code in button_text:
            selected_reason = reason_mapping[reason_code]
            break
    
    if selected_reason:
        if selected_reason in event.selected_reasons:
            event.selected_reasons.remove(selected_reason)
        else:
            event.selected_reasons.add(selected_reason)
    
    # Update the interface to show selected reasons
    buttons = []
    for reason_code, reason_text in reason_mapping.items():
        is_selected = reason_text in event.selected_reasons
        checkbox = "✅" if is_selected else "☐"
        buttons.append([Button.inline(f"{checkbox} {reason_text}", data=f"toggle_reason_{payment_id}_{reason_code}")])
    
    buttons.append([Button.inline("🚫 Other Reason", data=f"reject_other_{payment_id}")])
    
    if event.selected_reasons:
        buttons.append([Button.inline(f"🔴 REJECT WITH {len(event.selected_reasons)} REASONS", data=f"confirm_multiple_reject_{payment_id}")])
    
    buttons.append([Button.inline("🔙 Cancel", data=f"cancel_reject_{payment_id}")])
    
    selected_text = ", ".join(event.selected_reasons) if event.selected_reasons else "None"
    
    await event.edit(
        f"❌ **Reject Payment #{payment_id}**\n\n"
        f"**Selected Reasons:** {selected_text}\n\n"
        "Click reasons to select/deselect multiple:",
        buttons=buttons
    )

@bot.on(events.CallbackQuery(pattern=r'toggle_reason_(\d+)_(.+)'))
async def toggle_reason_handler(event):
    """Toggle individual reason selection"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    payment_id = int(event.pattern_match.group(1))
    reason_code = event.pattern_match.group(2).decode('utf-8')  # Convert bytes to string
    
    # Ensure selections exist for this user and payment
    if user_id not in user_rejection_selections:
        user_rejection_selections[user_id] = {}
    if payment_id not in user_rejection_selections[user_id]:
        user_rejection_selections[user_id][payment_id] = set()
    
    # Toggle the reason
    if reason_code in user_rejection_selections[user_id][payment_id]:
        user_rejection_selections[user_id][payment_id].remove(reason_code)
    else:
        user_rejection_selections[user_id][payment_id].add(reason_code)
    
    # Update the interface
    rejection_reasons = {
        'invalid_screenshot': '📸 Invalid Screenshot',
        'wrong_amount': '💰 Wrong Amount', 
        'no_payment_found': '❓ No Payment Found',
        'suspicious_activity': '🚫 Suspicious Activity',
        'duplicate_payment': '🔄 Duplicate Payment'
    }
    
    buttons = []
    for rc, reason_text in rejection_reasons.items():
        is_selected = rc in user_rejection_selections[user_id][payment_id]
        checkbox = "✅" if is_selected else "☐"
        buttons.append([Button.inline(f"{checkbox} {reason_text}", data=f"toggle_reason_{payment_id}_{rc}")])
    
    buttons.append([Button.inline("📝 Other Reason", data=f"reject_other_{payment_id}")])
    
    # Add confirm button if reasons are selected
    selected_count = len(user_rejection_selections[user_id][payment_id])
    if selected_count > 0:
        buttons.append([Button.inline(f"🔴 REJECT WITH {selected_count} REASONS", data=f"confirm_multiple_reject_{payment_id}")])
    
    buttons.append([Button.inline("🔙 Cancel", data=f"cancel_reject_{payment_id}")])
    
    # Build selected text - handle the case where selection might be empty
    selected_codes = user_rejection_selections[user_id][payment_id]
    selected_text = ", ".join([rejection_reasons.get(code, code) for code in selected_codes]) if selected_codes else "None"
    
    # Create a unique message to avoid MessageNotModifiedError
    message = (
        f"❌ **Reject Payment #{payment_id}**\n\n"
        f"**Selected Reasons:** {selected_text}\n\n"
        f"Click reasons to select/deselect. Current selections: {selected_count}"
    )
    
    try:
        await event.edit(message, buttons=buttons)
    except Exception as e:
        if "MessageNotModifiedError" not in str(e):
            logger.error(f"Error editing rejection interface: {e}")
            await event.answer("❌ Error updating interface")

@bot.on(events.CallbackQuery(pattern=r'confirm_multiple_reject_(\d+)'))
async def confirm_multiple_reject_handler(event):
    """Confirm rejection with multiple reasons"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    payment_id = int(event.pattern_match.group(1))
    
    # Get selected reasons
    if (user_id in user_rejection_selections and 
        payment_id in user_rejection_selections[user_id] and 
        user_rejection_selections[user_id][payment_id]):
        
        # Map reason codes to descriptions
        reason_descriptions = {
            'invalid_screenshot': 'Invalid or unclear screenshot',
            'wrong_amount': 'Incorrect payment amount',
            'no_payment_found': 'No payment received',
            'suspicious_activity': 'Suspicious payment activity',
            'duplicate_payment': 'Duplicate payment detected'
        }
        
        # Convert selected codes to readable reasons
        selected_reasons = [reason_descriptions[code] for code in user_rejection_selections[user_id][payment_id] if code in reason_descriptions]
        reasons_text = ", ".join(selected_reasons)
        
        # Process rejection
        success = await process_payment_rejection(payment_id, user_id, reasons_text, event)
        if success:
            # Clean up selection
            if user_id in user_rejection_selections and payment_id in user_rejection_selections[user_id]:
                del user_rejection_selections[user_id][payment_id]
            await event.answer(f"✅ Payment #{payment_id} rejected!")
        else:
            await event.answer("❌ Failed to reject payment")
    else:
        await event.answer("❌ Please select at least one rejection reason")


# Update the main reject handler to use multiple selection
user_rejection_selections = {}  # {user_id: {payment_id: set(reasons)}}

@bot.on(events.CallbackQuery(pattern=r'reject_(\d+)'))
async def reject_callback_handler(event):
    """Handle reject button clicks from notifications with multiple reason selection"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    # Extract payment_id using regex group
    payment_id = int(event.pattern_match.group(1))
    
    # Initialize selection for this user and payment
    if user_id not in user_rejection_selections:
        user_rejection_selections[user_id] = {}
    user_rejection_selections[user_id][payment_id] = set()
    
    # Show multiple rejection reason options
    rejection_reasons = {
        'invalid_screenshot': '📸 Invalid Screenshot',
        'wrong_amount': '💰 Wrong Amount', 
        'no_payment_found': '❓ No Payment Found',
        'suspicious_activity': '🚫 Suspicious Activity',
        'duplicate_payment': '🔄 Duplicate Payment'
    }
    
    buttons = []
    for reason_code, reason_text in rejection_reasons.items():
        is_selected = reason_code in user_rejection_selections[user_id][payment_id]
        checkbox = "✅" if is_selected else "☐"
        buttons.append([Button.inline(f"{checkbox} {reason_text}", data=f"toggle_reason_{payment_id}_{reason_code}")])
    
    buttons.append([Button.inline("📝 Other Reason", data=f"reject_other_{payment_id}")])
    
    # Add confirm button if reasons are selected
    selected_count = len(user_rejection_selections[user_id][payment_id])
    if selected_count > 0:
        buttons.append([Button.inline(f"🔴 REJECT WITH {selected_count} REASONS", data=f"confirm_multiple_reject_{payment_id}")])
    
    buttons.append([Button.inline("🔙 Cancel", data=f"cancel_reject_{payment_id}")])
    
    selected_text = ", ".join([rejection_reasons[code] for code in user_rejection_selections[user_id][payment_id]]) if user_rejection_selections[user_id][payment_id] else "None"
    
    try:
        await event.edit(
            f"❌ **Reject Payment #{payment_id}**\n\n"
            f"**Selected Reasons:** {selected_text}\n\n"
            "Click reasons to select/deselect:",
            buttons=buttons
        )
    except Exception as e:
        if "MessageNotModifiedError" not in str(e):
            logger.error(f"Error showing rejection interface: {e}")
            await event.answer("❌ Error loading rejection interface")

@bot.on(events.CallbackQuery(pattern=r'reject_other_(\d+)'))
async def reject_other_handler(event):
    """Handle other reason selection"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    payment_id = int(event.pattern_match.group(1))
    
    # Clean up any existing selections
    if user_id in user_rejection_selections and payment_id in user_rejection_selections[user_id]:
        del user_rejection_selections[user_id][payment_id]
    
    await event.edit(
        f"❌ **Reject Payment #{payment_id}**\n\n"
        "Please provide the rejection reason:\n"
        "(Send as a message in this chat)",
        buttons=[[Button.inline("🔙 Back", data=f"reject_{payment_id}")]]
    )
    
    # Store the pending rejection context
    if not hasattr(bot, 'pending_rejections'):
        bot.pending_rejections = {}
    bot.pending_rejections[user_id] = {
        'payment_id': payment_id,
        'reason_code': 'other'
    }

@bot.on(events.CallbackQuery(pattern=r'cancel_reject_(\d+)'))
async def cancel_reject_handler(event):
    """Cancel rejection process"""
    user_id = event.sender_id
    payment_id = int(event.pattern_match.group(1))
    
    # Clean up selections
    if user_id in user_rejection_selections and payment_id in user_rejection_selections[user_id]:
        del user_rejection_selections[user_id][payment_id]
    
    await event.answer("❌ Rejection cancelled.")
    await event.delete()

@bot.on(events.NewMessage(func=lambda e: e.sender_id in getattr(bot, 'pending_rejections', {})))
async def handle_custom_rejection_reason(event):
    """Handle custom rejection reasons from admins"""
    user_id = event.sender_id
    pending_data = bot.pending_rejections.get(user_id)
    
    if not pending_data:
        return
    
    payment_id = pending_data['payment_id']
    custom_reason = event.raw_text
    
    # Process rejection with custom reason
    success = await process_payment_rejection(payment_id, user_id, custom_reason, event)
    
    if success:
        await event.respond(f"✅ Payment #{payment_id} rejected with custom reason!")
    else:
        await event.respond("❌ Failed to reject payment")
    
    # Clean up pending rejection
    del bot.pending_rejections[user_id]

async def get_payment_stats():
    """Get comprehensive payment statistics"""
    try:
        db = await get_db()
        
        stats = await db.fetchrow("""
            SELECT 
                COUNT(*) as total_payments,
                COUNT(CASE WHEN status='approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status='rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN status='pending_approval' THEN 1 END) as pending,
                COUNT(CASE WHEN status='selected' THEN 1 END) as selected,
                COALESCE(SUM(CASE WHEN status='approved' THEN amount ELSE 0 END), 0) as total_revenue,
                COUNT(DISTINCT user_id) as unique_payers
            FROM payments
        """)
        
        # Get rejection reasons breakdown
        rejection_reasons = await db.fetch("""
            SELECT 
                CASE 
                    WHEN notes LIKE 'REJECTED: %' THEN SUBSTRING(notes FROM 11)
                    ELSE 'No reason provided'
                END as reason,
                COUNT(*) as count
            FROM payments 
            WHERE status='rejected'
            GROUP BY reason
            ORDER BY count DESC
        """)
        
        return stats, rejection_reasons
    except Exception as e:
        logger.error(f"Error getting payment stats: {e}")
        return None, None

@bot.on(events.CallbackQuery(pattern=r'admin_payments'))
async def admin_payments_handler(event):
    """Handle View All Pending button"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    try:
        db = await get_db()
        payments = await db.fetch(
            "SELECT p.* FROM payments p WHERE p.status='pending_approval' ORDER BY p.created_at DESC LIMIT 10"
        )
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        await event.answer("❌ Error accessing database.")
        return
    
    if not payments:
        await event.answer("✅ No pending payments.")
        return
    
    message = "⏳ **Pending Payments:**\n\n"
    for payment in payments:
        plan = PLANS.get(payment['plan_id'], {'name': 'Unknown', 'price_inr': 0, 'price_ton': 0})
        has_screenshot = "✅" if payment.get('screenshot_message_id') else "❌"
        message += (
            f"💰 **Payment #{payment['id']}**\n"
            f"User: `{payment['user_id']}`\n"
            f"Plan: {plan['name']} ({plan['price_ton']} TON | ₹{plan['price_inr']})\n"
            f"Method: {payment.get('payment_method', 'unknown')}\n"
            f"Screenshot: {has_screenshot}\n"
            f"Date: {payment['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    buttons = []
    for payment in payments:
        buttons.append([
            Button.inline(f"✅ Approve #{payment['id']}", data=f"approve_{payment['id']}"),
            Button.inline(f"❌ Reject #{payment['id']}", data=f"reject_{payment['id']}")
        ])
        # Add button to view screenshot if available
        if payment.get('screenshot_message_id'):
            buttons.append([
                Button.inline(f"📸 View Screenshot #{payment['id']}", data=f"view_screenshot_{payment['id']}")
            ])
    
    buttons.append([Button.inline("🔄 Refresh", data="admin_payments_refresh")])
    
    try:
        await event.edit(message, buttons=buttons)
    except Exception as e:
        if "MessageNotModifiedError" in str(e):
            # Message content is the same, just acknowledge the click
            await event.answer("✅ List is already up to date!")
        else:
            logger.error(f"Error editing message: {e}")
            await event.answer("❌ Error updating message.")

@bot.on(events.CallbackQuery(pattern=r'admin_payments_refresh'))
async def admin_payments_refresh_handler(event):
    """Handle Refresh button in payments list"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    # Show refreshing indicator
    await event.answer("🔄 Refreshing...")
    
    # Reuse the existing payments_handler logic
    await admin_payments_handler(event)

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
    
    try:
        stats, rejection_reasons = await get_payment_stats()
        
        if not stats:
            await event.respond("❌ Error fetching statistics.")
            return
        
        message = "📊 **Payment Statistics**\n\n"
        
        message += "📈 **Overview:**\n"
        message += f"• Total Payments: {stats['total_payments']}\n"
        message += f"• Approved: {stats['approved']}\n"
        message += f"• Rejected: {stats['rejected']}\n"
        message += f"• Pending: {stats['pending']}\n"
        message += f"• Selected: {stats['selected']}\n"
        message += f"• Unique Payers: {stats['unique_payers']}\n"
        message += f"• Total Revenue: ₹{stats['total_revenue']:.2f}\n\n"
        
        if rejection_reasons:
            message += "❌ **Rejection Reasons:**\n"
            for reason in rejection_reasons[:5]:  # Top 5 reasons
                message += f"• {reason['reason']}: {reason['count']}\n"
        
        # Add quick action buttons
        buttons = [
            [Button.inline("🔄 Refresh Stats", data="admin_stats_refresh")],
            [Button.inline("📋 Pending Payments", data="admin_payments")],
            [Button.inline("👥 User Management", data="admin_users_refresh")]
        ]
        
        await event.respond(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error in stats handler: {e}")
        await event.respond("❌ Error generating statistics.")

@bot.on(events.CallbackQuery(pattern=r'admin_refresh'))
async def admin_refresh_handler(event):
    """Handle admin refresh button"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    # Get stats for admin dashboard
    try:
        db = await get_db()
        pending_count = await db.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status='pending_approval'"
        )
        approved_today = await db.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status='approved' AND processed_at >= CURRENT_DATE"
        )
        revenue_today = await db.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='approved' AND processed_at >= CURRENT_DATE"
        )
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        pending_count = 0
        approved_today = 0
        revenue_today = 0
    
    await event.edit(
        f"👑 **Admin Panel**\n\n"
        f"📊 Today's Stats:\n"
        f"• Pending approvals: {pending_count}\n"
        f"• Approved today: {approved_today}\n"
        f"• Revenue today: ${revenue_today:.2f}\n\n"
        "Available commands:\n"
        "/payments - View pending payments\n"
        "/approve <payment_id> - Approve a payment\n"
        "/reject <payment_id> <reason> - Reject a payment\n"
        "/users - View all subscribers\n"
        "/stats - View payment statistics\n"
        "/addadmin <user_id> - Add new admin",
        buttons=[[Button.inline("🔄 Refresh", data="admin_refresh")]]
    )

@bot.on(events.CallbackQuery(pattern=r'pay_'))
async def payment_method_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    parts = data.split('_')
    method = parts[1]
    plan_id = parts[2]
    
    # Check for discount code
    discount_code = parts[3] if len(parts) > 3 else None
    
    if plan_id not in PLANS:
        await event.answer("Invalid plan selection")
        return
        
    plans_to_show = get_discounted_plans(discount_code)
    plan = plans_to_show[plan_id]
    
    # Update payment method in database
    try:
        db = await get_db()
        await db.execute(
            "UPDATE payments SET payment_method=$1, status='pending' WHERE user_id=$2",
            method, user_id
        )
    except Exception as e:
        logger.error(f"Error updating payment method: {e}")
    
    screenshot_instruction = (
        "**📸 After payment, please send your payment screenshot or transaction hash "
        "before clicking 'I've Paid'.**\n\n"
    )
    
    if method == "upi":
        await event.edit(
            f"💎 **{plan['name']} Plan**\n"
            f"💰 Amount: ₹{plan['price_inr']}\n\n"
            "**Please send payment to our UPI ID:**\n"
            f"`{UPI_ID}`\n\n"
            "**Payment Instructions:**\n"
            f"1. Open your UPI app (GPay, PhonePe, PayTM)\n"
            f"2. Send ₹{plan['price_inr']} to the UPI ID above\n"
            f"3. Save the transaction ID\n"
            f"4. Take a screenshot for verification\n\n"
            + screenshot_instruction +
            "**After sending screenshot, click 'I've Paid' below**\n"
            "We'll activate your plan within 24 hours.",
            buttons=[
                [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
            ]
        )
    
    elif method == "qr":
        try:
            # Delete the previous message for cleaner experience
            await event.delete()
            
            # Get the appropriate QR code file
            qr_file = QR_CODE_FILES.get(plan_id, QR_CODE_FILES["default"])
            
            # Prepare the caption/message
            caption = (
                f"💎 **{plan['name']} Plan**\n"
                f"💰 Amount: ₹{plan['price_inr']}\n\n"
                "**Scan the QR code using your UPI app:**\n\n"
                f"**Amount to pay: ₹{plan['price_inr']}**\n\n"
                "**Payment Instructions:**\n"
                f"1. Scan the QR code with your UPI app\n"
                f"2. Verify amount is ₹{plan['price_inr']}\n"
                f"3. Complete the payment\n"
                f"4. Save the transaction ID\n"
                f"5. Take a screenshot\n\n"
                + screenshot_instruction +
                ""
            )
            
            # Get the appropriate QR code file
            qr_file = QR_CODE_FILES.get(plan_id, QR_CODE_FILES["default"])
            
            # Send QR code as photo
            await bot.send_file(
                event.chat_id,
                file=qr_file,
                caption=caption,
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )
            
        except FileNotFoundError:
            logger.error(f"QR code file not found: {qr_file}")
            await event.respond(
                f"❌ QR code not available. Please use UPI payment instead.\n\n"
                f"Amount: ₹{plan['price_inr']}\nUPI ID: `{UPI_ID}`",
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )
        except Exception as e:
            logger.error(f"Error sending QR code: {e}")
            # Fallback to text message
            await event.respond(
                f"💎 **{plan['name']} Plan**\n"
                f"💰 Amount: ₹{plan['price_inr']}\n\n"
                "**QR Code payment is temporarily unavailable.**\n\n"
                f"Please use UPI payment instead:\nUPI ID: `{UPI_ID}`",
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )
    
    elif method == "paypal":
        await event.edit(
            f"💎 **{plan['name']} Plan**\n"
            f"💰 Amount: ${plan['price_usd']} (≈₹{plan['price_inr']})\n\n"
            "**International Payment via PayPal:**\n\n"
            "**After payment:**\n"
            "1. Save the transaction ID\n"
            "2. Take a screenshot\n"
            + screenshot_instruction +
            "Activation within 24 hours after verification.",
            buttons=[
                [Button.url("🌎 Pay with PayPal", PAYPAL_LINK)],
                [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
            ]
        )
    
    elif method == "ton":  # Add TON payment method
    # Delete the previous message for cleaner experience
        try:
            await event.delete()
        except:
            pass
        
        try:
            # Get the TON QR code file
            qr_file = QR_CODE_FILES.get("ton", QR_CODE_FILES["default"])
            
            caption = (
                f"💎 **{plan['name']} Plan**\n"
                f"💰 Amount: {plan['price_ton']} TON\n"
                f"    (≈₹{plan['price_inr']} | ≈${plan['price_usd']})\n\n"
                "**Payment Options:**\n\n"
                f"**Option 1: Scan QR Code**\n"
                f"1. Scan the QR code with your TON wallet app\n"
                f"2. Verify amount is {plan['price_ton']} TON\n"
                f"3. Complete the payment\n"
                f"4. Save the transaction hash\n\n"
                f"**Option 2: Manual Transfer**\n"
                f"1. Open your TON wallet app\n"
                f"2. Send exactly {plan['price_ton']} TON to:\n"
                f"`{TON_WALLET_ADDRESS}`\n"
                f"3. Save the transaction hash (TX ID)\n\n"
                "**After payment:**\n"
                "• Take a screenshot of the transaction\n"
                "• Or copy the transaction details\n"
                "• Click '✅ I've Paid' below\n\n"
                "We'll verify and activate your plan within 24 hours."
            )
            
            # Send QR code as photo
            await bot.send_file(
                event.chat_id,
                file=qr_file,
                caption=caption,
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )
            
        except FileNotFoundError:
            logger.error(f"TON QR code file not found: {qr_file}")
            # Fallback to text-only TON payment
            await event.respond(
                f"💎 **{plan['name']} Plan**\n"
                f"💰 Amount: {plan['price_ton']} TON\n"
                f"    (≈₹{plan['price_inr']} | ≈${plan['price_usd']})\n\n"
                "**Please send payment to our TON Wallet:**\n"
                f"`{TON_WALLET_ADDRESS}`\n\n"
                "**Payment Instructions:**\n"
                f"1. Open your TON wallet app\n"
                f"2. Send exactly {plan['price_ton']} TON to the address above\n"
                f"3. Save the transaction hash (TX ID)\n"
                f"4. Take a screenshot or copy the transaction details\n\n"
                + screenshot_instruction +
                "**After sending payment proof, click 'I've Paid' below**\n"
                "We'll activate your plan within 24 hours.",
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )
        except Exception as e:
            logger.error(f"Error sending TON QR code: {e}")
            # Fallback to text message
            await event.respond(
                f"💎 **{plan['name']} Plan**\n"
                f"💰 Amount: {plan['price_ton']} TON\n"
                f"    (≈₹{plan['price_inr']} | ≈${plan['price_usd']})\n\n"
                "**QR Code payment is temporarily unavailable.**\n\n"
                f"Please send {plan['price_ton']} TON to:\n"
                f"`{TON_WALLET_ADDRESS}`",
                buttons=[
                    [Button.inline("✅ I've Paid", data=f"confirm_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
                    [Button.inline("🔙 Back to Methods", data=f"back_methods_{plan_id}" + (f"_{discount_code}" if discount_code else ""))]
                ]
            )

@bot.on(events.CallbackQuery(pattern=r'confirm_'))
async def confirm_payment_handler(event):
    plan_id = event.data.decode('utf-8').split('_')[1]
    user_id = event.sender_id
    
    if plan_id not in PLANS:
        await event.answer("Invalid plan selection")
        return
        
    plan = PLANS[plan_id]
    
    # Check if user has sent a screenshot
    if user_id not in user_payment_screenshots:
        await event.answer("❌ Please send your payment screenshot first before clicking 'I've Paid'.", alert=True)
        return
    
    # Update payment status in database
    try:
        db = await get_db()
        await db.execute(
            "UPDATE payments SET status='pending_approval' WHERE user_id=$1",
            user_id
        )
        
        # Get payment record for notification
        payment = await db.fetchrow(
            "SELECT * FROM payments WHERE user_id=$1",
            user_id
        )
    except Exception as e:
        logger.error(f"Error updating payment status: {e}")
        payment = None
    
    await event.edit(
        "✅ **Payment Received for Verification**\n\n"
        "Thank you for your payment and screenshot! Our team will verify it within 24 hours and activate your premium plan.\n\n"
        "You will receive a confirmation message once your subscription is activated.\n\n"
        "If you have any questions, please contact support.",
        buttons=[
            [Button.url("🔙 Back to Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")]
        ]
    )
    
    # Notify admins with screenshot
    if payment:
        payment_id = payment['id']
        plan = PLANS.get(payment['plan_id'], {'name': 'Unknown', 'price_inr': 0, 'price_ton': 0})
        
        message = (
            "🆕 **New Payment Waiting Approval**\n\n"
            f"Payment ID: `{payment_id}`\n"
            f"User ID: `{user_id}`\n"
            f"Plan: {plan['name']}\n"
            f"Amount: {plan['price_ton']} TON | ₹{plan['price_inr']} (${plan['price_usd']})\n"
            f"Method: {payment.get('payment_method', 'unknown')}\n\n"
            "**Screenshot provided!** ✅\n\n"
            "Click the buttons below to manage this payment:"
        )
        
        # Get screenshot message to forward to admin
        screenshot_data = user_payment_screenshots.get(user_id)
        if screenshot_data:
            try:
                # Forward the screenshot to admin with payment info as caption
                caption = f"📸 Payment Screenshot\nPayment ID: {payment_id}\nUser ID: {user_id}"
                
                # Check if the media is a photo or document
                if isinstance(screenshot_data, dict) and 'message_id' in screenshot_data:
                    # Get the original message
                    original_msg = await bot.get_messages(
                        screenshot_data['chat_id'], 
                        ids=screenshot_data['message_id']
                    )
                    
                    if original_msg and original_msg.media:
                        # Forward with caption
                        await bot.send_file(
                            ADMIN_NOTIFICATION_CHAT,
                            file=original_msg.media,
                            caption=caption
                        )
                else:
                    # Fallback to regular forwarding if we can't add caption
                    await bot.forward_messages(
                        ADMIN_NOTIFICATION_CHAT,
                        screenshot_data['message_id'],
                        screenshot_data['chat_id']
                    )
                    # Send the payment info separately
                    await bot.send_message(ADMIN_NOTIFICATION_CHAT, caption)
                    
            except Exception as e:
                logger.error(f"Error forwarding screenshot: {e}")
                message += "\n\n⚠️ *Could not load screenshot*"
        
        buttons = [
            [
                Button.inline(f"✅ Approve #{payment_id}", data=f"approve_{payment_id}"),
                Button.inline(f"❌ Reject #{payment_id}", data=f"reject_{payment_id}")
            ],
            [Button.inline("📸 View Screenshot", data=f"view_screenshot_{payment_id}")]
        ]
        
        await notify_admins(message, buttons)
        
        # Clean up
        if user_id in user_payment_screenshots:
            del user_payment_screenshots[user_id]

# ---------------- ADMIN COMMANDS ----------------
@bot.on(events.NewMessage(pattern='/all_users'))
async def all_users_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    try:
        db = await get_db()
        
        # Get ALL users from users table with comprehensive data
        users = await db.fetch("""
            SELECT u.id as user_id, u.phone, u.session,
                   s.plan, s.expires_at, s.purchased_at,
                   a.last_activity, a.command_count, a.first_seen,
                   fs.is_active as forwarding_active,
                   fs.last_started as forwarding_started
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            LEFT JOIN user_activity a ON u.id = a.user_id
            LEFT JOIN forwarding_status fs ON u.id = fs.user_id
            ORDER BY a.last_activity DESC NULLS LAST, u.id DESC
        """)
        
        if not users:
            await event.respond("❌ No users found in the database.")
            return
        
        # Get additional statistics for each user
        user_stats = {}
        for user in users:
            user_id_val = user['user_id']
            
            # Get rules count and status
            rules = await db.fetch("""
                SELECT COUNT(*) as total_rules, 
                       COUNT(CASE WHEN is_active THEN 1 END) as active_rules
                FROM rules 
                WHERE user_id = $1
            """, user_id_val)
            
            # Get sources count (per rule)
            sources_count = await db.fetch("""
                SELECT rule_id, COUNT(*) as count 
                FROM sources 
                WHERE user_id = $1 
                GROUP BY rule_id
            """, user_id_val)
            
            # Get destinations count (per rule)
            destinations_count = await db.fetch("""
                SELECT rule_id, COUNT(*) as count 
                FROM destinations 
                WHERE user_id = $1 
                GROUP BY rule_id
            """, user_id_val)
            
            # Calculate totals
            total_sources = sum(rule['count'] for rule in sources_count)
            total_destinations = sum(rule['count'] for rule in destinations_count)
            
            user_stats[user_id_val] = {
                'total_rules': rules[0]['total_rules'] if rules else 0,
                'active_rules': rules[0]['active_rules'] if rules else 0,
                'total_sources': total_sources,
                'total_destinations': total_destinations,
                'rules_detail': sources_count  # Using sources_count to show per-rule breakdown
            }
        
        # Get statistics
        total_users = len(users)
        subscribed_users = sum(1 for user in users if user['plan'] is not None and user['expires_at'] and user['expires_at'] > datetime.now())
        
        # Count active users (used bot in last 7 days)
        active_users = 0
        forwarding_active_users = 0
        for user in users:
            if user['last_activity']:
                days_since_active = (datetime.now() - user['last_activity']).days
                if days_since_active < 7:
                    active_users += 1
            if user['forwarding_active']:
                forwarding_active_users += 1
        
        free_users = total_users - sum(1 for user in users if user['plan'] is not None)
        
        message = f"👥 **All Bot Users** ({total_users} total)\n\n"
        message += f"📊 **Statistics:**\n"
        message += f"• Total Registered: {total_users}\n"
        message += f"• Active Subscriptions: {subscribed_users}\n"
        message += f"• Free Users: {free_users}\n"
        message += f"• Recently Active: {active_users} (last 7 days)\n"
        message += f"• Forwarding Active: {forwarding_active_users}\n\n"
        message += "📋 **User Details:**\n\n"
        
        # Process users in batches to avoid message length limits
        for i, user in enumerate(users[:30], 1):  # Show first 30 users (reduced due to more info)
            user_id_val = user['user_id']
            stats = user_stats.get(user_id_val, {})
            
            # Get user info from Telegram
            try:
                # Try to get user info from Telegram
                user_entity = await bot.get_entity(user_id_val)
                username = f"@{user_entity.username}" if user_entity.username else "No username"
                first_name = user_entity.first_name or ""
                last_name = user_entity.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                
                if not full_name:
                    full_name = "No name"
                
                user_display = f"{full_name} ({username})"
                
            except Exception as e:
                # If we can't get user info, fall back to basic info
                logger.warning(f"Could not fetch user info for {user_id_val}: {e}")
                user_display = f"User ID: {user_id_val}"
                username = "Unknown"
                full_name = "Unknown"
            
            # Get subscription status
            if user['plan'] and user['expires_at'] and user['expires_at'] > datetime.now():
                status = "💎 Premium"
                days_remaining = (user['expires_at'] - datetime.now()).days
                status_detail = f" ({days_remaining}d left)"
                plan_info = f" | {user['plan']}"
            else:
                status = "🆓 Free"
                status_detail = ""
                plan_info = ""
            
            # Get user display info
            phone = user['phone'] or "No phone"
            
            # Get activity info
            if user['last_activity']:
                last_active = (datetime.now() - user['last_activity']).days
                activity_info = f" | Active: {last_active}d ago"
                activity_status = "🟢" if last_active < 7 else "🟡" if last_active < 30 else "🔴"
            else:
                activity_info = " | Never active"
                activity_status = "⚫"
            
            # Get forwarding status
            if user['forwarding_active']:
                forwarding_status = "🟢 Running"
                if user['forwarding_started']:
                    days_running = (datetime.now() - user['forwarding_started']).days
                    forwarding_info = f" ({days_running}d)"
                else:
                    forwarding_info = ""
            else:
                forwarding_status = "🔴 Stopped"
                forwarding_info = ""
            
            # Get command count
            command_count = user['command_count'] or 0
            
            # Rules status
            total_rules = stats.get('total_rules', 0)
            active_rules = stats.get('active_rules', 0)
            rules_status = f"📋 {active_rules}/{total_rules} rules"
            
            # Sources and destinations
            total_sources = stats.get('total_sources', 0)
            total_destinations = stats.get('total_destinations', 0)
            sources_dest_info = f"📥{total_sources} 📤{total_destinations}"
            
            message += f"{i}. {activity_status} **User:** {full_name}\n"
            message += f"   **Username:** {username}\n"
            message += f"   **User ID:** `{user_id_val}`\n"
            message += f"   **Phone:** `{phone}`\n"
            message += f"   **Status:** {status}{plan_info}{status_detail}\n"
            message += f"   **Forwarding:** {forwarding_status}{forwarding_info}\n"
            message += f"   **Rules:** {rules_status} | {sources_dest_info}\n"
            message += f"   **Commands:** {command_count}{activity_info}\n"
            
            if user['expires_at'] and user['plan']:
                message += f"   **Expires:** {user['expires_at'].strftime('%Y-%m-%d')}\n"
            
            if user['first_seen']:
                message += f"   **First Seen:** {user['first_seen'].strftime('%Y-%m-%d')}\n"
            
            message += "\n"
            
            # Split message if it's getting too long
            if len(message) > 3000:
                await event.respond(message)
                message = "👥 **All Bot Users** (continued)\n\n"
        
        # Add note if there are more users
        if len(users) > 30:
            message += f"\n... and {len(users) - 30} more users (showing first 30)"
        
        # Add filter buttons
        buttons = [
            [
                Button.inline("🆓 Free Only", data="filter_free_users"),
                Button.inline("💎 Premium Only", data="filter_premium_users")
            ],
            [
                Button.inline("🔄 Running Only", data="filter_running_users"),
                Button.inline("📊 Detailed View", data="users_detailed_view")
            ],
            [
                Button.inline("🔄 Refresh", data="refresh_all_users"),
                Button.inline("📈 Stats", data="users_stats_detailed")
            ],
            [Button.inline("👑 Admin Panel", data="admin_refresh")]
        ]
        
        await event.respond(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        await event.respond("❌ Error fetching users from database.")

@bot.on(events.CallbackQuery(pattern=r'filter_running_users'))
async def filter_running_users_handler(event):
    """Show only users with active forwarding"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    try:
        db = await get_db()
        
        # Get only users with active forwarding
        users = await db.fetch("""
            SELECT u.id as user_id, u.phone, u.session,
                   s.plan, s.expires_at, s.purchased_at,
                   a.last_activity, a.command_count, a.first_seen,
                   fs.is_active as forwarding_active,
                   fs.last_started as forwarding_started
            FROM users u
            JOIN forwarding_status fs ON u.id = fs.user_id
            LEFT JOIN subscriptions s ON u.id = s.user_id
            LEFT JOIN user_activity a ON u.id = a.user_id
            WHERE fs.is_active = TRUE
            ORDER BY fs.last_started DESC
        """)
        
        if not users:
            await event.respond("❌ No users with active forwarding found.")
            return
        
        # Get additional stats for each user
        user_stats = {}
        for user in users:
            user_id_val = user['user_id']
            
            rules = await db.fetch("""
                SELECT COUNT(*) as total_rules, 
                       COUNT(CASE WHEN is_active THEN 1 END) as active_rules
                FROM rules 
                WHERE user_id = $1
            """, user_id_val)
            
            sources_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id = $1", user_id_val)
            destinations_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id = $1", user_id_val)
            
            user_stats[user_id_val] = {
                'total_rules': rules[0]['total_rules'] if rules else 0,
                'active_rules': rules[0]['active_rules'] if rules else 0,
                'sources_count': sources_count or 0,
                'destinations_count': destinations_count or 0
            }
        
        message = f"🟢 **Users with Active Forwarding** ({len(users)} users)\n\n"
        
        for i, user in enumerate(users[:25], 1):
            user_id_val = user['user_id']
            stats = user_stats.get(user_id_val, {})
            
            phone = user['phone'] or "No phone"
            
            # Subscription status
            if user['plan'] and user['expires_at'] and user['expires_at'] > datetime.now():
                status = "💎 Premium"
                days_remaining = (user['expires_at'] - datetime.now()).days
                status_detail = f" ({days_remaining}d left)"
            else:
                status = "🆓 Free"
                status_detail = ""
            
            # Forwarding info
            if user['forwarding_started']:
                days_running = (datetime.now() - user['forwarding_started']).days
                forwarding_info = f" ({days_running}d running)"
            else:
                forwarding_info = ""
            
            command_count = user['command_count'] or 0
            
            message += f"{i}. **User ID:** `{user_id_val}`\n"
            message += f"   **Phone:** `{phone}`\n"
            message += f"   **Status:** {status}{status_detail}\n"
            message += f"   **Forwarding:** 🟢 Active{forwarding_info}\n"
            message += f"   **Rules:** {stats.get('active_rules', 0)}/{stats.get('total_rules', 0)} active\n"
            message += f"   **Sources/Dest:** 📥{stats.get('sources_count', 0)} 📤{stats.get('destinations_count', 0)}\n"
            message += f"   **Commands:** {command_count}\n\n"
            
            if len(message) > 3000:
                await event.respond(message)
                message = "🟢 **Active Forwarding Users** (continued)\n\n"
        
        if len(users) > 25:
            message += f"\n... and {len(users) - 25} more users"
        
        buttons = [
            [Button.inline("👥 Show All Users", data="refresh_all_users")],
            [Button.inline("👑 Admin Panel", data="admin_refresh")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error filtering running users: {e}")
        await event.answer("❌ Error filtering users.")

@bot.on(events.CallbackQuery(pattern=r'users_detailed_view'))
async def users_detailed_view_handler(event):
    """Show detailed view for a specific user or all users with full details"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    try:
        db = await get_db()
        
        # Get first 10 users with full details
        users = await db.fetch("""
            SELECT u.id as user_id, u.phone, u.session,
                   s.plan, s.expires_at, s.purchased_at,
                   a.last_activity, a.command_count, a.first_seen,
                   fs.is_active as forwarding_active,
                   fs.last_started as forwarding_started
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            LEFT JOIN user_activity a ON u.id = a.user_id
            LEFT JOIN forwarding_status fs ON u.id = fs.user_id
            ORDER BY a.last_activity DESC NULLS LAST
            LIMIT 10
        """)
        
        if not users:
            await event.respond("❌ No users found.")
            return
        
        message = "🔍 **Detailed User Overview** (First 10 users)\n\n"
        
        for i, user in enumerate(users, 1):
            user_id_val = user['user_id']
            
            # Get comprehensive user data
            rules = await db.fetch("SELECT * FROM rules WHERE user_id = $1 ORDER BY is_active DESC, rule_id", user_id_val)
            sources = await db.fetch("SELECT rule_id, COUNT(*) as count FROM sources WHERE user_id = $1 GROUP BY rule_id", user_id_val)
            destinations = await db.fetch("SELECT rule_id, COUNT(*) as count FROM destinations WHERE user_id = $1 GROUP BY rule_id", user_id_val)
            
            total_sources = sum(rule['count'] for rule in sources)
            total_destinations = sum(rule['count'] for rule in destinations)
            
            # Subscription status
            if user['plan'] and user['expires_at'] and user['expires_at'] > datetime.now():
                status = "💎 Premium"
                days_remaining = (user['expires_at'] - datetime.now()).days
                status_detail = f" ({user['plan']}, {days_remaining}d left)"
            else:
                status = "🆓 Free"
                status_detail = ""
            
            # Forwarding status
            if user['forwarding_active']:
                forwarding_status = "🟢 ACTIVE"
                if user['forwarding_started']:
                    days_running = (datetime.now() - user['forwarding_started']).days
                    forwarding_detail = f" ({days_running}d running)"
                else:
                    forwarding_detail = ""
            else:
                forwarding_status = "🔴 STOPPED"
                forwarding_detail = ""
            
            # Activity info
            if user['last_activity']:
                last_active = (datetime.now() - user['last_activity']).days
                activity_info = f"Last active: {last_active}d ago"
            else:
                activity_info = "Never active"
            
            message += f"**{i}. User ID:** `{user_id_val}`\n"
            message += f"**Phone:** `{user['phone'] or 'No phone'}`\n"
            message += f"**Subscription:** {status}{status_detail}\n"
            message += f"**Forwarding:** {forwarding_status}{forwarding_detail}\n"
            message += f"**Activity:** {activity_info} | Commands: {user['command_count'] or 0}\n"
            message += f"**Rules:** {len(rules)} total ({sum(1 for r in rules if r['is_active'])} active)\n"
            message += f"**Sources/Destinations:** 📥{total_sources} 📤{total_destinations}\n"
            
            # Show rule breakdown
            if rules:
                message += "**Active Rules:** "
                active_rules = [r for r in rules if r['is_active']]
                if active_rules:
                    message += ", ".join([r['name'] for r in active_rules[:3]])  # Show first 3 rule names
                    if len(active_rules) > 3:
                        message += f" ... (+{len(active_rules)-3} more)"
                else:
                    message += "None"
                message += "\n"
            
            message += "─" * 30 + "\n\n"
            
            if len(message) > 3500:
                await event.respond(message)
                message = "🔍 **Detailed User Overview** (continued)\n\n"
        
        buttons = [
            [Button.inline("👥 Compact View", data="refresh_all_users")],
            [Button.inline("🔄 Refresh", data="users_detailed_view")],
            [Button.inline("👑 Admin Panel", data="admin_refresh")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error showing detailed view: {e}")
        await event.answer("❌ Error loading detailed view.")

@bot.on(events.NewMessage(pattern='/edit_subscription'))
async def edit_subscription_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    
    if len(parts) < 2:
        # Show current plans with all pricing
        message = "📋 **Current Subscription Plans:**\n\n"
        for plan_id, plan_data in PLANS.items():
            message += f"• {plan_data['name']}\n"
            message += f"  💰 {plan_data['price_ton']} TON | ₹{plan_data['price_inr']} | ${plan_data['price_usd']}\n"
            message += f"  ⏰ {plan_data['days']} days"
            if 'discount' in plan_data:
                message += f" | {plan_data['discount']} OFF"
            message += "\n\n"
        
        message += "To edit a plan, use:\n"
        message += "/edit_subscription <plan_id> <ton_price> <inr_price> <usd_price> <days>\n"
        message += "Example: /edit_subscription 1month 2 99 2 30"
        
        await event.respond(message)
        return
    
    if len(parts) < 6:
        await event.respond("Usage: /edit_subscription <plan_id> <ton_price> <inr_price> <usd_price> <days>")
        await event.respond("Available plan_ids: " + ", ".join(PLANS.keys()))
        return
    
    plan_id = parts[1].lower()
    try:
        new_ton_price = float(parts[2])
        new_inr_price = int(parts[3])
        new_usd_price = float(parts[4])
        new_days = int(parts[5])
        
        if plan_id not in PLANS:
            await event.respond(f"❌ Invalid plan ID. Available options: {', '.join(PLANS.keys())}")
            return
            
        # Store old values for confirmation message
        old_ton_price = PLANS[plan_id]['price_ton']
        old_inr_price = PLANS[plan_id]['price_inr']
        old_usd_price = PLANS[plan_id]['price_usd']
        old_days = PLANS[plan_id]['days']
        
        # Update the plan
        PLANS[plan_id]['price_ton'] = new_ton_price
        PLANS[plan_id]['price_inr'] = new_inr_price
        PLANS[plan_id]['price_usd'] = new_usd_price
        PLANS[plan_id]['days'] = new_days
        
        # Update plan name to reflect changes
        if plan_id == "1month":
            PLANS[plan_id]['name'] = f"1 Month Premium"
        elif plan_id == "3months":
            PLANS[plan_id]['name'] = f"3 Months Premium"
            PLANS[plan_id]['discount'] = "10%"
        elif plan_id == "6months":
            PLANS[plan_id]['name'] = f"6 Months Premium"
            PLANS[plan_id]['discount'] = "20%"
        elif plan_id == "1year":
            PLANS[plan_id]['name'] = f"1 Year Premium"
            PLANS[plan_id]['discount'] = "50%"
        
        await event.respond(
            f"✅ Plan updated successfully!\n\n"
            f"**{plan_id}**:\n"
            f"TON Price: {old_ton_price} → {new_ton_price}\n"
            f"INR Price: ₹{old_inr_price} → ₹{new_inr_price}\n"
            f"USD Price: ${old_usd_price} → ${new_usd_price}\n"
            f"Duration: {old_days} days → {new_days} days\n\n"
            f"New users will see the updated prices immediately."
        )
        
        logger.info(f"Plan {plan_id} updated: {new_ton_price} TON | ₹{new_inr_price} | ${new_usd_price} | {new_days} days")
        
    except ValueError:
        await event.respond("❌ Invalid price or days format. TON and USD must be numbers, INR must be integer, days must be integer.")
    except Exception as e:
        logger.error(f"Error editing subscription: {e}")
        await event.respond("❌ Error updating subscription plan.")

@bot.on(events.NewMessage(pattern='/payments'))
async def payments_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
    
    try:
        db = await get_db()
        payments = await db.fetch("""
            SELECT p.*, s.expires_at as user_expiry
            FROM payments p 
            LEFT JOIN subscriptions s ON p.user_id = s.user_id
            WHERE p.status='pending_approval' 
            ORDER BY p.created_at DESC 
            LIMIT 10
        """)
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        await event.respond("❌ Error accessing database.")
        return
    
    if not payments:
        await event.respond("✅ No pending payments.")
        return
    
    message = "⏳ **Pending Payments:**\n\n"
    for payment in payments:
        plan = PLANS.get(payment['plan_id'], {'name': 'Unknown', 'price_inr': 0, 'price_ton': 0})
        has_screenshot = "✅" if payment.get('screenshot_message_id') else "❌"
        
        # Check if user already has active subscription
        has_active_sub = "⚠️" if payment['user_expiry'] and payment['user_expiry'] > datetime.now() else ""
        
        message += (
            f"💰 **Payment #{payment['id']}** {has_active_sub}\n"
            f"User: `{payment['user_id']}`\n"
            f"Plan: {plan['name']} ({plan['price_ton']} TON | ₹{plan['price_inr']})\n"
            f"Method: {payment.get('payment_method', 'unknown')}\n"
            f"Screenshot: {has_screenshot}\n"
            f"Date: {payment['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if has_active_sub:
            message += f"Note: User already has active subscription!\n"
        
        message += "\n"
    
    buttons = []
    for payment in payments:
        buttons.append([
            Button.inline(f"✅ Approve #{payment['id']}", data=f"approve_{payment['id']}"),
            Button.inline(f"❌ Reject #{payment['id']}", data=f"reject_{payment['id']}")
        ])
        if payment.get('screenshot_message_id'):
            buttons.append([
                Button.inline(f"📸 View Screenshot #{payment['id']}", data=f"view_screenshot_{payment['id']}")
            ])
    
    buttons.append([Button.inline("🔄 Refresh", data="admin_payments_refresh")])
    buttons.append([Button.inline("📊 Stats", data="admin_stats")])
    
    await event.respond(message, buttons=buttons)

@bot.on(events.NewMessage(pattern=r'/approve'))
async def approve_payment_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 2:
        await event.respond("Usage: /approve <payment_id>")
        return
        
    try:
        payment_id = int(parts[1])
        db = await get_db()
        
        # Get payment details with screenshot
        payment, screenshot_msg = await get_payment_with_screenshot(payment_id)
        
        if not payment:
            await event.respond("❌ Payment not found.")
            return
            
        if payment['status'] != 'pending_approval':
            await event.respond(f"❌ Payment is already {payment['status']}.")
            return
        
        # Get plan details
        plan = PLANS.get(payment['plan_id'])
        if not plan:
            await event.respond("❌ Invalid plan in payment record.")
            return
        
        # Update payment status FIRST
        await db.execute(
            "UPDATE payments SET status='approved', processed_at=NOW(), admin_id=$1 WHERE id=$2",
            user_id, payment_id
        )
        
        # THEN update the subscription in the shared database
        await update_subscription_in_main_bot(payment['user_id'], payment['plan_id'], plan['days'])
        
        # Notify user
        try:
            expires_at = datetime.now() + timedelta(days=plan['days'])
            await bot.send_message(
                payment['user_id'],
                f"🎉 **Your Premium Plan Has Been Activated!**\n\n"
                f"Plan: {plan['name']}\n"
                f"Expiry: {expires_at.strftime('%Y-%m-%d')}\n\n"
                "Thank you for your purchase! You can now enjoy enhanced forwarding capabilities.\n\n"
                "Return to your main bot to start using your premium features!",
                buttons=[
                    [Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")],
                    [Button.inline("📋 Check My Plan", data="show_my_plan")]
                ]
            )
        except Exception as e:
            logger.error(f"Could not notify user {payment['user_id']}: {e}")
        
        await event.respond(f"✅ Payment #{payment_id} approved successfully! Subscription updated.")
        
    except ValueError:
        await event.respond("❌ Invalid payment ID.")
    except Exception as e:
        logger.error(f"Error approving payment: {e}")
        await event.respond("❌ Error approving payment.")

@bot.on(events.NewMessage(pattern='/users'))
async def users_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    
    if len(parts) == 1:
        # Show all users with pagination
        await show_all_users(event)
    elif len(parts) == 2 and parts[1].isdigit():
        # Show specific user details
        await show_user_details(event, int(parts[1]))
    else:
        await event.respond(
            "👥 **User Management**\n\n"
            "Usage:\n"
            "/users - Show all users\n"
            "/users <user_id> - Show user details\n"
            "/users delete <user_id> - Delete user\n"
            "/users search <query> - Search users\n"
            "/users expire <user_id> - Expire user subscription\n"
            "/users renew <user_id> <days> - Renew subscription"
        )

async def show_all_users(event):
    """Show all users with pagination including limits"""
    try:
        db = await get_db()
        
        # Get total counts
        total_users = await db.fetchval("SELECT COUNT(*) FROM subscriptions")
        active_users = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE expires_at > NOW()"
        )
        expired_users = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE expires_at <= NOW() OR expires_at IS NULL"
        )
        
        # Get users with pagination
        users = await db.fetch("""
            SELECT s.user_id, s.plan, s.expires_at, s.purchased_at,
                   p.payment_method, p.status as payment_status
            FROM subscriptions s
            LEFT JOIN payments p ON s.user_id = p.user_id
            ORDER BY s.purchased_at DESC
            LIMIT 50
        """)
        
        if not users:
            if hasattr(event, 'edit'):
                await event.edit("❌ No users found in the database.")
            else:
                await event.respond("❌ No users found in the database.")
            return
        
        message = f"👥 **All Users**\n\n"
        message += f"📊 **Statistics:**\n"
        message += f"• Total Users: {total_users}\n"
        message += f"• Active Subscriptions: {active_users}\n"
        message += f"• Expired Subscriptions: {expired_users}\n\n"
        
        message += "📋 **Recent Users:**\n\n"
        
        for i, user in enumerate(users, 1):
            status = "✅ Active" if user['expires_at'] and user['expires_at'] > datetime.now() else "❌ Expired"
            plan = user['plan'] or "free"
            expires = user['expires_at'].strftime("%Y-%m-%d") if user['expires_at'] else "Never"
            
            # Get user limits based on subscription type
            limits = get_user_limits(plan)
            
            message += f"{i}. User ID: `{user['user_id']}`\n"
            message += f"   📦 Plan: {plan} | {status}\n"
            message += f"   ⏰ Expires: {expires}\n"
            message += f"   📋 Limits: {limits['rules']} rules, {limits['sources']} sources, {limits['destinations']} dests\n"
            message += f"   💳 Payment: {user.get('payment_method', 'N/A')}\n\n"
        
        # Add management buttons
        buttons = [
            [Button.inline("🔄 Refresh", data="admin_users_refresh")],
            [Button.inline("👤 Add User", data="add_user_quick")],
            [Button.inline("📊 Stats", data="admin_stats")],
            [Button.inline("🔍 Search Users", data="admin_search_users")]
        ]
        
        # Check if this is a callback query response or new message
        if hasattr(event, 'edit'):
            try:
                await event.edit(message, buttons=buttons)
            except Exception as e:
                # If editing fails, send a new message
                await event.respond(message, buttons=buttons)
        else:
            await event.respond(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error showing users: {e}")
        error_msg = "❌ Error fetching users from database."
        if hasattr(event, 'edit'):
            try:
                await event.edit(error_msg)
            except:
                await event.respond(error_msg)
        else:
            await event.respond(error_msg)

async def show_user_details(event, target_user_id):
    """Show detailed information about a specific user including current usage"""
    try:
        db = await get_db()
        
        # Get user subscription details
        user = await db.fetchrow("""
            SELECT s.*, p.payment_method, p.amount, p.status as payment_status,
                   p.created_at as payment_date, p.transaction_id
            FROM subscriptions s
            LEFT JOIN payments p ON s.user_id = p.user_id
            WHERE s.user_id = $1
            ORDER BY p.created_at DESC
            LIMIT 1
        """, target_user_id)
        
        if not user:
            await event.respond(f"❌ User `{target_user_id}` not found.")
            return
        
        # Get user's current usage statistics
        rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id = $1", target_user_id)
        active_rules_count = await db.fetchval("SELECT COUNT(*) FROM rules WHERE user_id = $1 AND is_active = TRUE", target_user_id)
        sources_count = await db.fetchval("SELECT COUNT(*) FROM sources WHERE user_id = $1", target_user_id)
        destinations_count = await db.fetchval("SELECT COUNT(*) FROM destinations WHERE user_id = $1", target_user_id)
        
        # Calculate days remaining
        days_remaining = 0
        if user['expires_at']:
            days_remaining = (user['expires_at'] - datetime.now()).days
            status = "✅ Active" if days_remaining > 0 else "❌ Expired"
        else:
            status = "❌ No subscription"
        
        # Get limits based on subscription type
        plan_type = user['plan'] or "free"
        limits = get_user_limits(plan_type)
        
        message = f"👤 **User Details:** `{target_user_id}`\n\n"
        message += f"📋 **Subscription:**\n"
        message += f"• Plan: {plan_type.upper()}\n"
        message += f"• Status: {status}\n"
        
        if user['expires_at']:
            message += f"• Expires: {user['expires_at'].strftime('%Y-%m-%d %H:%M')}\n"
            message += f"• Days remaining: {max(0, days_remaining)}\n"
        
        message += f"• Purchased: {user['purchased_at'].strftime('%Y-%m-%d')}\n\n"
        
        message += f"📊 **Current Usage:**\n"
        message += f"• Rules: {active_rules_count}/{rules_count} active (Limit: {limits['rules']})\n"
        message += f"• Sources: {sources_count} (Limit: {limits['sources']})\n"
        message += f"• Destinations: {destinations_count} (Limit: {limits['destinations']})\n\n"
        
        message += f"💳 **Payment Info:**\n"
        message += f"• Method: {user.get('payment_method', 'N/A')}\n"
        message += f"• Amount: {user.get('amount', 0)}\n"
        message += f"• Status: {user.get('payment_status', 'N/A')}\n"
        if user.get('transaction_id'):
            message += f"• Transaction ID: {user['transaction_id']}\n"
        message += f"• Payment Date: {user.get('payment_date', 'N/A')}\n\n"
        
        # Create management buttons
        buttons = [
            [
                Button.inline("🗑️ Delete User", data=f"delete_user_{target_user_id}"),
                Button.inline("⏰ Expire Now", data=f"expire_user_{target_user_id}")
            ],
            [
                Button.inline("🔄 Renew 30d", data=f"renew_user_{target_user_id}_30"),
                Button.inline("🔄 Renew 90d", data=f"renew_user_{target_user_id}_90")
            ],
            [Button.inline("📋 Back to Users", data="back_to_users")]
        ]
        
        await event.respond(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error showing user details: {e}")
        await event.respond("❌ Error fetching user details.")

def get_user_limits(plan_type):
    """Get user limits based on subscription type"""
    limits = {
        'free': {
            'rules': 5,
            'sources': 10,
            'destinations': 10
        },
        'premium': {
            'rules': 20,
            'sources': 50,
            'destinations': 50
        },
        '1month': {
            'rules': 20,
            'sources': 50,
            'destinations': 50
        },
        '3months': {
            'rules': 20,
            'sources': 50,
            'destinations': 50
        },
        '6months': {
            'rules': 20,
            'sources': 50,
            'destinations': 50
        },
        '1year': {
            'rules': 20,
            'sources': 50,
            'destinations': 50
        }
    }
    
    # Default to free limits if plan not found
    return limits.get(plan_type.lower(), limits['free'])

@bot.on(events.NewMessage(pattern='/add_user'))
async def add_user_handler(event):
    """Add a user manually and assign subscription"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    
    if len(parts) < 4:
        await event.respond(
            "👤 **Add User Manual Subscription**\n\n"
            "Usage: /add_user <user_id> <plan_type> <days>\n\n"
            "**Parameters:**\n"
            "• user_id - Telegram user ID to add\n"
            "• plan_type - premium, 1month, 3months, 6months, 1year\n"
            "• days - Number of days for subscription\n\n"
            "**Examples:**\n"
            "/add_user 123456789 premium 30\n"
            "/add_user 987654321 1month 30\n"
            "/add_user 555555555 1year 365\n\n"
            "**Available Plans:**\n" +
            "\n".join([f"• {plan_id} - {plan_data['name']}" for plan_id, plan_data in PLANS.items()])
        )
        return
    
    try:
        target_user_id = int(parts[1])
        plan_type = parts[2].lower()
        days = int(parts[3])
        
        # Validate plan type
        valid_plans = ['premium', '1month', '3months', '6months', '1year']
        if plan_type not in valid_plans and plan_type not in PLANS:
            await event.respond(
                f"❌ Invalid plan type. Available options:\n" +
                "\n".join([f"• {plan}" for plan in valid_plans]) + "\n" +
                "\n".join([f"• {plan_id}" for plan_id in PLANS.keys()])
            )
            return
        
        if days <= 0:
            await event.respond("❌ Days must be a positive number.")
            return
        
        # Calculate expiry date
        expires_at = datetime.now() + timedelta(days=days)
        
        db = await get_db()
        
        # Check if user already exists
        existing_user = await db.fetchrow(
            "SELECT * FROM subscriptions WHERE user_id = $1",
            target_user_id
        )
        
        if existing_user:
            # Update existing subscription
            await db.execute("""
                UPDATE subscriptions 
                SET plan = $1, expires_at = $2, purchased_at = NOW(),
                    notified_about_expiry = FALSE, notified_about_expiry_soon = FALSE
                WHERE user_id = $3
            """, plan_type, expires_at, target_user_id)
            
            action = "updated"
        else:
            # Create new subscription
            await db.execute("""
                INSERT INTO subscriptions (user_id, plan, expires_at, purchased_at)
                VALUES ($1, $2, $3, NOW())
            """, target_user_id, plan_type, expires_at)
            
            action = "added"
        
        # Also update the main bot's database if needed
        await update_subscription_in_main_bot(target_user_id, plan_type, days)
        
        # Try to notify the user
        try:
            plan_name = PLANS.get(plan_type, {}).get('name', plan_type.upper())
            await bot.send_message(
                target_user_id,
                f"🎉 **Your Subscription Has Been {action.capitalize()}!**\n\n"
                f"Plan: **{plan_name}**\n"
                f"Duration: **{days} days**\n"
                f"Purchase Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Expiry: {expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                "Thank you! You can now enjoy enhanced forwarding capabilities.\n\n"
                "Return to your main bot to start using your premium features!",
                buttons=[
                    [Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")],
                    [Button.inline("📋 Check My Plan", data="show_my_plan")]
                ]
            )
            user_notified = "✅ User notified"
        except Exception as e:
            logger.error(f"Could not notify user {target_user_id}: {e}")
            user_notified = "⚠️ User could not be notified"
        
        await event.respond(
            f"✅ **User Successfully {action.capitalize()}!**\n\n"
            f"**User ID:** `{target_user_id}`\n"
            f"**Plan:** {plan_type}\n"
            f"**Duration:** {days} days\n"
            f"**Expiry:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"**Status:** {user_notified}\n\n"
            f"Subscription has been activated in the system."
        )
        
        logger.info(f"User {target_user_id} {action} with {plan_type} plan for {days} days by admin {user_id}")
        
    except ValueError:
        await event.respond("❌ Invalid user ID or days format. Please use numbers.")
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        await event.respond("❌ Error adding user. Please check the parameters and try again.")

@bot.on(events.CallbackQuery(pattern=r'add_user_quick'))
async def add_user_quick_handler(event):
    """Quick add user interface"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    await event.edit(
        "👤 **Quick Add User**\n\n"
        "Please provide user details in the format:\n"
        "`/add_user <user_id> <plan_type> <days>`\n\n"
        "**Common Examples:**\n"
        "• `/add_user 123456789 premium 30` - 30 days premium\n"
        "• `/add_user 123456789 1month 30` - 1 month plan\n"
        "• `/add_user 123456789 1year 365` - 1 year plan\n\n"
        "**Available Plans:**\n" +
        "\n".join([f"• {plan_id} - {plan_data['name']}" for plan_id, plan_data in PLANS.items()]) + "\n" +
        "• premium - Generic premium plan",
        buttons=[
            [Button.inline("📋 Back to Users", data="back_to_users")],
            [Button.inline("👑 Admin Panel", data="admin_refresh")]
        ]
    )

@bot.on(events.NewMessage(pattern=r'/users delete'))
async def delete_user_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 3:
        await event.respond("Usage: /users delete <user_id>")
        return
        
    try:
        target_user_id = int(parts[2])
        db = await get_db()
        
        # Confirm deletion
        buttons = [
            [
                Button.inline("✅ Confirm Delete", data=f"confirm_delete_{target_user_id}"),
                Button.inline("❌ Cancel", data="cancel_delete")
            ]
        ]
        
        await event.respond(
            f"⚠️ **Confirm User Deletion**\n\n"
            f"Are you sure you want to delete user `{target_user_id}`?\n"
            f"This will remove all their subscription and payment data.",
            buttons=buttons
        )
        
    except ValueError:
        await event.respond("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error in delete user: {e}")
        await event.respond("❌ Error processing delete request.")

@bot.on(events.NewMessage(pattern=r'/users expire'))
async def expire_user_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 3:
        await event.respond("Usage: /users expire <user_id>")
        return
        
    try:
        target_user_id = int(parts[2])
        db = await get_db()
        
        # Set expiration to now
        await db.execute(
            "UPDATE subscriptions SET expires_at = NOW() WHERE user_id = $1",
            target_user_id
        )
        
        await event.respond(f"✅ Subscription for user `{target_user_id}` has been expired.")
        
    except ValueError:
        await event.respond("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error expiring user: {e}")
        await event.respond("❌ Error expiring subscription.")

@bot.on(events.NewMessage(pattern=r'/users renew'))
async def renew_user_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 4:
        await event.respond("Usage: /users renew <user_id> <days>")
        return
        
    try:
        target_user_id = int(parts[2])
        days = int(parts[3])
        db = await get_db()
        
        # Renew subscription
        new_expiry = datetime.now() + timedelta(days=days)
        
        # Get current plan or set to premium if none
        current_plan = await db.fetchval(
            "SELECT plan FROM subscriptions WHERE user_id = $1",
            target_user_id
        )
        
        if not current_plan:
            # Create new subscription if doesn't exist
            await db.execute("""
                INSERT INTO subscriptions (user_id, plan, expires_at)
                VALUES ($1, $2, $3)
            """, target_user_id, "premium", new_expiry)
        else:
            # Update existing subscription
            await db.execute("""
                UPDATE subscriptions SET expires_at = $1 WHERE user_id = $2
            """, new_expiry, target_user_id)
        
        await event.respond(
            f"✅ Subscription for user `{target_user_id}` renewed for {days} days.\n"
            f"New expiry: {new_expiry.strftime('%Y-%m-%d')}"
        )
        
    except ValueError:
        await event.respond("❌ Invalid user ID or days format.")
    except Exception as e:
        logger.error(f"Error renewing user: {e}")
        await event.respond("❌ Error renewing subscription.")

@bot.on(events.NewMessage(pattern=r'/users search'))
async def search_users_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    if len(parts) < 3:
        await event.respond("Usage: /users search <query>")
        return
        
    search_query = ' '.join(parts[2:])
    
    try:
        db = await get_db()
        
        # Search in user IDs and plans
        users = await db.fetch("""
            SELECT s.user_id, s.plan, s.expires_at, s.purchased_at
            FROM subscriptions s
            WHERE s.user_id::TEXT LIKE $1 OR s.plan ILIKE $2
            ORDER BY s.purchased_at DESC
            LIMIT 20
        """, f"%{search_query}%", f"%{search_query}%")
        
        if not users:
            await event.respond(f"❌ No users found matching '{search_query}'.")
            return
        
        message = f"🔍 **Search Results for '{search_query}':**\n\n"
        
        for i, user in enumerate(users, 1):
            status = "✅ Active" if user['expires_at'] and user['expires_at'] > datetime.now() else "❌ Expired"
            expires = user['expires_at'].strftime("%Y-%m-%d") if user['expires_at'] else "Never"
            
            message += f"{i}. User ID: `{user['user_id']}`\n"
            message += f"   Plan: {user['plan']} | {status}\n"
            message += f"   Expires: {expires}\n\n"
        
        await event.respond(message)
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        await event.respond("❌ Error searching users.")

# ---------------- NEW COMMAND: MY_PLAN ----------------
# Update the my_plan_handler to show expiry status more clearly
@bot.on(events.NewMessage(pattern='/my_plan'))
async def my_plan_handler(event):
    user_id = event.sender_id
    
    try:
        db = await get_db()
        
        # Get user's subscription details
        subscription = await db.fetchrow(
            "SELECT * FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        if not subscription:
            await event.respond(
                "📋 **Your Subscription Status**\n\n"
                "• Plan: **Free Tier**\n"
                "• Status: ❌ No active premium subscription\n\n"
                "💎 **Free Tier Features:**\n"
                "• Limited sources and targets\n"
                "• Basic forwarding capabilities\n\n"
                "Upgrade to premium to unlock all features!",
                buttons=[[Button.inline("💎 Upgrade to Premium", data="show_plans")]]
            )
            return
        
        # Calculate days remaining
        if subscription['expires_at']:
            days_remaining = (subscription['expires_at'] - datetime.now()).days
            status = "✅ Active" if days_remaining > 0 else "❌ Expired"
            expiry_date = subscription['expires_at'].strftime("%Y-%m-%d %H:%M UTC")
        else:
            days_remaining = 0
            status = "❌ Expired"
            expiry_date = "Never"
        
        message = "📋 **Your Subscription Details**\n\n"
        message += f"• Plan: **{subscription['plan'].upper() if subscription['plan'] else 'Free'}**\n"
        message += f"• Status: {status}\n"
        
        if subscription['expires_at']:
            message += f"• Expiry Date: {expiry_date}\n"
            if days_remaining > 0:
                message += f"• Days Remaining: **{days_remaining}** days\n"
                
                # Add warning if expiring soon
                if days_remaining <= 3:
                    message += f"⚠️ **Your plan expires soon! Renew now to avoid interruption.**\n"
            else:
                message += f"• Expired: **{abs(days_remaining)}** days ago\n"
                message += f"🔒 **Your premium features have been disabled.**\n"
        
        message += f"• Purchased: {subscription['purchased_at'].strftime('%Y-%m-%d')}\n\n"
        
        # Add premium features list for active subscribers
        if days_remaining > 0:
            message += "🎉 **Premium Features Active:**\n"
            message += "• 50 Sources + 50 Targets\n"
            message += "• 20 Rules\n"
            message += "• Auto-forwarding enabled\n"
            message += "• Header control\n"
            message += "• Media forwarding\n"
            message += "• Blacklist/Whitelist keywords\n"
            message += "• Unlimited forwards/day\n\n"
        else:
            message += "💎 **Upgrade to regain premium features!**\n\n"
        
        buttons = []
        if days_remaining <= 0:
            buttons.append([Button.inline("💎 Renew Subscription", data="show_plans")])
        elif days_remaining <= 7:
            buttons.append([Button.inline("💎 Renew Early", data="show_plans")])
        
        buttons.append([Button.inline("🔄 Refresh Status", data="refresh_my_plan")])
        buttons.append([Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")])
        
        await event.respond(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error fetching subscription details for user {user_id}: {e}")
        await event.respond(
            "❌ Error retrieving your subscription details. Please try again later.",
            buttons=[[Button.inline("🔄 Try Again", data="refresh_my_plan")]]
        )

@bot.on(events.CallbackQuery(pattern=r'show_plans(_(.+))?'))
async def show_plans_handler(event):
    """Show plans when user clicks Upgrade Plan"""
    try:
        data_parts = event.data.decode('utf-8').split('_')
        discount_code = data_parts[2] if len(data_parts) > 2 else None
        
        if discount_code and discount_code not in active_discounts:
            # Discount no longer valid, show regular plans
            discount_code = None
        
        await show_plans_with_discount(event, discount_code)
        
    except Exception as e:
        if "MessageNotModifiedError" in str(e):
            # Message content is the same, just acknowledge the click
            await event.answer("✅ Plans are already up to date!")
        else:
            logger.error(f"Error in show_plans_handler: {e}")
            await event.answer("❌ Error loading plans. Please try again.")

@bot.on(events.CallbackQuery(pattern=r'refresh_my_plan'))
async def refresh_my_plan_handler(event):
    """Refresh the my_plan display"""
    user_id = event.sender_id
    
    try:
        db = await get_db()
        subscription = await db.fetchrow(
            "SELECT * FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        if not subscription:
            await event.edit(
                "📋 **Your Subscription Status**\n\n"
                "• Plan: **Free Tier**\n"
                "• Status: ❌ No active premium subscription\n\n"
                "Upgrade to premium to unlock all features!",
                buttons=[[Button.inline("💎 Upgrade to Premium", data="show_plans")]]
            )
            return
        
        if subscription['expires_at']:
            days_remaining = (subscription['expires_at'] - datetime.now()).days
            status = "✅ Active" if days_remaining > 0 else "❌ Expired"
            expiry_date = subscription['expires_at'].strftime("%Y-%m-%d %H:%M UTC")
        else:
            days_remaining = 0
            status = "❌ Expired"
            expiry_date = "Never"
        
        message = "📋 **Your Subscription Details**\n\n"
        message += f"• Plan: **{subscription['plan'].upper() if subscription['plan'] else 'Free'}**\n"
        message += f"• Status: {status}\n"
        message += f"• Expiry Date: {expiry_date}\n"
        
        if days_remaining > 0:
            message += f"• Days Remaining: **{days_remaining}** days\n\n"
            message += "🎉 **Premium Features Active!**\n"
        else:
            message += f"• Expired: **{abs(days_remaining)}** days ago\n\n"
            message += "💎 **Upgrade to regain premium features!**\n"
        
        buttons = []
        if days_remaining <= 0:
            buttons.append([Button.inline("💎 Upgrade Plan", data="show_plans")])
        buttons.append([Button.inline("🔄 Refresh Status", data="refresh_my_plan")])
        buttons.append([Button.url("🔙 Back to Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")])
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error refreshing subscription details: {e}")
        await event.answer("❌ Error refreshing status. Please try again.")

@bot.on(events.CallbackQuery(pattern=r'back_to_plans'))
async def back_to_plans_handler(event):
    """Handle Back to Plans button"""
    await show_plans_with_discount(event)  # No discount code

@bot.on(events.CallbackQuery(pattern=r'back_methods_'))
async def back_methods_handler(event):
    """Handle Back to Methods button"""
    user_id = event.sender_id
    data_parts = event.data.decode('utf-8').split('_')
    plan_id = data_parts[2]
    
    # Check for discount code
    discount_code = data_parts[3] if len(data_parts) > 3 else None
    
    if plan_id not in PLANS:
        await event.answer("Invalid plan selection")
        return
        
    plan = PLANS[plan_id]
    
    # Delete any previous QR code message if present
    try:
        await event.delete()
    except:
        pass
    
    await event.respond(
        f"💎 **{plan['name']} Plan**\n"
        f"💰 Price: {plan['price_ton']} TON | ₹{plan['price_inr']} | ${plan['price_usd']}\n"
        f"⏰ Duration: {plan['days']} days\n\n"
        "Please choose your payment method:",
        buttons=[
            [Button.inline("💰 TON Crypto", data=f"pay_ton_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
            [Button.inline("🇮🇳 UPI Payment (₹)", data=f"pay_upi_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
            [Button.inline("📱 Scan QR Code (₹)", data=f"pay_qr_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
            [Button.inline("🌎 PayPal ($)", data=f"pay_paypal_{plan_id}" + (f"_{discount_code}" if discount_code else ""))],
            [Button.inline("🔙 Back to Plans", data="show_plans" + (f"_{discount_code}" if discount_code else ""))]
        ]
    )

@bot.on(events.CallbackQuery(pattern=r'show_my_plan'))
async def show_my_plan_handler(event):
    """Handle My Plan button click from plan selection"""
    # Reuse the my_plan_handler logic
    await my_plan_handler(event)

# ---------------- NEW CALLBACK HANDLERS FOR STATS AND SEARCH ----------------
@bot.on(events.CallbackQuery(pattern=r'admin_stats'))
async def admin_stats_handler(event):
    """Handle Stats button click"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    try:
        db = await get_db()
        
        # Get comprehensive statistics
        total_users = await db.fetchval("SELECT COUNT(*) FROM subscriptions")
        active_users = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE expires_at > NOW()"
        )
        expired_users = await db.fetchval(
            "SELECT COUNT(*) FROM subscriptions WHERE expires_at <= NOW() OR expires_at IS NULL"
        )
        
        # Payment statistics
        total_payments = await db.fetchval("SELECT COUNT(*) FROM payments")
        pending_payments = await db.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status='pending_approval'"
        )
        approved_payments = await db.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status='approved'"
        )
        rejected_payments = await db.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status='rejected'"
        )
        
        # Revenue statistics
        total_revenue = await db.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='approved'"
        )
        revenue_today = await db.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='approved' AND processed_at >= CURRENT_DATE"
        )
        revenue_this_week = await db.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='approved' AND processed_at >= CURRENT_DATE - INTERVAL '7 days'"
        )
        revenue_this_month = await db.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='approved' AND processed_at >= CURRENT_DATE - INTERVAL '30 days'"
        )
        
        # Plan distribution
        plan_stats = await db.fetch("""
            SELECT plan_id, COUNT(*) as count, SUM(amount) as revenue
            FROM payments 
            WHERE status='approved' 
            GROUP BY plan_id 
            ORDER BY count DESC
        """)
        
        message = "📊 **Payment Bot Statistics**\n\n"
        
        message += "👥 **User Statistics:**\n"
        message += f"• Total Users: {total_users}\n"
        message += f"• Active Subscriptions: {active_users}\n"
        message += f"• Expired Subscriptions: {expired_users}\n\n"
        
        message += "💳 **Payment Statistics:**\n"
        message += f"• Total Payments: {total_payments}\n"
        message += f"• Approved: {approved_payments}\n"
        message += f"• Pending: {pending_payments}\n"
        message += f"• Rejected: {rejected_payments}\n\n"
        
        message += "💰 **Revenue Statistics:**\n"
        message += f"• Total Revenue: ₹{total_revenue:.2f}\n"
        message += f"• Today: ₹{revenue_today:.2f}\n"
        message += f"• This Week: ₹{revenue_this_week:.2f}\n"
        message += f"• This Month: ₹{revenue_this_month:.2f}\n\n"
        
        if plan_stats:
            message += "📋 **Plan Distribution:**\n"
            for stat in plan_stats:
                plan_name = PLANS.get(stat['plan_id'], {}).get('name', stat['plan_id'])
                message += f"• {plan_name}: {stat['count']} users (₹{stat['revenue'] or 0:.2f})\n"
        
        buttons = [
            [Button.inline("🔄 Refresh Stats", data="admin_stats")],
            [Button.inline("📋 Back to Users", data="back_to_users")],
            [Button.inline("👑 Admin Panel", data="admin_refresh")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        await event.answer("❌ Error generating statistics.")
        # Try to send error message
        try:
            await event.edit("❌ Error generating statistics. Please try again.")
        except:
            pass

@bot.on(events.CallbackQuery(pattern=r'admin_search_users'))
async def admin_search_users_handler(event):
    """Handle Search Users button click"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    # Ask for search query
    try:
        await event.edit(
            "🔍 **Search Users**\n\n"
            "Please send your search query in the format:\n"
            "`/users search <query>`\n\n"
            "You can search by:\n"
            "• User ID\n"
            "• Plan name\n"
            "• Payment method\n\n"
            "Examples:\n"
            "`/users search 123456789`\n"
            "`/users search premium`\n"
            "`/users search upi`",
            buttons=[
                [Button.inline("📋 Back to Users", data="back_to_users")],
                [Button.inline("👑 Admin Panel", data="admin_refresh")]
            ]
        )
    except Exception as e:
        logger.error(f"Error in search users handler: {e}")
        await event.answer("❌ Error loading search interface.")

@bot.on(events.CallbackQuery(pattern=r'admin_users_refresh'))
async def admin_users_refresh_handler(event):
    """Handle Refresh button in users list"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    try:
        await show_all_users(event)
    except Exception as e:
        logger.error(f"Error refreshing users: {e}")
        await event.answer("❌ Error refreshing users.")

@bot.on(events.CallbackQuery(pattern=r'back_to_users'))
async def back_to_users_handler(event):
    """Handle Back to Users button from user details"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    try:
        await show_all_users(event)
    except Exception as e:
        logger.error(f"Error going back to users: {e}")
        await event.answer("❌ Error loading users list.")

@bot.on(events.CallbackQuery(pattern=r'delete_user_'))
async def delete_user_callback_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    target_user_id = int(event.data.decode('utf-8').split('_')[2])
    
    # Show confirmation
    buttons = [
        [Button.inline("✅ Confirm Delete", data=f"confirm_delete_{target_user_id}")],
        [Button.inline("❌ Cancel", data="cancel_delete")]
    ]
    
    await event.edit(
        f"⚠️ **Confirm User Deletion**\n\n"
        f"Are you sure you want to delete user `{target_user_id}`?\n"
        f"This will remove all their subscription and payment data.",
        buttons=buttons
    )

@bot.on(events.CallbackQuery(pattern=r'confirm_delete_'))
async def confirm_delete_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    target_user_id = int(event.data.decode('utf-8').split('_')[2])
    
    try:
        db = await get_db()
        
        # Delete user data
        await db.execute("DELETE FROM subscriptions WHERE user_id = $1", target_user_id)
        await db.execute("DELETE FROM payments WHERE user_id = $1", target_user_id)
        
        await event.edit(f"✅ User `{target_user_id}` and all their data has been deleted.")
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await event.answer("❌ Error deleting user.")

@bot.on(events.CallbackQuery(pattern=r'expire_user_'))
async def expire_user_callback_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    target_user_id = int(event.data.decode('utf-8').split('_')[2])
    
    try:
        db = await get_db()
        await db.execute(
            "UPDATE subscriptions SET expires_at = NOW() WHERE user_id = $1",
            target_user_id
        )
        
        await event.answer(f"✅ User {target_user_id} subscription expired.")
        await event.edit(f"✅ Subscription for user `{target_user_id}` has been expired.")
        
    except Exception as e:
        logger.error(f"Error expiring user: {e}")
        await event.answer("❌ Error expiring subscription.")

@bot.on(events.CallbackQuery(pattern=r'renew_user_'))
async def renew_user_callback_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
        
    data_parts = event.data.decode('utf-8').split('_')
    target_user_id = int(data_parts[2])
    days = int(data_parts[3])
    
    try:
        db = await get_db()
        new_expiry = datetime.now() + timedelta(days=days)
        
        await db.execute("""
            INSERT INTO subscriptions (user_id, plan, expires_at)
            VALUES ($1, 'premium', $2)
            ON CONFLICT (user_id) DO UPDATE SET expires_at = $2
        """, target_user_id, new_expiry)
        
        await event.answer(f"✅ User {target_user_id} renewed for {days} days.")
        await event.edit(
            f"✅ Subscription for user `{target_user_id}` renewed for {days} days.\n"
            f"New expiry: {new_expiry.strftime('%Y-%m-%d')}"
        )
        
    except Exception as e:
        logger.error(f"Error renewing user: {e}")
        await event.answer("❌ Error renewing subscription.")

@bot.on(events.CallbackQuery(pattern=r'cancel_delete'))
async def cancel_delete_handler(event):
    await event.answer("❌ Deletion cancelled.")
    await event.delete()

def generate_plan_buttons(discount_code=None):
    """Generate inline buttons for all available plans with optional discount"""
    buttons = []
    plans_to_show = get_discounted_plans(discount_code)
    
    for plan_id, plan_data in plans_to_show.items():
        if discount_code and discount_code in active_discounts:
            # Show discounted price
            button_text = f"{plan_data['name']} - {plan_data['price_ton']} TON | ₹{int(plan_data['price_inr'])} | ${int(plan_data['price_usd'])}"
        else:
            # Show regular price
            button_text = f"{plan_data['name']} - {plan_data['price_ton']} TON | ₹{plan_data['price_inr']} | ${int(plan_data['price_usd'])}"
        buttons.append([Button.inline(button_text, data=f"plan_{plan_id}" + (f"_{discount_code}" if discount_code else ""))])
    
    # Add My Plan and Back buttons
    additional_buttons = [
        Button.inline("📋 My Plan", data="show_my_plan"),
        Button.url("🔙 Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")
    ]
    
    if discount_code:
        additional_buttons.insert(0, Button.inline("🔙 Without Discount", data="show_plans"))
    
    buttons.append(additional_buttons)
    
    return buttons

async def update_all_plan_messages():
    """Update all active plan selection messages with current prices"""
    try:
        # This would typically involve tracking active plan selection messages
        # and updating them when plans change. For simplicity, we'll handle this
        # in the edit_subscription handler directly.
        pass
    except Exception as e:
        logger.error(f"Error updating plan messages: {e}")
  
# ---------------- DISCOUNT SYSTEM WITH AUTO PLAN UPDATES ----------------

# Global dictionary to store active discount codes
active_discounts = {}

def get_discounted_plans(discount_code=None):
    """Get plans with discounted prices if discount code is valid"""
    if not discount_code or discount_code not in active_discounts:
        return PLANS
    
    discount_data = active_discounts[discount_code]
    current_time = datetime.now()
    
    # Check if discount is still valid
    if discount_data['expires_at'] <= current_time:
        # Clean up expired discount
        del active_discounts[discount_code]
        return PLANS
    
    # Check max uses
    if (discount_data.get('max_uses') and 
        discount_data.get('used_count', 0) >= discount_data['max_uses']):
        return PLANS
    
    percentage = discount_data['percentage']
    
    # Create discounted plans copy
    discounted_plans = {}
    for plan_id, plan_data in PLANS.items():
        discounted_plan = plan_data.copy()
        discounted_plan['price_ton'] = plan_data['price_ton'] * (100 - percentage) / 100
        discounted_plan['price_usd'] = plan_data['price_usd'] * (100 - percentage) / 100
        discounted_plan['price_inr'] = plan_data['price_inr'] * (100 - percentage) / 100
        discounted_plan['original_price_ton'] = plan_data['price_ton']  # Store original for display
        discounted_plan['original_price_usd'] = plan_data['price_usd']  # Store original for display
        discounted_plan['original_price_inr'] = plan_data['price_inr']  # Store original for display
        discounted_plans[plan_id] = discounted_plan
    
    return discounted_plans

async def show_plans_with_discount(event, discount_code=None):
    """Show plans with optional discount applied"""
    try:
        user_id = event.sender_id
        plans_to_show = get_discounted_plans(discount_code)
        
        message = "💎 **Welcome to the Premium Upgrade Center!**\n\n"
        
        if discount_code and discount_code in active_discounts:
            discount_data = active_discounts[discount_code]
            percentage = discount_data['percentage']
            message += f"🎫 **Discount Applied: {discount_code} - {percentage}% OFF**\n\n"
        
        message += "**Choose a plan:**\n\n"
        
        for plan_id, plan_data in plans_to_show.items():
            if discount_code and discount_code in active_discounts:
                # Show discounted prices with strikethrough original
                percentage = active_discounts[discount_code]['percentage']
                original_plan = PLANS[plan_id]
                message += f"• {plan_data['name']}\n"
                message += f"  💰 ~~{original_plan['price_ton']} TON~~ **{plan_data['price_ton']:.1f} TON** | "
                message += f"~~₹{original_plan['price_inr']}~~ **₹{plan_data['price_inr']:.0f}** | "
                message += f"~~${original_plan['price_usd']}~~ **${plan_data['price_usd']:.2f}**\n"
                message += f"  ⏰ {plan_data['days']} days"
                if 'discount' in plan_data:
                    message += f" | {plan_data['discount']} OFF"
                message += f" | 🎫 **{percentage}% OFF**\n\n"
            else:
                # Show regular prices
                message += f"• {plan_data['name']}\n"
                message += f"  💰 {plan_data['price_ton']} TON | ₹{plan_data['price_inr']} | ${plan_data['price_usd']}\n"
                message += f"  ⏰ {plan_data['days']} days"
                if 'discount' in plan_data:
                    message += f" | {plan_data['discount']} OFF"
                message += "\n\n"
        
        message += (
            "🚀 **Premium Features:**\n"
            "• 50 Sources + 50 Targets\n"
            "• 20 Rules\n"
            "• Auto-forwarding enabled\n"
            "• Header control\n"
            "• Media forwarding\n"
            "• Add Blacklist Keywords\n"
            "• Add Whitelist keywords\n"
            "• Unlimited forwards/day\n\n"
        )
        
        if discount_code and discount_code in active_discounts:
            discount_data = active_discounts[discount_code]
            time_remaining = discount_data['expires_at'] - datetime.now()
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
            
            message += f"⏰ **Discount expires in:** {hours_remaining}h {minutes_remaining}m\n\n"
            message += "Select a plan below to purchase with discount:"
        else:
            message += "Select a plan below:"
        
        buttons = generate_plan_buttons(discount_code)
        
        # Try to edit the message, handle MessageNotModifiedError
        try:
            await event.edit(message, buttons=buttons)
        except Exception as edit_error:
            if "MessageNotModifiedError" in str(edit_error):
                await event.answer("✅ Plans are already up to date!")
            else:
                raise edit_error
                
    except Exception as e:
        logger.error(f"Error in show_plans_with_discount: {e}")
        await event.answer("❌ Error loading plans. Please try again.")

@bot.on(events.NewMessage(pattern='/discount'))
async def discount_handler(event):
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.respond("❌ Unauthorized. Admin access required.")
        return
        
    parts = event.raw_text.split()
    
    if len(parts) < 2:
        # Show current active discounts
        await show_active_discounts(event)
        return
    
    subcommand = parts[1].lower()
    
    if subcommand == "create":
        await create_discount_handler(event, parts)
    elif subcommand == "delete":
        await delete_discount_handler(event, parts)
    elif subcommand == "list":
        await show_active_discounts(event)
    elif subcommand == "apply":
        await apply_discount_handler(event, parts)
    else:
        await event.respond(
            "🎫 **Discount Management System**\n\n"
            "Available commands:\n"
            "/discount create <code> <percentage> <hours> - Create new discount\n"
            "/discount delete <code> - Delete discount code\n"
            "/discount list - Show all active discounts\n"
            "/discount apply <code> - Apply discount to see prices\n\n"
            "Examples:\n"
            "/discount create SUMMER20 20 24 - 20% off for 24 hours\n"
            "/discount delete SUMMER20\n"
            "/discount apply SUMMER20"
        )

async def show_active_discounts(event):
    """Show all active discount codes"""
    # Clean up expired discounts first
    current_time = datetime.now()
    expired_codes = [code for code, data in active_discounts.items() if data['expires_at'] <= current_time]
    for code in expired_codes:
        del active_discounts[code]
    
    if not active_discounts:
        await event.respond("❌ No active discount codes available.")
        return
    
    message = "🎫 **Active Discount Codes**\n\n"
    
    for code, discount_data in active_discounts.items():
        time_remaining = discount_data['expires_at'] - current_time
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        
        message += f"**{code}** - {discount_data['percentage']}% OFF\n"
        message += f"Expires in: {hours_remaining}h {minutes_remaining}m\n"
        message += f"Uses: {discount_data.get('used_count', 0)}/{discount_data.get('max_uses', 'Unlimited')}\n"
        message += f"Created by: Admin {discount_data['created_by']}\n\n"
    
    buttons = [
        [Button.inline("🔄 Refresh", data="refresh_discounts")],
        [Button.inline("🎫 Create New", data="create_discount")],
        [Button.inline("📢 Notify Users", data="notify_all_discounts")]
    ]
    
    await event.respond(message, buttons=buttons)

async def create_discount_handler(event, parts):
    """Handle discount creation"""
    if len(parts) < 5:
        await event.respond(
            "Usage: /discount create <code> <percentage> <hours> [max_uses]\n\n"
            "Examples:\n"
            "/discount create SUMMER20 20 24 - 20% off for 24 hours\n"
            "/discount create WELCOME10 10 48 - 10% off for 48 hours\n"
            "/discount create FLASH50 50 6 10 - 50% off for 6 hours, max 10 uses"
        )
        return
    
    discount_code = parts[2].upper()
    try:
        percentage = int(parts[3])
        hours = int(parts[4])
        
        # Optional: max uses
        max_uses = None
        if len(parts) > 5:
            max_uses = int(parts[5])
        
        if percentage <= 0 or percentage > 100:
            await event.respond("❌ Percentage must be between 1 and 100.")
            return
        
        if hours <= 0 or hours > 720:  # Max 30 days
            await event.respond("❌ Hours must be between 1 and 720 (30 days).")
            return
        
        # Check if code already exists
        if discount_code in active_discounts:
            await event.respond(f"❌ Discount code '{discount_code}' already exists.")
            return
        
        # Create discount
        expires_at = datetime.now() + timedelta(hours=hours)
        active_discounts[discount_code] = {
            'percentage': percentage,
            'expires_at': expires_at,
            'created_by': event.sender_id,
            'created_at': datetime.now(),
            'used_count': 0,
            'max_uses': max_uses
        }
        
        message = f"✅ **Discount Code Created!**\n\n"
        message += f"**Code:** `{discount_code}`\n"
        message += f"**Discount:** {percentage}% OFF\n"
        message += f"**Valid for:** {hours} hours\n"
        message += f"**Expires at:** {expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        
        if max_uses:
            message += f"**Max uses:** {max_uses}\n"
        else:
            message += "**Max uses:** Unlimited\n"
        
        # Show example of discounted prices
        message += f"\n**Example Discounted Prices:**\n"
        example_plan = list(PLANS.values())[0]  # Take first plan as example
        discounted_price_ton = example_plan['price_ton'] * (100 - percentage) / 100
        discounted_price_inr = example_plan['price_inr'] * (100 - percentage) / 100
        message += f"• {example_plan['name']}: ~~{example_plan['price_ton']} TON~~ **{discounted_price_ton:.1f} TON** | "
        message += f"~~₹{example_plan['price_inr']}~~ **₹{discounted_price_inr:.0f}**\n"
        
        buttons = [
            [Button.inline("🎫 View All Discounts", data="refresh_discounts")],
            [Button.inline("📢 Notify Users", data=f"notify_discount_{discount_code}")],
            [Button.inline("👀 Preview Plans", data=f"preview_discount_{discount_code}")]
        ]
        
        await event.respond(message, buttons=buttons)
        
        logger.info(f"Discount code '{discount_code}' created by admin {event.sender_id}")
        
        # Auto-update all active plan messages
        await update_all_plan_messages_with_discount(discount_code)
        
    except ValueError:
        await event.respond("❌ Invalid percentage or hours format. Please use numbers.")

async def delete_discount_handler(event, parts):
    """Handle discount deletion"""
    if len(parts) < 3:
        await event.respond("Usage: /discount delete <code>")
        return
    
    discount_code = parts[2].upper()
    
    if discount_code not in active_discounts:
        await event.respond(f"❌ Discount code '{discount_code}' not found.")
        return
    
    # Delete the discount
    del active_discounts[discount_code]
    
    await event.respond(f"✅ Discount code '{discount_code}' has been deleted.")
    
    logger.info(f"Discount code '{discount_code}' deleted by admin {event.sender_id}")

async def apply_discount_handler(event, parts):
    """Handle discount application for users"""
    if len(parts) < 3:
        await event.respond("Usage: /discount apply <code>")
        return
    
    discount_code = parts[2].upper()
    user_id = event.sender_id
    
    # Check if discount exists and is valid
    if discount_code not in active_discounts:
        await event.respond(f"❌ Discount code '{discount_code}' not found or expired.")
        return
    
    discount_data = active_discounts[discount_code]
    current_time = datetime.now()
    
    if discount_data['expires_at'] <= current_time:
        await event.respond(f"❌ Discount code '{discount_code}' has expired.")
        # Clean up expired discount
        del active_discounts[discount_code]
        return
    
    # Check max uses
    if (discount_data.get('max_uses') and 
        discount_data.get('used_count', 0) >= discount_data['max_uses']):
        await event.respond(f"❌ Discount code '{discount_code}' has reached its usage limit.")
        return
    
    # Show plans with discount applied
    await show_plans_with_discount(event, discount_code)

async def check_qr_code_files():
    """Check if QR code files exist and log warnings if not"""
    for plan_id, file_path in QR_CODE_FILES.items():
        if not os.path.exists(file_path):
            logger.warning(f"QR code file not found: {file_path} for {plan_id}")
    
    # Check default QR code
    default_file = QR_CODE_FILES.get("default")
    if default_file and not os.path.exists(default_file):
        logger.error(f"Default QR code file not found: {default_file}")
    
    # Check TON QR code
    ton_file = QR_CODE_FILES.get("ton")
    if ton_file and not os.path.exists(ton_file):
        logger.warning(f"TON QR code file not found: {ton_file}. TON payments will work with address only.")

@bot.on(events.CallbackQuery(pattern=r'preview_discount_(.+)'))
async def preview_discount_handler(event):
    """Preview how plans look with discount"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    discount_code = event.data.decode('utf-8').split('_')[-1]
    
    if discount_code not in active_discounts:
        await event.answer("❌ Discount code not found.")
        return
    
    await show_plans_with_discount(event, discount_code)

async def update_all_plan_messages_with_discount(discount_code):
    """Update all active plan selection messages with discount prices"""
    try:
        # This would update all active plan messages to show discounted prices
        # In a real implementation, you might track active plan messages and update them
        logger.info(f"Discount '{discount_code}' created - plan prices updated system-wide")
        
        # You could implement message tracking and updating here
        # For now, we'll just log that discounts are active
        pass
        
    except Exception as e:
        logger.error(f"Error updating plan messages with discount: {e}")

# Update the start handler to show TON information
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    
    # Check if user is admin
    if await is_admin(user_id):
        await event.respond(
            "👑 **Admin Panel**\n\n"
            "Available commands:\n"
            "/payments - View pending payments\n"
            "/approve <payment_id> - Approve a payment\n"
            "/reject <payment_id> <reason> - Reject a payment\n"
            "/users - View all subscribers\n"
            "/add_user - Add A user to premium plan\n"
            "/stats - View payment statistics\n"
            "/edit_subscription - Edit plan prices\n"
            "/discount - Manage discount codes",
            buttons=[[Button.inline("🔄 Refresh Payments", data="admin_payments")]]
        )
        return
    
    # Check active discounts and show promotion if available
    active_discount_list = []
    current_time = datetime.now()
    
    for code, data in active_discounts.items():
        if data['expires_at'] > current_time:
            if not data.get('max_uses') or data.get('used_count', 0) < data.get('max_uses', float('inf')):
                active_discount_list.append(code)
    
    promotion_message = ""
    if active_discount_list:
        promotion_message = f"🎫 **Active Discounts Available!**\nUse code: {', '.join(active_discount_list)}\n\n"
    
    # Rest of your existing start handler code...
    # Check if user has an existing subscription
    try:
        db = await get_db()
        subscription = await db.fetchrow(
            "SELECT * FROM subscriptions WHERE user_id = $1",
            user_id
        )
        
        has_subscription = subscription and (
            not subscription['expires_at'] or 
            subscription['expires_at'] > datetime.now()
        )
        
        if has_subscription:
            # User has active subscription - show quick access menu
            expires_at = subscription['expires_at']
            days_remaining = (expires_at - datetime.now()).days if expires_at else 0
            
            message = f"🎉 **Welcome Back!**\n\n"
            message += f"Your **{subscription['plan']}** plan is active"
            
            if days_remaining > 0:
                message += f" with **{days_remaining}** days remaining.\n\n"
            else:
                message += ".\n\n"
            
            if promotion_message:
                message += promotion_message
            
            message += "What would you like to do?"
            
            buttons = [
                [Button.inline("📋 View My Plan", data="show_my_plan")],
                [Button.inline("💎 Upgrade Plan", data="show_plans")],
            ]
            
            # Add discount button if discounts available
            if active_discount_list:
                buttons.insert(1, [Button.inline("🎫 View Discounts", data="show_discounts")])
            
            buttons.append([Button.url("🚀 Use Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")])
            
            await event.respond(message, buttons=buttons)
            return
            
    except Exception as e:
        logger.error(f"Error checking subscription in start: {e}")
        # Continue with normal flow if there's an error
    
    # Regular user flow - show plans with promotion
    message = "💎 **Welcome to the Premium Upgrade Center!**\n\n"
    
    if promotion_message:
        message += promotion_message
    
    message += "**Choose a plan:**\n\n"
    
    for plan_id, plan_data in PLANS.items():
        message += f"• {plan_data['name']}\n"
        message += f"  💰 {plan_data['price_ton']} TON | ₹{plan_data['price_inr']} | ${plan_data['price_usd']}\n"
        message += f"  ⏰ {plan_data['days']} days"
        if 'discount' in plan_data:
            message += f" | {plan_data['discount']} OFF"
        message += "\n\n"
    
    message += (
        "🚀 **Features:**\n"
        "• 50 Sources + 50 Targets\n"
        "• 20 Rules\n"
        "• Auto-forwarding enabled\n"
        "• Header control\n"
        "• Media forwarding\n"
        "• Add Blacklist Keywords\n"
        "• Add Whitelist keywords\n"
        "• Unlimited forwards/day\n\n"
        "Select a plan below:"
    )
    
    buttons = generate_plan_buttons()
    
    # Add discount button if discounts available
    if active_discount_list:
        # Replace the last button row to include discount button
        buttons = buttons[:-1]  # Remove last row
        buttons.append([
            Button.inline("🎫 View Discounts", data="show_discounts"),
            Button.inline("📋 My Plan", data="show_my_plan")
        ])
        buttons.append([Button.url("🔙 Main Bot", f"https://t.me/{MAIN_BOT_USERNAME[1:]}")])
    
    await event.respond(message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'show_discounts'))
async def show_discounts_handler(event):
    """Show available discounts to users"""
    # Clean up expired discounts first
    current_time = datetime.now()
    expired_codes = [code for code, data in active_discounts.items() if data['expires_at'] <= current_time]
    for code in expired_codes:
        del active_discounts[code]
    
    active_discount_list = []
    for code, data in active_discounts.items():
        if not data.get('max_uses') or data.get('used_count', 0) < data.get('max_uses', float('inf')):
            active_discount_list.append((code, data))
    
    if not active_discount_list:
        await event.answer("❌ No active discounts available.", alert=True)
        return
    
    message = "🎫 **Active Discount Codes**\n\n"
    
    for code, data in active_discount_list:
        time_remaining = data['expires_at'] - current_time
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        
        message += f"**{code}** - {data['percentage']}% OFF\n"
        message += f"Expires in: {hours_remaining}h {minutes_remaining}m\n"
        
        if data.get('max_uses'):
            remaining_uses = data['max_uses'] - data.get('used_count', 0)
            message += f"Remaining uses: {remaining_uses}\n"
        
        message += "\n"
    
    message += "Click a discount code below to apply it:"
    
    buttons = []
    for code, data in active_discount_list:
        buttons.append([Button.inline(f"🎫 {code} - {data['percentage']}% OFF", data=f"apply_discount_{code}")])
    
    buttons.append([Button.inline("🔙 Back to Plans", data="show_plans")])
    
    await event.edit(message, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=r'apply_discount_(.+)'))
async def apply_discount_callback_handler(event):
    """Apply discount when user clicks on discount button"""
    discount_code = event.data.decode('utf-8').split('_')[-1]
    
    if discount_code not in active_discounts:
        await event.answer("❌ Discount code no longer valid.", alert=True)
        return
    
    await show_plans_with_discount(event, discount_code)

# Add this to your existing update_all_plan_messages function
async def update_all_plan_messages():
    """Update all active plan selection messages with current prices"""
    try:
        # This would typically involve tracking active plan selection messages
        # and updating them when plans change. For simplicity, we'll handle this
        # in the edit_subscription handler directly.
        
        # When discounts are active, the system automatically shows discounted prices
        # through the get_discounted_plans() function
        pass
    except Exception as e:
        logger.error(f"Error updating plan messages: {e}")
              
@bot.on(events.CallbackQuery(pattern=r'notify_all_discounts'))
async def notify_all_discounts_handler(event):
    """Notify all users (both premium and free) about active discounts"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    # Clean up expired discounts first
    current_time = datetime.now()
    expired_codes = [code for code, data in active_discounts.items() if data['expires_at'] <= current_time]
    for code in expired_codes:
        del active_discounts[code]
    
    if not active_discounts:
        await event.answer("❌ No active discounts to notify about.")
        return
    
    await event.edit("🔄 Preparing to notify all users about active discounts...")
    
    try:
        db = await get_db()
        
        # Get ALL users from both subscriptions AND users table to include free users
        all_users = set()
        
        # Get users from subscriptions table (premium users)
        subscribed_users = await db.fetch("SELECT user_id FROM subscriptions")
        for user in subscribed_users:
            all_users.add(user['user_id'])
        
        # Get users from users table (free users)
        free_users = await db.fetch("SELECT id as user_id FROM users")
        for user in free_users:
            all_users.add(user['user_id'])
        
        # Convert set to list
        users_list = list(all_users)
        
        if not users_list:
            await event.edit("❌ No users found to notify.")
            return
        
        message = "🎉 **Special Discounts Available!** 🎉\n\n"
        message += "We have limited-time discount codes for premium plans:\n\n"
        
        for code, data in active_discounts.items():
            time_remaining = data['expires_at'] - current_time
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
            
            message += f"**{code}** - {data['percentage']}% OFF\n"
            message += f"Expires in: {hours_remaining}h {minutes_remaining}m\n\n"
        
        message += "🎁 **Perfect time to upgrade to Premium!** 🎁\n\n"
        message += "💎 **Premium Features:**\n"
        message += "• 50 Sources + 50 Targets\n"
        message += "• 20 Rules\n"
        message += "• Auto-forwarding enabled\n"
        message += "• Header control\n"
        message += "• Media forwarding\n"
        message += "• Blacklist/Whitelist keywords\n"
        message += "• Unlimited forwards/day\n\n"
        message += "Click the button below to view discounted plans:\n"
        
        buttons = [[Button.inline("🎫 View Discounted Plans", data="show_discounts")]]
        
        success_count = 0
        fail_count = 0
        premium_count = 0
        free_count = 0
        
        # Check subscription status for each user
        for user_id in users_list:
            try:
                # Check if user has active subscription
                subscription = await db.fetchrow(
                    "SELECT * FROM subscriptions WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())",
                    user_id
                )
                
                user_type = "💎 Premium" if subscription else "🆓 Free"
                
                # Send notification
                await bot.send_message(user_id, message, buttons=buttons)
                success_count += 1
                
                # Count user types
                if subscription:
                    premium_count += 1
                else:
                    free_count += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Could not notify user {user_id}: {e}")
                fail_count += 1
        
        await event.edit(
            f"📢 **Discount Notification Results**\n\n"
            f"✅ Successfully notified: {success_count} users\n"
            f"• 💎 Premium users: {premium_count}\n"
            f"• 🆓 Free users: {free_count}\n"
            f"❌ Failed to notify: {fail_count} users\n"
            f"📊 Total users attempted: {len(users_list)}\n\n"
            f"Discount codes have been broadcast to all users."
        )
        
    except Exception as e:
        logger.error(f"Error in notify_all_discounts: {e}")
        await event.edit("❌ Error sending discount notifications.")
        
    except Exception as e:
        logger.error(f"Error in notify_all_discounts: {e}")
        await event.edit("❌ Error sending discount notifications.")

@bot.on(events.CallbackQuery(pattern=r'notify_discount_(.+)'))
async def notify_specific_discount_handler(event):
    """Notify all users (premium and free) about a specific discount code"""
    user_id = event.sender_id
    
    if not await is_admin(user_id):
        await event.answer("❌ Unauthorized. Admin access required.")
        return
    
    discount_code = event.data.decode('utf-8').split('_')[-1]
    
    if discount_code not in active_discounts:
        await event.answer("❌ Discount code not found or expired.")
        return
    
    discount_data = active_discounts[discount_code]
    
    await event.edit(f"🔄 Preparing to notify all users about discount {discount_code}...")
    
    try:
        db = await get_db()
        
        # Get ALL users from both tables
        all_users = set()
        
        # Get premium users from subscriptions
        subscribed_users = await db.fetch("SELECT user_id FROM subscriptions")
        for user in subscribed_users:
            all_users.add(user['user_id'])
        
        # Get free users from users table
        free_users = await db.fetch("SELECT id as user_id FROM users")
        for user in free_users:
            all_users.add(user['user_id'])
        
        users_list = list(all_users)
        
        if not users_list:
            await event.edit("❌ No users found to notify.")
            return
        
        message = f"🎉 **Special Discount Available!** 🎉\n\n"
        message += f"Use code **{discount_code}** for {discount_data['percentage']}% OFF on all premium plans!\n\n"
        
        time_remaining = discount_data['expires_at'] - datetime.now()
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        
        message += f"⏰ **Limited Time Offer:** Expires in {hours_remaining}h {minutes_remaining}m\n\n"
        
        # Different message based on user type (we'll determine this per user)
        message += "🎁 **Perfect opportunity to upgrade or renew your plan!** 🎁\n\n"
        message += "💎 **Premium Features:**\n"
        message += "• 50 Sources + 50 Targets\n"
        message += "• 20 Rules\n"
        message += "• Auto-forwarding enabled\n"
        message += "• Header control\n"
        message += "• Media forwarding\n"
        message += "• Blacklist/Whitelist keywords\n"
        message += "• Unlimited forwards/day\n\n"
        
        message += "Don't miss this opportunity to get premium features at a discounted price!\n"
        
        buttons = [[Button.inline(f"🎫 Apply {discount_code} Discount", data=f"apply_discount_{discount_code}")]]
        
        success_count = 0
        fail_count = 0
        premium_count = 0
        free_count = 0
        
        for user_id in users_list:
            try:
                # Check user subscription status
                subscription = await db.fetchrow(
                    "SELECT * FROM subscriptions WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())",
                    user_id
                )
                
                user_type = "💎 Premium" if subscription else "🆓 Free"
                
                await bot.send_message(user_id, message, buttons=buttons)
                success_count += 1
                
                if subscription:
                    premium_count += 1
                else:
                    free_count += 1
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Could not notify user {user_id}: {e}")
                fail_count += 1
        
        await event.edit(
            f"📢 **Discount Notification Results**\n\n"
            f"Discount: **{discount_code}** ({discount_data['percentage']}% OFF)\n\n"
            f"✅ Successfully notified: {success_count} users\n"
            f"• 💎 Premium users: {premium_count}\n"
            f"• 🆓 Free users: {free_count}\n"
            f"❌ Failed to notify: {fail_count} users\n"
            f"📊 Total users attempted: {len(users_list)}"
        )
        
    except Exception as e:
        logger.error(f"Error in notify_specific_discount: {e}")
        await event.edit("❌ Error sending discount notifications.")
                      
# ---------------- MAIN ----------------
# Update the main function to start the background task
async def main():
    # Initialize database first (with error handling)
    try:
        await init_db()
        await update_database_schema()  # Ensure this is called
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database initialization - tables may already exist")
    
    # Check QR code files
    await check_qr_code_files()
    
    await bot.start()
    logger.info("Payment bot started!")
    
    # Start the subscription monitor task
    asyncio.create_task(subscription_monitor_task())
    logger.info("Subscription monitor task started!")
    
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # Use this approach instead of asyncio.run()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()