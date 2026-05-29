from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import config

def get_reply_main_menu():
    keyboard = [
        ["🛒 Place Order"],
        ["📦 Check Status", "📋 History"],
        ["ℹ️ Details", "💵 Prices"],
        ["🎉 Event"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_plans_menu():
    keyboard = []
    for plan_id, plan_data in config.PLANS.items():
        text = f"{plan_data['name']} - ${plan_data['price']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"select_{plan_id}")])
    return InlineKeyboardMarkup(keyboard)

def get_back_button():
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_order")]]
    return InlineKeyboardMarkup(keyboard)

def get_post_order_buttons():
    keyboard = [
        [InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{config.ADMIN_USERNAME.strip('@')}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_completion_buttons():
    keyboard = [
        [InlineKeyboardButton("💬 Contact Support", url=f"https://t.me/{config.ADMIN_USERNAME.strip('@')}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_setup_keyboard(selected_asset=None, selected_network=None):
    asset_row = []
    for asset in ["USDT", "USDC"]:
        text = f"✅ {asset}" if selected_asset == asset else asset
        asset_row.append(InlineKeyboardButton(text, callback_data=f"payment_asset_{asset}"))
    
    network_row = []
    for net in ["BSC", "Base", "Polygon", "Arbitrum"]:
        text = f"✅ {net}" if selected_network == net else net
        network_row.append(InlineKeyboardButton(text, callback_data=f"payment_network_{net}"))
    
    keyboard = [
        asset_row,
        network_row,
        [InlineKeyboardButton("Continue", callback_data="payment_continue")],
        [InlineKeyboardButton("⬅️ Back", callback_data="cancel_order"), InlineKeyboardButton("🏠 Home", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(keyboard)
