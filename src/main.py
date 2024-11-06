import logging
import uuid
import asyncio
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo, ReplyKeyboardMarkup, ReplyKeyboardRemove, constants
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, JobQueue
from storage import ReservationStorage, BikeStorage, UserStorage
from datetime import datetime, timedelta
import os

# Conversation stages and button labels
CHOOSING_FIELD, CHOOSE_PICKUP_TIME, CHOOSE_DURATION, CHOOSE_BIKE, CHOOSE_ASSOCIATION, SET_EMAIL = range(6)
DURATION_OPTIONS = ["30 minutes", "1 hour", "3 hours", "5 hours", "1 day"]

# Variables
bot_token = os.getenv("BOT_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the storage for reservations
reservation_storage = ReservationStorage()
bike_storage = BikeStorage()
user_storage = UserStorage()

def get_main_menu_text(user_data):
    text = f"<b>New Reservation:</b> \n" + get_reservation_text(user_data)
    return text

def get_reservation_text(user_data):
    bike_name = bike_storage.get_bike_by_id(user_data['bike'])['name'] if 'bike' in user_data else 'Not set'
    text = (
        f"Pickup Time: {user_data.get('pickup_time').strftime('%d-%m-%Y %H:%M') if 'pickup_time' in user_data else 'Not set'}\n"
        f"Duration: {user_data.get('duration', 'Not set')}\n"
        f"Bike: {bike_name}\n"
        f"Association: {user_data.get('association', 'Not set')}\n"
        f"Email: {user_data.get('email', 'Not set')}\n"
    )
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}, blablabla je prete des cargos.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Use /res to manage or create your reservations.",
    )

async def res_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all reservations for the user and a button to create a new reservation."""
    user_id = update.effective_user.id
    reservations = reservation_storage.list_reservations_for_user(user_id)

    # Create buttons for each reservation
    keyboard = [
        [InlineKeyboardButton(f"Reservation {n+1} - {res['start_datetime'].strftime('%d/%m/%Y')} ({res['status']})", callback_data=f"view_{res['reservation_id']}")] for n, res in enumerate(reservations)
    ]
    keyboard.append([InlineKeyboardButton("+ New Reservation...", callback_data="new_reservation")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if reservations:
        await update.message.reply_text("Here are your reservations:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You currently have no reservations.", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("view_"):
        print("Viewing reservation")
        reservation_id = int(query.data.split("_")[1])
        reservation = reservation_storage.get_reservation_by_id(reservation_id)
        reservation_details = "\n".join([f"{key}: {value}" for key, value in reservation.items()])
        await query.message.reply_text(f"Details for reservation {reservation_id}:\n{reservation_details}")
    
    elif query.data == "new_reservation":
        """Display the main menu for creating a new reservation."""
        if 'main_menu_message_id' in context.user_data:
            await cancel(update, context)
        context.user_data.clear()  # Clear any previous reservation data
        
        # Set user association and email if already saved
        user = user_storage.get_user_by_id(update.effective_user.id)
        if user:
            context.user_data['association'] = user['association']
            context.user_data['email'] = user['email']
        return await show_main_menu(update, context)
    
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the reservation input options with current values."""
    user_data = context.user_data
    text = get_main_menu_text(user_data)

    keyboard = [
        [InlineKeyboardButton(f"Choose Pickup Time{' ✔️' if 'pickup_time' in user_data else ''}", callback_data="choose_pickup_time")],
        [InlineKeyboardButton(f"Choose Duration{' ✔️' if 'duration' in user_data else ''}" , callback_data="choose_duration")],
        [InlineKeyboardButton(f"Choose Bike{' ✔️' if 'bike' in user_data else ''}", callback_data="choose_bike")],
        [InlineKeyboardButton(f"Set Association{' ✔️' if 'association' in user_data else ''}", callback_data="choose_association")],
        [InlineKeyboardButton(f"Set Email{' ✔️' if 'email' in user_data else ''}", callback_data="set_email")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_reservation")],
    ]
    if all(field in user_data for field in ["pickup_time", "duration", "bike", "association", "email"]):
        keyboard.append([InlineKeyboardButton("✅ Validate", callback_data="validate_reservation")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if 'main_menu_message_id' in user_data:
        await context.bot.edit_message_text(
            text=text,
            chat_id=update.effective_chat.id,
            message_id=user_data['main_menu_message_id'],
            reply_markup=reply_markup,
            parse_mode=constants.ParseMode.HTML
        )
    else:
        message = await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=constants.ParseMode.HTML)
        context.user_data['main_menu_message_id'] = message.message_id

    return CHOOSING_FIELD

async def handle_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Route to the correct handler based on the selected option."""
    query = update.callback_query
    await query.answer()

    if query.data == "choose_pickup_time":
        query_text = "Select%20pickup%20time"
        query_min = datetime.now().strftime('%Y-%m-%d')
        query_max = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        query_url = f"https://expented.github.io/tgdtp/?text={query_text}&min={query_min}&max={query_max}"
        
        await query.edit_message_text("Please select pickup time")
        msg = await query.message.reply_text("selecting...", reply_markup=ReplyKeyboardMarkup([
            [MenuButtonWebApp("Select Pickup Time", web_app=WebAppInfo(url=query_url))]
        ], resize_keyboard=True, one_time_keyboard=True))
        context.user_data['pickup_time_keyboard_message_id'] = msg.message_id
        return CHOOSE_PICKUP_TIME

    elif query.data == "choose_duration":
        # Provide duration options
        keyboard = [[InlineKeyboardButton(duration, callback_data=f"duration_{duration}")] for duration in DURATION_OPTIONS]
        await query.edit_message_text("Choose a duration:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSE_DURATION
    
    elif query.data == "choose_bike":
        # Provide bike options
        bikes = bike_storage.list_bikes()
        keyboard = [[InlineKeyboardButton(f"{bike['bike_id']} - {bike['name']} ({bike['size']})", callback_data=f"bike_{bike['bike_id']}")] for bike in bikes]
        await query.edit_message_text("Choose a bike:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSE_BIKE

    elif query.data == "choose_association":
        message = await query.edit_message_text("Please send the association name:")
        # context.user_data['association_message_id'] = message.message_id
        return CHOOSE_ASSOCIATION

    elif query.data == "set_email":
        message = await query.edit_message_text("Please send your email:")
        # context.user_data['email_message_id'] = message.message_id
        return SET_EMAIL
    
    elif query.data == "cancel_reservation":
        await cancel(update, context)
        return ConversationHandler.END
    
    elif query.data == "validate_reservation":
        # Validate and save the reservation if all fields are filled
        return await validate_reservation(update, context)

async def handle_web_app_pickup_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup time received from web app."""
    web_app_data = update.message.web_app_data.data.split("_")
    timestamp = int(web_app_data[0])
    start_datetime = datetime.fromtimestamp(timestamp / 1000)
    context.user_data['pickup_time'] = start_datetime
    
    # Delete the pickup keyboard message
    await context.bot.delete_message(update.effective_chat.id, context.user_data['pickup_time_keyboard_message_id'])
    
    return await show_main_menu(update, context)

async def set_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set duration from button selection."""
    query = update.callback_query
    await query.answer()
    context.user_data['duration'] = query.data.split("_")[1]
        
    # Delete the duration message
    # await query.message.delete()
    
    return await show_main_menu(update, context)

async def set_bike(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set bike name based on user input."""
    query = update.callback_query
    await query.answer()
    context.user_data['bike'] = int(query.data.split("_")[1])
    
    return await show_main_menu(update, context)

async def set_association(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set association name based on user input."""
    context.user_data['association'] = update.message.text
    
    # Delete the association message and user's message
    await update.message.delete()
    # await context.bot.delete_message(update.effective_chat.id, context.user_data['association_message_id'])
    return await show_main_menu(update, context)

async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set email based on user input."""
    context.user_data['email'] = update.message.text
    
    # Delete the email message and user's message
    await update.message.delete()
    # await context.bot.delete_message(update.effective_chat.id, context.user_data['email_message_id'])
    return await show_main_menu(update, context)

async def validate_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate reservation fields and save if all fields are filled."""
    required_fields = ["pickup_time", "duration", "bike", "association", "email"]
    missing_fields = [field for field in required_fields if field not in context.user_data]

    if missing_fields:
        warning_msg = await update.callback_query.message.reply_text(f"Missing fields: {', '.join(missing_fields)}")
        await asyncio.sleep(2)
        await warning_msg.delete()
        return CHOOSING_FIELD
    
    # Calculate end datetime
    duration_parts = context.user_data['duration'].split()
    if "minute" in duration_parts[1]:
        context.user_data['end_datetime'] = context.user_data['pickup_time'] + timedelta(minutes=int(duration_parts[0]))
    else:
        context.user_data['end_datetime'] = context.user_data['pickup_time'] + timedelta(hours=int(duration_parts[0]))

    # Save reservation
    reservation_storage.add_reservation(
        update.effective_user.id,
        update.effective_user.username,
        update.effective_user.first_name,
        update.effective_user.last_name,
        context.user_data['association'],
        context.user_data['email'],
        context.user_data['bike'],
        context.user_data['pickup_time'],
        context.user_data['end_datetime'],
        'accepted',
    )
    
    # Save user in db if not already saved
    if not user_storage.get_user_by_id(update.effective_user.id):
        user_storage.add_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name,
        context.user_data['association'],
            context.user_data['email'],
        )
    # Update association and email if user already exists
    else:
        user_storage.update_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name,
            context.user_data['association'],
            context.user_data['email'],
        )
    
    # Delete main menu message
    await context.bot.delete_message(update.effective_chat.id, context.user_data['main_menu_message_id'])
    
    # Validate and display reservation
    text = "Reservation created successfully!\n\n" + get_reservation_text(context.user_data)
    await update.callback_query.message.reply_text(text)
    
    context.user_data.clear()  # Clear data after saving
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await context.bot.send_message(update.effective_chat.id, "Reservation creation canceled.")
    await context.bot.delete_message(update.effective_chat.id, context.user_data['main_menu_message_id'])
        
    # Delete any messages that were sent during the conversation
    if context.user_data.get('pickup_time_keyboard_message_id'):
        await context.bot.delete_message(update.effective_chat.id, context.user_data['pickup_time_keyboard_message_id'])

    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
     # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("res", res_command))
    
    # Set up the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback, pattern='^new_reservation$')],
        states={
            CHOOSING_FIELD: [CallbackQueryHandler(handle_field_callback)],
            CHOOSE_PICKUP_TIME: [MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_pickup_data)],
            CHOOSE_DURATION: [CallbackQueryHandler(set_duration, pattern="^duration_")],
            CHOOSE_BIKE: [CallbackQueryHandler(set_bike, pattern="^bike_")],
            CHOOSE_ASSOCIATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_association)],
            SET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(handle_field_callback, pattern='^cancel_reservation$')],
    )
    application.add_handler(conv_handler)
    
    # Handle callback queries for reservation buttons
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == '__main__':
    main()
