from telegram import Update
from telegram.ext import ContextTypes
from handlers.states import MENU
from handlers.menu import get_main_menu_keyboard

async def handle_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    analytics_service = context.bot_data.get("analytics_service")
    if not analytics_service:
        await update.message.reply_text("Analytics service not initialized.")
        return MENU

    question = update.message.text
    await update.message.reply_text("Analyzing database... Please wait.")

    try:
        answer = await analytics_service.answer_question(question)
        await update.message.reply_text(answer, reply_markup=get_main_menu_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=get_main_menu_keyboard())

    return MENU
