from telegram import Update
from telegram.ext import ContextTypes
from handlers.states import MENU
from handlers.menu import get_main_menu_keyboard

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_service = context.bot_data.get("query_service")
    vector_store = context.bot_data.get("vector_store")
    
    if not query_service or not vector_store:
        await update.message.reply_text("Search service not initialized.")
        return MENU

    if vector_store.collection.count() == 0:
        await update.message.reply_text(
            "No indexed resumes yet. Use /index first",
            reply_markup=get_main_menu_keyboard()
        )
        return MENU

    query = update.message.text
    await update.message.reply_text("Searching for candidates...")

    try:
        result = await query_service.search(query)

        if result.get("error"):
            await update.message.reply_text(result["error"], reply_markup=get_main_menu_keyboard())
            return MENU

        if not result["candidates"]:
            await update.message.reply_text("No candidates found.", reply_markup=get_main_menu_keyboard())
            return MENU

        await update.message.reply_text(f"Results for: {query}")
        for i, c in enumerate(result["candidates"], 1):
            text = f"<b>{i}. {c['source']}</b> (score: {c['score']:.4f})\n\n{c['explanation']}"
            
            await update.message.reply_text(text, parse_mode="HTML")
        
        await update.message.reply_text("What would you like to do next?", reply_markup=get_main_menu_keyboard())
        return MENU
    except Exception as e:
        await update.message.reply_text(f"Search error: {e}", reply_markup=get_main_menu_keyboard())
        return MENU
