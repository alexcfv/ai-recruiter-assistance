import asyncio
import os
from contextlib import AsyncExitStack

import chromadb
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import load_config
from db.sqlite.migrations import init_db
from db.vector_store import VectorStore
from embedding.embedder import MistralEmbedder
from ingestion.loader import ResumeLoader
from ingestion.parser import ResumeParser
from repositories.profile_repo import ProfileRepository
from services.explainer import LLMExplainer
from services.index_service import IndexService
from services.profile_builder import ProfileBuilder
from services.query_service import QueryService
from services.rate_limiter import RateLimiter
from services.profile_reranker import ProfileReranker
from services.analytics_service import AnalyticsService
from github.mcp_client import GitHubMCPClient
from github.collector import GitHubDataCollector
from github.analyzer import GitHubCodeAnalyzer

cfg = load_config()
init_db()

MISTRAL_API_KEY = cfg["api"]["mistral_key"]
TELEGRAM_BOT_TOKEN = cfg["api"]["telegram_key"]

rate_limiter = RateLimiter(min_interval=cfg["rate_limiter"]["min_interval"])

embedder = MistralEmbedder(MISTRAL_API_KEY, model=cfg["embedder"]["model"], timeout=cfg["embedder"]["timeout"], rate_limiter=rate_limiter)
explainer = LLMExplainer(MISTRAL_API_KEY, model=cfg["explainer"]["model"], timeout=cfg["explainer"]["timeout"], rate_limiter=rate_limiter)
loader = ResumeLoader()
parser = ResumeParser()
profile_repository = ProfileRepository()
profile_builder = ProfileBuilder(MISTRAL_API_KEY, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter)
profile_reranker = ProfileReranker(MISTRAL_API_KEY, model=cfg["reranker"]["model"], timeout=cfg["reranker"]["timeout"], rate_limiter=rate_limiter)
analytics_service = AnalyticsService(profile_builder)
client = chromadb.PersistentClient(path="./chromadb")
vector_store = VectorStore(client)

github_client = None
github_collector = None
github_analyzer = None
exit_stack = AsyncExitStack()

# Lazy initialization - will be done in post_init
_github_config = cfg.get("github", {})
_github_enabled = bool(_github_config and _github_config.get("mcp_server_command"))

if _github_enabled:
    try:
        github_client = GitHubMCPClient(_github_config["mcp_server_command"], _github_config.get("env", {}))
        github_collector = GitHubDataCollector(github_client)
        github_analyzer = GitHubCodeAnalyzer(MISTRAL_API_KEY, model=cfg["profile_builder"]["model"], timeout=cfg["profile_builder"]["timeout"], rate_limiter=rate_limiter)
        print("GitHub MCP client created (will be started in post_init)")
    except Exception as e:
        print(f"Failed to create GitHub MCP client: {e}")
        print("Continuing without GitHub analysis...")
        github_client = None
        github_collector = None
        github_analyzer = None

index_service = IndexService(embedder, loader, vector_store, profile_builder, profile_repository, github_collector, github_analyzer, parser)
query_service = QueryService(embedder, vector_store, explainer, profile_repository, profile_reranker, llm_client=profile_builder)

from handlers.states import MENU, SEARCHING, ANALYTICS
from handlers import menu, search, analytics


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
    if not context.args:
        await update.message.reply_text("Usage: /index /path/to/resumes")
        return

    dir_path = " ".join(context.args)

    if not os.path.isdir(dir_path):
        await update.message.reply_text(f"Directory not found: {dir_path}")
        return

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if vector_store.collection.count() == 0:
        await update.message.reply_text(
            "No indexed resumes yet. Use /index first"
        )
        return

    query = update.message.text
    await update.message.reply_text("Searching for candidates...")

    try:
        result = await query_service.search(query)

        if not result["candidates"]:
            await update.message.reply_text("No candidates found.")
            return

        await update.message.reply_text(f"Results for: {query}")
        for i, c in enumerate(result["candidates"], 1):
            text = f"<b>{i}. {c['source']}</b> (score: {c['score']:.4f})\n\n{c['explanation']}"
            
            profile = c.get("profile", {})
            github = profile.get("github_analysis")
            
            if github:
                if "error" in github:
                    text += f"\n\n <i>GitHub Analysis: {github['error']}</i>"
                elif github.get('overall_assessment') not in [None, "None"]:
                    text += (
                        f"\n\n<b>GitHub Analysis:</b>\n"
                        f"• <b>Quality:</b> {github.get('code_quality', 'N/A')}\n"
                        f"• <b>Depth:</b> {github.get('technical_depth', 'N/A')}\n"
                        f"• <b>Tech:</b> {', '.join(github.get('key_technologies', []))}\n"
                        f"• <b>Summary:</b> {github.get('overall_assessment', 'N/A')}"
                    )
            
        await update.message.reply_text(text, parse_mode="HTML")
        
        await update.message.reply_text("What would you like to do next?", reply_markup=get_main_menu_keyboard())
        return MENU
    except Exception as e:
        await update.message.reply_text(f"Search error: {e}", reply_markup=get_main_menu_keyboard())
        return MENU


async def post_init(application: Application):
    print("post_init called")
    
    # Store services in bot_data for handlers to access
    application.bot_data["index_service"] = index_service
    application.bot_data["query_service"] = query_service
    application.bot_data["analytics_service"] = analytics_service
    application.bot_data["vector_store"] = vector_store
    application.bot_data["github_enabled"] = _github_enabled

    if github_client:
        try:
            print("Starting GitHub MCP client...")
            await exit_stack.enter_async_context(github_client)
            print("GitHub MCP client started successfully")
        except Exception as e:
            print(f"Failed to start GitHub MCP client: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing without GitHub analysis...")
    else:
        print("GitHub client not configured, skipping")


async def post_shutdown(application: Application):
    print("post_shutdown called")
    await exit_stack.aclose()
    print("Exit stack closed")


def main():
    print("Bot started. Press Ctrl+C to stop.")
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", menu.start)],
        states={
            MENU: [
                MessageHandler(filters.Regex("^Find Candidate$"), menu.prepare_search),
                MessageHandler(filters.Regex("^Database Analytics$"), menu.prepare_analytics),
                MessageHandler(filters.Regex("^Status$"), menu.start),
            ],
            SEARCHING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Cancel$"), search.handle_message),
                MessageHandler(filters.Regex("^Cancel$"), menu.cancel),
            ],
    ANALYTICS: [
        MessageHandler(filters.Regex("^Cancel$"), menu.cancel),
        MessageHandler(filters.TEXT & ~filters.COMMAND, analytics.handle_analytics),
    ],
        },
        fallbacks=[CommandHandler("start", menu.start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("index", menu.index))
    
    app.run_polling()



if __name__ == "__main__":
    main()
