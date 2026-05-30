import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram import BotCommand
import config
import database
import handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application: Application):
    await database.init_db()
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot and open the menu"),
        BotCommand("pending", "Admin: View pending orders"),
        BotCommand("broadcast", "Admin: Send message to all users"),
        BotCommand("setevent", "Admin: Set event message"),
        BotCommand("users", "Admin: View all users"),
        BotCommand("stats", "Admin: View global analytics"),
    ])

import asyncio

def main():
    asyncio.set_event_loop(asyncio.new_event_loop())
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("setadmin", handlers.set_admin_command))
    application.add_handler(CommandHandler("complete", handlers.complete_order_command))
    application.add_handler(CommandHandler("pending", handlers.pending_orders_command))
    application.add_handler(CommandHandler("broadcast", handlers.broadcast_command))
    application.add_handler(CommandHandler("setevent", handlers.setevent_command))
    application.add_handler(CommandHandler("users", handlers.users_command))
    application.add_handler(CommandHandler("stats", handlers.stats_command))
    application.add_handler(CallbackQueryHandler(handlers.users_page_callback, pattern='^users_page_'))
    
    # Reply keyboard menu text handlers
    application.add_handler(MessageHandler(filters.Regex('^🛒 Place Order$'), handlers.menu_place_order))
    application.add_handler(MessageHandler(filters.Regex('^💵 Prices$'), handlers.menu_prices))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ Details$'), handlers.menu_details))
    application.add_handler(MessageHandler(filters.Regex('^🎉 Event$'), handlers.menu_event))
    application.add_handler(MessageHandler(filters.Regex('^📋 History$'), handlers.menu_history))
    
    # Check Status conversation handler
    status_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📦 Check Status$'), handlers.menu_check_status_start)],
        states={
            handlers.AWAITING_ORDER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), handlers.receive_order_id)]
        },
        fallbacks=[
            CommandHandler('cancel', handlers.cancel),
            MessageHandler(filters.Regex('^❌ Cancel$'), handlers.start),
            MessageHandler(filters.Regex('^🛒 Place Order$'), handlers.menu_place_order),
            MessageHandler(filters.Regex('^📦 Check Status$'), handlers.menu_check_status_start),
            MessageHandler(filters.Regex('^📋 History$'), handlers.menu_history),
            MessageHandler(filters.Regex('^ℹ️ Details$'), handlers.menu_details),
            MessageHandler(filters.Regex('^💵 Prices$'), handlers.menu_prices),
            MessageHandler(filters.Regex('^🎉 Event$'), handlers.menu_event)
        ],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )
    application.add_handler(status_handler)
    
    # Conversation handler for the ordering flow
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.select_plan, pattern='^select_')],
        states={
            handlers.AWAITING_X_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), handlers.receive_x_username)],
            handlers.AWAITING_PAYMENT_SELECTION: [CallbackQueryHandler(handlers.handle_payment_selection, pattern='^payment_')],
            handlers.AWAITING_TX_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^❌ Cancel$'), handlers.receive_tx_hash)]
        },
        fallbacks=[
            CommandHandler('cancel', handlers.cancel), 
            CallbackQueryHandler(handlers.cancel, pattern='^cancel_order$'),
            MessageHandler(filters.Regex('^❌ Cancel$'), handlers.start),
            # Menu buttons cancel current flow
            MessageHandler(filters.Regex('^🛒 Place Order$'), handlers.menu_place_order),
            MessageHandler(filters.Regex('^📦 Check Status$'), handlers.menu_check_status_start),
            MessageHandler(filters.Regex('^📋 History$'), handlers.menu_history),
            MessageHandler(filters.Regex('^ℹ️ Details$'), handlers.menu_details),
            MessageHandler(filters.Regex('^💵 Prices$'), handlers.menu_prices),
            MessageHandler(filters.Regex('^🎉 Event$'), handlers.menu_event)
        ]
    )
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
