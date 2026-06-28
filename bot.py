import asyncio
import os

import chromadb
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
client = chromadb.PersistentClient(path="./chromadb")
vector_store = VectorStore(client)

github_client = None
github_collector = None
github_analyzer = None

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
query_service = QueryService(embedder, vector_store, explainer, profile_repository, profile_reranker)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    github_status = "enabled" if github_collector else "disabled"
    await update.message.reply_text(
        "I'm an AI recruiter. I search through indexed resumes to find the best candidates.\n\n"
        "Commands:\n"
        "/index <path> — index a folder with PDF resumes\n"
        "Just send a message describing who you need — I'll find the best matches\n\n"
        f"GitHub analysis: {github_status}"
    )


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
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, index_service.index_folder, dir_path)
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
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, query_service.search, query)

        if not result["candidates"]:
            await update.message.reply_text("No candidates found.")
            return

        await update.message.reply_text(f"Results for: {query}")
        for i, c in enumerate(result["candidates"], 1):
            text = f"{i}. {c['source']} (score: {c['score']:.4f})\n\n{c['explanation']}"
            await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Search error: {e}")


async def post_init(application: Application):
    print("post_init called")
    if github_client:
        try:
            print("Starting GitHub MCP client...")
            # Add timeout to prevent blocking bot startup
            await asyncio.wait_for(github_client.__aenter__(), timeout=10.0)
            print("GitHub MCP client started successfully")
        except asyncio.TimeoutError:
            print("GitHub MCP client startup timed out, continuing without GitHub analysis")
        except Exception as e:
            print(f"Failed to start GitHub MCP client: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("GitHub client not configured, skipping")


async def post_shutdown(application: Application):
    print("post_shutdown called")
    if github_client:
        try:
            print("Stopping GitHub MCP client...")
            await asyncio.wait_for(github_client.__aexit__(None, None, None), timeout=5.0)
            print("GitHub MCP client stopped successfully")
        except asyncio.TimeoutError:
            print("GitHub MCP client shutdown timed out")
        except Exception as e:
            print(f"Failed to stop GitHub MCP client: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("GitHub client not configured, skipping")


def main():
    print("Bot started. Press Ctrl+C to stop.")
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("index", index))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()


if __name__ == "__main__":
    main()
