from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import datetime
import html

import config
import database
import keyboards

AWAITING_X_USERNAME, AWAITING_TX_HASH, AWAITING_ORDER_ID, AWAITING_PAYMENT_SELECTION = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await database.add_user(user.id, user.username, user.first_name)
    
    welcome_text = (
        f"<b>Welcome to Xkart</b>\n\n"
        f"Get Twitter Premium at the best price, Use the menu below to get started.\n\n"
        f"<a href='https://xkart-hazel.vercel.app/'>Website</a>"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()
        await context.bot.send_message(chat_id=user.id, text=welcome_text, parse_mode=ParseMode.HTML, reply_markup=keyboards.get_reply_main_menu(), disable_web_page_preview=True)
    else:
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=keyboards.get_reply_main_menu(), disable_web_page_preview=True)
    
    return ConversationHandler.END

async def menu_place_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Please select a subscription plan:"
    await update.message.reply_text(text, reply_markup=keyboards.get_plans_menu())

async def menu_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💵 <b>Our Prices</b>\n\n"
    for plan_id, plan in config.PLANS.items():
        text += f"• {plan['name']}: <b>${plan['price']}</b>\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def menu_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ <b>Service Details</b>\n\n"
        "We provide instant upgrades for your X (Twitter) account to Premium status.\n"
        "All upgrades are processed quickly after your crypto payment is confirmed.\n\n"
        f"For support, contact {config.ADMIN_USERNAME}."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def menu_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_text = await database.get_setting("event_text", "🎉 <b>Current Events</b>\n\nNo active events at the moment. Stay tuned!")
    await update.message.reply_text(event_text, parse_mode=ParseMode.HTML)

async def menu_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = await database.get_user_orders(user.id)
    if not orders:
        await update.message.reply_text("You have no past orders.")
        return
        
    text = "📋 <b>Your Recent Orders</b>\n\n"
    for order in orders:
        order_id, plan_id, status, created_at = order
        plan_name = config.PLANS.get(plan_id, {}).get('name', 'Unknown')
        text += f"📦 <code>{order_id}</code> - {plan_name} ({status})\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def menu_check_status_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your Order ID (e.g., PM05271234):", reply_markup=keyboards.get_back_button())
    return AWAITING_ORDER_ID

async def receive_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order_id = update.message.text.strip()
    order = await database.get_order(order_id)
    if not order:
        await update.message.reply_text("Order not found. Please check the ID and try again.", reply_markup=keyboards.get_reply_main_menu())
    else:
        status = order[5] # status
        await update.message.reply_text(f"📦 Order <code>{order_id}</code>\nStatus: <b>{status}</b>", parse_mode=ParseMode.HTML, reply_markup=keyboards.get_reply_main_menu())
    return ConversationHandler.END

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    plan_id = query.data.split('_', 1)[1]
    context.user_data['plan_id'] = plan_id
    
    text = "Please enter your X (Twitter) username (without '@'):"
    await query.edit_message_text(text, reply_markup=keyboards.get_back_button())
    return AWAITING_X_USERNAME

async def receive_x_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['x_username'] = username
    
    context.user_data['payment_asset'] = None
    context.user_data['payment_network'] = None
    
    text = (
        f"💳 <b>Crypto Payment Setup</b>\n\n"
        f"Asset: Not selected\n"
        f"Network: Not selected\n\n"
        f"How to choose:\n"
        f"1) Tap one asset first: USDT or USDC.\n"
        f"2) Tap one network: BSC, Base, Polygon, or Arbitrum.\n"
        f"3) Tap Continue after both are selected.\n\n"
        f"<b>Important:</b>\n"
        f"• The asset and network must match what you send.\n"
        f"• Do not send native coins like BNB, ETH, MATIC, or SOL.\n"
        f"• Solana is not supported here.\n"
        f"• Sending with the wrong network may permanently lose funds."
    )
    
    await update.message.reply_text(
        text, 
        parse_mode=ParseMode.HTML, 
        reply_markup=keyboards.get_payment_setup_keyboard()
    )
    return AWAITING_PAYMENT_SELECTION

async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "payment_continue":
        asset = context.user_data.get('payment_asset')
        network = context.user_data.get('payment_network')
        
        if not asset or not network:
            await query.answer("Please select both an Asset and a Network!", show_alert=True)
            return AWAITING_PAYMENT_SELECTION
            
        plan_id = context.user_data['plan_id']
        plan = config.PLANS[plan_id]
        username = context.user_data['x_username']
        
        text = (
            f"📝 <b>Order Summary</b>\n\n"
            f"Product: {config.PRODUCT_NAME}\n"
            f"Plan: {plan['name']}\n"
            f"Price: ${plan['price']}\n"
            f"X Username: {html.escape(username)}\n\n"
            f"💳 <b>Payment Information</b>\n"
            f"Please send <b>${plan['price']} {asset} ({network})</b> to the following address:\n\n"
            f"<code>{config.PAYMENT_ADDRESS}</code>\n\n"
            f"After making the payment, please reply with your <b>Transaction Hash (TxID)</b>."
        )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboards.get_back_button())
        return AWAITING_TX_HASH
        
    if data.startswith("payment_asset_"):
        context.user_data['payment_asset'] = data.split("_")[2]
    elif data.startswith("payment_network_"):
        context.user_data['payment_network'] = data.split("_")[2]
        
    asset = context.user_data.get('payment_asset', 'Not selected')
    network = context.user_data.get('payment_network', 'Not selected')
    
    text = (
        f"💳 <b>Crypto Payment Setup</b>\n\n"
        f"Asset: {asset}\n"
        f"Network: {network}\n\n"
        f"How to choose:\n"
        f"1) Tap one asset first: USDT or USDC.\n"
        f"2) Tap one network: BSC, Base, Polygon, or Arbitrum.\n"
        f"3) Tap Continue after both are selected.\n\n"
        f"<b>Important:</b>\n"
        f"• The asset and network must match what you send.\n"
        f"• Do not send native coins like BNB, ETH, MATIC, or SOL.\n"
        f"• Solana is not supported here.\n"
        f"• Sending with the wrong network may permanently lose funds."
    )
    
    try:
        await query.edit_message_text(
            text, 
            parse_mode=ParseMode.HTML, 
            reply_markup=keyboards.get_payment_setup_keyboard(
                context.user_data.get('payment_asset'),
                context.user_data.get('payment_network')
            )
        )
    except Exception:
        pass
        
    return AWAITING_PAYMENT_SELECTION

async def receive_tx_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tx_hash = update.message.text
    user = update.effective_user
    
    plan_id = context.user_data['plan_id']
    plan = config.PLANS[plan_id]
    x_username = context.user_data['x_username']
    
    order_id = await database.create_order(user.id, x_username, plan_id, tx_hash)
    
    date_str = datetime.datetime.now().strftime("%d %b %Y")
    
    user_msg = (
        f"📦 <b>Order {order_id}</b>\n\n"
        f"X Username: {html.escape(x_username)}\n"
        f"Product: {config.PRODUCT_NAME}\n"
        f"Plan: {plan['name']}\n"
        f"Price: ${plan['price']}\n"
        f"Payment: On-chain\n"
        f"Status: Processing\n"
        f"Date: {date_str}\n\n"
        f"<i>Your order has been submitted and will be reviewed shortly. You will receive an update once it is completed.</i>"
    )
    await update.message.reply_text(user_msg, parse_mode=ParseMode.HTML, reply_markup=keyboards.get_completion_buttons())
    
    asset = context.user_data.get('payment_asset', 'Unknown')
    network = context.user_data.get('payment_network', 'Unknown')
    
    admins = await database.get_admins()
    safe_username = html.escape(user.username) if user.username else "Unknown"
    admin_msg = (
        f"🔔 <b>New Order Received!</b>\n\n"
        f"Order ID: <code>{order_id}</code>\n"
        f"Telegram User: @{safe_username} ({user.id})\n"
        f"X Username: {html.escape(x_username)}\n"
        f"Plan: {plan['name']}\n"
        f"Amount: ${plan['price']}\n"
        f"Asset: {asset}\n"
        f"Network: {network}\n"
        f"Tx Hash: <code>{html.escape(tx_hash)}</code>\n\n"
        f"To complete this order, use:\n<code>/complete {order_id}</code>"
    )
    
    for admin_id in admins:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Failed to send admin message to {admin_id}: {e}")
            
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Action cancelled.", reply_markup=keyboards.get_reply_main_menu())
    else:
        await update.message.reply_text("Action cancelled.", reply_markup=keyboards.get_reply_main_menu())
    return ConversationHandler.END

async def set_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if f"@{user.username}" == config.ADMIN_USERNAME or user.username == config.ADMIN_USERNAME.strip('@'):
        await database.add_user(user.id, user.username, user.first_name)
        await database.set_admin(user.id)
        await update.message.reply_text("You have been successfully registered as an admin.")
    else:
        await update.message.reply_text("You are not authorized to become an admin.")

async def complete_order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admins = await database.get_admins()
    
    if user.id not in admins:
        await update.message.reply_text("You are not authorized to use this command.")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /complete <order_id>")
        return
        
    order_id = context.args[0]
    order = await database.get_order(order_id)
    
    if not order:
        await update.message.reply_text(f"Order {order_id} not found.")
        return
        
    await database.update_order_status(order_id, "Completed")
    
    customer_id = order[1]
    
    success_msg = f"✅ <b>Order {order_id} completed.</b>\n\nCongratulations! Your account has been upgraded successfully. Thank you for your order."
    
    try:
        await context.bot.send_message(
            chat_id=customer_id, 
            text=success_msg, 
            parse_mode=ParseMode.HTML
        )
        await update.message.reply_text(f"Order {order_id} has been marked as completed and the user has been notified.")
    except Exception as e:
        await update.message.reply_text(f"Order updated in DB, but failed to notify user: {e}")

async def pending_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admins = await database.get_admins()
    if user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
        
    orders = await database.get_pending_orders()
    if not orders:
        await update.message.reply_text("No pending orders!")
        return
        
    text = "📋 <b>Pending Orders:</b>\n\n"
    for o in orders:
        plan_name = config.PLANS.get(o[2], {}).get('name', o[2])
        text += f"📦 <b>Order:</b> <code>{o[0]}</code>\n"
        text += f"💎 <b>Plan:</b> {plan_name}\n"
        text += f"👤 <b>X User:</b> {o[1]}\n"
        text += f"🔗 <b>Tx Hash:</b> <code>{o[3]}</code>\n"
        text += f"✅ <b>Action:</b> <code>/complete {o[0]}</code>\n"
        text += "───────────────\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admins = await database.get_admins()
    if user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
        
    msg = update.message.text.partition(' ')[2].strip()
    users = await database.get_all_users()
    
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 <b>Broadcast</b>\n\n{msg}", parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            pass
            
    await update.message.reply_text(f"Broadcast sent to {sent}/{len(users)} users.")

async def setevent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admins = await database.get_admins()
    if user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
        
    if not context.args:
        await update.message.reply_text("Usage: /setevent <message>")
        return
        
    event_message = update.message.text.partition(' ')[2].strip()
    await database.set_setting("event_text", event_message)
    await update.message.reply_text("✅ Event text updated successfully!")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admins = await database.get_admins()
    if user.id not in admins:
        await update.message.reply_text("Unauthorized.")
        return
        
    all_users = list(reversed(await database.get_all_users()))
    total_users = len(all_users)
    
    per_page = 10
    total_pages = (total_users + per_page - 1) // per_page
    
    if total_users == 0:
        await update.message.reply_text("No users found.")
        return
        
    page = 0
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_users = all_users[start_idx:end_idx]
    
    text = f"👥 <b>Total Users: {total_users}</b> (Page {page+1}/{total_pages})\n\n"
    for u in page_users:
        username = f"@{u[1]}" if u[1] else "No Username"
        first_name = html.escape(u[2]) if u[2] else "Unknown"
        text += f"ID: <code>{u[0]}</code> | {username} | {first_name}\n"
        
    keyboard = keyboards.get_users_pagination_keyboard(page, total_pages)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

async def users_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    admins = await database.get_admins()
    if user.id not in admins:
        await query.edit_message_text("Unauthorized.")
        return
        
    page = int(query.data.split('_')[2])
    all_users = list(reversed(await database.get_all_users()))
    total_users = len(all_users)
    
    per_page = 10
    total_pages = (total_users + per_page - 1) // per_page
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_users = all_users[start_idx:end_idx]
    
    text = f"👥 <b>Total Users: {total_users}</b> (Page {page+1}/{total_pages})\n\n"
    for u in page_users:
        username = f"@{u[1]}" if u[1] else "No Username"
        first_name = html.escape(u[2]) if u[2] else "Unknown"
        text += f"ID: <code>{u[0]}</code> | {username} | {first_name}\n"
        
    keyboard = keyboards.get_users_pagination_keyboard(page, total_pages)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
