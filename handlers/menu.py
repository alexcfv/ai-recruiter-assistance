import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.states import MENU, SEARCHING

def get_main_menu_keyboard():
    keyboard = [["Find Candidate"], ["Status"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    github_enabled = context.bot_data.get("github_enabled", False)
    github_status = "enabled" if github_enabled else "disabled"
    
    message = (
        "I am an AI recruiter. I help you find the best candidates from the indexed resume database.\n\n"
        f"GitHub analysis: {github_status}\n\n"
        "/index <path> — index a folder with PDF resumes\n"
        "Click the button below to start searching."
    )
    await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())
    return MENU

async def prepare_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please enter the candidate description (e.g., 'Python developer with experience in asyncio'):",
        reply_markup=ReplyKeyboardMarkup([["Cancel"]], resize_keyboard=True)
    )
    return SEARCHING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Search cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    return MENU

async def index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index_service = context.bot_data.get("index_service")
    if not index_service:
        await update.message.reply_text("Index service not initialized.")
        return MENU

    if not context.args:
        await update.message.reply_text("Usage: /index /path/to/resumes")
        return MENU

    dir_path = " ".join(context.args)

    if not os.path.isdir(dir_path):
        await update.message.reply_text(f"Directory not found: {dir_path}")
        return MENU

    await update.message.reply_text("Indexing resumes... This may take a while.")

    try:        
        result = await index_service.index_folder(dir_path)
        await update.message.reply_text(
            f"Done!\n"
            f"Files: {result['total_files']}\n"
            f"New chunks: {result['new_chunks']}\n"
            f"New profiles: {len(result['new_profiles'])}"
        )
    except Exception as e:
        await update.message.reply_text(f"Indexing error: {e}")
    
    return MENU
